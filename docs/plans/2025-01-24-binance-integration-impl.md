# Binance 集成与 API 状态指示实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 Binance 公开 API 集成（WebSocket 实时 + REST API 按需）和 API 获取状态指示功能

**Architecture:**
- `sources/binance.py` 封装 Binance WebSocket 和 REST API
- `core/fetch_status.py` 提供统一的获取状态管理
- 服务启动时自动连接 WebSocket 订阅 BTC/ETH 实时价格
- REST API 按需获取 K 线和其他币种，带智能缓存

**Tech Stack:** httpx (异步 HTTP), websockets (WebSocket 客户端), asyncio, FastAPI

---

## Task 1: 添加 Binance 配置项

**Files:**
- Modify: `/home/chery/personal/MarketPulse/config/base.py:93-96`

**Step 1: 在 config/base.py 添加 Binance 配置**

在 `FETCH_NOTATESLA_NEWS: bool = True` 之后，`FILTER_TO_TOP_TIER_ONLY` 之前添加：

```python
    # ==================== Binance 配置 ====================
    BINANCE_WS_SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT"]
    BINANCE_WS_RECONNECT_DELAY: int = 5  # 秒
    BINANCE_REST_TIMEOUT: int = 10  # 秒
    BINANCE_REST_RETRY_COUNT: int = 2
    BINANCE_KLINE_CACHE_TTL: dict = {
        "1m": 30,
        "15m": 300,
        "1h": 900,
        "4h": 1800,
        "1d": 7200,
    }
```

**Step 2: 验证配置可访问**

Run: `cd /home/chery/personal/MarketPulse && python -c "from config.base import settings; print(settings.BINANCE_WS_SYMBOLS)"`

Expected: `['BTCUSDT', 'ETHUSDT']`

**Step 3: Commit**

```bash
git add config/base.py
git commit -m "feat(config): add Binance integration settings"
```

---

## Task 2: 创建获取状态管理器

**Files:**
- Create: `/home/chery/personal/MarketPulse/core/fetch_status.py`
- Create: `/home/chery/personal/MarketPulse/tests/unit/test_fetch_status.py`

**Step 1: 编写测试文件**

```python
"""获取状态管理器测试"""
import pytest
from core.fetch_status import FetchStatus, FetchStatusManager


class TestFetchStatus:
    """FetchStatus 枚举测试"""

    def test_status_values(self):
        assert FetchStatus.IDLE == "idle"
        assert FetchStatus.FETCHING == "fetching"
        assert FetchStatus.SUCCESS == "success"
        assert FetchStatus.ERROR == "error"


class TestFetchStatusManager:
    """FetchStatusManager 测试"""

    def test_start_fetch(self):
        manager = FetchStatusManager()
        manager.start_fetch("binance", "获取 BTC 价格")

        status = manager.get_status("binance")
        assert status["status"] == FetchStatus.FETCHING
        assert status["description"] == "获取 BTC 价格"

    def test_complete_fetch_success(self):
        manager = FetchStatusManager()
        manager.start_fetch("binance", "获取 BTC 价格")
        manager.complete_fetch("binance", success=True)

        status = manager.get_status("binance")
        assert status["status"] == FetchStatus.SUCCESS

    def test_complete_fetch_error(self):
        manager = FetchStatusManager()
        manager.start_fetch("binance", "获取 BTC 价格")
        manager.complete_fetch("binance", success=False, error="超时")

        status = manager.get_status("binance")
        assert status["status"] == FetchStatus.ERROR
        assert status["error"] == "超时"

    def test_get_all_status(self):
        manager = FetchStatusManager()
        manager.start_fetch("binance", "获取价格")
        manager.start_fetch("finnhub", "获取新闻")

        all_status = manager.get_all_status()
        assert "binance" in all_status
        assert "finnhub" in all_status

    def test_get_status_unknown_source(self):
        manager = FetchStatusManager()
        status = manager.get_status("unknown")
        assert status["status"] == FetchStatus.IDLE
```

