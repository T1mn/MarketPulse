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
