/**
 * Session management
 */

import { streamText } from 'ai'
import type { ChatMessage, Session, LLMProvider } from '@marketpulse/shared'
import { generateId } from '@marketpulse/shared'
import { getProvider, getDefaultProvider } from './providers'
import { tools } from './tools'

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
 * Stream chat completion
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

/**
 * Get all sessions
 */
export function getAllSessions(): Session[] {
  return Array.from(sessions.values())
}
