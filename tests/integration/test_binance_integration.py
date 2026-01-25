"""Binance 集成端到端测试"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
class TestBinanceIntegration:
    """Binance API 集成测试"""

    @pytest.fixture
    def mock_binance_service(self):
        """模拟 Binance 服务"""
        from sources.binance import CryptoPrice, Ticker24h, Kline

        mock_service = MagicMock()
        mock_service.get_price = AsyncMock(return_value=(
            CryptoPrice(symbol="BTCUSDT", price=43250.00),
            "rest"
        ))
        mock_service.get_24h_ticker = AsyncMock(return_value=(
            Ticker24h(
                symbol="BTCUSDT",
                price_change=500.0,
                price_change_percent=1.17,
                last_price=43250.00,
                high_price=43800.00,
                low_price=42500.00,
                volume=12345.67,
                quote_volume=534567890.12,
            ),
            "rest"
        ))
        mock_service.get_klines = AsyncMock(return_value=[
            Kline(
                open_time=1706090400000,
                open=43000.0,
                high=43500.0,
                low=42800.0,
                close=43250.0,
                volume=1234.56,
                close_time=1706094000000,
            )
            for _ in range(10)
        ])
        mock_service.get_ws_status = MagicMock(return_value={
            "connected": True,
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "cached_prices": 2,
        })

        return mock_service

    async def test_binance_service_get_price(self):
        """测试获取价格"""
        from sources.binance import BinanceService, CryptoPrice

        service = BinanceService()
        # 模拟 WebSocket 缓存
        service.ws_client._prices["BTCUSDT"] = CryptoPrice(
            symbol="BTCUSDT",
            price=43250.00,
        )

        price, source = await service.get_price("BTCUSDT")
        assert price.symbol == "BTCUSDT"
        assert price.price == 43250.00
        assert source == "websocket"

    async def test_binance_service_get_ticker(self):
        """测试获取 24h 统计"""
        from sources.binance import BinanceService, Ticker24h

        service = BinanceService()
        # 模拟 WebSocket 缓存
        service.ws_client._tickers["ETHUSDT"] = Ticker24h(
            symbol="ETHUSDT",
            price_change=50.0,
            price_change_percent=2.5,
            last_price=2050.00,
            high_price=2100.00,
            low_price=1980.00,
            volume=50000.0,
            quote_volume=100000000.0,
        )

        ticker, source = await service.get_24h_ticker("ETHUSDT")
        assert ticker.symbol == "ETHUSDT"
        assert ticker.price_change_percent == 2.5
        assert source == "websocket"

    async def test_fetch_status_manager(self):
        """测试获取状态管理器"""
        from core.fetch_status import FetchStatusManager, FetchStatus

        manager = FetchStatusManager()

        # 开始获取
        manager.start_fetch("binance", "获取 BTC 价格")
        status = manager.get_status("binance")
        assert status["status"] == FetchStatus.FETCHING

        # 完成获取
        manager.complete_fetch("binance", success=True, elapsed_ms=100)
        status = manager.get_status("binance")
        assert status["status"] == FetchStatus.SUCCESS

    async def test_kline_cache(self):
        """测试 K 线缓存"""
        from sources.binance import KlineCache, Kline

        cache = KlineCache()

        # 设置缓存
        klines = [
            Kline(
                open_time=1706090400000,
                open=43000.0,
                high=43500.0,
                low=42800.0,
                close=43250.0,
                volume=1234.56,
                close_time=1706094000000,
            )
        ]
        cache.set("BTCUSDT:100", "1h", klines)

        # 获取缓存
        cached = cache.get("BTCUSDT:100", "1h")
        assert cached is not None
        assert len(cached) == 1
        assert cached[0].close == 43250.0

    async def test_ws_client_handle_message(self):
        """测试 WebSocket 消息处理"""
        from sources.binance import BinanceWebSocketClient

        client = BinanceWebSocketClient(symbols=["BTCUSDT"])

        # 模拟接收消息
        message = {
            "s": "BTCUSDT",
            "c": "43250.00",
            "P": "1.17",
            "h": "43800.00",
            "l": "42500.00",
            "v": "12345.67",
            "q": "534567890.12",
        }
        client._handle_ticker_message(message)

        # 验证价格已更新
        price = client.get_price("BTCUSDT")
        assert price is not None
        assert price.price == 43250.00

        # 验证统计已更新
        ticker = client.get_ticker("BTCUSDT")
        assert ticker is not None
        assert ticker.price_change_percent == 1.17


class TestDataStructures:
    """数据结构测试"""

    def test_crypto_price_to_dict(self):
        from sources.binance import CryptoPrice

        price = CryptoPrice(
            symbol="BTCUSDT",
            price=43250.00,
            timestamp="2025-01-24T10:00:00"
        )
        data = price.to_dict()

        assert data["symbol"] == "BTCUSDT"
        assert data["price"] == 43250.00
        assert data["timestamp"] == "2025-01-24T10:00:00"

    def test_kline_to_dict(self):
        from sources.binance import Kline

        kline = Kline(
            open_time=1706090400000,
            open=43000.0,
            high=43500.0,
            low=42800.0,
            close=43250.0,
            volume=1234.56,
            close_time=1706094000000,
        )
        data = kline.to_dict()

        assert data["open"] == 43000.0
        assert data["close"] == 43250.0
        assert data["high"] == 43500.0
        assert data["low"] == 42800.0

    def test_ticker_24h_to_dict(self):
        from sources.binance import Ticker24h

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
        data = ticker.to_dict()

        assert data["symbol"] == "BTCUSDT"
        assert data["price_change_percent"] == 1.17
