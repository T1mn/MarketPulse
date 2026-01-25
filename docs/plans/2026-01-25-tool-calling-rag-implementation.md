# Tool Calling + RAG 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 MarketPulse 实现 Tool Calling（LLM 自动调用 Binance/新闻 API）和 RAG（基于预置金融知识的检索增强生成）

**Architecture:** Tool Calling 使用 Vercel AI SDK 的 `tools` 参数实现自动调用；RAG 使用 ChromaDB 存储金融知识向量，查询时检索 Top 3 相关片段注入 system prompt

**Tech Stack:** Vercel AI SDK、ChromaDB、@chroma-core/default-embed

---

## 前置条件

在开始前，确保 ChromaDB 服务器运行：

```bash
# 安装 Chroma CLI（如未安装）
pip install chromadb

# 启动 Chroma 服务器（持久化到 .chroma 目录）
chroma run --path ./.chroma
```

---

## Task 1: Tool Calling - 实现 getMarketPriceTool

**Files:**
- Modify: `packages/core/src/tools.ts:11-25`

**Step 1: 修改 getMarketPriceTool 实现**

```typescript
import { getPrice, getPrices } from './market'

export const getMarketPriceTool = tool({
  description: '获取指定加密货币的当前市场价格。支持单个或多个交易对（最多10个）。',
  parameters: z.object({
    symbols: z.array(z.string()).min(1).max(10).describe('交易对符号数组，如 ["BTCUSDT", "ETHUSDT"]'),
  }),
  execute: async ({ symbols }) => {
    if (symbols.length > 10) {
      return {
        error: '一次最多查询 10 个交易对，请分批查询',
        results: [],
      }
    }

    try {
      const results = await getPrices(symbols)
      return {
        error: null,
        results: results.map(r => ({
          symbol: r.symbol,
          price: r.price,
          change24h: r.change24h,
          timestamp: r.timestamp,
        })),
      }
    } catch (error) {
      return {
        error: `获取价格失败: ${error instanceof Error ? error.message : '未知错误'}`,
        results: [],
      }
    }
  },
})
```

**Step 2: 验证修改**

```bash
cd /home/chery/personal/MarketPulse
bun run build
```

Expected: Build 成功，无类型错误

**Step 3: Commit**

```bash
git add packages/core/src/tools.ts
git commit -m "feat(tools): implement getMarketPriceTool with Binance API"
```

---

## Task 2: Tool Calling - 实现 searchNewsTool

**Files:**
- Modify: `packages/core/src/tools.ts:30-44`

**Step 1: 修改 searchNewsTool 实现**

```typescript
import { searchNews, getNews } from './news'

export const searchNewsTool = tool({
  description: '搜索金融新闻。如果不提供关键词则返回最新新闻。',
  parameters: z.object({
    query: z.string().optional().describe('搜索关键词（可选）'),
    limit: z.number().min(1).max(20).optional().default(5).describe('返回结果数量，默认5条'),
  }),
  execute: async ({ query, limit = 5 }) => {
    try {
      const finnhubApiKey = process.env.FINNHUB_API_KEY

      let results
      if (query && query.trim()) {
        results = await searchNews(query, { finnhubApiKey })
      } else {
        results = await getNews({ finnhubApiKey, limit })
      }

      return {
        error: null,
        query: query || null,
        results: results.slice(0, limit).map(item => ({
          title: item.title,
          summary: item.summary,
          source: item.source,
          url: item.url,
          publishedAt: new Date(item.publishedAt).toISOString(),
        })),
        total: results.length,
      }
    } catch (error) {
      return {
        error: `获取新闻失败: ${error instanceof Error ? error.message : '未知错误'}`,
        query: query || null,
        results: [],
        total: 0,
      }
    }
  },
})
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/tools.ts
git commit -m "feat(tools): implement searchNewsTool with RSS/Finnhub"
```

---

## Task 3: Tool Calling - 删除 analyzeSentimentTool 并清理

**Files:**
- Modify: `packages/core/src/tools.ts:48-73`

**Step 1: 删除 analyzeSentimentTool，添加 TODO 注释**

删除 `analyzeSentimentTool` 定义（第 48-62 行），在文件末尾添加：

