import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 加载.env文件
load_dotenv()

# ===================== API Keys 配置 =====================
# 从环境变量获取API Keys
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ===================== 新闻获取模块配置 =====================
# 是否开启各类新闻的获取
FETCH_GENERAL_NEWS = True  # 获取宏观新闻
FETCH_FOREX_NEWS = True  # 获取外汇新闻
FETCH_CRYPTO_NEWS = True  # 获取加密货币新闻
FETCH_COMPANY_NEWS = True  # 获取美股公司新闻

# 获取公司新闻的时间范围（天）
COMPANY_NEWS_DAYS_AGO = 2

# 每个类别/代码获取的新闻数量限制
MAX_NEWS_PER_CATEGORY = 5
MAX_NEWS_PER_SYMBOL = 5

# 新闻获取间隔（分钟）
NEWS_FETCH_INTERVAL = 15

# 市场分类配置
MARKET_SYMBOLS = {
    "etf": [  # 大盘指数ETF
        "SPY",  # 标普500 ETF，代表整个市场
        "DIA",  # 道琼斯指数 ETF
        "QQQ",  # 纳斯达克100 ETF
        "AAPL",  # 苹果
        "MSFT",  # 微软
        "GOOGL",  # 谷歌
        "AMZN",  # 亚马逊
        "TSLA",  # 特斯拉
    ],
}

# ===================== 推送模块配置 =====================
# Bark 设备的 Keys（从环境变量获取）
BARK_KEYS = []
for i in range(1, 4):  # 支持最多3个设备
    key = os.getenv(f"BARK_KEY_{i}")
    if key:
        BARK_KEYS.append(key)

# Bark 推送分组
BARK_GROUP = "MarketPulse-金融资讯AI分析推送"

# PushPlus 推送配置
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
# PushPlus 推送群组代码 (可选, 留空则推送到个人)
PUSHPLUS_TOPIC = os.getenv("PUSHPLUS_TOPIC")

# ===================== 状态管理配置 =====================

# 用于存储应用状态的文件路径, 例如已处理的新闻ID和推送服务状态
APP_STATE_FILE = "app_state.json"

# ===================== 日志配置 =====================
# 日志目录
LOG_DIR = BASE_DIR / "logs"
# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)

# 应用日志
APP_LOG_FILE = LOG_DIR / "market_pulse.log"
# 守护进程日志
DAEMON_LOG_FILE = LOG_DIR / "daemon.log"
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# PID文件路径
PID_FILE = BASE_DIR / "market_pulse.pid"
