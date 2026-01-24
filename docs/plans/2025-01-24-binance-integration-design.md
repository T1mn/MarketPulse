# Binance 集成与 API 状态指示设计

**日期：** 2025-01-24
**状态：** 已批准

---

## 概述

本设计包含两个功能：
1. **API 获取状态指示** - 前端显示加载状态 + 后端日志记录
2. **Binance 公开接口集成** - 实时价格、K线、24h统计，用于新闻分析和交易助手对话

---

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (React)                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │  状态指示组件: "[加载中] 正在获取行情..."         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                      │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ 状态管理器    │◄───│ Binance 服务  │                   │
│  │ FetchStatus  │    │ (新增模块)    │                   │
│  └──────────────┘    └──────────────┘                   │
│         │                   │                           │
│         ▼                   ▼                           │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ 日志/监控     │    │ 交易助手Agent │                   │
│  └──────────────┘    │ 新闻分析流水线 │                   │
│                      └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## Binance 数据层设计

### 混合数据获取策略

```
┌─────────────────────────────────────────────────────────┐
│                   Binance 数据层                         │
│                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐     │
│  │  WebSocket 实时流    │    │   REST API 按需获取   │     │
│  │  (BTC, ETH)         │    │   (其他币种/K线)      │     │
│  └─────────────────────┘    └─────────────────────┘     │
│            │                          │                 │
│            ▼                          ▼                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │              内存缓存 (CryptoDataStore)          │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │     交易助手 Agent  /  新闻分析流水线             │    │
│  │     (直接读取缓存，无需等待)                      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### WebSocket 实时订阅

- **订阅币种：** BTCUSDT, ETHUSDT
- **订阅内容：** 实时价格 + 24h 统计
- **触发时机：** 服务启动时自动连接
- **重连机制：** 断开后 5 秒自动重连

### REST API 按需获取

- **用途：** K线数据、非主流币种价格查询
- **K线周期：** 1m, 15m, 1h, 4h, 1d
- **完整周期保证：** 自动剔除当前未完成的 K 线

---

## K 线缓存策略

| 周期 | 缓存时间 | 说明 |
|------|----------|------|
| 1m   | 30 秒    | 高频更新 |
| 15m  | 5 分钟   | 中频 |
| 1h   | 15 分钟  | |
| 4h   | 30 分钟  | |
| 1d   | 2 小时   | 日线变化慢 |

```python
async def get_klines(symbol: str, interval: str, limit: int) -> list:
    """
    获取 K 线数据

    - 只返回已完成的 K 线（排除当前未收盘的 K 线）
    - Binance API 返回的最后一根 K 线是当前未完成的
    - 处理时自动剔除最后一根
    """
    raw_klines = await self._fetch_klines(symbol, interval, limit + 1)
    completed_klines = raw_klines[:-1]
    return completed_klines[-limit:]
```

---

## 获取状态管理器

### 状态类型

```python
class FetchStatus:
    IDLE = "idle"           # 空闲
    FETCHING = "fetching"   # 获取中
    SUCCESS = "success"     # 成功
    ERROR = "error"         # 失败
```

### 接口设计

```python
class FetchStatusManager:
    def start_fetch(source: str, description: str)
    def complete_fetch(source: str, success: bool)
    def get_current_status() -> dict
```

---

## 前端状态指示

### 状态样式

- `cached` - 无提示，直接显示内容
- `fetching` - `[加载中]` + 加载动画（spinner）
- `error` - `[错误]` + 红色文字

### 交互示例

```
┌─────────────────────────────────────────┐
│  用户: BTC 现在多少钱？                   │
├─────────────────────────────────────────┤
│  BTC 实时价格                            │
│  $43,250.00 (+2.3%)                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  用户: 给我看 SOL 的 4 小时 K 线          │
├─────────────────────────────────────────┤
│  [加载中] 正在获取 SOL 行情数据...        │
├─────────────────────────────────────────┤
│  SOL/USDT 4H K线                         │
│  [K线图表...]                            │
└─────────────────────────────────────────┘
```

---

## 文件结构

### 新增文件

```
MarketPulse/
├── sources/
│   └── binance.py          # Binance REST API + WebSocket
├── core/
│   └── fetch_status.py     # 获取状态管理器
└── api/
    └── routes/
        └── market.py       # 行情数据 API 端点
```

### 修改文件

```
├── api/app.py              # 注册 market 路由 + WebSocket 生命周期
├── core/agents/
│   └── trading_assistant_agent.py  # 集成 Binance 数据查询
├── MarketPulse/
│   └── news_aggregator.py  # 集成 Binance 作为加密货币数据源
└── config/
    └── settings.py         # 新增 Binance 相关配置项
```

### 配置项

```python
# Binance 配置
BINANCE_WS_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
BINANCE_WS_RECONNECT_DELAY = 5

# K 线缓存配置（秒）
BINANCE_KLINE_CACHE_TTL = {
    "1m": 30,
    "15m": 300,
    "1h": 900,
    "4h": 1800,
    "1d": 7200,
}
```

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| WebSocket 断开 | 自动重连（延迟 5 秒），重连期间使用缓存数据 |
| REST API 超时 | 重试 2 次，间隔 1 秒 |
| API 返回错误 | 记录日志，返回缓存数据或错误提示 |
| 币种不存在 | 返回明确错误信息："无效的交易对" |

---

## 后端日志

```
INFO  [Binance] WebSocket 已连接，订阅: BTCUSDT, ETHUSDT
INFO  [Binance] 收到价格更新: BTCUSDT = 43250.00
WARN  [Binance] WebSocket 断开，5 秒后重连...
INFO  [Binance] WebSocket 重连成功
INFO  [FetchStatus] REST API 请求: SOL 4h K线 (耗时 0.23s)
ERROR [Binance] API 请求失败: 429 Too Many Requests
```

---

## Binance 服务模块接口

```python
class BinanceService:
    """Binance 公开数据服务"""

    # 实时价格
    async def get_price(symbol: str) -> dict

    # 24小时行情统计
    async def get_24h_ticker(symbol: str) -> dict

    # K线历史数据
    async def get_klines(symbol: str, interval: str, limit: int) -> list

    # 批量获取价格
    async def get_all_prices() -> list
```

---

## 后续扩展（可选）

- 监控指标：WebSocket 连接状态、API 请求成功率、平均响应时间
- 更多币种的 WebSocket 订阅
- K线图表前端组件