```typescript
// TODO: 情感分析功能计划在后续版本中集成到 LLM prompt，而非独立工具

/**
 * All available tools for AI agents
 */
export const tools = {
  getMarketPrice: getMarketPriceTool,
  searchNews: searchNewsTool,
}

export type ToolName = keyof typeof tools
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/tools.ts
git commit -m "refactor(tools): remove analyzeSentimentTool, add TODO for future LLM integration"
```

---

## Task 4: Tool Calling - 集成到 streamChat

**Files:**
- Modify: `packages/core/src/session.ts:76-116`

**Step 1: 导入 tools 并修改 streamChat**

```typescript
import { streamText } from 'ai'
import type { ChatMessage, Session, LLMProvider } from '@marketpulse/shared'
import { generateId } from '@marketpulse/shared'
import { getProvider, getDefaultProvider } from './providers'
import { tools } from './tools'

// ... 其他代码保持不变 ...

/**
 * Stream chat completion with tool calling support
 */
export async function* streamChat(
  sessionId: string,
  userMessage: string
): AsyncGenerator<string, void, unknown> {
  const session = sessions.get(sessionId)
  if (!session) {
    throw new Error(`Session not found: ${sessionId}`)
  }

  // Add user message
  addMessage(sessionId, 'user', userMessage)

  // Get provider
  const provider = getProvider(session.provider) ?? getDefaultProvider()
  if (!provider) {
    throw new Error('No LLM provider available')
  }

  // Build messages for API
  const messages = session.messages.map((m) => ({
    role: m.role as 'user' | 'assistant' | 'system',
    content: m.content,
  }))

  // Stream response with tools
  const { textStream } = await streamText({
    model: provider.client(provider.model),
    messages,
    system: `你是 MarketPulse 金融智能助手，专注于提供专业的金融市场分析和投资建议。

你可以使用以下工具获取实时数据：
- getMarketPrice: 获取加密货币实时价格
- searchNews: 搜索金融新闻

当用户询问价格、行情时，主动调用 getMarketPrice 工具获取真实数据。
当用户询问新闻、资讯时，主动调用 searchNews 工具获取最新信息。

请用中文回答，并基于工具返回的真实数据进行分析。`,
    tools,
    maxSteps: 5, // 允许多轮工具调用
  })

  let fullResponse = ''

  for await (const text of textStream) {
    fullResponse += text
    yield text
  }

  // Add assistant message
  addMessage(sessionId, 'assistant', fullResponse)
}
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/session.ts
git commit -m "feat(session): integrate tool calling into streamChat with maxSteps=5"
```

---

## Task 5: RAG - 添加 ChromaDB 依赖

**Files:**
- Modify: `packages/core/package.json`

**Step 1: 添加依赖**

```bash
cd /home/chery/personal/MarketPulse/packages/core
bun add chromadb @chroma-core/default-embed
```

**Step 2: 验证安装**

```bash
bun run build
```

Expected: Build 成功，依赖已安装

**Step 3: Commit**

```bash
git add packages/core/package.json bun.lockb
git commit -m "chore(core): add chromadb and default-embed dependencies"
```

---

## Task 6: RAG - 创建 embedding.ts

**Files:**
- Create: `packages/core/src/embedding.ts`

**Step 1: 创建 embedding 封装**

```typescript
/**
 * Embedding service for RAG
 * 使用 @chroma-core/default-embed 提供的默认嵌入
 */

import { DefaultEmbeddingFunction } from '@chroma-core/default-embed'

let embeddingFunction: DefaultEmbeddingFunction | null = null

/**
 * 获取嵌入函数实例（单例）
 */
export function getEmbeddingFunction(): DefaultEmbeddingFunction {
  if (!embeddingFunction) {
    embeddingFunction = new DefaultEmbeddingFunction()
  }
  return embeddingFunction
}

/**
 * 生成文本嵌入向量
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  const fn = getEmbeddingFunction()
  const embeddings = await fn.generate([text])
  return embeddings[0]
}

/**
 * 批量生成嵌入向量
 */
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  const fn = getEmbeddingFunction()
  return fn.generate(texts)
}
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/embedding.ts
git commit -m "feat(core): add embedding service with default-embed"
```

---

## Task 7: RAG - 创建 rag.ts

**Files:**
- Create: `packages/core/src/rag.ts`

**Step 1: 创建 RAG 服务**

