# 新闻推送服务集成计划

## 背景

当前项目存在两套独立入口：
- `main.py` - 新的统一 API 服务
- `MarketPulse/main.py` - 原新闻定时推送服务

目标是将原新闻推送服务集成到新 API 中作为后台任务。

## 当前状态

### 原服务 (`MarketPulse/`)
- 定时任务：每 30 分钟执行一次 `run_job()`
- 流程：获取新闻 → 过滤已处理 → AI 分析 → 推送通知
- 状态管理：`app_state.json` 存储已处理新闻 ID

### 新服务 (`api/`)
- FastAPI 应用，支持 chatbot、market 等 API
- 已有生命周期管理（lifespan）启动 Binance WebSocket

## 集成方案

### 方案 A：后台定时任务（推荐）
在 FastAPI lifespan 中启动后台定时任务。

```python
# api/app.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动定时任务
    scheduler.add_job(run_news_job, 'interval', minutes=30)
    scheduler.start()

    yield

    scheduler.shutdown()
```

优点：
- 统一进程管理
- 共享配置和日志
- 便于监控

### 方案 B：独立 Worker 进程
保持独立，通过消息队列协调。

优点：
- 隔离性好
- 可独立扩展

缺点：
- 部署复杂度增加

## 实施步骤

1. **重构新闻服务为异步**
   - 将 `MarketPulse/main.py` 中的 `run_job()` 改为 async
   - 确保 AI 分析和推送使用 async HTTP 客户端

2. **创建后台任务模块**
   - 新建 `services/news_scheduler.py`
   - 封装定时任务逻辑

3. **集成到 API 生命周期**
   - 在 `api/app.py` 的 lifespan 中启动调度器
   - 添加配置开关控制是否启用

4. **添加管理 API**
   - `POST /api/v1/admin/news/trigger` - 手动触发
   - `GET /api/v1/admin/news/status` - 查看状态

5. **迁移状态管理**
   - 将 `app_state.json` 迁移到 Redis（可选）
   - 或保持文件存储，统一路径

## 依赖

```
apscheduler>=3.10.0
```

## 配置

```python
# config/base.py
NEWS_SCHEDULER_ENABLED: bool = True
NEWS_FETCH_INTERVAL: int = 30  # 分钟
```

## 测试

- 单元测试：调度器启停
- 集成测试：API 触发新闻任务
- E2E 测试：完整流程验证
