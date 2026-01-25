"""响应生成器"""
import logging
import random
from typing import Dict, Optional

from config import chatbot_config
from .nlu import NLUResult
from .state_tracker import dialogue_state_tracker

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    响应生成器

    功能：
    1. 生成自然语言响应
    2. 调用对应的 Agent 处理请求
    3. 个性化响应
    4. 多语言支持
    """

    def __init__(self):
        self.templates = chatbot_config.default_responses
        self._agents = None  # 延迟加载

    def _get_agents(self):
        """延迟加载 Agents，避免循环导入"""
        if self._agents is None:
            from core.agents.customer_service_agent import CustomerServiceAgent
            from core.agents.market_analysis_agent import MarketAnalysisAgent
            from core.agents.trading_assistant_agent import TradingAssistantAgent
            from core.agents.workflow_automation_agent import WorkflowAutomationAgent

            self._agents = {
                "customer_service": CustomerServiceAgent(),
                "market_analysis": MarketAnalysisAgent(),
                "trading_assistant": TradingAssistantAgent(),
                "workflow_automation": WorkflowAutomationAgent(),
            }
        return self._agents

    async def generate(
        self,
        nlu_result: NLUResult,
        session_id: str,
        agent_name: str,
        user_input: Optional[str] = None,
    ) -> Dict:
        """
        生成响应

        Args:
            nlu_result: NLU 结果
            session_id: 会话 ID
            agent_name: Agent 名称
            user_input: 原始用户输入

        Returns:
            Dict: 响应内容和元数据
        """
        intent = nlu_result.intent.name

        # 特殊意图的快速响应
        if intent == "greeting":
            return self._generate_greeting_response(nlu_result.language)

        # 调用对应的 Agent 处理
        return await self._call_agent(
            agent_name=agent_name,
            user_input=user_input or "",
            nlu_result=nlu_result,
            session_id=session_id
        )

    async def _call_agent(
        self,
        agent_name: str,
        user_input: str,
        nlu_result: NLUResult,
        session_id: str
    ) -> Dict:
        """调用对应的 Agent 处理请求"""
        agents = self._get_agents()

        # 获取对应的 Agent
        agent = agents.get(agent_name)
        if not agent:
            logger.warning(f"Agent not found: {agent_name}, falling back to customer_service")
            agent = agents.get("customer_service")

        # 准备实体和上下文
        entities = {e.type: e.value for e in nlu_result.entities}

        # 从意图中提取的实体也加入
        if nlu_result.intent.entities:
            entities.update(nlu_result.intent.entities)

        # 获取对话历史（最近10轮）
        conversation_history = dialogue_state_tracker.get_context(session_id, last_n=20)

        context = {
            "session_id": session_id,
            "language": nlu_result.language,
            "confidence": nlu_result.confidence,
            "conversation_history": conversation_history,  # 添加对话历史
        }

        try:
            # 调用 Agent 处理
            logger.info(f"🤖 Calling agent: {agent_name} for intent: {nlu_result.intent.name}")

            response = await agent.process(
                user_input=user_input,
                intent=nlu_result.intent.name,
                entities=entities,
                context=context
            )

            return {
                "content": response.content,
                "type": "text",
                "agent": response.agent_name,
                "confidence": response.confidence,
                "metadata": response.metadata,
                "data": response.data,
                "suggested_actions": response.suggested_actions,
                "requires_confirmation": response.requires_user_confirmation,
            }

        except Exception as e:
            logger.error(f"Agent error: {e}")
            return self.generate_error_response(nlu_result.language)

    def _generate_greeting_response(self, language: str) -> Dict:
        """生成问候响应"""
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

        return {
            "content": content,
            "type": "text",
            "agent": "customer_service",
        }

    def generate_error_response(self, language: str = "zh-CN") -> Dict:
        """生成错误响应"""
        responses = self.templates.get("error", [])
        if responses:
            content = random.choice(responses)
        else:
            content = "抱歉，系统出现了一点问题，请稍后重试。"

        return {
            "content": content,
            "type": "error",
        }
