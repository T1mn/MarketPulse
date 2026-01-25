# CLAUDE.md

为 Claude Code 提供项目上下文。

## 项目概述

MarketPulse 是企业级金融智能助手，提供：
- AI 驱动的金融新闻分析与推送
- 多轮对话聊天机器人
- 实时加密货币行情（Binance）
- RAG 知识库检索

## 技术栈决策 (2025-01-25)

> 参考 [OpenCode](https://github.com/anomalyco/opencode) 架构，采用 TypeScript 全栈方案。

### 核心技术栈

| 层级 | 技术 | 版本要求 | 说明 |
|------|------|----------|------|
| **Runtime** | Bun | ≥1.1 | 替代 Node.js，内置打包器，性能更优 |
| **语言** | TypeScript | ≥5.0 | 全栈统一，类型安全 |
| **API Server** | Hono | ≥4.0 | 轻量级 Web 框架，类似 Express |
| **TUI** | SolidJS + @opentui/solid | - | 响应式终端 UI |
| **Desktop** | Tauri 2.x | ≥2.0 | Rust 内核，比 Electron 轻 10x |
| **AI SDK** | @ai-sdk/* (Vercel) | latest | 统一 LLM 接口，支持 75+ 模型 |
| **Monorepo** | Turbo + Bun workspaces | - | 构建编排 |

### LLM 提供商优先级

1. **DeepSeek** - 主力模型，性价比最优
2. **本地模型** (Ollama) - 离线场景
3. **OpenAI** - 备用

> 已移除 Google Gemini 依赖。

### 目标架构

```
┌─────────────────────────────────────────────────────────┐
│                      Clients                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │   TUI   │  │ Desktop │  │ VSCode  │  │   Web   │    │
│  │ SolidJS │  │  Tauri  │  │  Ext    │  │  React  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘    │
│       └────────────┴────────────┴────────────┘          │
│                         │ HTTP + SSE                    │
│                    ┌────┴────┐                          │
│                    │  Hono   │  ← Port 3000             │
│                    │ Server  │                          │
│                    └────┬────┘                          │
│       ┌─────────────────┼─────────────────┐             │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌─┴──┐        │
│  │ Session │  │ Provider│  │  Tools  │  │... │        │
│  │ Manager │  │  Router │  │ Executor│  │    │        │
│  └─────────┘  └─────────┘  └─────────┘  └────┘        │
└─────────────────────────────────────────────────────────┘
```

### 目标 Monorepo 结构

```
packages/
├── core/                   # 核心库：Session、Provider、Tools
├── server/                 # Hono HTTP Server
├── cli/                    # CLI 入口
├── tui/                    # TUI 客户端 (SolidJS)
├── desktop/                # Tauri 桌面应用
├── web/                    # React Web 客户端
├── sdk/                    # TypeScript SDK
└── shared/                 # 共享类型和工具
```

### 分发方式

```bash
# NPM 全局安装
npm i -g marketpulse
# 或
bun add -g marketpulse

# Homebrew (macOS/Linux)
brew install marketpulse

# 单命令启动
marketpulse          # 启动 TUI
marketpulse server   # 启动 API Server
marketpulse desktop  # 启动桌面应用
```

---

## 当前架构 (Python - 待迁移)

```
MarketPulse/
├── main.py                 # 统一入口 (api/ui/init-knowledge/test)
├── api/                    # FastAPI 服务层
│   ├── app.py              # 应用入口，中间件配置
│   ├── routes/             # 路由：chatbot, market, health, admin
│   └── middleware/         # 日志、限流中间件
├── core/                   # 核心业务逻辑
│   ├── agents/             # 智能体：客服、市场分析、交易助手
│   ├── dialogue/           # 对话管理：NLU、状态追踪、响应生成
│   ├── llm/                # LLM 路由器（DeepSeek/Gemini/OpenAI）
│   └── rag/                # RAG：文档加载、向量存储、检索
├── config/                 # 配置中心（Pydantic Settings）
├── services/               # 业务服务
├── sources/                # 数据源（Binance WebSocket/REST）
├── MarketPulse/            # 原新闻推送服务（待集成到 API）
├── frontend/               # React 前端
└── tests/                  # 测试
```

## 常用命令

### 当前 (Python)
```bash
python main.py api          # 启动 API 服务
python main.py ui           # 启动前端
python main.py test         # 运行测试
```

### 目标 (TypeScript)
```bash
bun install                 # 安装依赖
bun run dev                 # 开发模式（Server + TUI）
bun run build               # 构建所有包
bun run test                # 运行测试
turbo run build --filter=@marketpulse/server  # 单独构建
```

## 环境变量

必需（至少配置一个 LLM）：
- `DEEPSEEK_API_KEY` - DeepSeek API（主力）
- `OPENAI_API_KEY` - OpenAI API（备用）

可选：
- `OLLAMA_BASE_URL` - 本地 Ollama 服务地址
- `FINNHUB_API_KEY` - 金融新闻数据
- `BARK_KEY_1` - iOS 推送
- `PUSHPLUS_TOKEN` - 微信推送

## API 端点

- `POST /api/v1/chat` - 聊天对话
- `GET /api/v1/market/price/{symbol}` - 获取价格
- `GET /api/v1/market/klines/{symbol}` - 获取 K 线
- `GET /health` - 健康检查
- `GET /events` - SSE 实时事件流 (新增)

## 代码约定

### TypeScript (新代码)
- 使用 `console` 的 structured logging wrapper
- 严格模式 (`strict: true`)
- 使用 Zod 做运行时类型校验
- AI prompt 和输出使用中文
- API key 从环境变量读取，禁止硬编码

### Python (遗留代码)
- 使用 `logging` 模块，禁止 `print()`
- 新功能优先用 TypeScript 实现

## 扩展指南

### 添加 LLM 提供商 (TypeScript)
```typescript
// packages/core/src/providers/your-provider.ts
import { createProvider } from '@ai-sdk/provider-utils'

export const yourProvider = createProvider({
  // 实现 Provider 接口
})
```

### 添加工具 (Tool)
```typescript
// packages/core/src/tools/your-tool.ts
import { tool } from 'ai'
import { z } from 'zod'

export const yourTool = tool({
  description: '工具描述',
  parameters: z.object({ /* ... */ }),
  execute: async (params) => { /* ... */ }
})
```

## 迁移计划

1. **Phase 1**: 搭建 TypeScript monorepo 骨架
2. **Phase 2**: 迁移 Hono Server + LLM Provider
3. **Phase 3**: 迁移 TUI + Desktop
4. **Phase 4**: 删除 Python 代码，发布 v2.0
