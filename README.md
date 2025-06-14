# MarketPulse - 金融资讯 AI 分析推送服务

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

</div>

MarketPulse 是一个轻量级的金融资讯分析推送服务，它基于 Google Gemini AI 和 Bark 推送服务构建，能够自动获取最新的金融新闻，进行智能分析，并将分析结果推送到您的设备。

> 本项目完全开源，欢迎社区贡献和改进。如果您觉得这个项目对您有帮助，欢迎给个 star ⭐️

## 核心特性

- 🤖 基于 [Google Gemini AI](https://github.com/google/generative-ai-python) 的智能分析
- 🔔 通过 [Bark](https://github.com/Finb/Bark) 实现多设备实时推送
- 📰 通过 [Finnhub](https://finnhub.io/) 获取最新金融新闻（支持 Reuters、Bloomberg 等权威来源）
- 📊 提供市场影响评估和投资建议
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
git clone https://github.com/T1mn/MarketPulse.git
cd MarketPulse
```

### 3. 创建虚拟环境并安装依赖

```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

uv pip install -r requirements.txt

uv pip install -e .
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
python ./MarketPulse/main.py
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
- `google-generativeai`: [Google Gemini AI](https://github.com/google/generative-ai-python) 接口
- `python-dotenv`: 环境变量管理
- `schedule`: 定时任务调度
- `requests`: HTTP 请求

## 贡献指南

我们欢迎任何形式的贡献，包括但不限于：
- 提交问题和建议
- 改进文档
- 提交代码改进
- 分享使用经验

## 致谢

- [Google Gemini AI](https://github.com/google/generative-ai-python) - 提供强大的 AI 分析能力
- [Bark](https://github.com/Finb/Bark) - 提供便捷的推送服务
- [Finnhub](https://finnhub.io/) - 提供优质的金融新闻数据 API


## 许可证

MIT License 

[![Star History Chart](https://api.star-history.com/svg?repos=T1mn/MarketPulse&type=Date)](https://www.star-history.com/#T1mn/MarketPulse&Date)
