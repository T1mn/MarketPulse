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
