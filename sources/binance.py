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
