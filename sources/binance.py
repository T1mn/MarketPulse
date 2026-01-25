"""Binance 公开 API 服务

提供 WebSocket 实时订阅和 REST API 按需获取功能。
无需 API Key。
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Binance API 基础 URL
BINANCE_REST_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_WS_BASE_URL = "wss://stream.binance.com:9443/ws"


@dataclass
class CryptoPrice:
    """加密货币价格"""
    symbol: str
    price: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp,
        }


@dataclass
class Kline:
    """K 线数据"""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float = 0.0
    trades: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "open_time": self.open_time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "close_time": self.close_time,
            "quote_volume": self.quote_volume,
            "trades": self.trades,
        }


@dataclass
class Ticker24h:
    """24 小时行情统计"""
    symbol: str
    price_change: float
    price_change_percent: float
    last_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price_change": self.price_change,
            "price_change_percent": self.price_change_percent,
            "last_price": self.last_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "volume": self.volume,
            "quote_volume": self.quote_volume,
        }


import asyncio
import time

import httpx

from config.base import settings
from core.fetch_status import fetch_status_manager


class KlineCache:
    """K 线缓存"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str, interval: str) -> Optional[List[Kline]]:
        """获取缓存"""
        cache_key = f"{key}:{interval}"
        if cache_key not in self._cache:
            return None

        entry = self._cache[cache_key]
        ttl = settings.BINANCE_KLINE_CACHE_TTL.get(interval, 60)

        if time.time() - entry["timestamp"] > ttl:
            del self._cache[cache_key]
            return None

        return entry["data"]

    def set(self, key: str, interval: str, data: List[Kline]) -> None:
        """设置缓存"""
        cache_key = f"{key}:{interval}"
        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time(),
        }


class BinanceRestClient:
    """
    Binance REST API 客户端

    提供按需获取 K 线、价格、24h 统计等功能。
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._kline_cache = KlineCache()

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=settings.BINANCE_REST_TIMEOUT,
                headers={"Accept": "application/json"},
                proxy=f"http://127.0.0.1:7890",
            )
        return self._client

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        source_desc: str = "Binance API"
    ) -> Any:
        """
        发送请求

        带重试和状态管理。
        """
        url = f"{BINANCE_REST_BASE_URL}{endpoint}"
        client = await self._get_client()

        fetch_status_manager.start_fetch("binance", source_desc)
        start_time = time.time()

        for attempt in range(settings.BINANCE_REST_RETRY_COUNT + 1):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()

                elapsed_ms = (time.time() - start_time) * 1000
                fetch_status_manager.complete_fetch(
                    "binance", success=True, elapsed_ms=elapsed_ms
                )

                return response.json()

            except httpx.TimeoutException as e:
                if attempt < settings.BINANCE_REST_RETRY_COUNT:
                    logger.warning(f"[Binance] 请求超时，重试 {attempt + 1}...")
                    await asyncio.sleep(1)
                    continue

                fetch_status_manager.complete_fetch(
                    "binance", success=False, error="请求超时"
                )
                raise

            except httpx.HTTPStatusError as e:
                fetch_status_manager.complete_fetch(
                    "binance", success=False, error=f"HTTP {e.response.status_code}"
                )
                raise

            except Exception as e:
                fetch_status_manager.complete_fetch(
                    "binance", success=False, error=str(e)
                )
                raise

    async def get_price(self, symbol: str) -> CryptoPrice:
        """
        获取实时价格

        Args:
            symbol: 交易对 (如 "BTCUSDT")

        Returns:
            CryptoPrice 对象
        """
        data = await self._request(
            "/ticker/price",
            params={"symbol": symbol},
            source_desc=f"获取 {symbol} 价格"
        )

        return CryptoPrice(
            symbol=data["symbol"],
            price=float(data["price"]),
        )

    async def get_24h_ticker(self, symbol: str) -> Ticker24h:
        """
        获取 24 小时行情统计

        Args:
            symbol: 交易对

        Returns:
            Ticker24h 对象
        """
        data = await self._request(
            "/ticker/24hr",
            params={"symbol": symbol},
            source_desc=f"获取 {symbol} 24h 统计"
        )

        return Ticker24h(
            symbol=data["symbol"],
            price_change=float(data["priceChange"]),
            price_change_percent=float(data["priceChangePercent"]),
            last_price=float(data["lastPrice"]),
            high_price=float(data["highPrice"]),
            low_price=float(data["lowPrice"]),
            volume=float(data["volume"]),
            quote_volume=float(data["quoteVolume"]),
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[Kline]:
        """
        获取 K 线数据

        只返回已完成的 K 线（排除当前未收盘的）。

        Args:
            symbol: 交易对
            interval: K 线周期 (1m, 15m, 1h, 4h, 1d)
            limit: 返回数量

        Returns:
            Kline 列表
        """
        # 检查缓存
        cache_key = f"{symbol}:{limit}"
        cached = self._kline_cache.get(cache_key, interval)
        if cached is not None:
            logger.debug(f"[Binance] 使用缓存: {symbol} {interval} K线")
            return cached

        # 请求多一条，用于排除未完成的
        data = await self._request(
            "/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit + 1,
            },
            source_desc=f"获取 {symbol} {interval} K线"
        )

        # 排除最后一条未完成的 K 线
        completed_data = data[:-1] if len(data) > limit else data

        klines = [
            Kline(
                open_time=item[0],
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
                close_time=item[6],
                quote_volume=float(item[7]),
                trades=int(item[8]),
            )
            for item in completed_data[-limit:]
        ]

        # 缓存结果
        self._kline_cache.set(cache_key, interval, klines)

        return klines

    async def get_all_prices(self) -> List[CryptoPrice]:
        """获取所有交易对价格"""
        data = await self._request(
            "/ticker/price",
            source_desc="获取所有交易对价格"
        )

        return [
            CryptoPrice(symbol=item["symbol"], price=float(item["price"]))
            for item in data
        ]

    async def close(self) -> None:
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


import json
import websockets


class BinanceWebSocketClient:
    """
    Binance WebSocket 客户端

    服务启动时自动连接，订阅主流币种实时价格。
    """

    def __init__(self, symbols: Optional[List[str]] = None):
        self.symbols = symbols or settings.BINANCE_WS_SYMBOLS
        self._prices: Dict[str, CryptoPrice] = {}
        self._tickers: Dict[str, Ticker24h] = {}
        self._ws = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._ws is not None and self._running

    def get_price(self, symbol: str) -> Optional[CryptoPrice]:
        """获取缓存的实时价格"""
        return self._prices.get(symbol)

    def get_ticker(self, symbol: str) -> Optional[Ticker24h]:
        """获取缓存的 24h 统计"""
        return self._tickers.get(symbol)

    def get_all_prices(self) -> Dict[str, CryptoPrice]:
        """获取所有缓存的价格"""
        return self._prices.copy()

    def get_all_tickers(self) -> Dict[str, Ticker24h]:
        """获取所有缓存的统计"""
        return self._tickers.copy()

    def _handle_ticker_message(self, message: Dict) -> None:
        """处理 24h ticker 消息"""
        symbol = message.get("s")
        if not symbol:
            return

        # 更新价格
        self._prices[symbol] = CryptoPrice(
            symbol=symbol,
            price=float(message.get("c", 0)),
        )

        # 更新 24h 统计
        self._tickers[symbol] = Ticker24h(
            symbol=symbol,
            price_change=float(message.get("p", 0)),
            price_change_percent=float(message.get("P", 0)),
            last_price=float(message.get("c", 0)),
            high_price=float(message.get("h", 0)),
            low_price=float(message.get("l", 0)),
            volume=float(message.get("v", 0)),
            quote_volume=float(message.get("q", 0)),
        )

    async def _connect(self) -> None:
        """连接 WebSocket"""
        # 构建订阅流
        streams = [f"{s.lower()}@ticker" for s in self.symbols]
        stream_path = "/".join(streams)
        url = f"{BINANCE_WS_BASE_URL}/{stream_path}"

        logger.info(f"[Binance] WebSocket 连接中: {self.symbols}")

        while self._running:
            try:
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    logger.info(f"[Binance] WebSocket 已连接，订阅: {', '.join(self.symbols)}")

                    async for message in ws:
                        if not self._running:
                            break

                        try:
                            data = json.loads(message)
                            self._handle_ticker_message(data)
                        except json.JSONDecodeError:
                            logger.warning("[Binance] 无法解析 WebSocket 消息")

            except websockets.ConnectionClosed:
                logger.warning("[Binance] WebSocket 断开连接")
            except Exception as e:
                logger.error(f"[Binance] WebSocket 错误: {e}")

            self._ws = None

            if self._running:
                delay = settings.BINANCE_WS_RECONNECT_DELAY
                logger.info(f"[Binance] {delay} 秒后重连...")
                await asyncio.sleep(delay)

    async def start(self) -> None:
        """启动 WebSocket 连接"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._connect())
        logger.info("[Binance] WebSocket 客户端已启动")

    async def stop(self) -> None:
        """停止 WebSocket 连接"""
        self._running = False

        if self._ws:
            await self._ws.close()
            self._ws = None

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("[Binance] WebSocket 客户端已停止")


