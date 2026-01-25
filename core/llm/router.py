"""LLM 智能路由器"""
from typing import List, Optional, Literal, Dict
import asyncio
import logging

from config import settings, llm_config
from .base import BaseLLM, LLMMessage, LLMResponse, LLMError
from .providers.deepseek import DeepSeekLLM
from .providers.gemini import GeminiLLM
from .providers.openai import OpenAILLM
from .cache import LLMCache

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    LLM 智能路由器

    功能：
    1. 多模型管理（DeepSeek, Gemini, OpenAI）
    2. 智能路由（基于成本/速度/质量）
    3. 自动降级（主模型失败时切换备用）
    4. 成本追踪
    5. 缓存管理
    """

    def __init__(self):
        self.cache = LLMCache()
        self.providers: Dict[str, BaseLLM] = {}
        self._init_providers()

        # 成本追踪
        self.total_cost = 0.0
        self.request_count = 0

    def _init_providers(self):
        """初始化所有可用的 LLM 提供商"""

        # DeepSeek
        if settings.DEEPSEEK_API_KEY:
            try:
                self.providers["deepseek"] = DeepSeekLLM(
                    api_key=settings.DEEPSEEK_API_KEY,
                    model_name="deepseek-chat",
                )
                logger.info("✅ DeepSeek provider initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to init DeepSeek: {e}")

        # Gemini
        if settings.GEMINI_API_KEY:
            try:
                self.providers["gemini"] = GeminiLLM(
                    api_key=settings.GEMINI_API_KEY,
                    model_name="gemini-2.0-flash-exp",
                )
                logger.info("✅ Gemini provider initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to init Gemini: {e}")

        # OpenAI
        if settings.OPENAI_API_KEY:
            try:
                self.providers["openai"] = OpenAILLM(
                    api_key=settings.OPENAI_API_KEY,
                    model_name="gpt-4o-mini",
                )
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to init OpenAI: {e}")

        if not self.providers:
            raise ValueError("No LLM providers available! Please configure API keys.")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_preference: Optional[Literal["cost", "speed", "quality", "balanced"]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_cache: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        智能生成文本

        Args:
            prompt: 用户输入
            system_prompt: 系统提示
            model_preference: 模型偏好
            temperature: 温度参数
            max_tokens: 最大 token 数
            use_cache: 是否使用缓存
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应对象
        """
        # 1. 构建消息
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))

        # 2. 检查缓存
        if use_cache and llm_config.enable_cache:
            cache_key = self.cache.generate_key(messages, temperature, max_tokens)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info("✅ Cache hit")
                cached_response.cached = True
                return cached_response

        # 3. 选择最佳模型
        provider = self._select_provider(model_preference or llm_config.routing_strategy)

        # 4. 调用模型（带重试和降级）
        response = await self._generate_with_fallback(
            provider=provider,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # 5. 缓存响应
        if use_cache and llm_config.enable_cache:
            self.cache.set(cache_key, response, ttl=llm_config.cache_ttl)

        # 6. 记录成本
        self._track_cost(response)

        return response

    def _select_provider(
        self,
        strategy: Literal["cost", "speed", "quality", "balanced"]
    ) -> str:
        """
        根据策略选择最佳提供商

        策略说明：
        - cost: 成本最低（优先 DeepSeek）
        - speed: 速度最快（优先 DeepSeek）
        - quality: 质量最高（优先 Gemini）
        - balanced: 综合平衡（DeepSeek 性价比高）
        """
        if strategy == "cost":
            # DeepSeek 最便宜
            return "deepseek" if "deepseek" in self.providers else list(self.providers.keys())[0]

        elif strategy == "speed":
            # DeepSeek 速度快
            return "deepseek" if "deepseek" in self.providers else list(self.providers.keys())[0]

        elif strategy == "quality":
            # Gemini 质量高（但也可以用 DeepSeek Reasoner）
            return "gemini" if "gemini" in self.providers else list(self.providers.keys())[0]

        else:  # balanced
            # DeepSeek 性价比最高
            return "deepseek" if "deepseek" in self.providers else list(self.providers.keys())[0]

    async def _generate_with_fallback(
        self,
        provider: str,
        messages: List[LLMMessage],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> LLMResponse:
        """带降级策略的生成"""

        # 构建尝试顺序
        if llm_config.enable_fallback:
            try_order = [provider] + [
                p for p in llm_config.fallback_order
                if p != provider and p in self.providers
            ]
        else:
            try_order = [provider]

        last_error = None

        for attempt, provider_name in enumerate(try_order):
            try:
                logger.info(f"🔄 Attempt {attempt + 1}: Using {provider_name}")

                llm = self.providers[provider_name]
                response = await llm.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                if attempt > 0:
                    logger.warning(f"✅ Fallback successful: {provider} → {provider_name}")

                return response

            except Exception as e:
                last_error = e
                logger.error(f"❌ {provider_name} failed: {str(e)}")

                if attempt < len(try_order) - 1:
                    # 还有备选，继续重试
                    await asyncio.sleep(llm_config.retry_delay)
                    continue
                else:
                    # 所有备选都失败
                    break

        # 所有模型都失败
        raise LLMError(f"All providers failed. Last error: {last_error}")

    def _track_cost(self, response: LLMResponse):
        """追踪 API 成本"""
        model_config = llm_config.models.get(response.model)
        if model_config:
            cost = (response.usage["total_tokens"] / 1000) * model_config.cost_per_1k_tokens
            self.total_cost += cost
            self.request_count += 1

            logger.info(
                f"💰 Cost tracking: ${cost:.6f} | "
                f"Total: ${self.total_cost:.4f} | "
                f"Requests: {self.request_count}"
            )

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_cost": self.total_cost,
            "request_count": self.request_count,
            "avg_cost_per_request": self.total_cost / self.request_count if self.request_count > 0 else 0,
            "available_providers": list(self.providers.keys()),
            "cache_stats": self.cache.get_stats(),
        }


# 全局路由器实例
llm_router = LLMRouter()