```typescript
/**
 * RAG (Retrieval-Augmented Generation) Service
 * 使用 ChromaDB 存储和检索金融知识
 */

import { ChromaClient, Collection } from 'chromadb'
import { getEmbeddingFunction } from './embedding'
import * as fs from 'fs'
import * as path from 'path'

const COLLECTION_NAME = 'financial_knowledge'
const CHROMA_HOST = process.env.CHROMA_HOST || 'http://localhost:8000'

let client: ChromaClient | null = null
let collection: Collection | null = null

/**
 * 初始化 ChromaDB 客户端
 */
export async function initRAG(): Promise<void> {
  if (client && collection) return

  client = new ChromaClient({ path: CHROMA_HOST })

  const embeddingFunction = getEmbeddingFunction()

  // 获取或创建集合
  collection = await client.getOrCreateCollection({
    name: COLLECTION_NAME,
    embeddingFunction,
    metadata: { description: 'MarketPulse 金融知识库' },
  })

  console.log(`[RAG] Initialized collection: ${COLLECTION_NAME}`)
}

/**
 * 知识片段结构
 */
export interface KnowledgeChunk {
  id: string
  content: string
  metadata: {
    source: string
    title: string
    category: string
  }
}

/**
 * 从 Markdown 文件解析知识片段
 * 按 ## 标题分块
 */
export function parseMarkdownToChunks(
  filePath: string,
  category: string
): KnowledgeChunk[] {
  const content = fs.readFileSync(filePath, 'utf-8')
  const fileName = path.basename(filePath, '.md')
  const chunks: KnowledgeChunk[] = []

  // 按 ## 分割
  const sections = content.split(/^## /m).filter(Boolean)

  for (let i = 0; i < sections.length; i++) {
    const section = sections[i].trim()
    if (!section) continue

    const lines = section.split('\n')
    const title = lines[0].trim()
    const body = lines.slice(1).join('\n').trim()

    if (body.length > 50) {  // 忽略太短的片段
      chunks.push({
        id: `${fileName}-${i}`,
        content: `## ${title}\n\n${body}`,
        metadata: {
          source: filePath,
          title,
          category,
        },
      })
    }
  }

  return chunks
}

/**
 * 加载知识库目录下的所有 Markdown 文件
 */
export async function loadKnowledgeBase(knowledgeDir: string): Promise<number> {
  await initRAG()
  if (!collection) throw new Error('Collection not initialized')

  const files = fs.readdirSync(knowledgeDir).filter(f => f.endsWith('.md'))
  let totalChunks = 0

  for (const file of files) {
    const filePath = path.join(knowledgeDir, file)
    const category = file.replace('.md', '').replace(/-/g, '_')
    const chunks = parseMarkdownToChunks(filePath, category)

    if (chunks.length > 0) {
      await collection.add({
        ids: chunks.map(c => c.id),
        documents: chunks.map(c => c.content),
        metadatas: chunks.map(c => c.metadata),
      })
      totalChunks += chunks.length
      console.log(`[RAG] Loaded ${chunks.length} chunks from ${file}`)
    }
  }

  console.log(`[RAG] Total chunks loaded: ${totalChunks}`)
  return totalChunks
}

/**
 * 检索相关知识片段
 */
export async function retrieveKnowledge(
  query: string,
  topK: number = 3
): Promise<KnowledgeChunk[]> {
  await initRAG()
  if (!collection) throw new Error('Collection not initialized')

  const results = await collection.query({
    queryTexts: [query],
    nResults: topK,
  })

  if (!results.documents?.[0]) return []

  return results.documents[0].map((doc, i) => ({
    id: results.ids[0][i],
    content: doc || '',
    metadata: (results.metadatas?.[0]?.[i] || {}) as KnowledgeChunk['metadata'],
  }))
}

/**
 * 获取集合统计信息
 */
export async function getRAGStats(): Promise<{ count: number }> {
  await initRAG()
  if (!collection) throw new Error('Collection not initialized')

  const count = await collection.count()
  return { count }
}

/**
 * 清空知识库
 */
export async function clearKnowledgeBase(): Promise<void> {
  if (!client) return

  try {
    await client.deleteCollection({ name: COLLECTION_NAME })
    collection = null
    console.log(`[RAG] Collection ${COLLECTION_NAME} deleted`)
  } catch (error) {
    // Collection may not exist
  }
}
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/rag.ts
git commit -m "feat(core): add RAG service with ChromaDB integration"
```

---

## Task 8: RAG - 更新 index.ts 导出

**Files:**
- Modify: `packages/core/src/index.ts`

**Step 1: 添加导出**

```typescript
/**
 * @marketpulse/core
 * 核心业务逻辑：Session、Provider、Tools、Market、RAG
 */

