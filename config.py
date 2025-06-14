import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# ===================== API Keys 配置 =====================
# 从环境变量获取API Keys
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ===================== 新闻获取模块配置 =====================
# Finnhub新闻类别，'general' 代表一般财经新闻
NEWS_CATEGORY = "general"

# 新闻获取间隔（分钟）
NEWS_FETCH_INTERVAL = 30

# 每次获取的最新新闻数量限制
MAX_NEWS_COUNT = 10

# 信任的新闻源
TRUSTED_SOURCES = [
    "Reuters",
    "Bloomberg",
    "The Wall Street Journal",
    "Associated Press",
    "CNBC",
    "Dow Jones Newswires",
    "MarketWatch"
]

# 美国市场股票代码
US_MARKET_SYMBOLS = [
    "SPY",    # 标普500 ETF，代表整个市场
    "DIA",    # 道琼斯指数 ETF
    "QQQ",    # 纳斯达克100 ETF
    "AAPL",   # 苹果
    "MSFT",   # 微软
    "GOOGL",  # 谷歌
    "AMZN",   # 亚马逊
    "TSLA"    # 特斯拉
]

# ===================== 推送模块配置 =====================
# Bark 设备的 Keys（从环境变量获取）
BARK_KEYS = []
for i in range(1, 4):  # 支持最多3个设备
    key = os.getenv(f'BARK_KEY_{i}')
    if key:
        BARK_KEYS.append(key)

# Bark 推送分组
BARK_GROUP = "MarketPulse-金融资讯AI分析推送"

# ===================== 状态管理配置 =====================
# 用于存储已处理新闻ID的文件路径
PROCESSED_NEWS_FILE = "processed_news.json"