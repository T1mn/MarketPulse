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
FETCH_TOP_TIER_NEWS = True # 单独获取顶级新闻源的新闻
FETCH_FOREX_NEWS = True  # 获取外汇新闻
FETCH_CRYPTO_NEWS = True  # 获取加密货币新闻
FETCH_COMPANY_NEWS = True  # 获取美股公司新闻
FETCH_COMMODITY_NEWS = True  # 获取商品新闻(包括黄金、石油等)
FETCH_CHINA_A_SHARE_NEWS = False  # 获取中国A股新闻，打开需要付费

# 获取公司新闻的时间范围（天）
COMPANY_NEWS_DAYS_AGO = 2

# 每个类别/代码获取的新闻数量限制
MAX_NEWS_PER_CATEGORY = 10
MAX_NEWS_PER_SYMBOL = 10

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

# 中国A股核心公司列表
CHINA_A_SHARE_SYMBOLS = [
    # 科技与互联网巨头
    "601138.SS",  # 工业富联 (Foxconn Industrial Internet)
    "002230.SZ",  # 科大讯飞 (iFLYTEK)
    # 新能源与制造业龙头
    "300750.SZ",  # 宁德时代 (CATL)
    "002594.SZ",  # 比亚迪 (BYD)
    "601012.SS",  # 隆基绿能 (LONGi)
    # 消费与白酒
    "600519.SS",  # 贵州茅台 (Kweichow Moutai)
    "000858.SZ",  # 五粮液 (Wuliangye)
    # 金融与保险
    "601318.SS",  # 中国平安 (Ping An Insurance)
    "600036.SS",  # 招商银行 (China Merchants Bank)
    # 医药健康
    "600276.SS",  # 恒瑞医药 (Hengrui Medicine)
    "603259.SS",  # 药明康德 (WuXi AppTec)
    # 资源与周期股
    "601899.SS",  # 紫金矿业 (Zijin Mining)
    "600019.SS",  # 宝钢股份 (Baoshan Iron & Steel)
]

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
PUSHPLUS_TOPIC = os.getenv("PUSHPLUS_TOPIC", "")  # 默认为空

# 顶级新闻源列表，用于提供更高质量的分析和推送
TOP_TIER_NEWS_SOURCES = {
    'Reuters',
    'Bloomberg',
    'Dow Jones Newswires',
    'Associated Press',
    'The Wall Street Journal',
    'Financial Times',
    'Dow Jones'
}

# ===================== 状态管理配置 =====================

# 用于存储应用状态的文件路径, 例如已处理的新闻ID和推送服务状态
APP_STATE_FILE = "app_state.json"

# ===================== 日志配置 =====================
# 日志目录
LOG_DIR = BASE_DIR / "logs"
# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)

# 应用日志
APP_LOG_FILE = LOG_DIR / "app.log"
# 守护进程日志
DAEMON_LOG_FILE = LOG_DIR / "daemon.log"
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# PID文件路径
PID_FILE = BASE_DIR / "market_pulse.pid"