// Providers
export * from './providers'

// Session
export * from './session'

// Tools
export * from './tools'

// Config
export * from './config'

// Market Data
export * from './market'

// News
export * from './news'

// RAG
export * from './rag'

// Embedding
export * from './embedding'
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/index.ts
git commit -m "feat(core): export RAG and embedding modules"
```

---

## Task 9: RAG - 创建金融知识文档

**Files:**
- Create: `packages/core/data/knowledge/crypto-basics.md`
- Create: `packages/core/data/knowledge/trading-terms.md`
- Create: `packages/core/data/knowledge/financial-metrics.md`
- Create: `packages/core/data/knowledge/strategies.md`

**Step 1: 创建目录和文件**

```bash
mkdir -p /home/chery/personal/MarketPulse/packages/core/data/knowledge
```

**Step 2: 创建 crypto-basics.md**

```markdown
# 加密货币基础知识

## 比特币 (Bitcoin, BTC)

比特币是第一个去中心化的加密货币，由中本聪（Satoshi Nakamoto）于2008年提出，2009年正式上线。

核心特点：
- 总量上限：2100万枚
- 区块时间：约10分钟
- 共识机制：工作量证明（PoW）
- 减半周期：约4年减半一次，最近一次减半是2024年4月

比特币被视为"数字黄金"，是市值最大的加密货币。

## 以太坊 (Ethereum, ETH)

以太坊是一个开源的区块链平台，支持智能合约和去中心化应用（DApp）。

核心特点：
- 创始人：Vitalik Buterin（V神）
- 共识机制：权益证明（PoS），2022年完成合并（The Merge）
- 区块时间：约12秒
- Gas费：用于支付交易和合约执行费用

以太坊是 DeFi 和 NFT 生态的主要平台。

## 区块链 (Blockchain)

区块链是一种分布式账本技术，数据以区块形式链式存储，具有不可篡改性。

关键概念：
- 区块：包含交易数据的数据包
- 哈希：区块的唯一标识符
- 节点：运行区块链软件的计算机
- 共识：节点就账本状态达成一致的机制

## DeFi (去中心化金融)

DeFi 是指在区块链上构建的金融服务，无需传统中介。

主要类型：
- DEX（去中心化交易所）：Uniswap、SushiSwap
- 借贷协议：Aave、Compound
- 稳定币：USDT、USDC、DAI
- 流动性挖矿：提供流动性获取收益

## 稳定币 (Stablecoin)

稳定币是价值锚定法币（通常是美元）的加密货币。

主要类型：
- 法币抵押型：USDT、USDC（1:1 美元储备）
- 加密资产抵押型：DAI（超额抵押 ETH 等）
- 算法稳定币：通过算法调节供应量

## NFT (非同质化代币)

NFT 是区块链上的唯一数字资产，代表所有权证明。

应用场景：
- 数字艺术品
- 游戏道具
- 会员权益
- 域名

## 钱包 (Wallet)

加密货币钱包用于存储私钥和管理资产。

类型：
- 热钱包：联网，方便但风险较高（MetaMask、Trust Wallet）
- 冷钱包：离线，安全但不便（Ledger、Trezor）
- 托管钱包：交易所管理（Binance、Coinbase）

私钥 = 资产所有权，务必妥善保管！
```

**Step 3: 创建 trading-terms.md**

```markdown
# 交易术语

## K线图 (Candlestick Chart)

K线图是展示价格走势的图表，每根K线包含四个价格：

- 开盘价 (Open)：周期开始时的价格
- 收盘价 (Close)：周期结束时的价格
- 最高价 (High)：周期内最高价格
- 最低价 (Low)：周期内最低价格

阳线：收盘价 > 开盘价（通常为绿色/白色）
阴线：收盘价 < 开盘价（通常为红色/黑色）

## MACD 指标

MACD（Moving Average Convergence Divergence，指数平滑异同移动平均线）是趋势跟踪指标。

组成部分：
- DIF（快线）：12日EMA - 26日EMA
- DEA（慢线）：DIF的9日EMA
- MACD柱：(DIF - DEA) × 2

