"""
市场数据服务 - Yahoo Finance 集成

提供实时股票、加密货币价格查询，历史数据获取，公司信息查询等功能。
"""
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache
import asyncio

# 配置代理（用于访问 Yahoo Finance）- 必须在 import yfinance 之前设置
# 清除可能存在的 socks 代理，使用 http 代理
for key in ["ALL_PROXY", "all_proxy", "SOCKS_PROXY", "socks_proxy"]:
    os.environ.pop(key, None)

PROXY = "http://127.0.0.1:7890"
os.environ["HTTP_PROXY"] = PROXY
os.environ["HTTPS_PROXY"] = PROXY
os.environ["http_proxy"] = PROXY
os.environ["https_proxy"] = PROXY

import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    市场数据服务

    使用 Yahoo Finance API 获取实时市场数据
    """

    # 股票代码映射（中文名称/英文名称 -> 股票代码）
    SYMBOL_MAPPING = {
        # 美股 - 中文
        "特斯拉": "TSLA",
        "苹果": "AAPL",
        "谷歌": "GOOGL",
        "微软": "MSFT",
        "亚马逊": "AMZN",
        "英伟达": "NVDA",
        "脸书": "META",
        "奈飞": "NFLX",
        "台积电": "TSM",
        "阿里巴巴": "BABA",
        "京东": "JD",
        "拼多多": "PDD",
        "百度": "BIDU",
        "腾讯": "TCEHY",
        "英特尔": "INTC",
        "高通": "QCOM",
        "波音": "BA",
        "可口可乐": "KO",
        "麦当劳": "MCD",
        "星巴克": "SBUX",
        "迪士尼": "DIS",
        "耐克": "NKE",
        # 美股 - 英文名称（关键修复！）
        "tesla": "TSLA",
        "apple": "AAPL",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "microsoft": "MSFT",
        "amazon": "AMZN",
        "nvidia": "NVDA",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX",
        "tsmc": "TSM",
        "alibaba": "BABA",
        "jd": "JD",
        "pinduoduo": "PDD",
        "baidu": "BIDU",
        "tencent": "TCEHY",
        "intel": "INTC",
        "amd": "AMD",
        "qualcomm": "QCOM",
        "boeing": "BA",
        "coca-cola": "KO",
        "cocacola": "KO",
        "mcdonald": "MCD",
        "mcdonalds": "MCD",
        "starbucks": "SBUX",
        "disney": "DIS",
        "nike": "NKE",
        # 加密货币
        "比特币": "BTC-USD",
        "btc": "BTC-USD",
        "bitcoin": "BTC-USD",
        "以太坊": "ETH-USD",
        "eth": "ETH-USD",
        "ethereum": "ETH-USD",
        "狗狗币": "DOGE-USD",
        "doge": "DOGE-USD",
        "dogecoin": "DOGE-USD",
        "瑞波币": "XRP-USD",
        "xrp": "XRP-USD",
        "ripple": "XRP-USD",
        "莱特币": "LTC-USD",
        "ltc": "LTC-USD",
        "litecoin": "LTC-USD",
        "索拉纳": "SOL-USD",
        "sol": "SOL-USD",
        "solana": "SOL-USD",
        # 指数
        "标普500": "^GSPC",
        "sp500": "^GSPC",
        "s&p500": "^GSPC",
        "纳斯达克": "^IXIC",
        "nasdaq": "^IXIC",
        "道琼斯": "^DJI",
        "dow": "^DJI",
        "dow jones": "^DJI",
        "上证指数": "000001.SS",
        "沪深300": "000300.SS",
        "恒生指数": "^HSI",
    }

    # 缓存设置
    CACHE_TTL = 60  # 缓存有效期（秒）

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    def _normalize_symbol(self, query: str) -> str:
        """
        将用户查询转换为标准股票代码

        Args:
            query: 用户输入（如 "特斯拉", "TSLA", "tsla"）

        Returns:
            标准股票代码
        """
        query_lower = query.lower().strip()

        # 先检查映射表
        if query_lower in self.SYMBOL_MAPPING:
            return self.SYMBOL_MAPPING[query_lower]

        # 检查中文名称
        if query in self.SYMBOL_MAPPING:
            return self.SYMBOL_MAPPING[query]

        # 否则假设是股票代码，转大写
        return query.upper()

    def _is_cache_valid(self, symbol: str) -> bool:
        """检查缓存是否有效"""
        if symbol not in self._cache_timestamps:
            return False

        elapsed = (datetime.now() - self._cache_timestamps[symbol]).total_seconds()
        return elapsed < self.CACHE_TTL

    def _get_from_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        if self._is_cache_valid(symbol):
            logger.debug(f"Cache hit for {symbol}")
            return self._cache.get(symbol)
        return None

    def _set_cache(self, symbol: str, data: Dict[str, Any]):
        """设置缓存"""
        self._cache[symbol] = data
        self._cache_timestamps[symbol] = datetime.now()

    async def get_quote(self, query: str) -> Dict[str, Any]:
        """
        获取实时行情

        Args:
            query: 股票代码或名称

        Returns:
            行情数据字典
        """
        symbol = self._normalize_symbol(query)

        # 检查缓存
        cached = self._get_from_cache(symbol)
        if cached:
            return cached

        try:
            # 使用线程池执行同步操作
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._fetch_quote_sync, symbol)

            if data:
                self._set_cache(symbol, data)
                logger.info(f"✅ Fetched quote for {symbol}")

            return data

        except Exception as e:
            logger.error(f"❌ Error fetching quote for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    def _fetch_quote_sync(self, symbol: str) -> Dict[str, Any]:
        """同步获取行情（供异步包装调用）"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 获取历史数据用于计算变化
            hist = ticker.history(period="2d")

            if hist.empty:
                return {
                    "symbol": symbol,
                    "error": "无法获取数据，请检查股票代码是否正确",
                    "success": False
                }

            # 当前价格
            current_price = info.get("currentPrice") or info.get("regularMarketPrice") or (hist["Close"].iloc[-1] if len(hist) > 0 else None)

            # 前一交易日收盘价
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or (hist["Close"].iloc[-2] if len(hist) > 1 else current_price)

            # 计算涨跌
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
            else:
                change = 0
                change_percent = 0

            # 判断资产类型
            asset_type = self._detect_asset_type(symbol, info)

            result = {
                "success": True,
                "symbol": symbol,
                "name": info.get("shortName") or info.get("longName") or symbol,
                "asset_type": asset_type,
                "current_price": round(current_price, 2) if current_price else None,
                "previous_close": round(previous_close, 2) if previous_close else None,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": info.get("currency", "USD"),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "avg_volume": info.get("averageVolume"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "timestamp": datetime.now().isoformat(),
            }

            # 股票特有信息
            if asset_type == "stock":
                result.update({
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "employees": info.get("fullTimeEmployees"),
                    "website": info.get("website"),
                    "description": info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else None,
                })

            return result

        except Exception as e:
            logger.error(f"Error in _fetch_quote_sync for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    def _detect_asset_type(self, symbol: str, info: Dict) -> str:
        """检测资产类型"""
        if "-USD" in symbol or symbol in ["BTC", "ETH", "DOGE", "XRP", "SOL", "LTC"]:
            return "crypto"
        elif symbol.startswith("^"):
            return "index"
        elif info.get("quoteType") == "CRYPTOCURRENCY":
            return "crypto"
        elif info.get("quoteType") == "INDEX":
            return "index"
        elif info.get("quoteType") == "ETF":
            return "etf"
        else:
            return "stock"

    async def get_history(
        self,
        query: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        获取历史数据

        Args:
            query: 股票代码或名称
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            历史数据
        """
        symbol = self._normalize_symbol(query)

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                self._fetch_history_sync,
                symbol,
                period,
                interval
            )
            return data

        except Exception as e:
            logger.error(f"❌ Error fetching history for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    def _fetch_history_sync(
        self,
        symbol: str,
        period: str,
        interval: str
    ) -> Dict[str, Any]:
        """同步获取历史数据"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return {
                    "symbol": symbol,
                    "error": "无历史数据",
                    "success": False
                }

            # 转换为列表格式
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]) if row["Volume"] else 0,
                })

            # 计算趋势
            if len(records) >= 2:
                start_price = records[0]["close"]
                end_price = records[-1]["close"]
                total_change = end_price - start_price
                total_change_percent = (total_change / start_price) * 100
                trend = "up" if total_change > 0 else "down" if total_change < 0 else "flat"
            else:
                total_change = 0
                total_change_percent = 0
                trend = "unknown"

            return {
                "success": True,
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": records,
                "summary": {
                    "start_price": records[0]["close"] if records else None,
                    "end_price": records[-1]["close"] if records else None,
                    "total_change": round(total_change, 2),
                    "total_change_percent": round(total_change_percent, 2),
                    "trend": trend,
                    "highest": max(r["high"] for r in records) if records else None,
                    "lowest": min(r["low"] for r in records) if records else None,
                    "avg_volume": sum(r["volume"] for r in records) // len(records) if records else 0,
                    "data_points": len(records),
                }
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    async def get_company_info(self, query: str) -> Dict[str, Any]:
        """
        获取公司详细信息

        Args:
            query: 股票代码或名称

        Returns:
            公司信息
        """
        symbol = self._normalize_symbol(query)

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._fetch_company_info_sync, symbol)
            return data

        except Exception as e:
            logger.error(f"❌ Error fetching company info for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    def _fetch_company_info_sync(self, symbol: str) -> Dict[str, Any]:
        """同步获取公司信息"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "success": True,
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "city": info.get("city"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "description": info.get("longBusinessSummary"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "profit_margins": info.get("profitMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "52_week_change": info.get("52WeekChange"),
                "analyst_target_price": info.get("targetMeanPrice"),
                "analyst_recommendation": info.get("recommendationKey"),
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    async def get_multiple_quotes(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取多个股票行情

        Args:
            queries: 股票代码或名称列表

        Returns:
            行情数据列表
        """
        tasks = [self.get_quote(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "symbol": queries[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append(result)

        return processed_results

    def format_quote_message(self, data: Dict[str, Any]) -> str:
        """
        格式化行情数据为用户友好的消息

        Args:
            data: 行情数据

        Returns:
            格式化的消息字符串
        """
        if not data.get("success"):
            return f"❌ 无法获取 {data.get('symbol', '未知')} 的数据: {data.get('error', '未知错误')}"

        symbol = data["symbol"]
        name = data.get("name", symbol)
        price = data.get("current_price")
        change = data.get("change", 0)
        change_pct = data.get("change_percent", 0)
        currency = data.get("currency", "USD")

        # 涨跌表情
        if change > 0:
            trend_emoji = "📈"
            change_str = f"+{change:.2f} (+{change_pct:.2f}%)"
        elif change < 0:
            trend_emoji = "📉"
            change_str = f"{change:.2f} ({change_pct:.2f}%)"
        else:
            trend_emoji = "➡️"
            change_str = "0.00 (0.00%)"

        # 货币符号
        currency_symbols = {"USD": "$", "CNY": "¥", "HKD": "HK$", "EUR": "€", "GBP": "£"}
        currency_symbol = currency_symbols.get(currency, currency + " ")

        # 格式化市值
        market_cap = data.get("market_cap")
        if market_cap:
            if market_cap >= 1e12:
                market_cap_str = f"{market_cap/1e12:.2f} 万亿"
            elif market_cap >= 1e8:
                market_cap_str = f"{market_cap/1e8:.2f} 亿"
            else:
                market_cap_str = f"{market_cap:,.0f}"
        else:
            market_cap_str = "N/A"

        # 构建消息
        lines = [
            f"📊 **{name}** ({symbol}) 实时行情",
            "",
            f"💰 当前价格：{currency_symbol}{price:,.2f}",
            f"{trend_emoji} 今日涨跌：{change_str}",
        ]

        if data.get("day_high") and data.get("day_low"):
            lines.append(f"📊 今日区间：{currency_symbol}{data['day_low']:,.2f} - {currency_symbol}{data['day_high']:,.2f}")

        if data.get("week_52_high") and data.get("week_52_low"):
            lines.append(f"📈 52周区间：{currency_symbol}{data['week_52_low']:,.2f} - {currency_symbol}{data['week_52_high']:,.2f}")

        if market_cap_str != "N/A":
            lines.append(f"🏢 市值：{currency_symbol}{market_cap_str}")

        if data.get("pe_ratio"):
            lines.append(f"📐 市盈率：{data['pe_ratio']:.2f}")

        if data.get("volume"):
            vol = data["volume"]
            if vol >= 1e6:
                vol_str = f"{vol/1e6:.2f}M"
            elif vol >= 1e3:
                vol_str = f"{vol/1e3:.2f}K"
            else:
                vol_str = str(vol)
            lines.append(f"📊 成交量：{vol_str}")

        return "\n".join(lines)

    def clear_cache(self):
        """清除所有缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")


# 创建全局单例
market_data_service = MarketDataService()