**Step 2: 运行测试确认失败**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_fetch_status.py -v`

Expected: FAIL (模块不存在)

**Step 3: 实现 FetchStatusManager**

```python
"""获取状态管理器

统一管理 API 获取状态，支持前端状态展示和后端日志记录。
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from threading import Lock

logger = logging.getLogger(__name__)


class FetchStatus(str, Enum):
    """获取状态枚举"""
    IDLE = "idle"
    FETCHING = "fetching"
    SUCCESS = "success"
    ERROR = "error"


class FetchStatusManager:
    """
    获取状态管理器

    线程安全，支持多数据源状态管理。
    """

    def __init__(self):
        self._status: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def start_fetch(self, source: str, description: str) -> None:
        """
        开始获取

        Args:
            source: 数据源名称 (如 "binance", "finnhub")
            description: 获取描述 (如 "获取 BTC 价格")
        """
        with self._lock:
            self._status[source] = {
                "status": FetchStatus.FETCHING,
                "description": description,
                "started_at": datetime.now().isoformat(),
                "error": None,
            }
        logger.info(f"[FetchStatus] 开始获取: {source} - {description}")

    def complete_fetch(
        self,
        source: str,
        success: bool,
        error: Optional[str] = None,
        elapsed_ms: Optional[float] = None
    ) -> None:
        """
        完成获取

        Args:
            source: 数据源名称
            success: 是否成功
            error: 错误信息 (失败时)
            elapsed_ms: 耗时 (毫秒)
        """
        with self._lock:
            if source not in self._status:
                self._status[source] = {}

            self._status[source].update({
                "status": FetchStatus.SUCCESS if success else FetchStatus.ERROR,
                "completed_at": datetime.now().isoformat(),
                "error": error,
                "elapsed_ms": elapsed_ms,
            })

        if success:
            elapsed_str = f" (耗时 {elapsed_ms:.0f}ms)" if elapsed_ms else ""
            logger.info(f"[FetchStatus] 完成获取: {source} - 成功{elapsed_str}")
        else:
            logger.warning(f"[FetchStatus] 完成获取: {source} - 失败: {error}")

    def get_status(self, source: str) -> Dict[str, Any]:
        """
        获取指定数据源状态

        Args:
            source: 数据源名称

        Returns:
            状态信息字典
        """
        with self._lock:
            if source not in self._status:
                return {
                    "status": FetchStatus.IDLE,
                    "description": None,
                    "error": None,
                }
            return self._status[source].copy()

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有数据源状态

        Returns:
            所有状态信息
        """
        with self._lock:
            return {k: v.copy() for k, v in self._status.items()}

    def reset(self, source: str) -> None:
        """重置指定数据源状态"""
        with self._lock:
            if source in self._status:
                del self._status[source]


# 全局实例
fetch_status_manager = FetchStatusManager()
```

**Step 4: 运行测试确认通过**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_fetch_status.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add core/fetch_status.py tests/unit/test_fetch_status.py
git commit -m "feat(core): add FetchStatusManager for API status tracking"
```

---

## Task 3: 创建 Binance 服务模块 - 数据结构

**Files:**
- Create: `/home/chery/personal/MarketPulse/sources/binance.py`
- Create: `/home/chery/personal/MarketPulse/tests/unit/test_binance.py`

**Step 1: 编写数据结构测试**

```python
"""Binance 服务测试"""
import pytest
from sources.binance import CryptoPrice, Kline, Ticker24h


class TestDataStructures:
    """数据结构测试"""

    def test_crypto_price(self):
        price = CryptoPrice(
            symbol="BTCUSDT",
            price=43250.00,
            timestamp="2025-01-24T10:00:00"
        )
        assert price.symbol == "BTCUSDT"
        assert price.price == 43250.00

        data = price.to_dict()
        assert data["symbol"] == "BTCUSDT"
        assert data["price"] == 43250.00

    def test_kline(self):
        kline = Kline(
            open_time=1706090400000,
            open=43000.0,
            high=43500.0,
            low=42800.0,
            close=43250.0,
            volume=1234.56,
            close_time=1706094000000,
        )
        assert kline.open == 43000.0
        assert kline.close == 43250.0

    def test_ticker_24h(self):
        ticker = Ticker24h(
            symbol="BTCUSDT",
            price_change=500.0,
            price_change_percent=1.17,
            last_price=43250.0,
            high_price=43800.0,
            low_price=42500.0,
            volume=12345.67,
            quote_volume=534567890.12,
        )
        assert ticker.price_change_percent == 1.17
```