使用方法：
- 金叉（DIF上穿DEA）：买入信号
- 死叉（DIF下穿DEA）：卖出信号
- 柱状图由负转正：趋势转强

## RSI 指标

RSI（Relative Strength Index，相对强弱指数）衡量价格变动的速度和幅度。

计算公式：RSI = 100 - 100/(1 + RS)
其中 RS = 平均上涨幅度 / 平均下跌幅度

解读：
- RSI > 70：超买区域，可能回调
- RSI < 30：超卖区域，可能反弹
- RSI = 50：多空平衡

## 布林带 (Bollinger Bands)

布林带由三条线组成，用于判断价格波动范围。

组成：
- 中轨：20日移动平均线
- 上轨：中轨 + 2倍标准差
- 下轨：中轨 - 2倍标准差

使用方法：
- 价格触及上轨：可能超买
- 价格触及下轨：可能超卖
- 带宽收窄：可能即将突破

## 支撑位与阻力位

支撑位：价格下跌时遇到的支撑，买盘较强
阻力位：价格上涨时遇到的阻力，卖盘较强

识别方法：
- 历史高点/低点
- 整数关口（如 BTC $100,000）
- 移动平均线
- 趋势线

## 交易量 (Volume)

交易量是指一定时间内的成交数量，用于确认趋势。

量价关系：
- 价涨量增：趋势健康，可能继续
- 价涨量缩：上涨乏力，注意风险
- 价跌量增：抛压较重，可能继续下跌
- 价跌量缩：下跌动能减弱，可能企稳

## 做多与做空

做多 (Long)：预期价格上涨，先买入后卖出获利
做空 (Short)：预期价格下跌，借入卖出后低价买回获利

杠杆交易会放大收益和风险，需谨慎使用。

## 止损与止盈

止损 (Stop Loss)：设定亏损上限，自动平仓控制风险
止盈 (Take Profit)：设定盈利目标，自动平仓锁定收益

建议：
- 单笔交易风险不超过总资金的1-2%
- 设定合理的风险收益比（至少1:2）
```

**Step 4: 创建 financial-metrics.md**

```markdown
# 财务指标

## 市盈率 (P/E Ratio)

市盈率 = 股价 / 每股收益 (EPS)

解读：
- 市盈率越高，估值越贵
- 需与行业平均对比
- 高成长公司通常市盈率较高

加密货币领域一般不使用此指标。

## 市净率 (P/B Ratio)

市净率 = 股价 / 每股净资产

解读：
- P/B < 1：可能被低估
- P/B > 3：可能被高估
- 适用于重资产行业

## 市值 (Market Cap)

市值 = 当前价格 × 流通量

加密货币分类：
- 大盘币：市值 > $100亿（BTC、ETH）
- 中盘币：市值 $10-100亿
- 小盘币：市值 < $10亿

注意：高市值≠低风险

## 总锁仓量 TVL (Total Value Locked)

TVL 是 DeFi 协议中锁定的总资产价值，用于衡量协议规模。

查看网站：DeFiLlama、DeFi Pulse

TVL 高不代表安全，需关注：
- 智能合约审计
- 团队背景
- 经济模型

## 完全稀释估值 FDV (Fully Diluted Valuation)

FDV = 代币价格 × 代币总量（包括未释放）

与市值对比：
- FDV >> 市值：大量代币未释放，可能有抛压
- FDV ≈ 市值：代币已基本流通

## 流通量与总量

流通量 (Circulating Supply)：当前市场上流通的代币数量
总量 (Total Supply)：代币的最大供应量

注意：
- 代币释放计划
- 团队和投资者解锁时间
- 通胀/通缩机制

## 年化收益率 APY/APR

APR (Annual Percentage Rate)：年化利率，不含复利
APY (Annual Percentage Yield)：年化收益率，含复利

计算：APY = (1 + APR/n)^n - 1
其中 n 为复利次数

DeFi 高 APY 通常伴随高风险，需警惕。

## 夏普比率 (Sharpe Ratio)

夏普比率 = (投资收益率 - 无风险收益率) / 收益率标准差

解读：
- > 1：较好
- > 2：很好
- > 3：优秀

用于评估风险调整后的收益。
```

**Step 5: 创建 strategies.md**

```markdown
# 交易策略

## 定投策略 (DCA)

定投（Dollar Cost Averaging）是定期定额购买的策略。

