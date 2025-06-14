import os

from dotenv import load_dotenv

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
NEWS_FETCH_INTERVAL = 30

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

# ===================== 状态管理配置 =====================
# 用于存储已处理新闻ID的文件路径
PROCESSED_NEWS_FILE = "processed_news.json"
