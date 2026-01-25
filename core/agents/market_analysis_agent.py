"""市场分析 Agent"""
import logging
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from core.llm.router import llm_router
from services.market_data_service import market_data_service

logger = logging.getLogger(__name__)


class MarketAnalysisAgent(BaseAgent):
    """
    市场分析 Agent

    职责：
    1. 市场行情查询
    2. 金融新闻分析
    3. 趋势预测
    4. 投资建议（仅建议，不执行交易）
    5. 技术指标分析
    """

    def __init__(self):
        super().__init__(
            name="market_analysis",
            description="市场分析专家，提供行情查询、新闻解读、趋势分析"
        )

        self.supported_intents = {
            "market_query",
            "news_analysis",
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
        logger.info(f"📊 MarketAnalysisAgent processing: {intent}")

        if intent == "market_query":
            return await self._handle_market_query(user_input, entities, context)

        elif intent == "news_analysis":
            return await self._handle_news_analysis(user_input, entities, context)

        else:
            return self._create_response(
                content="抱歉，我无法处理这个市场分析请求。",
                confidence=0.5
            )

    async def _handle_market_query(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理市场查询"""
        asset = entities.get("asset", "市场")

        # 使用 Yahoo Finance 获取实时市场数据
        market_data = await self._fetch_market_data(asset)

        # 格式化市场数据用于显示和 LLM 分析
        if market_data.get("success"):
            formatted_data = market_data_service.format_quote_message(market_data)
            data_for_llm = self._format_data_for_llm(market_data)
        else:
            formatted_data = f"无法获取 {asset} 的数据"
            data_for_llm = f"无法获取 {asset} 的实时数据"

        # 使用 LLM 分析市场数据
        system_prompt = f"""你是一位资深的金融分析师。

用户查询：{asset} 的市场行情

市场数据：
{data_for_llm}

请提供专业的分析，包括：
1. 当前价格和变化解读
2. 市场趋势（短期/中期判断）
3. 关键支撑位和阻力位（如果适用）
4. 投资建议（做多/做空/观望）
5. 风险提示

保持专业、客观，突出关键信息。回复控制在 200 字以内。
注意：你可以参考之前的对话历史来理解用户的问题上下文。"""

        try:
            # 获取对话历史
            conversation_history = context.get("conversation_history", [])

            response = await llm_router.generate_with_history(
                conversation_history=conversation_history,
                user_input=user_input,
                system_prompt=system_prompt,
                model_preference="balanced",
                temperature=0.4,
                max_tokens=1000,
            )

            # 组合市场数据和 AI 分析
            if market_data.get("success"):
                full_content = f"""{formatted_data}

---
📝 **AI 分析：**
{response.content}

⚠️ 风险提示：以上分析仅供参考，不构成投资建议。"""
            else:
                full_content = response.content

            return self._create_response(
                content=full_content,
                confidence=0.9,
                metadata={
                    "asset": asset,
                    "market_data": market_data,
                    "analysis_type": "market_query"
                },
                data={
                    "asset": asset,
                    "current_price": market_data.get("current_price"),
                    "change_percent": market_data.get("change_percent"),
                }
            )

        except Exception as e:
            logger.error(f"Market query error: {e}")
            # 如果 LLM 失败但有市场数据，仍返回数据
            if market_data.get("success"):
                return self._create_response(
                    content=formatted_data + "\n\n（AI 分析暂时不可用）",
                    confidence=0.7,
                    data=market_data
                )
            return self._create_response(
                content=f"抱歉，暂时无法获取 {asset} 的市场数据，请稍后重试。",
                confidence=0.3
            )

    async def _handle_news_analysis(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理新闻分析"""
        # TODO: 集成 RAG 从新闻库检索相关新闻
        # TODO: 调用原有的 news_aggregator 和 ai_analyzer

        system_prompt = """你是一位专业的金融新闻分析师。

请分析最新的金融新闻，提供：
1. 新闻要点总结
2. 市场影响分析
3. 受影响的资产和行业
4. 投资机会和风险
5. 建议关注的后续发展

保持客观、准确、及时。
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
                max_tokens=1200,
            )

            return self._create_response(
                content=response.content,
                confidence=0.85,
                metadata={"analysis_type": "news_analysis"},
                suggested_actions=[
                    {"action": "subscribe_news", "label": "订阅相关新闻推送"},
                    {"action": "set_alert", "label": "设置价格提醒"},
                ]
            )

        except Exception as e:
            logger.error(f"News analysis error: {e}")
            return self._create_response(
                content="抱歉，暂时无法分析新闻，请稍后重试。",
                confidence=0.3
            )

    async def _fetch_market_data(self, asset: str) -> Dict[str, Any]:
        """获取市场数据（使用 Yahoo Finance）"""
        try:
            data = await market_data_service.get_quote(asset)
            return data
        except Exception as e:
            logger.error(f"Error fetching market data for {asset}: {e}")
            return {
                "symbol": asset,
                "error": str(e),
                "success": False
            }

    def _format_data_for_llm(self, data: Dict[str, Any]) -> str:
        """格式化市场数据供 LLM 分析"""
        if not data.get("success"):
            return "无法获取市场数据"

        lines = [
            f"资产: {data.get('name', data.get('symbol'))} ({data.get('symbol')})",
            f"类型: {data.get('asset_type', 'stock')}",
            f"当前价格: {data.get('current_price')} {data.get('currency', 'USD')}",
            f"今日涨跌: {data.get('change'):+.2f} ({data.get('change_percent'):+.2f}%)",
        ]

        if data.get("day_high") and data.get("day_low"):
            lines.append(f"今日区间: {data.get('day_low')} - {data.get('day_high')}")

        if data.get("week_52_high") and data.get("week_52_low"):
            lines.append(f"52周区间: {data.get('week_52_low')} - {data.get('week_52_high')}")

        if data.get("market_cap"):
            cap = data.get("market_cap")
            if cap >= 1e12:
                cap_str = f"{cap/1e12:.2f}万亿"
            elif cap >= 1e8:
                cap_str = f"{cap/1e8:.2f}亿"
            else:
                cap_str = f"{cap:,.0f}"
            lines.append(f"市值: {cap_str} {data.get('currency', 'USD')}")

        if data.get("pe_ratio"):
            lines.append(f"市盈率: {data.get('pe_ratio'):.2f}")

        if data.get("volume"):
            lines.append(f"成交量: {data.get('volume'):,}")

        return "\n".join(lines)