优点：
- 分散入场时机风险
- 无需择时
- 适合长期投资

执行方式：
- 选择固定周期（每周/每月）
- 固定金额（如每月 $500）
- 坚持执行，不受短期波动影响

适合：长期看好的优质资产（BTC、ETH）

## 网格交易 (Grid Trading)

网格交易在设定的价格区间内自动低买高卖。

设置参数：
- 价格区间：如 $60,000 - $70,000
- 网格数量：如 10 格
- 每格资金：总资金 / 网格数

优点：震荡市场获利
缺点：单边行情可能被套或踏空

## 趋势跟踪

顺势而为，跟随市场趋势交易。

判断趋势：
- 均线排列（多头/空头排列）
- 高点和低点走势
- 趋势线

执行规则：
- 上升趋势只做多
- 下降趋势只做空或观望
- 趋势反转时及时止损

## 突破交易

在价格突破关键位置时入场。

类型：
- 阻力位突破做多
- 支撑位突破做空
- 形态突破（三角形、矩形）

注意：
- 确认突破有效（收盘价突破、放量）
- 设置止损防假突破

## 套利策略

利用价格差异获取无风险收益。

类型：
- 交易所套利：不同交易所价差
- 期现套利：现货与期货价差
- 三角套利：三种货币汇率差异

注意：
- 考虑手续费和滑点
- 资金转移时间
- 大资金才能获得可观收益

## 风险管理原则

1. 仓位控制
   - 单笔交易不超过总资金 10%
   - 总仓位根据市场情况调整

2. 止损设置
   - 每笔交易必须设止损
   - 单笔亏损不超过总资金 1-2%

3. 分散投资
   - 不要把所有资金放在一个资产
   - 考虑不同类型的资产配置

4. 保持冷静
   - 不要 FOMO（害怕错过）
   - 不要恐慌性抛售
   - 按计划执行，控制情绪

## 投资心态

- 只投资能承受损失的资金
- 不要加杠杆超出能力范围
- 持续学习，保持谦虚
- 市场永远存在，不急于一时
```

**Step 6: Commit**

```bash
git add packages/core/data/knowledge/
git commit -m "feat(core): add financial knowledge base documents"
```

---

## Task 10: RAG - 集成到 streamChat

**Files:**
- Modify: `packages/core/src/session.ts`

**Step 1: 在 streamChat 中添加 RAG 检索**

```typescript
import { streamText } from 'ai'
import type { ChatMessage, Session, LLMProvider } from '@marketpulse/shared'
import { generateId } from '@marketpulse/shared'
import { getProvider, getDefaultProvider } from './providers'
import { tools } from './tools'
import { retrieveKnowledge } from './rag'

// ... 其他代码保持不变 ...

/**
 * Stream chat completion with tool calling and RAG support
 */
export async function* streamChat(
  sessionId: string,
  userMessage: string
): AsyncGenerator<string, void, unknown> {
  const session = sessions.get(sessionId)
  if (!session) {
    throw new Error(`Session not found: ${sessionId}`)
  }

  // Add user message
  addMessage(sessionId, 'user', userMessage)

  // Get provider
  const provider = getProvider(session.provider) ?? getDefaultProvider()
  if (!provider) {
    throw new Error('No LLM provider available')
  }

  // RAG: 检索相关知识
  let knowledgeContext = ''
  try {
    const relevantChunks = await retrieveKnowledge(userMessage, 3)
    if (relevantChunks.length > 0) {
      knowledgeContext = `\n\n【相关知识】\n${relevantChunks.map(c => c.content).join('\n\n')}\n`
    }
  } catch (error) {
    // RAG 失败不影响主流程
    console.warn('[RAG] Knowledge retrieval failed:', error)
  }

  // Build messages for API
  const messages = session.messages.map((m) => ({
    role: m.role as 'user' | 'assistant' | 'system',
    content: m.content,
  }))

  // Stream response with tools and RAG context
  const { textStream } = await streamText({
    model: provider.client(provider.model),
    messages,
    system: `你是 MarketPulse 金融智能助手，专注于提供专业的金融市场分析和投资建议。

你可以使用以下工具获取实时数据：
- getMarketPrice: 获取加密货币实时价格
- searchNews: 搜索金融新闻

当用户询问价格、行情时，主动调用 getMarketPrice 工具获取真实数据。
当用户询问新闻、资讯时，主动调用 searchNews 工具获取最新信息。
${knowledgeContext}
请用中文回答，结合知识库信息和工具返回的真实数据进行分析。`,
    tools,
    maxSteps: 5,
  })

  let fullResponse = ''

  for await (const text of textStream) {
    fullResponse += text
    yield text
  }

  // Add assistant message
  addMessage(sessionId, 'assistant', fullResponse)
}
```

**Step 2: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 3: Commit**

```bash
git add packages/core/src/session.ts
git commit -m "feat(session): integrate RAG knowledge retrieval into streamChat"
```

---

## Task 11: 服务器初始化 - 添加 RAG 启动逻辑

**Files:**
- Modify: `packages/server/src/index.ts`

**Step 1: 在服务器启动时初始化 RAG**

在文件开头添加导入和初始化逻辑：

```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { streamSSE } from 'hono/streaming'
import {
  createSession,
  getSession,
  streamChat,
  initProviders,
  getAvailableProviders,
  getPrice,
  getPrices,
  getKlines,
  getNews,
  searchNews,
  initRAG,
  loadKnowledgeBase,
  getRAGStats,
} from '@marketpulse/core'
import * as path from 'path'

