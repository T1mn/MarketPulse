# MarketPulse - Financial News AI Analysis Notification Service

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

</div>

MarketPulse is a lightweight financial news analysis and notification service built on top of Google Gemini AI and Bark push service. It automatically fetches the latest financial news, performs intelligent analysis, and delivers insights to your devices.

> This project is completely open source. Community contributions and improvements are welcome. If you find this project helpful, please consider giving it a star ⭐️

## Core Features

- 🤖 Intelligent analysis powered by [Google Gemini AI](https://github.com/google/generative-ai-python)
- 🔔 Real-time multi-device notifications via [Bark](https://github.com/Finb/Bark)
- 📰 Latest financial news from [Finnhub](https://finnhub.io/) (supports Reuters, Bloomberg, and other authoritative sources)
- 📊 Market impact assessment and investment recommendations
- ⚙️ Multi-device push support
- 🔄 Automatic deduplication to prevent duplicate notifications
- 🛡️ Secure environment variable configuration

## System Requirements

- Python 3.8+
- uv (recommended for Python environment management)

## Quick Start

### 1. Install uv (Recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Project

```bash
git clone https://github.com/T1mn/MarketPulse.git
cd MarketPulse
```

### 3. Create Virtual Environment and Install Dependencies

```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

uv pip install -r requirements.txt

uv pip install -e .
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` file with your API keys:

```env
# API Keys
FINNHUB_API_KEY=your_finnhub_api_key
GEMINI_API_KEY=your_gemini_api_key

# Bark Keys
BARK_KEY_1=your_first_bark_key
# BARK_KEY_2=your_second_bark_key
# BARK_KEY_3=your_third_bark_key
```

### 5. Run the Service

```bash
python ./MarketPulse/main.py
```

## Configuration Guide

### News Sources Configuration

Configure trusted news sources in `config.py`:

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

### Market Watch Configuration

Configure stock symbols to monitor:

```python
US_MARKET_SYMBOLS = [
    "SPY",    # S&P 500 ETF
    "DIA",    # Dow Jones ETF
    "QQQ",    # NASDAQ 100 ETF
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "GOOGL",  # Google
    "AMZN",   # Amazon
    "TSLA"    # Tesla
]
```

### Notification Interval Configuration

Default news check interval is 30 minutes, can be modified in `config.py`:

```python
NEWS_FETCH_INTERVAL = 30  # minutes
```

## Notification Content

Each notification includes:
- News headline
- AI analysis summary
- Market impact assessment
- Investment recommendations
- Related stock symbols
- News source link

## Important Notes

1. Ensure all API keys are properly configured
2. Using uv for environment management is recommended for better dependency resolution
3. The service runs immediately upon startup, then follows the configured interval
4. Processed news IDs are saved in `processed_news.json` to prevent duplicate notifications

## Dependencies

Main dependencies include:
- `google-generativeai`: [Google Gemini AI](https://github.com/google/generative-ai-python) interface
- `python-dotenv`: Environment variable management
- `schedule`: Task scheduling
- `requests`: HTTP requests

## Contributing

We welcome all forms of contributions, including but not limited to:
- Submitting issues and suggestions
- Improving documentation
- Submitting code improvements
- Sharing usage experiences

## Acknowledgments

- [Google Gemini AI](https://github.com/google/generative-ai-python) - For providing powerful AI analysis capabilities
- [Bark](https://github.com/Finb/Bark) - For providing convenient push notification service
- [Finnhub](https://finnhub.io/) - For providing high-quality financial news data API



## License

MIT License 

[![Star History Chart](https://api.star-history.com/svg?repos=T1mn/MarketPulse&type=Date)](https://www.star-history.com/#T1mn/MarketPulse&Date)