**Step 2: 运行测试确认失败**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestDataStructures -v`

Expected: FAIL (模块不存在)

**Step 3: 实现数据结构**

```python
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
```

**Step 4: 运行测试确认通过**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestDataStructures -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add sources/binance.py tests/unit/test_binance.py
git commit -m "feat(sources): add Binance data structures"
```

---

## Task 4: 实现 Binance REST API 客户端

**Files:**
- Modify: `/home/chery/personal/MarketPulse/sources/binance.py`
- Modify: `/home/chery/personal/MarketPulse/tests/unit/test_binance.py`

**Step 1: 添加 REST API 测试**

在 `tests/unit/test_binance.py` 末尾添加：

```python
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


class TestBinanceRestClient:
    """REST API 客户端测试"""

    @pytest.fixture
    def client(self):
        from sources.binance import BinanceRestClient
        return BinanceRestClient()

    @pytest.mark.asyncio
    async def test_get_price(self, client):
        mock_response = {"symbol": "BTCUSDT", "price": "43250.00"}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            price = await client.get_price("BTCUSDT")

            assert price.symbol == "BTCUSDT"
            assert price.price == 43250.00

    @pytest.mark.asyncio
    async def test_get_24h_ticker(self, client):
        mock_response = {
            "symbol": "BTCUSDT",
            "priceChange": "500.00",
            "priceChangePercent": "1.17",
            "lastPrice": "43250.00",
            "highPrice": "43800.00",
            "lowPrice": "42500.00",
            "volume": "12345.67",
            "quoteVolume": "534567890.12",
        }

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            ticker = await client.get_24h_ticker("BTCUSDT")

            assert ticker.symbol == "BTCUSDT"
            assert ticker.price_change_percent == 1.17

    @pytest.mark.asyncio
    async def test_get_klines(self, client):
        mock_response = [
            [1706090400000, "43000.0", "43500.0", "42800.0", "43250.0", "1234.56",
             1706094000000, "53456789.0", 1000, "600.0", "25900000.0", "0"],
            [1706094000000, "43250.0", "43600.0", "43100.0", "43400.0", "987.65",
             1706097600000, "42800000.0", 800, "500.0", "21700000.0", "0"],
        ]

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            klines = await client.get_klines("BTCUSDT", "1h", limit=2)

            assert len(klines) == 2
            assert klines[0].open == 43000.0
            assert klines[0].close == 43250.0

    @pytest.mark.asyncio
    async def test_get_klines_excludes_incomplete(self, client):
        """测试排除未完成的 K 线"""
        # 3 条 K 线，最后一条是未完成的
        mock_response = [
            [1706090400000, "43000.0", "43500.0", "42800.0", "43250.0", "1234.56",
             1706094000000, "53456789.0", 1000, "600.0", "25900000.0", "0"],
            [1706094000000, "43250.0", "43600.0", "43100.0", "43400.0", "987.65",
             1706097600000, "42800000.0", 800, "500.0", "21700000.0", "0"],
            [1706097600000, "43400.0", "43700.0", "43300.0", "43500.0", "500.00",
             1706101200000, "21700000.0", 400, "250.0", "10850000.0", "0"],
        ]

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            # 请求 2 条，内部会请求 3 条然后排除最后一条
            klines = await client.get_klines("BTCUSDT", "1h", limit=2)

            # 应该只返回前 2 条完整的
            assert len(klines) == 2
```

**Step 2: 运行测试确认失败**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestBinanceRestClient -v`

Expected: FAIL (BinanceRestClient 不存在)

**Step 3: 实现 BinanceRestClient**

在 `sources/binance.py` 末尾添加：

```python
import asyncio
import time
from functools import wraps

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
```

**Step 4: 运行测试确认通过**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestBinanceRestClient -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add sources/binance.py tests/unit/test_binance.py
git commit -m "feat(sources): add Binance REST API client with caching"
```

