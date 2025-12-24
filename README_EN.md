# MarketPulse - Financial News AI Analysis Notification Service

<div align="center">

[中文版本](README.md)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

</div>

> This project is completely open source. Community contributions and improvements are welcome. If you find this project helpful, please consider giving it a star ⭐️

## Contributing

We welcome all forms of contributions, including but not limited to:
- Submitting issues and suggestions
- Improving documentation
- Submitting code improvements
- Sharing usage experiences

MarketPulse is a lightweight financial news analysis service built on Google Gemini AI. It automatically fetches the latest financial news, performs intelligent analysis, and delivers results with clear **investment advice**, **confidence scores**, and **source reliability** to your devices via **Bark** and **PushPlus**.

## Core Features

- 🤖 Intelligent analysis powered by [Google Gemini AI](https://github.com/google/generative-ai-python)
- 🔔 Real-time multi-device notifications via [Bark](https://github.com/Finb/Bark) and [PushPlus](https://www.pushplus.plus/)
- 📰 Latest financial news from [Finnhub](https://finnhub.io/)
- 📊 Provides market impact, investment advice, confidence scores, and source reliability (as percentages)
- ⚙️ Multi-channel, multi-device push support with optimized message formatting
- 🔄 Automatic deduplication to prevent repeat notifications
- 🛡️ Secure configuration using environment variables
- 🎛️ Daemon process management (start / stop / restart / status)
- 🧠 State management to automatically handle API rate limits

## Push Previews

<details>
<summary>Click to see Bark and PushPlus notification previews</summary>

#### PushPlus Wechat Notification

![PushPlus Preview](img/pushplus.png)

#### Bark Notification

Markdown does not support embedded videos, but you can [click here to see a screen recording of a Bark notification](img/bark.mp4).

</details>

## System Requirements

- Python 3.8+
- uv (recommended for Python environment management)

## Quick Start

### 1. Install uv (Optional but Recommended)

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

Edit the `.env` file with your API keys:

```env
# API Keys
FINNHUB_API_KEY=your_finnhub_api_key
GEMINI_API_KEY=your_gemini_api_key

# Bark Keys (at least one is required)
BARK_KEY_1=your_first_bark_key
# BARK_KEY_2=your_second_bark_key

# PushPlus Token (optional)
PUSHPLUS_TOKEN=your_pushplus_token
# PushPlus Topic (optional, sends to your account if left blank)
PUSHPLUS_TOPIC=your_topic_code
```

### 5. Run the Service

```bash
# Run directly in the foreground (for debugging)
python -m MarketPulse.main

# Or run as a daemon in the background (recommended)
python -m MarketPulse.daemon_manager start
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

1.  **API Keys**: Ensure all required API keys are configured correctly.
2.  **Environment Management**: Using `uv` is recommended for better dependency resolution.
3.  **First Run**: The service runs a job immediately on startup, then follows the interval set in `config.py`.
4.  **State File**: Processed news IDs and notifier status (e.g., rate limits) are saved in `app_state.json` to prevent duplicate notifications and respect API limits.

## Dependencies

Main dependencies include:
- `google-generativeai`: [Google Gemini AI](https://github.com/google/generative-ai-python) interface
- `python-dotenv`: Environment variable management
- `schedule`: Task scheduling
- `requests`: HTTP requests

## Acknowledgments

- [Google Gemini AI](https://github.com/google/generative-ai-python) - For providing powerful AI analysis capabilities
- [Bark](https://github.com/Finb/Bark) - For providing convenient push notification service
- [Finnhub](https://finnhub.io/) - For providing high-quality financial news data API

## Service Management

### Running as a Daemon

MarketPulse supports running as a daemon service with complete process management:

```bash
# Start the service
python -m MarketPulse.daemon_manager start

# Stop the service
python -m MarketPulse.daemon_manager stop

# Restart the service
python -m MarketPulse.daemon_manager restart

# Check service status
python -m MarketPulse.daemon_manager status
```

The service will run completely in the background without occupying your terminal. You can safely close your terminal after starting the service.

### Logging System

The service uses a hierarchical logging system. All log files are stored in the `logs` directory:

- `logs/market_pulse.log`: Main application logs
- `logs/daemon.log`: Daemon process logs

Monitor logs in real-time:
```bash
# View main application logs
tail -f logs/market_pulse.log

# View daemon process logs
tail -f logs/daemon.log
```

Log files are automatically rotated:
- Main log: Maximum 10MB per file, keeps 5 backup files
- Daemon log: Maximum 5MB per file, keeps 3 backup files

### Process Management

The service maintains a PID file at `market_pulse.pid` for process management. You don't need to handle this file directly as it's managed by the daemon manager.

Key features:
- Complete detachment from terminal
- Automatic process management
- Graceful startup and shutdown
- Signal handling (SIGTERM, SIGINT)

## License

MIT License 

[![Star History Chart](https://api.star-history.com/svg?repos=T1mn/MarketPulse&type=Date)](https://www.star-history.com/#T1mn/MarketPulse&Date)