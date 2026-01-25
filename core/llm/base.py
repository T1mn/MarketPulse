"""LLM 基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass
import time


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict] = None


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    latency: float  # 响应延迟（秒）
    finish_reason: str
    cached: bool = False


@dataclass
class LLMStreamChunk:
    """流式响应块"""
    content: str
    finish_reason: Optional[str] = None


class BaseLLM(ABC):
    """LLM 基类 - 所有 LLM 提供商必须实现此接口"""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应对象
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        流式生成文本

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数

        Yields:
            LLMStreamChunk: 流式响应块
        """
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        生成文本嵌入

        Args:
            texts: 文本列表
            **kwargs: 其他参数

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        pass

    def _messages_to_dict(self, messages: List[LLMMessage]) -> List[Dict]:
        """将 LLMMessage 转换为字典格式"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"function_call": msg.function_call} if msg.function_call else {}),
            }
            for msg in messages
        ]

    def _calculate_cost(self, usage: Dict[str, int], cost_per_1k: float) -> float:
        """计算 API 调用成本"""
        total_tokens = usage.get("total_tokens", 0)
        return (total_tokens / 1000) * cost_per_1k


class LLMError(Exception):
    """LLM 相关错误"""
    pass


class LLMRateLimitError(LLMError):
    """速率限制错误"""
    pass


class LLMTimeoutError(LLMError):
    """超时错误"""
    pass


class LLMInvalidRequestError(LLMError):
    """无效请求错误"""
    pass
