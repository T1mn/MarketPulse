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