---

## Task 5: 实现 Binance WebSocket 客户端

**Files:**
- Modify: `/home/chery/personal/MarketPulse/sources/binance.py`
- Modify: `/home/chery/personal/MarketPulse/tests/unit/test_binance.py`

**Step 1: 添加 WebSocket 测试**

在 `tests/unit/test_binance.py` 末尾添加：

```python
class TestBinanceWebSocketClient:
    """WebSocket 客户端测试"""

    @pytest.fixture
    def ws_client(self):
        from sources.binance import BinanceWebSocketClient
        return BinanceWebSocketClient(symbols=["BTCUSDT", "ETHUSDT"])

    def test_init(self, ws_client):
        assert ws_client.symbols == ["BTCUSDT", "ETHUSDT"]
        assert ws_client.is_connected is False

    def test_get_price_not_connected(self, ws_client):
        price = ws_client.get_price("BTCUSDT")
        assert price is None

    def test_parse_ticker_message(self, ws_client):
        message = {
            "e": "24hrTicker",
            "s": "BTCUSDT",
            "c": "43250.00",
            "P": "1.17",
            "h": "43800.00",
            "l": "42500.00",
            "v": "12345.67",
            "q": "534567890.12",
        }

        ws_client._handle_ticker_message(message)

        price = ws_client.get_price("BTCUSDT")
        assert price is not None
        assert price.price == 43250.00

        ticker = ws_client.get_ticker("BTCUSDT")
        assert ticker is not None
        assert ticker.price_change_percent == 1.17
```

**Step 2: 运行测试确认失败**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestBinanceWebSocketClient -v`

Expected: FAIL (BinanceWebSocketClient 不存在)

**Step 3: 实现 BinanceWebSocketClient**

在 `sources/binance.py` 末尾添加：

```python
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
```

**Step 4: 运行测试确认通过**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestBinanceWebSocketClient -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add sources/binance.py tests/unit/test_binance.py
git commit -m "feat(sources): add Binance WebSocket client for real-time prices"
```

---

## Task 6: 创建 Binance 统一服务

**Files:**
- Modify: `/home/chery/personal/MarketPulse/sources/binance.py`
- Modify: `/home/chery/personal/MarketPulse/tests/unit/test_binance.py`

**Step 1: 添加统一服务测试**

在 `tests/unit/test_binance.py` 末尾添加：

```python
class TestBinanceService:
    """统一服务测试"""

    @pytest.fixture
    def service(self):
        from sources.binance import BinanceService
        return BinanceService()

    def test_init(self, service):
        assert service.rest_client is not None
        assert service.ws_client is not None

    @pytest.mark.asyncio
    async def test_get_price_from_ws_cache(self, service):
        """优先从 WebSocket 缓存获取价格"""
        # 模拟 WebSocket 缓存
        from sources.binance import CryptoPrice
        service.ws_client._prices["BTCUSDT"] = CryptoPrice(
            symbol="BTCUSDT",
            price=43250.00,
        )

        price, source = await service.get_price("BTCUSDT")
        assert price.price == 43250.00
        assert source == "websocket"

    @pytest.mark.asyncio
    async def test_get_price_fallback_to_rest(self, service):
        """WebSocket 无缓存时回退到 REST API"""
        mock_price = CryptoPrice(symbol="SOLUSDT", price=95.20)

        with patch.object(
            service.rest_client, 'get_price',
            new_callable=AsyncMock, return_value=mock_price
        ):
            price, source = await service.get_price("SOLUSDT")
            assert price.price == 95.20
            assert source == "rest"
```

