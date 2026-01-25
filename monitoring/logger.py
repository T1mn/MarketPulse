"""日志配置"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import settings


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    to_console: bool = True
):
    """
    配置日志系统

    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        to_console: 是否输出到控制台
    """
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or str(settings.LOG_DIR / "app.log")

    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 控制台处理器
    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 控制台使用彩色格式（如果可能）
        try:
            from colorlog import ColoredFormatter
            console_formatter = ColoredFormatter(
                '%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(console_formatter)
        except ImportError:
            console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)

    # 设置第三方库日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    logging.info(f"✅ Logging configured: level={log_level}, file={log_file}")


# 在导入时自动配置
setup_logging()
