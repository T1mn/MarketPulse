"""客服 Agent"""
import logging
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from core.llm.router import llm_router
from core.llm.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)


class CustomerServiceAgent(BaseAgent):
    """
    客服 Agent

    职责：
    1. 处理用户咨询和问题
    2. 提供使用帮助
    3. FAQ 查询
    4. 问候和闲聊
    5. 引导到其他 Agent
    """

    def __init__(self):
        super().__init__(
            name="customer_service",
            description="客服专员，处理用户咨询、FAQ、使用帮助"
        )

        # 可以处理的意图
        self.supported_intents = {
            "customer_service",
            "greeting",
            "chitchat",
        }

    async def can_handle(self, intent: str) -> bool:
        """判断是否可以处理该意图"""
        return intent in self.supported_intents

    async def process(
        self,
        user_input: str,
        intent: str,
        entities: Dict[str, Any],
        context: Dict[str, Any],
        **kwargs
    ) -> AgentResponse:
        """处理用户请求"""
        logger.info(f"👨‍💼 CustomerServiceAgent processing: {intent}")

        # 根据不同意图处理
        if intent == "greeting":
            return await self._handle_greeting(user_input, context)

        elif intent == "chitchat":
            return await self._handle_chitchat(user_input, context)

        elif intent == "customer_service":
            return await self._handle_customer_service(user_input, entities, context)

        else:
            return self._create_response(
                content="抱歉，我无法处理这个请求。",
                confidence=0.5
            )

    async def _handle_greeting(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理问候"""
        # 根据时间返回不同的问候
        from datetime import datetime
        hour = datetime.now().hour

        if 5 <= hour < 12:
            greeting = "早上好"
        elif 12 <= hour < 18:
            greeting = "下午好"
        else:
            greeting = "晚上好"

        content = f"{greeting}！我是 MarketPulse AI，您的金融智能助手。\n\n我可以帮您：\n" \
                  "📊 查询市场行情和分析\n" \
                  "📰 解读金融新闻\n" \
                  "💼 提供交易建议\n" \
                  "⚙️ 设置自动化任务\n\n" \
                  "请问有什么可以帮您的？"

        return self._create_response(
            content=content,
            confidence=1.0,
            metadata={"greeting_type": "time_based"}
        )

    async def _handle_chitchat(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理闲聊"""
        # 使用 LLM 生成友好的回复
        system_prompt = """你是 MarketPulse AI 的客服助手，友好、专业、有趣。
用户在和你闲聊，请给出简短、友好的回复（不超过50字）。
适当引导用户回到金融话题。"""

        try:
            # 获取对话历史
            conversation_history = context.get("conversation_history", [])

            response = await llm_router.generate_with_history(
                conversation_history=conversation_history,
                user_input=user_input,
                system_prompt=system_prompt,
                model_preference="speed",
                temperature=0.8,  # 稍高温度增加趣味性
                max_tokens=200,
            )

            return self._create_response(
                content=response.content,
                confidence=0.9,
                metadata={"type": "chitchat"}
            )

        except Exception as e:
            logger.error(f"Chitchat error: {e}")
            return self._create_response(
                content="😊 很高兴和您聊天！有什么金融问题需要帮助吗？",
                confidence=0.7
            )

    async def _handle_customer_service(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理客服咨询"""
        # TODO: 集成 RAG 从知识库检索答案
        # 现在先使用 LLM 生成

        # 构建 Prompt（使用 PromptManager）
        # 这里简化处理，直接调用 LLM
        system_prompt = """你是 MarketPulse AI 的客服专员。

常见问题：
1. 如何充值？- 支持银行卡、支付宝、微信支付
2. 如何修改密码？- 进入"设置"->"安全"->"修改密码"
3. 交易费用？- 股票交易 0.1%，加密货币 0.05%
4. 客服时间？- 7x24 小时在线服务

请简洁、准确地回答用户问题。如果不确定，建议联系人工客服。
注意：你可以参考之前的对话历史来理解用户的问题上下文。"""

        try:
            # 获取对话历史
            conversation_history = context.get("conversation_history", [])

            response = await llm_router.generate_with_history(
                conversation_history=conversation_history,
                user_input=user_input,
                system_prompt=system_prompt,
                model_preference="balanced",
                temperature=0.3,
                max_tokens=500,
            )

            return self._create_response(
                content=response.content,
                confidence=0.85,
                metadata={"type": "faq"}
            )

        except Exception as e:
            logger.error(f"Customer service error: {e}")
            return self._create_response(
                content="抱歉，我现在无法回答这个问题。请联系人工客服获取帮助。",
                confidence=0.5
            )