**Step 2: 运行测试确认失败**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestBinanceService -v`

Expected: FAIL (BinanceService 不存在)

**Step 3: 实现 BinanceService**

在 `sources/binance.py` 末尾添加：

```python
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

    async def get_price(self, symbol: str) -> tuple[CryptoPrice, str]:
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

    async def get_24h_ticker(self, symbol: str) -> tuple[Ticker24h, str]:
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
```

**Step 4: 运行测试确认通过**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/unit/test_binance.py::TestBinanceService -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add sources/binance.py tests/unit/test_binance.py
git commit -m "feat(sources): add unified BinanceService with WS/REST integration"
```

---

## Task 7: 创建 Market API 路由

**Files:**
- Create: `/home/chery/personal/MarketPulse/api/routes/market.py`
- Modify: `/home/chery/personal/MarketPulse/api/routes/__init__.py`
- Modify: `/home/chery/personal/MarketPulse/api/app.py`

**Step 1: 创建 market.py 路由**

```python
"""Market 数据 API 路由"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from sources.binance import binance_service
from core.fetch_status import fetch_status_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class PriceResponse(BaseModel):
    """价格响应"""
    symbol: str
    price: float
    source: str  # "websocket" or "rest"
    timestamp: str


class Ticker24hResponse(BaseModel):
    """24h 统计响应"""
    symbol: str
    price_change: float
    price_change_percent: float
    last_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    source: str


class KlineResponse(BaseModel):
    """K 线响应"""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


class FetchStatusResponse(BaseModel):
    """获取状态响应"""
    status: str
    description: Optional[str] = None
    error: Optional[str] = None


@router.get("/price/{symbol}", response_model=PriceResponse)
async def get_price(symbol: str):
    """
    获取加密货币价格

    Args:
        symbol: 交易对 (如 BTCUSDT, ETHUSDT)
    """
    try:
        symbol = symbol.upper()
        price, source = await binance_service.get_price(symbol)

        return PriceResponse(
            symbol=price.symbol,
            price=price.price,
            source=source,
            timestamp=price.timestamp,
        )

    except Exception as e:
        logger.error(f"获取价格失败: {symbol}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}", response_model=Ticker24hResponse)
async def get_24h_ticker(symbol: str):
    """
    获取 24 小时行情统计

    Args:
        symbol: 交易对
    """
    try:
        symbol = symbol.upper()
        ticker, source = await binance_service.get_24h_ticker(symbol)

        return Ticker24hResponse(
            symbol=ticker.symbol,
            price_change=ticker.price_change,
            price_change_percent=ticker.price_change_percent,
            last_price=ticker.last_price,
            high_price=ticker.high_price,
            low_price=ticker.low_price,
            volume=ticker.volume,
            quote_volume=ticker.quote_volume,
            source=source,
        )

    except Exception as e:
        logger.error(f"获取 24h 统计失败: {symbol}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{symbol}", response_model=List[KlineResponse])
async def get_klines(
    symbol: str,
    interval: str = Query("1h", regex="^(1m|15m|1h|4h|1d)$"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    获取 K 线数据

    Args:
        symbol: 交易对
        interval: K 线周期 (1m, 15m, 1h, 4h, 1d)
        limit: 返回数量 (1-1000)
    """
    try:
        symbol = symbol.upper()
        klines = await binance_service.get_klines(symbol, interval, limit)

        return [
            KlineResponse(
                open_time=k.open_time,
                open=k.open,
                high=k.high,
                low=k.low,
                close=k.close,
                volume=k.volume,
                close_time=k.close_time,
            )
            for k in klines
        ]

    except Exception as e:
        logger.error(f"获取 K 线失败: {symbol} {interval}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=dict)
async def get_fetch_status():
    """获取所有数据源的获取状态"""
    return {
        "fetch_status": fetch_status_manager.get_all_status(),
        "websocket": binance_service.get_ws_status(),
    }


@router.get("/status/{source}", response_model=FetchStatusResponse)
async def get_source_status(source: str):
    """获取指定数据源的获取状态"""
    status = fetch_status_manager.get_status(source)
    return FetchStatusResponse(
        status=status["status"],
        description=status.get("description"),
        error=status.get("error"),
    )
```

**Step 2: 更新 routes/__init__.py**

