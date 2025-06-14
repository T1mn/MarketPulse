# 金融资讯 AI 分析推送服务

这是一个基于 Python 的金融资讯分析推送服务，它能够自动获取最新的金融新闻，使用 Google Gemini AI 进行分析，并通过 Bark 推送服务将分析结果发送到您的设备。

## 功能特点

- 📰 自动获取最新金融新闻（支持 Reuters、Bloomberg 等权威来源）
- 🤖 使用 Google Gemini AI 进行智能分析
- 📊 提供市场影响评估和投资建议
- 🔔 通过 Bark 推送服务实时通知
- ⚙️ 支持多设备推送
- 🔄 自动去重，避免重复推送
- 🛡️ 安全的环境变量配置

## 系统要求

- Python 3.8+
- uv（推荐用于 Python 环境管理）

## 快速开始

### 1. 安装 uv（推荐）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆项目

```bash
git clone <your-repository-url>
cd notifier
```

### 3. 创建虚拟环境并安装依赖

```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

uv pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 文件并重命名为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 API 密钥：

```env
# API Keys
FINNHUB_API_KEY=your_finnhub_api_key
GEMINI_API_KEY=your_gemini_api_key

# Bark Keys
BARK_KEY_1=your_first_bark_key
# BARK_KEY_2=your_second_bark_key
# BARK_KEY_3=your_third_bark_key
```

### 5. 运行服务

```bash
python main.py
```

## 配置说明

### 新闻源配置

在 `config.py` 中可以配置信任的新闻源：

```python
TRUSTED_SOURCES = [
    "Reuters",
    "Bloomberg",
    "The Wall Street Journal",
    "Associated Press",
    "CNBC",
    "Dow Jones Newswires",
    "MarketWatch"
]
```

### 市场关注配置

可以配置关注的股票代码：

```python
US_MARKET_SYMBOLS = [
    "SPY",    # 标普500 ETF
    "DIA",    # 道琼斯指数 ETF
    "QQQ",    # 纳斯达克100 ETF
    "AAPL",   # 苹果
    "MSFT",   # 微软
    "GOOGL",  # 谷歌
    "AMZN",   # 亚马逊
    "TSLA"    # 特斯拉
]
```

### 推送间隔配置

默认每 30 分钟检查一次新闻，可以在 `config.py` 中修改：

```python
NEWS_FETCH_INTERVAL = 30  # 分钟
```

## 推送效果

推送通知包含以下信息：
- 新闻标题
- AI 分析摘要
- 市场影响评估
- 投资建议
- 相关股票代码
- 新闻来源链接

## 注意事项

1. 确保所有 API 密钥都已正确配置
2. 建议使用 uv 进行环境管理，以获得更好的依赖解析性能
3. 首次运行时会立即执行一次任务，之后按配置的间隔时间运行
4. 已处理的新闻 ID 会保存在 `processed_news.json` 中，避免重复推送

## 依赖说明

主要依赖包括：
- `python-dotenv`: 环境变量管理
- `schedule`: 定时任务调度
- `google-generativeai`: Google Gemini AI 接口
- `requests`: HTTP 请求

## 许可证

MIT License 