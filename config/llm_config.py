"""LLM 配置"""
from typing import Dict, Literal
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """单个模型配置"""
    name: str
    provider: str
    api_base: str = ""
    cost_per_1k_tokens: float = 0.0
    avg_latency_ms: float = 1000.0
    quality_score: float = 80.0  # 0-100
    max_tokens: int = 4096
    temperature: float = 0.7
    supports_streaming: bool = True
    supports_function_calling: bool = True


class LLMConfig(BaseModel):
    """LLM 总体配置"""

    # 默认使用的 AI 提供商
    default_provider: Literal["deepseek", "gemini", "openai", "local"] = "deepseek"

    # 是否启用降级策略
    enable_fallback: bool = True

    # 降级顺序
    fallback_order: list[str] = ["deepseek", "gemini", "openai"]

    # 路由策略: cost(成本优先), speed(速度优先), quality(质量优先), balanced(平衡)
    routing_strategy: Literal["cost", "speed", "quality", "balanced"] = "balanced"

    # 是否启用缓存
    enable_cache: bool = True
    cache_ttl: int = 3600  # 缓存有效期（秒）

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0

    # 超时配置
    timeout: int = 60  # 秒

    # 模型配置
    models: Dict[str, ModelConfig] = {
        "deepseek-chat": ModelConfig(
            name="deepseek-chat",
            provider="deepseek",
            api_base="https://api.deepseek.com",
            cost_per_1k_tokens=0.0014,  # $0.14/M 输入, $0.28/M 输出
            avg_latency_ms=800,
            quality_score=92,
            max_tokens=8192,
            temperature=0.7,
            supports_streaming=True,
            supports_function_calling=True,
        ),
        "deepseek-reasoner": ModelConfig(
            name="deepseek-reasoner",
            provider="deepseek",
            api_base="https://api.deepseek.com",
            cost_per_1k_tokens=0.55,  # 推理模型更贵
            avg_latency_ms=2000,
            quality_score=96,
            max_tokens=8192,
            temperature=0.7,
            supports_streaming=True,
            supports_function_calling=False,
        ),
        "gemini-2.0-flash": ModelConfig(
            name="gemini-2.0-flash-exp",
            provider="gemini",
            api_base="",
            cost_per_1k_tokens=0.075,  # 估算
            avg_latency_ms=1200,
            quality_score=88,
            max_tokens=8192,
            temperature=0.7,
            supports_streaming=True,
            supports_function_calling=True,
        ),
        "gemini-1.5-flash": ModelConfig(
            name="gemini-1.5-flash",
            provider="gemini",
            api_base="",
            cost_per_1k_tokens=0.075,
            avg_latency_ms=1000,
            quality_score=85,
            max_tokens=8192,
            temperature=0.7,
            supports_streaming=True,
            supports_function_calling=True,
        ),
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini",
            provider="openai",
            api_base="https://api.openai.com/v1",
            cost_per_1k_tokens=0.15,
            avg_latency_ms=1500,
            quality_score=90,
            max_tokens=16384,
            temperature=0.7,
            supports_streaming=True,
            supports_function_calling=True,
        ),
    }

    # 场景化模型选择
    scenario_models: Dict[str, str] = {
        "nlu": "deepseek-chat",  # 意图识别使用快速模型
        "dialogue": "deepseek-chat",  # 对话生成
        "analysis": "deepseek-chat",  # 市场分析
        "reasoning": "deepseek-reasoner",  # 复杂推理
        "summary": "gemini-1.5-flash",  # 摘要生成
        "translation": "deepseek-chat",  # 翻译
    }

    # Prompt 配置
    system_prompt_template: str = """你是 MarketPulse AI，一个专业的金融智能助手。

你的核心能力：
1. 实时市场分析和投资建议
2. 金融新闻解读和趋势预测
3. 交易策略辅助和风险评估
4. 多语言客户服务支持

交互原则：
- 专业、准确、负责任
- 用户友好的语言表达
- 基于数据和事实的分析
- 明确风险提示

当前语言：{language}
当前时间：{timestamp}
"""


# 全局 LLM 配置实例
llm_config = LLMConfig()
