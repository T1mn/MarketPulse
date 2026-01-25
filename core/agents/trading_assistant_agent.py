"""交易助手 Agent"""
import logging
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from core.llm.router import llm_router

logger = logging.getLogger(__name__)


class TradingAssistantAgent(BaseAgent):
    """
    交易助手 Agent

    职责：
    1. 账户查询
    2. 交易执行辅助（需用户确认）
    3. 风险评估
    4. 仓位管理建议
    5. 止损止盈设置
    """

    def __init__(self):
        super().__init__(
            name="trading_assistant",
            description="交易助手，提供交易执行、账户管理、风险控制"
        )

        self.supported_intents = {
            "trade_execute",
            "account_inquiry",
            "risk_alert",
            "crypto_price",
            "crypto_analysis",
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
        logger.info(f"💼 TradingAssistantAgent processing: {intent}")

        if intent == "trade_execute":
            return await self._handle_trade_execute(user_input, entities, context)

        elif intent == "account_inquiry":
            return await self._handle_account_inquiry(user_input, entities, context)

        elif intent == "risk_alert":
            return await self._handle_risk_alert(user_input, entities, context)

        elif intent == "crypto_price":
            return await self._handle_crypto_price(user_input, entities, context)

        elif intent == "crypto_analysis":
            return await self._handle_crypto_analysis(user_input, entities, context)

        else:
            return self._create_response(
                content="抱歉，我无法处理这个交易请求。",
                confidence=0.5
            )

    async def _handle_trade_execute(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理交易执行"""
        asset = entities.get("asset", "未知资产")
        action = entities.get("action", "未知操作")
        quantity = entities.get("quantity", "未指定数量")

        # ⚠️ 重要：交易操作需要用户明确确认
        logger.warning(f"⚠️ Trade request: {action} {quantity} {asset}")

        # 风险评估
        risk_assessment = await self._assess_trade_risk(asset, action, quantity)

        content = f"""📋 交易准备

**交易详情：**
- 资产：{asset}
- 操作：{action}
- 数量：{quantity}

**风险评估：**
{risk_assessment}

⚠️ **重要提示：**
1. 投资有风险，入市需谨慎
2. 请确认交易详情无误
3. 建议设置止损止盈

请回复 "确认交易" 来执行，或 "取消" 来放弃。"""

        return self._create_response(
            content=content,
            confidence=0.95,
            requires_user_confirmation=True,
            metadata={
                "trade_details": {
                    "asset": asset,
                    "action": action,
                    "quantity": quantity,
                },
                "risk_level": "medium",
            },
            suggested_actions=[
                {"action": "confirm_trade", "label": "确认交易"},
                {"action": "cancel_trade", "label": "取消"},
                {"action": "modify_trade", "label": "修改参数"},
            ]
        )

    async def _handle_account_inquiry(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理账户查询"""
        # TODO: 集成真实的账户系统
        # 现在返回模拟数据

        account_data = await self._fetch_account_data(context.get("user_id"))

        content = f"""💼 账户信息

**账户余额：** ${account_data['balance']:,.2f}
**可用资金：** ${account_data['available']:,.2f}
**持仓市值：** ${account_data['positions_value']:,.2f}
**今日盈亏：** ${account_data['daily_pnl']:+,.2f} ({account_data['daily_pnl_percent']:+.2f}%)
**总盈亏：** ${account_data['total_pnl']:+,.2f} ({account_data['total_pnl_percent']:+.2f}%)

**持仓概览：**
{self._format_positions(account_data['positions'])}

需要查看详细持仓或交易记录吗？"""

        return self._create_response(
            content=content,
            confidence=1.0,
            metadata={"account_data": account_data},
            data=account_data,
            suggested_actions=[
                {"action": "view_positions", "label": "查看详细持仓"},
                {"action": "view_history", "label": "交易记录"},
            ]
        )

    async def _handle_risk_alert(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理风险提示"""
        asset = entities.get("asset", "该资产")

        # 使用 LLM 进行风险分析
        system_prompt = f"""你是一位专业的风险管理专家。

请对 {asset} 进行全面的风险评估，包括：

1. **市场风险**
   - 价格波动性
   - 流动性风险
   - 市场情绪

2. **基本面风险**
   - 行业风险
   - 公司财务状况
   - 政策风险

3. **技术面风险**
   - 超买超卖情况
   - 关键支撑位
   - 趋势强度

4. **综合建议**
   - 风险等级（低/中/高）
   - 建议仓位（%）
   - 止损建议
   - 注意事项

保持客观、专业、负责任。"""

        try:
            response = await llm_router.generate(
                prompt=f"用户请求：{user_input}",
                system_prompt=system_prompt,
                model_preference="quality",  # 使用高质量模型
                temperature=0.2,
                max_tokens=1500,
            )

            return self._create_response(
                content=response.content,
                confidence=0.9,
                metadata={
                    "asset": asset,
                    "assessment_type": "comprehensive_risk"
                },
                suggested_actions=[
                    {"action": "set_stop_loss", "label": "设置止损"},
                    {"action": "reduce_position", "label": "减仓"},
                ]
            )

        except Exception as e:
            logger.error(f"Risk alert error: {e}")
            return self._create_response(
                content=f"⚠️ 风险提示：{asset} 存在一定投资风险，建议谨慎操作。",
                confidence=0.6
            )

    async def _assess_trade_risk(
        self,
        asset: str,
        action: str,
        quantity: str
    ) -> str:
        """评估交易风险"""
        # 简化的风险评估
        risk_factors = []

        # 检查波动性
        risk_factors.append("- 市场波动性：中等")

        # 检查仓位
        risk_factors.append("- 建议仓位：不超过总资金的 20%")

        # 检查止损
        risk_factors.append("- 建议止损：-5% 至 -8%")

        return "\n".join(risk_factors)

    async def _fetch_account_data(self, user_id: str) -> Dict[str, Any]:
        """获取账户数据（模拟）"""
        # TODO: 集成真实的账户系统
        import random

        return {
            "balance": 50000.00,
            "available": 35000.00,
            "positions_value": 15000.00,
            "daily_pnl": random.uniform(-500, 500),
            "daily_pnl_percent": random.uniform(-2, 2),
            "total_pnl": random.uniform(-1000, 3000),
            "total_pnl_percent": random.uniform(-5, 15),
            "positions": [
                {"symbol": "AAPL", "quantity": 50, "avg_cost": 180.00, "current_price": 185.20},
                {"symbol": "TSLA", "quantity": 20, "avg_cost": 235.00, "current_price": 242.50},
            ]
        }

    def _format_positions(self, positions: list) -> str:
        """格式化持仓信息"""
        if not positions:
            return "暂无持仓"

        lines = []
        for pos in positions:
            pnl = (pos['current_price'] - pos['avg_cost']) * pos['quantity']
            pnl_percent = (pos['current_price'] - pos['avg_cost']) / pos['avg_cost'] * 100

            lines.append(
                f"• {pos['symbol']}: {pos['quantity']}股 @ ${pos['current_price']:.2f} "
                f"(盈亏: ${pnl:+.2f}, {pnl_percent:+.2f}%)"
            )

        return "\n".join(lines)

    async def _handle_crypto_price(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理加密货币价格查询"""
        from sources.binance import binance_service

        symbol = entities.get("symbol", "BTCUSDT").upper()
        if not symbol.endswith("USDT"):
            symbol = f"{symbol}USDT"

        try:
            price, source = await binance_service.get_price(symbol)
            ticker, _ = await binance_service.get_24h_ticker(symbol)

            # 格式化涨跌幅
            change_sign = "+" if ticker.price_change_percent >= 0 else ""
            change_color = "上涨" if ticker.price_change_percent >= 0 else "下跌"

            content = f"""**{symbol} 实时行情**

当前价格: ${price.price:,.2f}
24h涨跌: {change_sign}{ticker.price_change_percent:.2f}% ({change_color} ${abs(ticker.price_change):,.2f})
24h最高: ${ticker.high_price:,.2f}
24h最低: ${ticker.low_price:,.2f}
24h成交量: {ticker.volume:,.2f}
24h成交额: ${ticker.quote_volume:,.2f}

数据来源: {'实时推送' if source == 'websocket' else 'API查询'}"""

            return self._create_response(
                content=content,
                confidence=1.0,
                data={
                    "symbol": symbol,
                    "price": price.price,
                    "change_percent": ticker.price_change_percent,
                },
                suggested_actions=[
                    {"action": "view_klines", "label": "查看K线"},
                    {"action": "set_alert", "label": "设置提醒"},
                ]
            )

        except Exception as e:
            logger.error(f"获取加密货币价格失败: {e}")
            return self._create_response(
                content=f"获取 {symbol} 价格失败，请稍后重试。",
                confidence=0.5
            )

    async def _handle_crypto_analysis(
        self,
        user_input: str,
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AgentResponse:
        """处理加密货币 K 线分析"""
        from sources.binance import binance_service

        symbol = entities.get("symbol", "BTCUSDT").upper()
        if not symbol.endswith("USDT"):
            symbol = f"{symbol}USDT"

        interval = entities.get("interval", "4h")

        try:
            klines = await binance_service.get_klines(symbol, interval, limit=20)
            ticker, _ = await binance_service.get_24h_ticker(symbol)

            # 简单的趋势分析
            closes = [k.close for k in klines]
            avg_price = sum(closes) / len(closes)
            current_price = closes[-1]
            trend = "上涨趋势" if current_price > avg_price else "下跌趋势"

            # 计算波动率
            high_prices = [k.high for k in klines]
            low_prices = [k.low for k in klines]
            volatility = (max(high_prices) - min(low_prices)) / avg_price * 100

            content = f"""**{symbol} {interval} K线分析**

当前价格: ${current_price:,.2f}
均价 (20周期): ${avg_price:,.2f}
趋势判断: {trend}
波动率: {volatility:.2f}%

最近 K 线概况:
- 最高: ${max(high_prices):,.2f}
- 最低: ${min(low_prices):,.2f}
- 振幅: ${max(high_prices) - min(low_prices):,.2f}

注意: 以上为技术指标参考，不构成投资建议。"""

            return self._create_response(
                content=content,
                confidence=0.9,
                data={
                    "symbol": symbol,
                    "interval": interval,
                    "trend": trend,
                    "volatility": volatility,
                },
                suggested_actions=[
                    {"action": "view_1h", "label": "查看1小时"},
                    {"action": "view_1d", "label": "查看日线"},
                ]
            )

        except Exception as e:
            logger.error(f"获取 K 线分析失败: {e}")
            return self._create_response(
                content=f"获取 {symbol} K线数据失败，请稍后重试。",
                confidence=0.5
            )
