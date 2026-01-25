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
