"""基础配置"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """应用基础配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== 应用信息 ====================
    APP_NAME: str = "MarketPulse"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # ==================== API Keys ====================
    # 原有 API Keys
    FINNHUB_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # 新增 API Keys
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None  # 备用

    # ==================== 推送服务 ====================
    BARK_KEY_1: Optional[str] = None
    BARK_KEY_2: Optional[str] = None
    BARK_KEY_3: Optional[str] = None
    PUSHPLUS_TOKEN: Optional[str] = None
    PUSHPLUS_TOPIC: str = ""

    # ==================== 数据库 ====================
    REDIS_URL: str = "redis://localhost:6379/0"
    VECTOR_DB_PATH: str = str(BASE_DIR / "data" / "embeddings")

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = BASE_DIR / "logs"

    # ==================== 服务配置 ====================
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # ==================== 安全配置 ====================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ==================== CORS 配置 ====================
    CORS_ORIGINS: List[str] = ["*"]

    # ==================== 业务配置 ====================
    # 新闻获取间隔（分钟）
    NEWS_FETCH_INTERVAL: int = 30

    # 每批处理的新闻数量
    NEWS_BATCH_SIZE: int = 5

    # 顶级新闻源
    TOP_TIER_NEWS_SOURCES: List[str] = [
        "Reuters",
        "Bloomberg",
        "Dow Jones Newswires",
        "Associated Press",
        "The Wall Street Journal",
        "Financial Times",
        "CLS",
        "Not a Tesla App",
    ]

    # ==================== 功能开关 ====================
    FETCH_GENERAL_NEWS: bool = False
    FETCH_FOREX_NEWS: bool = False
    FETCH_CRYPTO_NEWS: bool = False
    FETCH_COMPANY_NEWS: bool = False
    FETCH_CHINA_A_SHARE_NEWS: bool = False
    FETCH_CLS_NEWS: bool = True
    FETCH_BLOOMBERG_RSS: bool = False
    FETCH_REUTERS_RSS: bool = False
    FETCH_WSJ_RSS: bool = False
    FETCH_NOTATESLA_NEWS: bool = True

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

    FILTER_TO_TOP_TIER_ONLY: bool = True

    @property
    def bark_keys(self) -> List[str]:
        """获取所有有效的 Bark Keys"""
        keys = []
        for i in range(1, 4):
            key = getattr(self, f"BARK_KEY_{i}", None)
            if key:
                keys.append(key)
        return keys

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保日志目录存在
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
