"""对话管理器"""
import logging
from typing import Dict, Optional

from .nlu import NLUEngine, NLUResult
from .state_tracker import DialogueStateTracker, dialogue_state_tracker
from .response_generator import ResponseGenerator
from config import chatbot_config

logger = logging.getLogger(__name__)


class DialogueManager:
    """
    对话管理器

    核心职责：
    1. 协调 NLU、状态追踪、响应生成
    2. 管理对话流程
    3. 处理多轮对话
    4. 路由到合适的 Agent
    """

    def __init__(self):
        self.nlu = NLUEngine()
        self.state_tracker = dialogue_state_tracker
        self.response_generator = ResponseGenerator()

    async def process_message(
        self,
        user_input: str,
        session_id: str,
        user_id: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        处理用户消息

        Args:
            user_input: 用户输入
            session_id: 会话 ID
            user_id: 用户 ID
            language: 语言

        Returns:
            Dict: 包含响应和元数据
        """
        logger.info(f"💬 Processing message from {user_id}: {user_input[:50]}...")

        # 1. 获取或创建对话状态
        state = self.state_tracker.get_or_create_state(session_id, user_id)

        # 2. NLU 理解
        context = self.state_tracker.get_context(session_id, last_n=5)
        nlu_result = await self.nlu.understand(
            user_input=user_input,
            context=context,
            language=language
        )

        # 3. 检查置信度
        if nlu_result.confidence < chatbot_config.intent_confidence_threshold:
            logger.warning(
                f"⚠️ Low confidence: {nlu_result.confidence:.2f}, "
                f"using clarification"
            )
            return await self._handle_low_confidence(
                nlu_result, session_id, user_input
            )

        # 4. 更新对话状态
        entities_dict = {
            entity.type: entity.value
            for entity in nlu_result.entities
        }
        self.state_tracker.update_state(
            session_id=session_id,
            intent=nlu_result.intent.name,
            entities=entities_dict,
            user_message=user_input,
        )

        # 5. 确定处理的 Agent
        agent_name = self._route_to_agent(nlu_result.intent.name)

        # 6. 生成响应
        response = await self.response_generator.generate(
            nlu_result=nlu_result,
            session_id=session_id,
            agent_name=agent_name,
            user_input=user_input,
        )

        # 7. 更新状态（添加 assistant 消息）
        self.state_tracker.update_state(
            session_id=session_id,
            assistant_message=response["content"],
        )

        # 8. 返回结果
        return {
            "content": response["content"],
            "intent": nlu_result.intent.name,
            "confidence": nlu_result.confidence,
            "language": nlu_result.language,
            "agent": agent_name,
            "entities": entities_dict,
            "session_id": session_id,
            "turn_count": state.turn_count,
        }

    async def _handle_low_confidence(
        self,
        nlu_result: NLUResult,
        session_id: str,
        user_input: str
    ) -> Dict:
        """处理低置信度情况"""

        # 使用澄清策略
        clarification = chatbot_config.default_responses["clarification"][0]

        # 如果有实体，尝试澄清
        if nlu_result.entities:
            asset = next(
                (e.value for e in nlu_result.entities if e.type == "asset"),
                None
            )
            if asset:
                clarification = clarification.format(
                    asset=asset,
                    intent=nlu_result.intent.name
                )

        return {
            "content": clarification,
            "intent": "clarification",
            "confidence": nlu_result.confidence,
            "language": nlu_result.language,
            "agent": "customer_service",
            "entities": {},
            "session_id": session_id,
            "requires_clarification": True,
        }

    def _route_to_agent(self, intent: str) -> str:
        """路由到合适的 Agent"""
        intent_config = chatbot_config.intents.get(intent)
        if intent_config:
            return intent_config.agent

        # 默认路由到客服
        return "customer_service"

    def reset_session(self, session_id: str):
        """重置会话"""
        self.state_tracker.delete_state(session_id)
        logger.info(f"🔄 Session reset: {session_id}")

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        state = self.state_tracker.states.get(session_id)
        if state:
            return state.to_dict()
        return None


# 全局对话管理器实例
dialogue_manager = DialogueManager()
