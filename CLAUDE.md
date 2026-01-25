# CLAUDE.md

MarketPulse v2.0 - 企业级金融智能助手

## 项目概述

TypeScript 全栈金融智能助手，提供：
- AI 驱动的金融分析（DeepSeek / OpenAI / Ollama）
- 实时加密货币行情（Binance API）
- 金融新闻聚合（RSS + Finnhub）
- 多端支持（Web / TUI / Desktop）

## 技术栈

| 层级 | 技术 |
|------|------|
| Runtime | Bun |
| 语言 | TypeScript |
| API Server | Hono |
| AI SDK | @ai-sdk/* (Vercel) |
| Web 前端 | React + Vite + Tailwind |
| Monorepo | Turbo + Bun workspaces |

## 项目结构

```
MarketPulse/
├── packages/
│   ├── shared/     # 共享类型和工具
│   ├── core/       # 核心业务逻辑
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

# 启动后端
bun run packages/server/src/index.ts

# 启动前端 (另一个终端)
cd packages/web && bun run dev
```

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
- `DEEPSEEK_API_KEY` - DeepSeek API（主力）
- `OPENAI_API_KEY` - OpenAI API（备用）

可选：
- `OLLAMA_BASE_URL` - 本地 Ollama 服务
- `FINNHUB_API_KEY` - 金融新闻数据
- `PORT` - 服务器端口（默认 3000）

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
