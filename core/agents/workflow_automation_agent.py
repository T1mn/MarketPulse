"""工作流自动化 Agent"""
import logging
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from core.llm.router import llm_router

logger = logging.getLogger(__name__)


class WorkflowAutomationAgent(BaseAgent):
    """
    工作流自动化 Agent

    职责：
    1. 定时提醒和通知
    2. 价格监控和告警
    3. 自动化交易策略
    4. 定期报告生成
    5. 个性化推送设置
    """

    def __init__(self):
        super().__init__(
            name="workflow_automation",
            description="工作流自动化专家，设置定时任务、监控告警、自动化策略"
        )

        self.supported_intents = {
            "workflow_automation",
        }

        # 任务存储（实际应该用数据库）
        self.tasks = {}

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
        logger.info(f"⚙️ WorkflowAutomationAgent processing: {intent}")

        task_type = entities.get("task_type", "").lower()

        # 根据任务类型处理
        if "提醒" in task_type or "通知" in task_type:
            return await self._handle_reminder(user_input, entities, context)

        elif "监控" in task_type or "告警" in task_type:
            return await self._handle_alert(user_input, entities, context)

        elif "定投" in task_type or "自动" in task_type:
            return await self._handle_auto_invest(user_input, entities, context)

        else:
            return await self._handle_generic_automation(user_input, entities, context)

    async def _handle_reminder(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理提醒设置"""
        time_entity = entities.get("time", "每天早上9点")

        # 解析时间
        # TODO: 使用更专业的时间解析库
        reminder_time = time_entity

        content = f"""✅ 提醒已设置

**提醒时间：** {reminder_time}
**提醒内容：** 市场开盘提醒

我会在 {reminder_time} 推送以下信息：
- 📊 市场开盘概况
- 📰 重要财经新闻
- 💼 您的持仓快报
- 📈 当日关注重点

需要调整提醒内容或时间吗？"""

        # 保存任务（简化）
        task_id = f"reminder_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "type": "reminder",
            "time": reminder_time,
            "user_id": context.get("user_id"),
        }

        return self._create_response(
            content=content,
            confidence=1.0,
            metadata={
                "task_id": task_id,
                "task_type": "reminder",
                "schedule": reminder_time,
            },
            suggested_actions=[
                {"action": "modify_reminder", "label": "修改提醒"},
                {"action": "view_all_tasks", "label": "查看所有任务"},
            ]
        )

    async def _handle_alert(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理价格告警"""
        asset = entities.get("asset", "未知资产")
        price = entities.get("price", "未指定价格")

        content = f"""🔔 价格告警已设置

**监控资产：** {asset}
**触发条件：** 价格 {price}

告警方式：
- 📱 App 推送通知
- 📧 邮件提醒
- 💬 微信消息

告警将在价格达到设定条件时立即发送，帮助您把握交易时机。

需要设置更多告警条件吗？"""

        # 保存告警任务
        task_id = f"alert_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "type": "price_alert",
            "asset": asset,
            "price": price,
            "user_id": context.get("user_id"),
        }

        return self._create_response(
            content=content,
            confidence=1.0,
            metadata={
                "task_id": task_id,
                "task_type": "price_alert",
                "asset": asset,
                "trigger_price": price,
            },
            suggested_actions=[
                {"action": "add_more_alerts", "label": "添加更多告警"},
                {"action": "manage_alerts", "label": "管理告警"},
            ]
        )

    async def _handle_auto_invest(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理自动定投"""
        asset = entities.get("asset", "未指定资产")
        quantity = entities.get("quantity", "未指定金额")
        time_entity = entities.get("time", "每月1日")

        content = f"""📅 定投计划已创建

**投资标的：** {asset}
**定投金额：** {quantity}
**执行频率：** {time_entity}

**定投优势：**
- 分散风险，平滑成本
- 纪律投资，避免追涨杀跌
- 长期持有，享受复利

⚠️ **风险提示：**
定投不保证盈利，请根据自身风险承受能力合理安排。

确认开始定投吗？"""

        task_id = f"auto_invest_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "type": "auto_invest",
            "asset": asset,
            "amount": quantity,
            "frequency": time_entity,
            "user_id": context.get("user_id"),
            "status": "pending_confirmation",
        }

        return self._create_response(
            content=content,
            confidence=0.95,
            requires_user_confirmation=True,
            metadata={
                "task_id": task_id,
                "task_type": "auto_invest",
                "details": {
                    "asset": asset,
                    "amount": quantity,
                    "frequency": time_entity,
                }
            },
            suggested_actions=[
                {"action": "confirm_auto_invest", "label": "确认开始"},
                {"action": "modify_plan", "label": "修改计划"},
                {"action": "cancel", "label": "取消"},
            ]
        )

    async def _handle_generic_automation(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理通用自动化请求"""
        # 使用 LLM 理解和建议
        system_prompt = """你是一个工作流自动化专家。

用户想要设置某种自动化任务，请：
1. 理解用户需求
2. 提供可行的自动化方案
3. 说明具体执行方式
4. 提示注意事项

保持专业、清晰、可操作。"""

        try:
            response = await llm_router.generate(
                prompt=f"用户需求：{user_input}",
                system_prompt=system_prompt,
                model_preference="balanced",
                temperature=0.4,
                max_tokens=800,
            )

            return self._create_response(
                content=response.content,
                confidence=0.8,
                metadata={"automation_type": "custom"}
            )

        except Exception as e:
            logger.error(f"Automation error: {e}")
            return self._create_response(
                content="抱歉，我现在无法设置这个自动化任务。请提供更多细节。",
                confidence=0.5
            )
