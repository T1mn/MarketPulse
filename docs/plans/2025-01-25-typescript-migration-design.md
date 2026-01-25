# MarketPulse TypeScript 迁移设计

**日期**: 2025-01-25
**状态**: 已批准
**参考**: [OpenCode](https://github.com/anomalyco/opencode)

## 背景

当前 MarketPulse 使用 Python (FastAPI) 后端 + React 前端的架构。为了：
1. 统一启动入口 (`npm start` 或 `npx`)
2. 便于分发 (`npm i -g marketpulse`)
3. 前后端技术栈统一

决定参考 OpenCode 项目，迁移到 TypeScript 全栈架构。

## 技术调研结论

| 项目 | 主语言 | Runtime | Server | Desktop | 结论 |
|------|--------|---------|--------|---------|------|
| **OpenCode** | TypeScript 86% | Bun | Hono | Tauri | ✅ 采用 |
| **Codex** | Rust 97% | Native | - | - | ❌ 学习成本高 |
| **Claude Code** | TypeScript | Node.js | - | - | 参考 |

OpenCode 的优势：
- 开发效率高（TypeScript 生态成熟）
- 可复用现有 React 前端
- Bun 性能优于 Node.js
- Tauri 桌面应用体积小

## 核心技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| Runtime | Bun ≥1.1 | 替代 Node.js |
| 语言 | TypeScript ≥5.0 | 全栈统一 |
| API Server | Hono ≥4.0 | 轻量级 Web 框架 |
| TUI | SolidJS + @opentui/solid | 响应式终端 UI |
| Desktop | Tauri 2.x | Rust 内核 |
| AI SDK | @ai-sdk/* (Vercel) | 统一 LLM 接口 |
| Monorepo | Turbo + Bun workspaces | 构建编排 |

## LLM 提供商

1. **DeepSeek** - 主力模型
2. **本地模型** (Ollama) - 离线场景
3. **OpenAI** - 备用

移除 Google Gemini 依赖。

## 目标架构

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

## Monorepo 结构

```
packages/
├── core/                   # 核心库：Session、Provider、Tools
├── server/                 # Hono HTTP Server
├── cli/                    # CLI 入口
├── tui/                    # TUI 客户端 (SolidJS)
├── desktop/                # Tauri 桌面应用
├── web/                    # React Web 客户端 (现有 frontend/ 迁移)
├── sdk/                    # TypeScript SDK
└── shared/                 # 共享类型和工具
```

## 迁移计划

### Phase 1: 搭建骨架
- [ ] 初始化 Bun monorepo
- [ ] 配置 Turbo
- [ ] 创建 packages 目录结构
- [ ] 配置 TypeScript、ESLint、Prettier

### Phase 2: 核心迁移
- [ ] 实现 Hono Server
- [ ] 实现 LLM Provider (DeepSeek, OpenAI, Ollama)
- [ ] 实现 Session Manager
- [ ] 迁移 API 端点

### Phase 3: 客户端迁移
- [ ] 实现 CLI 入口
- [ ] 实现 TUI (SolidJS)
- [ ] 迁移 React Web 前端
- [ ] 实现 Tauri Desktop

### Phase 4: 发布
- [ ] 删除 Python 代码
- [ ] 配置 npm 发布
- [ ] 配置 Homebrew tap
- [ ] 发布 v2.0

## 分发方式

```bash
# NPM 全局安装
npm i -g marketpulse

# Homebrew
brew install marketpulse

# 使用
marketpulse          # TUI
marketpulse server   # API Server
marketpulse desktop  # 桌面应用
```

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 学习曲线 (Bun, Hono, SolidJS) | 渐进式迁移，先实现 Server |
| 功能不完整 | 保持 Python 版本可用直到 Phase 4 |
| 性能问题 | Bun 性能通常优于 Node.js |

## 参考资料

- [OpenCode GitHub](https://github.com/anomalyco/opencode)
- [OpenCode DeepWiki](https://deepwiki.com/anomalyco/opencode)
- [Vercel AI SDK](https://sdk.vercel.ai/)
- [Hono](https://hono.dev/)
- [Tauri](https://tauri.app/)