const app = new Hono()

// ... 中间件配置 ...

// 初始化
async function initialize() {
  // 初始化 LLM providers
  initProviders()

  // 初始化 RAG
  try {
    await initRAG()

    // 加载知识库
    const knowledgeDir = path.join(import.meta.dir, '../../core/data/knowledge')
    await loadKnowledgeBase(knowledgeDir)

    const stats = await getRAGStats()
    console.log(`[Server] RAG initialized with ${stats.count} knowledge chunks`)
  } catch (error) {
    console.warn('[Server] RAG initialization failed, continuing without RAG:', error)
  }
}

// 执行初始化
initialize()

// ... 路由定义 ...
```

**Step 2: 添加 RAG 状态端点**

```typescript
// RAG stats endpoint
app.get('/api/v1/rag/stats', async (c) => {
  try {
    const stats = await getRAGStats()
    return c.json({
      success: true,
      data: stats,
    })
  } catch (error) {
    return c.json({
      success: false,
      error: 'RAG not initialized',
    }, 500)
  }
})
```

**Step 3: 验证修改**

```bash
bun run build
```

Expected: Build 成功

**Step 4: Commit**

```bash
git add packages/server/src/index.ts
git commit -m "feat(server): initialize RAG on startup and add stats endpoint"
```

---

## Task 12: 最终验证

**Step 1: 构建整个项目**

```bash
cd /home/chery/personal/MarketPulse
bun run build
```

Expected: 所有包构建成功

**Step 2: 启动 ChromaDB（需要单独终端）**

```bash
chroma run --path ./.chroma
```

**Step 3: 启动服务器**

```bash
bun run packages/server/src/index.ts
```

Expected: 服务器启动，RAG 初始化成功

**Step 4: 测试 Tool Calling**

```bash
curl -X POST http://localhost:3000/api/v1/session
# 记录返回的 sessionId

curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "<sessionId>", "message": "BTC 现在多少钱？"}'
```

Expected: 返回包含真实 BTC 价格的回答

**Step 5: 测试 RAG**

```bash
curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "<sessionId>", "message": "什么是 MACD？"}'
```

Expected: 返回基于知识库的 MACD 解释

**Step 6: Final Commit**

```bash
git add -A
git commit -m "feat: complete Tool Calling and RAG implementation

- Tool Calling: getMarketPrice and searchNews with real APIs
- RAG: ChromaDB with preset financial knowledge
- Integration: both features work together in streamChat"
```

---

## 实现检查清单

- [ ] Task 1: getMarketPriceTool 实现
- [ ] Task 2: searchNewsTool 实现
- [ ] Task 3: 删除 analyzeSentimentTool
- [ ] Task 4: streamChat 集成 tools
- [ ] Task 5: 添加 ChromaDB 依赖
- [ ] Task 6: 创建 embedding.ts
- [ ] Task 7: 创建 rag.ts
- [ ] Task 8: 更新 index.ts 导出
- [ ] Task 9: 创建金融知识文档
- [ ] Task 10: streamChat 集成 RAG
- [ ] Task 11: 服务器初始化 RAG
- [ ] Task 12: 最终验证
