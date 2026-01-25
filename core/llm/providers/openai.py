"""OpenAI LLM 实现"""
from typing import List, Optional, AsyncIterator
import time
from openai import AsyncOpenAI

from ..base import (
    BaseLLM,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class OpenAILLM(BaseLLM):
    """OpenAI LLM 实现"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        api_base: str = "https://api.openai.com/v1",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        super().__init__(model_name, api_key, temperature, max_tokens, **kwargs)

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=self._messages_to_dict(messages),
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=False,
                **kwargs
            )

            latency = time.time() - start_time

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                latency=latency,
                finish_reason=response.choices[0].finish_reason,
                cached=False,
            )

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                raise LLMRateLimitError(f"OpenAI rate limit: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise LLMTimeoutError(f"OpenAI timeout: {error_msg}")
            else:
                raise LLMError(f"OpenAI error: {error_msg}")

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[LLMStreamChunk]:
        """流式生成文本"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=self._messages_to_dict(messages),
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield LLMStreamChunk(
                        content=chunk.choices[0].delta.content,
                        finish_reason=chunk.choices[0].finish_reason,
                    )

        except Exception as e:
            raise LLMError(f"OpenAI stream error: {str(e)}")

    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
        **kwargs
    ) -> List[List[float]]:
        """生成文本嵌入"""
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=texts,
                **kwargs
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise LLMError(f"OpenAI embedding error: {str(e)}")