class BinanceService:
    """
    Binance 统一服务

    整合 WebSocket 和 REST API，提供统一的数据访问接口。
    优先使用 WebSocket 缓存，无缓存时回退到 REST API。
    """

    def __init__(self):
        self.rest_client = BinanceRestClient()
        self.ws_client = BinanceWebSocketClient()

    async def start(self) -> None:
        """启动服务（启动 WebSocket 连接）"""
        await self.ws_client.start()

    async def stop(self) -> None:
        """停止服务"""
        await self.ws_client.stop()
        await self.rest_client.close()

    async def get_price(self, symbol: str) -> tuple:
        """
        获取价格

        优先从 WebSocket 缓存获取，无缓存时调用 REST API。

        Args:
            symbol: 交易对

        Returns:
            (CryptoPrice, source) - source 为 "websocket" 或 "rest"
        """
        # 优先 WebSocket 缓存
        cached = self.ws_client.get_price(symbol)
        if cached is not None:
            return cached, "websocket"

        # 回退到 REST API
        price = await self.rest_client.get_price(symbol)
        return price, "rest"

    async def get_24h_ticker(self, symbol: str) -> tuple:
        """
        获取 24h 统计

        优先从 WebSocket 缓存获取。

        Args:
            symbol: 交易对

        Returns:
            (Ticker24h, source)
        """
        # 优先 WebSocket 缓存
        cached = self.ws_client.get_ticker(symbol)
        if cached is not None:
            return cached, "websocket"

        # 回退到 REST API
        ticker = await self.rest_client.get_24h_ticker(symbol)
        return ticker, "rest"

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[Kline]:
        """
        获取 K 线数据（仅 REST API）

        Args:
            symbol: 交易对
            interval: K 线周期 (1m, 15m, 1h, 4h, 1d)
            limit: 返回数量

        Returns:
            Kline 列表
        """
        return await self.rest_client.get_klines(symbol, interval, limit)

    def get_ws_status(self) -> Dict[str, Any]:
        """获取 WebSocket 连接状态"""
        return {
            "connected": self.ws_client.is_connected,
            "symbols": self.ws_client.symbols,
            "cached_prices": len(self.ws_client._prices),
        }


# 全局服务实例
binance_service = BinanceService()
