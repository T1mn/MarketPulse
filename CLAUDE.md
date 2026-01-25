# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

MarketPulse 是一个基于 AI 的金融资讯分析推送服务，用于获取金融新闻、进行智能分析，并推送投资建议到用户设备。

## 核心架构

### 主要模块结构

```
MarketPulse/
├── main.py                 # 主入口：定时任务调度和工作流编排
├── news_aggregator.py      # 新闻聚合器：从多个数据源获取新闻
├── ai_analyzer.py          # AI分析引擎：使用 Google Gemini 进行分析
├── notifier.py            # 通知推送：Bark 和 PushPlus 推送服务
├── state_manager.py       # 状态管理：已处理新闻ID和推送服务状态
├── daemon_manager.py      # 守护进程管理
├── config.py              # 配置中心
└── sources/               # 新闻源实现
    ├── finnhub.py         # Finnhub API 新闻源
    ├── rss.py             # RSS 新闻源
    ├── cailianpress.py    # 财联社新闻源
    └── notatesla.py       # Not a Tesla App 新闻源
```

### AI 分析流水线

项目使用两阶段 AI 分析流水线（在 `ai_analyzer.py` 中实现）：

1. **InformationExtractor** (gemini-1.5-flash)：从原始新闻提取精炼摘要（≤50字）
2. **MarketAnalyst** (gemini-2.0-flash-lite)：基于摘要生成投资分析，包括：
   - 市场影响评估
   - 可操作的投资建议（做多/做空/观望）
   - 信心指数（0-100%）
   - 来源可靠度评估

### 工作流程

1. `main.py` 中的 `run_job()` 定时执行（默认30分钟）
2. `news_aggregator.fetch_latest_news()` 从多个数据源获取新闻
3. 使用 `state_manager` 过滤已处理的新闻
4. 新闻分批（每批5条）通过 `ai_analyzer.run_analysis_pipeline()` 进行 AI 分析
5. 有效的分析结果通过 `notifier.send_summary_notification()` 推送
6. 更新已处理新闻ID到 `app_state.json`

## 常用命令

### 环境设置

```bash
# 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -r requirements.txt
uv pip install -e .
```

### 运行服务

```bash
# 前台运行（调试）
python -m MarketPulse.main

# 守护进程管理
python -m MarketPulse.daemon_manager start    # 启动
python -m MarketPulse.daemon_manager stop     # 停止
python -m MarketPulse.daemon_manager restart  # 重启
python -m MarketPulse.daemon_manager status   # 状态
```

### 测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_ai_analyzer.py

# 运行特定测试函数
pytest tests/test_ai_analyzer.py::test_function_name

# 带覆盖率报告
pytest --cov=MarketPulse --cov-report=html
```

### 代码格式化

```bash
# 使用项目提供的格式化脚本
./format.sh

# 手动格式化
black MarketPulse/
isort MarketPulse/

# 代码检查
flake8 MarketPulse/
```

### 日志查看

```bash
# 查看主程序日志
tail -f logs/market_pulse.log

# 查看守护进程日志
tail -f logs/daemon.log
```

## 配置要点

### 环境变量（.env 文件）

必需的 API 密钥：
- `FINNHUB_API_KEY`: Finnhub 金融数据 API
- `GEMINI_API_KEY`: Google Gemini AI API
- `BARK_KEY_1`: Bark 推送服务密钥（至少一个）
- `PUSHPLUS_TOKEN`: PushPlus 推送服务（可选）

### config.py 关键配置

- `NEWS_FETCH_INTERVAL`: 新闻获取间隔（分钟）
- `FETCH_*_NEWS`: 控制各类新闻源的开关
- `TOP_TIER_NEWS_SOURCES`: 顶级新闻源列表，用于高质量分析
- `FILTER_TO_TOP_TIER_ONLY`: 是否只处理顶级新闻源
- `MARKET_SYMBOLS`: 关注的股票代码

### 状态管理

- `app_state.json`: 存储已处理的新闻ID和推送服务状态
- `market_pulse.pid`: 守护进程 PID 文件

## AI 模型集成模式

当前使用的是基于抽象基类 `AIBaseAnalyst` 的设计模式：

```python
class AIBaseAnalyst(ABC):
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = ""  # 子类定义

    @abstractmethod
    def _create_prompt(self, articles: list) -> str:
        pass

    def run(self, articles: list):
        # 统一的 API 调用逻辑
        pass
```

如需添加新的 AI 服务（如 DeepSeek），应遵循此模式创建新的分析师类。

## 新闻源扩展

在 `sources/` 目录下添加新的新闻源时，需要：
1. 创建新的 Python 模块
2. 实现返回标准格式的新闻列表：`[{"id": str, "title": str, "content": str, "source": str, ...}]`
3. 在 `news_aggregator.py` 中集成新数据源
4. 在 `config.py` 中添加相应的配置开关

## Binance 加密货币数据

项目集成了 Binance 公开 API（无需 API Key）：

### 数据获取方式

- **WebSocket 实时推送**: BTC、ETH 价格和 24h 统计，服务启动时自动连接
- **REST API 按需获取**: K 线数据和其他币种，带智能缓存

### K 线缓存策略

| 周期 | 缓存时间 |
|------|----------|
| 1m   | 30 秒    |
| 15m  | 5 分钟   |
| 1h   | 15 分钟  |
| 4h   | 30 分钟  |
| 1d   | 2 小时   |

### API 端点

- `GET /api/v1/market/price/{symbol}` - 获取价格
- `GET /api/v1/market/ticker/{symbol}` - 获取 24h 统计
- `GET /api/v1/market/klines/{symbol}?interval=1h&limit=100` - 获取 K 线
- `GET /api/v1/market/status` - 获取数据源状态

### 配置项

```python
BINANCE_WS_SYMBOLS = ["BTCUSDT", "ETHUSDT"]  # WebSocket 订阅币种
BINANCE_WS_RECONNECT_DELAY = 5               # 重连延迟秒数
BINANCE_KLINE_CACHE_TTL = {...}              # K 线缓存配置
```

## 推送服务

支持两种推送渠道：
- **Bark**: iOS 推送，支持多设备（最多3个）
- **PushPlus**: 微信推送，支持个人和群组

推送消息格式在 `notifier.py` 中为不同渠道优化。

## 开发注意事项

- 使用 `logging` 模块记录日志，不要使用 `print()`
- 所有 AI 分析都使用中文 prompt 和中文输出
- 新闻按批处理（每批5条），避免 API 限制
- 状态文件定期保存，确保服务重启后不重复处理
