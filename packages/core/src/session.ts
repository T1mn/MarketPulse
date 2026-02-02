/**
 * Session management
 */

import { streamText } from 'ai'
import type { ChatMessage, Session, LLMProvider } from '@marketpulse/shared'
import { generateId } from '@marketpulse/shared'
import { getProvider, getDefaultProvider } from './providers'
import { createSessionTools } from './tools'
import { retrieveKnowledge } from './rag'

/**
 * Session store (in-memory for now, can be replaced with persistent storage)
 */
const sessions = new Map<string, Session>()

/**
 * Create a new session
 */
export function createSession(provider?: LLMProvider): Session {
  const defaultProvider = getDefaultProvider()

  const session: Session = {
    id: generateId(),
    messages: [],
    provider: provider ?? defaultProvider?.id ?? 'deepseek',
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }

  sessions.set(session.id, session)
  return session
}

/**
 * Get session by ID
 */
export function getSession(id: string): Session | undefined {
  return sessions.get(id)
}

/**
 * Delete session
 */
export function deleteSession(id: string): boolean {
  return sessions.delete(id)
}

/**
 * Add message to session
 */
export function addMessage(
  sessionId: string,
  role: ChatMessage['role'],
  content: string
): ChatMessage | undefined {
  const session = sessions.get(sessionId)
  if (!session) {
    return undefined
  }

  const message: ChatMessage = {
    id: generateId(),
    role,
    content,
    timestamp: Date.now(),
  }

  session.messages.push(message)
  session.updatedAt = Date.now()

  return message
}

/**
 * Chat stream event types
 */
export type ChatStreamEvent =
  | { type: 'text'; content: string }
  | { type: 'tool-call'; toolName: string; args: unknown }
  | { type: 'tool-result'; toolName: string; result: unknown }

/**
 * Stream chat completion
 */
export async function* streamChat(
  sessionId: string,
  userMessage: string
): AsyncGenerator<ChatStreamEvent, void, unknown> {
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

  // Create session-aware tools
  const sessionTools = createSessionTools(sessionId)

  // Stream response with tools
  const { fullStream } = await streamText({
    model: provider.client(provider.model),
    messages,
    system: `你是 MarketPulse 金融智能助手，专注于提供专业的金融市场分析和投资建议。

你可以使用以下工具获取实时数据：
- getCryptoPrice: 获取加密货币实时价格（BTC、ETH 等）。数据源：Binance
- getStockPrice: 获取美股股票实时价格（AAPL、MSFT、GOOGL 等）。数据源：Yahoo Finance
- getCommodityPrice: 获取贵金属价格（黄金、白银）
- searchNews: 获取金融新闻资讯
- searchTwitter: 搜索本地缓存的 Twitter 推文
- triggerTwitterScrape: 触发后台抓取 Twitter 推文

【重要】工具调用规则：
1. 用户询问比特币、以太坊等加密货币价格 → 调用 getCryptoPrice
2. 用户询问苹果、微软、谷歌等美股股票价格 → 调用 getStockPrice
3. 用户询问黄金、白银价格 → 调用 getCommodityPrice
4. 用户询问新闻、资讯、消息、动态、发生了什么 → 调用 searchNews
5. 用户询问推特/Twitter 讨论 → 调用 searchTwitter
6. 不要猜测数据，必须通过工具获取真实信息

【Twitter 推文搜索工作流】
1. 首先调用 searchTwitter 搜索本地缓存的推文
2. 如果结果为空或太少（< 3 条），告诉用户："本地没有关于 [关键词] 的推文缓存。是否需要后台抓取？抓取完成后会自动通知您。"
3. 用户确认后，调用 triggerTwitterScrape 触发后台抓取
4. 当用户说"推文抓取已完成"、"分析"、"查看结果"等，表示抓取已经完成，直接调用 searchTwitter 搜索并分析结果，不要再询问是否抓取

【股票代码提示】
- 苹果 = AAPL, 微软 = MSFT, 谷歌 = GOOGL, 亚马逊 = AMZN
- 英伟达 = NVDA, 特斯拉 = TSLA, Meta = META, AMD = AMD
- 英特尔 = INTC, 网飞 = NFLX, Salesforce = CRM, 甲骨文 = ORCL
${knowledgeContext}
请用中文回答，结合知识库信息和工具返回的真实数据进行分析。`,
    tools: sessionTools,
    maxSteps: 5, // 允许多轮工具调用
  })

  let fullResponse = ''

  for await (const part of fullStream) {
    switch (part.type) {
      case 'text-delta':
        fullResponse += part.textDelta
        yield { type: 'text', content: part.textDelta }
        break
      case 'tool-call':
        console.log(`[Tool] 🔧 Calling: ${part.toolName}`)
        console.log(`[Tool]    Args: ${JSON.stringify(part.args)}`)
        yield { type: 'tool-call', toolName: part.toolName, args: part.args }
        break
      case 'tool-result':
        console.log(`[Tool] ✅ Result: ${part.toolName}`)
        console.log(`[Tool]    Output: ${JSON.stringify(part.result).slice(0, 200)}${JSON.stringify(part.result).length > 200 ? '...' : ''}`)
        yield { type: 'tool-result', toolName: part.toolName, result: part.result }
        break
    }
  }

  // Add assistant message
  addMessage(sessionId, 'assistant', fullResponse)
}

/**
 * Get all sessions
 */
export function getAllSessions(): Session[] {
  return Array.from(sessions.values())
}
