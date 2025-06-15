import logging
import sys
from logging.handlers import RotatingFileHandler

from MarketPulse import config


def setup_logging(to_console=False):
    """
    配置日志系统，支持同时输出到文件和控制台（可选）
    """
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    # 防止重复添加处理程序
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 创建循环文件处理程序（最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        config.APP_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 如果需要，添加控制台输出
    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logging.info("日志系统初始化完成")


def setup_daemon_logging():
    """
    配置守护进程专用的日志处理
    """
    daemon_logger = logging.getLogger("daemon")
    daemon_logger.setLevel(logging.INFO)

    # 创建守护进程日志处理程序
    handler = RotatingFileHandler(
        config.DAEMON_LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s - DAEMON - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    daemon_logger.addHandler(handler)

    return daemon_logger