```python
"""路由模块"""
from . import chatbot, health, admin, market

__all__ = ["chatbot", "health", "admin", "market"]
```

**Step 3: 更新 api/app.py 注册路由和生命周期**

在 `api/app.py` 中：

1. 在文件顶部添加导入：
```python
from sources.binance import binance_service
```

2. 在 `from .routes import chatbot, health, admin` 后添加：
```python
from .routes import market
```

3. 更新 `lifespan` 函数：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("MarketPulse API starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # 启动 Binance WebSocket
    await binance_service.start()

    yield

    # 关闭时执行
    await binance_service.stop()
    logger.info("MarketPulse API shutting down...")
```

4. 在路由注册部分添加：
```python
# Market API
app.include_router(market.router, prefix=f"{settings.API_PREFIX}/market", tags=["Market"])
```

**Step 4: 验证 API 可访问**

Run: `cd /home/chery/personal/MarketPulse && python -c "from api.routes.market import router; print('Market router loaded')"`

Expected: `Market router loaded`

**Step 5: Commit**

```bash
git add api/routes/market.py api/routes/__init__.py api/app.py
git commit -m "feat(api): add Market API routes for crypto data"
```

---

## Task 8: 集成到交易助手 Agent

**Files:**
- Modify: `/home/chery/personal/MarketPulse/core/agents/trading_assistant_agent.py`

**Step 1: 添加加密货币查询意图处理**

在 `TradingAssistantAgent` 类中：

1. 更新 `supported_intents`：
```python
self.supported_intents = {
    "trade_execute",
    "account_inquiry",
    "risk_alert",
    "crypto_price",      # 新增
    "crypto_analysis",   # 新增
}
```

2. 在 `process` 方法中添加新的意图处理：
```python
elif intent == "crypto_price":
    return await self._handle_crypto_price(user_input, entities, context)

elif intent == "crypto_analysis":
    return await self._handle_crypto_analysis(user_input, entities, context)
```

3. 添加新的处理方法：
```python
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
```

**Step 2: 验证导入正常**

Run: `cd /home/chery/personal/MarketPulse && python -c "from core.agents.trading_assistant_agent import TradingAssistantAgent; print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
git add core/agents/trading_assistant_agent.py
git commit -m "feat(agents): integrate Binance data into TradingAssistantAgent"
```

---

## Task 9: 更新 NLU 支持加密货币意图

**Files:**
- Modify: `/home/chery/personal/MarketPulse/core/dialogue/nlu.py`

**Step 1: 查看当前 NLU 实现**

先读取文件了解结构，然后添加新的意图识别规则。

**Step 2: 添加加密货币相关意图**

在意图识别逻辑中添加：

```python
# 加密货币价格查询意图
crypto_price_patterns = [
    r"(btc|eth|比特币|以太坊|加密货币).*(价格|多少钱|行情)",
    r"(价格|多少钱|行情).*(btc|eth|比特币|以太坊)",
    r"(btc|eth|bitcoin|ethereum)\s*(usdt)?",
]

# 加密货币分析意图
crypto_analysis_patterns = [
    r"(btc|eth|比特币|以太坊).*(k线|分析|走势|趋势)",
    r"(k线|分析|走势).*(btc|eth|比特币|以太坊)",
]
```

**Step 3: Commit**

```bash
git add core/dialogue/nlu.py
git commit -m "feat(nlu): add crypto price and analysis intent recognition"
```

---

## Task 10: 端到端测试

**Files:**
- Create: `/home/chery/personal/MarketPulse/tests/integration/test_binance_integration.py`

**Step 1: 创建集成测试**

```python
"""Binance 集成端到端测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBinanceIntegration:
    """Binance API 集成测试"""

    @pytest.fixture
    async def client(self):
        from api.app import app
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_get_btc_price(self, client):
        """测试获取 BTC 价格"""
        response = await client.get("/api/v1/market/price/BTCUSDT")
        assert response.status_code == 200

        data = response.json()
        assert data["symbol"] == "BTCUSDT"
        assert data["price"] > 0
        assert data["source"] in ["websocket", "rest"]

    async def test_get_eth_ticker(self, client):
        """测试获取 ETH 24h 统计"""
        response = await client.get("/api/v1/market/ticker/ETHUSDT")
        assert response.status_code == 200

        data = response.json()
        assert data["symbol"] == "ETHUSDT"
        assert "price_change_percent" in data

    async def test_get_klines(self, client):
        """测试获取 K 线"""
        response = await client.get(
            "/api/v1/market/klines/BTCUSDT",
            params={"interval": "1h", "limit": 10}
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 10
        assert all("open" in k and "close" in k for k in data)

    async def test_get_status(self, client):
        """测试获取状态"""
        response = await client.get("/api/v1/market/status")
        assert response.status_code == 200

        data = response.json()
        assert "fetch_status" in data
        assert "websocket" in data

    async def test_invalid_symbol(self, client):
        """测试无效交易对"""
        response = await client.get("/api/v1/market/price/INVALIDXXX")
        assert response.status_code == 500

    async def test_invalid_interval(self, client):
        """测试无效 K 线周期"""
        response = await client.get(
            "/api/v1/market/klines/BTCUSDT",
            params={"interval": "2h"}  # 无效周期
        )
        assert response.status_code == 422  # Validation error
```

**Step 2: 运行集成测试**

Run: `cd /home/chery/personal/MarketPulse && pytest tests/integration/test_binance_integration.py -v`

Expected: All tests PASS (需要网络连接)

**Step 3: Commit**

```bash
git add tests/integration/test_binance_integration.py
git commit -m "test: add Binance integration end-to-end tests"
```

---

## Task 11: 更新文档

**Files:**
- Modify: `/home/chery/personal/MarketPulse/CLAUDE.md`

**Step 1: 在 CLAUDE.md 添加 Binance 相关文档**

在 "新闻源扩展" 部分之后添加：

```markdown
## Binance 加密货币数据

项目集成了 Binance 公开 API（无需 API Key）：

### 数据获取方式

- **WebSocket 实时推送**: BTC、ETH 价格和 24h 统计，服务启动时自动连接
- **REST API 按需获取**: K 线数据和其他币种，带智能缓存

### K 线缓存策略

| 周期 | 缓存时间 |
|------|----------|
| 1m   | 30 秒    |
| 15m  | 5 分钟   |
| 1h   | 15 分钟  |
| 4h   | 30 分钟  |
| 1d   | 2 小时   |

### API 端点

- `GET /api/v1/market/price/{symbol}` - 获取价格
- `GET /api/v1/market/ticker/{symbol}` - 获取 24h 统计
- `GET /api/v1/market/klines/{symbol}?interval=1h&limit=100` - 获取 K 线
- `GET /api/v1/market/status` - 获取数据源状态

### 配置项

```python
BINANCE_WS_SYMBOLS = ["BTCUSDT", "ETHUSDT"]  # WebSocket 订阅币种
BINANCE_WS_RECONNECT_DELAY = 5               # 重连延迟秒数
BINANCE_KLINE_CACHE_TTL = {...}              # K 线缓存配置
```
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Binance integration documentation"
```

---

## 实现完成检查清单

- [ ] Task 1: 添加 Binance 配置项
- [ ] Task 2: 创建获取状态管理器
- [ ] Task 3: 创建 Binance 数据结构
- [ ] Task 4: 实现 REST API 客户端
- [ ] Task 5: 实现 WebSocket 客户端
- [ ] Task 6: 创建统一服务
- [ ] Task 7: 创建 Market API 路由
- [ ] Task 8: 集成到交易助手 Agent
- [ ] Task 9: 更新 NLU 意图识别
- [ ] Task 10: 端到端测试
- [ ] Task 11: 更新文档

---

## 验收标准

1. 服务启动后自动连接 Binance WebSocket，订阅 BTC/ETH 实时价格
2. 用户查询 BTC/ETH 价格时，直接从缓存返回，无加载延迟
3. 用户查询其他币种或 K 线时，显示加载状态，然后返回数据
4. 后端日志记录所有 API 请求状态和耗时
5. 所有测试通过
