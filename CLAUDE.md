# CLAUDE.md

MarketPulse v2.0 - 企业级金融智能助手

## 项目概述

TypeScript 全栈金融智能助手，提供：
- AI 驱动的金融分析（DeepSeek / OpenAI / Ollama / **vLLM 自部署模型**）
- Tool Calling - LLM 自动调用 Binance/新闻 API 获取实时数据
- RAG 知识库 - 基于 ChromaDB 的金融知识检索增强生成
- 实时加密货币行情（Binance API）
- 美股行情（Yahoo Finance）
- 贵金属行情（黄金、白银 via Yahoo Finance）
- 金融新闻聚合（RSS + Finnhub）
- **Twitter 推文抓取**（Playwright 自动化）
- 多端支持（Web / TUI / Desktop）

## 技术栈

| 层级 | 技术 |
|------|------|
| Runtime | Bun |
| 语言 | TypeScript |
| API Server | Hono |
| AI SDK | @ai-sdk/* (Vercel) |
| 向量数据库 | ChromaDB |
| Embedding | Ollama (nomic-embed-text) / OpenAI |
| Web 前端 | React + Vite + Tailwind |
| Monorepo | Turbo + Bun workspaces |

## 项目结构

```
MarketPulse/
├── packages/
│   ├── shared/     # 共享类型和工具
│   ├── core/       # 核心业务逻辑
│   │   ├── src/
│   │   │   ├── providers.ts   # LLM 提供商
│   │   │   ├── session.ts     # 会话管理 (Tool Calling + RAG)
│   │   │   ├── tools.ts       # AI 工具定义
│   │   │   ├── market.ts      # Binance API
│   │   │   ├── news.ts        # 新闻聚合
│   │   │   ├── rag.ts         # RAG 服务 (ChromaDB)
│   │   │   ├── embedding.ts   # Embedding 服务 (Ollama/OpenAI)
│   │   │   ├── twitter.ts     # Twitter 数据类型与解析
│   │   │   ├── twitter-store.ts # Twitter SQLite 存储
│   │   │   └── twitter-scraper.ts # Playwright 自动抓取
│   │   └── data/knowledge/    # 预置金融知识库
│   ├── server/     # Hono HTTP Server
│   ├── cli/        # CLI 入口
│   ├── web/        # React Web 前端
│   ├── tui/        # 终端 UI (待实现)
│   ├── desktop/    # Tauri 桌面应用 (待实现)
│   └── sdk/        # TypeScript SDK
├── package.json    # Monorepo 根配置
├── turbo.json      # Turbo 配置
└── tsconfig.json   # TypeScript 配置
```

## 快速开始

```bash
# 安装依赖
bun install --registry=https://registry.npmmirror.com

# 构建
bun run build

# 启动开发环境（自动启动 ChromaDB + Server）
bun run dev

# 或启动全部（ChromaDB + Server + Web）
bun run dev:all
```

### 可用命令

| 命令 | 说明 |
|------|------|
| `bun run dev` | 启动 ChromaDB + Server |
| `bun run dev:all` | 启动 ChromaDB + Server + Web |
| `bun run dev:server` | 仅启动 Server |
| `bun run dev:web` | 仅启动 Web 前端 |
| `bun run build` | 构建所有包 |

## 网络与镜像配置

```bash
# 使用淘宝镜像
bun install --registry=https://registry.npmmirror.com

# 或使用代理
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
bun install
```

## 环境变量

必需（至少一个 LLM）：
- `DEEPSEEK_API_KEY` - DeepSeek API
- `OPENAI_API_KEY` - OpenAI API（或 vLLM 任意值）

OpenAI 兼容服务（vLLM / LocalAI 等）：
- `OPENAI_BASE_URL` - 自定义服务地址（如 `http://172.26.190.100:1995`）
- `OPENAI_MODEL_NAME` - 模型名称（如 `qwen3-8b`）

可选：
- `OLLAMA_BASE_URL` - 本地 Ollama 服务（也用于 RAG embedding）
- `FINNHUB_API_KEY` - 金融新闻数据
- `CHROMA_HOST` - ChromaDB 地址（默认 http://localhost:8000）
- `PORT` - 服务器端口（默认 3000）

Twitter Scraper：
- `TWITTER_AUTH_TOKEN` - Twitter 认证 Token（必需）
- `TWITTER_SEARCH_QUERIES` - 抓取查询，逗号分隔，支持 Twitter 搜索语法（默认 `BTC,ETH,crypto`）
  - 关键词搜索：`BTC`、`ETH`、`crypto`
  - 用户推文：`from:elonmusk`、`from:realDonaldTrump`、`from:saylor` 等
  - 当前默认配置：`BTC,ETH,crypto,from:elonmusk,from:realDonaldTrump,from:saylor,from:BillGates,from:JeffBezos,from:WarrenBuffett`
- `TWITTER_SCRAPE_INTERVAL` - 定时抓取间隔，分钟（默认 30）
- `TWITTER_MAX_TWEETS_PER_QUERY` - 每个关键词最大推文数（默认 100）
- `TWITTER_SCRAPE_ON_STARTUP` - 启动时立即抓取（默认 false）

> **注意**：`export` 设置的环境变量会覆盖 `.env` 文件中的定义

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 信息 |
| `/health` | GET | 健康检查 |
| `/api/v1/chat` | POST | 聊天（SSE streaming） |
| `/api/v1/session` | POST | 创建会话 |
| `/api/v1/market/price/:symbol` | GET | 单个价格 |
| `/api/v1/market/prices` | GET | 批量价格 |
| `/api/v1/market/klines/:symbol` | GET | K线数据 |
| `/api/v1/news` | GET | 新闻列表 |
| `/api/v1/news/search?q=` | GET | 搜索新闻 |
| `/api/v1/rag/stats` | GET | RAG 知识库状态 |
| `/api/v1/twitter/search?q=` | GET | 搜索推文 |
| `/api/v1/twitter/top` | GET | 热门推文 |
| `/api/v1/twitter/stats` | GET | 推文统计 |
| `/api/v1/twitter/scrape` | POST | 手动触发抓取 |
| `/api/v1/twitter/scraper/status` | GET | 抓取器状态 |
| `/api/v1/twitter/scraper/start` | POST | 启动定时抓取 |
| `/api/v1/twitter/scraper/stop` | POST | 停止定时抓取 |

## Tool Calling

LLM 自动识别用户意图并调用工具：

| 工具 | 功能 | 数据源 |
|------|------|--------|
| `getCryptoPrice` | 获取加密货币实时价格（最多 10 个交易对并行） | Binance API |
| `getStockPrice` | 获取美股实时价格（最多 10 个股票并行） | Yahoo Finance |
| `getCommodityPrice` | 获取贵金属价格（黄金/白银期货、ETF） | Yahoo Finance |
| `searchNews` | 搜索金融新闻 | RSS + Finnhub |

- 调用模式：自动（LLM 决定何时调用）
- 最大步数：5（`maxSteps: 5`）

### Tool Calling 工作原理

```
用户消息 → AI SDK 发送 tools 定义给 LLM → LLM 决定调用哪个工具
    → vLLM 解析工具调用格式 → AI SDK 执行工具 → 结果返回 LLM → 生成最终回答
```

## vLLM 自部署模型

支持通过 vLLM 部署本地模型（如 Qwen3-8B），需启用 Tool Calling 支持。

### vLLM 启动命令

```bash
nohup python -m vllm.entrypoints.openai.api_server \
    --model /path/to/Qwen3-8B \
    --served-model-name qwen3-8b \
    --host 0.0.0.0 \
    --port 1995 \
    --trust-remote-code \
    --dtype bfloat16 \
    --max-model-len 16384 \
    --gpu-memory-utilization 0.85 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    > vllm.log 2>&1 &
```

### 关键参数说明

| 参数 | 说明 |
|------|------|
| `--enable-auto-tool-choice` | 启用自动工具选择（**必需**） |
| `--tool-call-parser hermes` | 工具调用格式解析器（**必需**） |
| `--served-model-name` | API 中使用的模型名称 |
| `--dtype bfloat16` | 使用 BF16 精度减少显存 |

### 环境变量配置

```bash
# .env 文件
OPENAI_BASE_URL=http://172.26.190.100:1995
OPENAI_MODEL_NAME=qwen3-8b
OPENAI_API_KEY=any-value  # vLLM 不校验 API Key

# 或通过 export 覆盖（优先级更高）
export OPENAI_MODEL_NAME=other-model
```

### 推荐模型

| 模型 | 说明 |
|------|------|
| Qwen3-8B | 支持 Tool Calling，已包含指令微调 |
| Qwen2.5-7B-Instruct | 稳定，Tool Calling 支持好 |
| ❌ Qwen2.5-VL-7B | 视觉模型，Tool Calling 支持有限 |

## RAG 知识库

基于 ChromaDB 的检索增强生成：

- **向量数据库**：ChromaDB（本地持久化）
- **Embedding**：Ollama `nomic-embed-text`（优先）或 OpenAI `text-embedding-3-small`
- **知识源**：`packages/core/data/knowledge/*.md`（手动编写）
- **分块策略**：按 `##` 标题分块
- **检索**：Top 3 相关片段注入 system prompt

启动 RAG 需要：
1. Ollama 运行 + `ollama pull nomic-embed-text`
2. ChromaDB 运行：`chroma run --path ./.chroma`
3. 设置 `OLLAMA_BASE_URL=http://localhost:11434`

## Twitter Scraper

基于 Playwright 的自动化推文抓取：

- **运行模式**：Headless Chrome + 反检测配置
- **认证方式**：Cookie auth_token 注入
- **数据获取**：拦截 GraphQL SearchTimeline 响应
- **排序方式**：默认 Top（热门），按相关性排序
- **存储**：SQLite + FTS5 全文搜索

### 安装浏览器

```bash
bunx playwright install chromium
```

### API 使用

```bash
# 手动触发抓取
curl -X POST http://localhost:3000/api/v1/twitter/scrape \
  -H "Content-Type: application/json" \
  -d '{"queries": ["Bitcoin", "ETH"]}'

# 查看抓取器状态
curl http://localhost:3000/api/v1/twitter/scraper/status

# 启动定时抓取（可指定间隔分钟数）
curl -X POST http://localhost:3000/api/v1/twitter/scraper/start \
  -H "Content-Type: application/json" \
  -d '{"intervalMinutes": 30}'

# 停止定时抓取
curl -X POST http://localhost:3000/api/v1/twitter/scraper/stop

# 搜索已抓取的推文
curl "http://localhost:3000/api/v1/twitter/search?q=BTC"
```

## Web 前端特性

### Thinking Block（思考块）

支持 `<think>` 标签的模型（如 Qwen3）会在前端显示 ChatGPT 风格的思考块：

- **思考中**：显示脉冲动画 "正在思考 · Xs"
- **思考完成**：可折叠块 "已深度思考（用时 X 秒）"，点击展开查看思考过程
- 前端解析 `<think>` 标签，不显示原始标签文本

### 上下文对话（Session 管理）

前端通过 `backendSessionId` 维护与后端的对话上下文：

- 每个前端 Conversation 关联一个后端 Session
- `sessionId` 存储在 localStorage，随请求发送
- 后端内存存储 Session，重启后失效
- Session 失效时显示提示，引导用户开始新对话

**多用户隔离**：不同浏览器有各自的 localStorage，完全隔离。

### Typography

- 字体：系统字体栈（system-ui, -apple-system, Segoe UI...）
- 正文：14px，行高 1.5
- 标题：24px（欢迎页）
- 段落间距：1em

## 代码约定

- 严格模式 TypeScript (`strict: true`)
- 使用 Zod 做运行时类型校验
- AI prompt 使用中文
- API key 从环境变量读取

## 扩展指南

### 添加 LLM 提供商
```typescript
// packages/core/src/providers.ts
export function createYourProvider(): ProviderInstance | null {
  // ...
}
```

### 添加 API 端点
```typescript
// packages/server/src/index.ts
app.get('/api/v1/your-endpoint', async (c) => {
  // ...
})
```
