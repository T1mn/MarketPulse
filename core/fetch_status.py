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
