"""Google Gemini LLM 实现"""
from typing import List, Optional, AsyncIterator
import time
from google import genai
from google.genai import types

from core.llm.base import (
    BaseLLM,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)


class GeminiLLM(BaseLLM):
    """Google Gemini LLM 实现"""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        **kwargs
    ):
        super().__init__(model_name, api_key, temperature, max_tokens, **kwargs)

        # 初始化 Gemini 客户端
        self.client = genai.Client(api_key=api_key)

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
            # 转换消息格式
            contents = self._convert_messages_to_gemini_format(messages)

            # 调用 Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature or self.temperature,
                    max_output_tokens=max_tokens or self.max_tokens,
                    **kwargs
                )
            )

            latency = time.time() - start_time

            return LLMResponse(
                content=response.text,
                model=self.model_name,
                provider="gemini",
                usage={
                    "prompt_tokens": 0,  # Gemini 不提供详细 token 统计
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                latency=latency,
                finish_reason="stop",
                cached=False,
            )

        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise LLMRateLimitError(f"Gemini rate limit: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise LLMTimeoutError(f"Gemini timeout: {error_msg}")
            else:
                raise LLMError(f"Gemini error: {error_msg}")

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[LLMStreamChunk]:
        """流式生成文本"""
        try:
            contents = self._convert_messages_to_gemini_format(messages)

            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature or self.temperature,
                    max_output_tokens=max_tokens or self.max_tokens,
                    **kwargs
                )
            )

            for chunk in stream:
                if chunk.text:
                    yield LLMStreamChunk(
                        content=chunk.text,
                        finish_reason=None,
                    )

        except Exception as e:
            raise LLMError(f"Gemini stream error: {str(e)}")

    async def embed(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """生成文本嵌入"""
        try:
            embeddings = []
            for text in texts:
                result = self.client.models.embed_content(
                    model="text-embedding-004",
                    contents=text,
                )
                embeddings.append(result.embeddings[0].values)
            return embeddings

        except Exception as e:
            raise LLMError(f"Gemini embedding error: {str(e)}")

    def _convert_messages_to_gemini_format(self, messages: List[LLMMessage]) -> str:
        """将消息转换为 Gemini 格式"""
        # Gemini 使用简单的文本格式
        # 将 system + user 消息合并
        system_msg = ""
        user_msgs = []

        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            elif msg.role == "user":
                user_msgs.append(msg.content)
            elif msg.role == "assistant":
                # 可以处理多轮对话
                pass

        # 合并系统提示和用户输入
        if system_msg:
            prompt = f"{system_msg}\n\n用户: {' '.join(user_msgs)}"
        else:
            prompt = ' '.join(user_msgs)

        return prompt
