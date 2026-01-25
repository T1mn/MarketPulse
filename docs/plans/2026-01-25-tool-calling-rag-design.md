# Tool Calling + RAG 功能设计

> 日期: 2026-01-25
> 状态: 已确认

## 概述

为 MarketPulse 金融助手添加两个核心能力：

1. **Tool Calling** - 让 LLM 自动识别意图并调用真实 API（Binance 行情、新闻搜索）
2. **RAG 知识库** - 基于预置金融知识的检索增强生成

---

## 第一部分：Tool Calling

### 架构

```
用户输入 "BTC 现在多少钱"
       ↓
   LLM 分析意图
       ↓
   自动调用 getMarketPriceTool
       ↓
   执行 market.getPrice("BTCUSDT")
       ↓
   LLM 整合结果生成回答
       ↓
"BTC 当前价格 $67,432，24h 涨幅 2.3%"
```

### 工具清单

| 工具 | 功能 | 状态 |
|------|------|------|
| `getMarketPriceTool` | 获取加密货币价格 | 待实现 |
| `searchNewsTool` | 搜索金融新闻 | 待实现 |
| `analyzeSentimentTool` | 情感分析 | 删除（TODO: 后续集成到 LLM） |

### 设计决策

- **调用模式**: 自动模式（LLM 自动决定何时调用）
- **并发策略**: 并行调用，单次最多 10 个交易对
- **超限处理**: 返回提示 "一次最多查询 10 个交易对，请分批查询"

### 改动点

| 文件 | 改动 |
|------|------|
| `packages/core/src/tools.ts` | 实现执行逻辑，删除 `analyzeSentimentTool` |
| `packages/core/src/session.ts` | `streamChat()` 传入 `tools`，启用 `maxSteps` |

---

## 第二部分：RAG 知识库

### 架构

```
启动时加载
data/knowledge/*.md  →  ChromaDB (本地持久化)

用户提问 "什么是 MACD"
       ↓
   Embedding 向量化
       ↓
   ChromaDB 相似度检索
       ↓
   返回相关知识片段 (Top 3)
       ↓
   LLM 结合知识生成回答
```

### 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| 向量数据库 | ChromaDB | 轻量、本地持久化 |
| Embedding | OpenAI `text-embedding-3-small` 或 DeepSeek | 复用现有 API Key |
| 分块策略 | 按 `##` 标题分块 | 每个知识点独立检索 |
| Reranking | 暂不实现 | 后续可加 BGE/Cohere |

### 数据源

**预置金融知识**（手动编写 Markdown）：

- 加密货币基础 - BTC/ETH 介绍、区块链概念、DeFi 术语
- 传统金融术语 - K线形态、技术指标（MACD/RSI）、财务指标（PE/ROE）
- 交易策略 - 网格、定投、套利等

**不入库**：
- 新闻数据 - 保持实时获取，不存入向量库

### 目录结构

```
packages/core/
├── src/
│   ├── rag.ts              # RAG 服务（初始化、检索）
│   └── embedding.ts        # Embedding 封装
└── data/
    └── knowledge/
        ├── crypto-basics.md      # 加密货币基础
        ├── trading-terms.md      # 交易术语
        ├── financial-metrics.md  # 财务指标
        └── strategies.md         # 交易策略
```

---

## 第三部分：整体集成

### 聊天流程

```
用户: "MACD 是什么？BTC 现在多少钱？"
                ↓
         LLM 分析意图
        ↙          ↘
  知识类问题      数据类问题
      ↓              ↓
  RAG 检索      Tool Calling
  (ChromaDB)    (Binance API)
      ↓              ↓
  MACD 知识片段   BTC=$67,432
        ↘          ↙
         LLM 整合回答
                ↓
"MACD 是一种趋势跟踪指标...
 另外 BTC 当前价格是 $67,432"
```

### 改动文件清单

| 文件 | 改动 | 优先级 |
|------|------|--------|
| `packages/core/src/tools.ts` | 实现工具执行逻辑，删除 sentiment | P0 |
| `packages/core/src/session.ts` | 启用 tools + RAG 上下文注入 | P0 |
| `packages/core/src/rag.ts` | 新增：ChromaDB 初始化、检索 | P0 |
| `packages/core/src/embedding.ts` | 新增：Embedding 封装 | P0 |
| `packages/core/data/knowledge/*.md` | 新增：金融知识文档 | P1 |
| `packages/core/package.json` | 添加 chromadb 依赖 | P0 |

### 新增依赖

```json
{
  "chromadb": "^1.x",
  "chromadb-default-embed": "^2.x"
}
```

---

## 后续扩展（未来）

- [ ] Reranking（BGE-reranker-base 本地运行）
- [ ] 情感分析集成到 LLM prompt
- [ ] 用户上传文档支持
- [ ] 历史对话向量化
