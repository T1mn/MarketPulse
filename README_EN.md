# Financial News AI Analysis Notification Service

A Python-based financial news analysis and notification service that automatically fetches the latest financial news, analyzes it using Google Gemini AI, and delivers insights to your devices through the Bark notification service.

## Features

- 📰 Automatic fetching of latest financial news (supports Reuters, Bloomberg, and other authoritative sources)
- 🤖 Intelligent analysis using Google Gemini AI
- 📊 Market impact assessment and investment recommendations
- 🔔 Real-time notifications via Bark push service
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
git clone <your-repository-url>
cd notifier
```

### 3. Create Virtual Environment and Install Dependencies

```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

uv pip install -r requirements.txt
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
python main.py
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
- `python-dotenv`: Environment variable management
- `schedule`: Task scheduling
- `google-generativeai`: Google Gemini AI interface
- `requests`: HTTP requests

## License

MIT License 