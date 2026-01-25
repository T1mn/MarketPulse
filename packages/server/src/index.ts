/**
 * @marketpulse/server
 * Hono HTTP Server
 */

import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { streamSSE } from 'hono/streaming'

import * as path from 'path'

import { APP_NAME, APP_VERSION, API_ENDPOINTS } from '@marketpulse/shared'
import {
  getConfig,
  loadConfig,
  initProviders,
  createSession,
  getSession,
  streamChat,
  getAvailableProviders,
  getPrice,
  getPrices,
  getKlines,
  POPULAR_SYMBOLS,
  getNews,
  searchNews,
  initRAG,
  loadKnowledgeBase,
  getRAGStats,
} from '@marketpulse/core'

// Initialize
loadConfig()

// Async initialization for RAG
async function initialize() {
  // Initialize LLM providers
  initProviders()

  // Initialize RAG
  try {
    await initRAG()

    // Load knowledge base
    const knowledgeDir = path.join(import.meta.dir, '../../core/data/knowledge')
    await loadKnowledgeBase(knowledgeDir)

    const stats = await getRAGStats()
    console.log(`[Server] RAG initialized with ${stats.count} knowledge chunks`)
  } catch (error) {
    console.warn('[Server] RAG initialization failed, continuing without RAG:', error)
  }
}

// Execute initialization
initialize()

// Create app
const app = new Hono()

// Middleware
app.use('*', cors())
app.use('*', logger())

// Root route
app.get('/', (c) => {
  return c.json({
    name: APP_NAME,
    version: APP_VERSION,
    description: '企业级金融智能助手 API',
    endpoints: {
      health: '/health',
      chat: '/api/v1/chat',
      session: '/api/v1/session',
      market: {
        price: '/api/v1/market/price/:symbol',
        prices: '/api/v1/market/prices',
        klines: '/api/v1/market/klines/:symbol',
      },
      news: {
        list: '/api/v1/news',
        search: '/api/v1/news/search',
      },
      rag: {
        stats: '/api/v1/rag/stats',
      },
    },
  })
})

// Health check
app.get(API_ENDPOINTS.HEALTH, (c) => {
  return c.json({
    status: 'ok',
    name: APP_NAME,
    version: APP_VERSION,
    timestamp: new Date().toISOString(),
    providers: getAvailableProviders(),
  })
})

// ==================== Session ====================

// Create session
app.post('/api/v1/session', (c) => {
  const session = createSession()
  return c.json({
    success: true,
    data: session,
  })
})

// Get session
app.get('/api/v1/session/:id', (c) => {
  const session = getSession(c.req.param('id'))
  if (!session) {
    return c.json({ success: false, error: 'Session not found' }, 404)
  }
  return c.json({ success: true, data: session })
})

// ==================== Chat ====================

// Chat endpoint with SSE streaming
app.post(API_ENDPOINTS.CHAT, async (c) => {
  const body = await c.req.json<{ sessionId?: string; message: string }>()
  const { message } = body
  let { sessionId } = body

  // Create session if not provided
  if (!sessionId) {
    const session = createSession()
    sessionId = session.id
  }

  // Verify session exists
  const session = getSession(sessionId)
  if (!session) {
    return c.json({ success: false, error: 'Session not found' }, 404)
  }

  // Stream response
  return streamSSE(c, async (stream) => {
    try {
      for await (const text of streamChat(sessionId, message)) {
        await stream.writeSSE({
          event: 'message',
          data: JSON.stringify({ text }),
        })
      }
      await stream.writeSSE({
        event: 'done',
        data: JSON.stringify({ sessionId }),
      })
    } catch (error) {
      await stream.writeSSE({
        event: 'error',
        data: JSON.stringify({ error: String(error) }),
      })
    }
  })
})

// ==================== Market ====================

// Get single price
app.get(`${API_ENDPOINTS.MARKET_PRICE}/:symbol`, async (c) => {
  const symbol = c.req.param('symbol')
  try {
    const price = await getPrice(symbol)
    return c.json({ success: true, data: price })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Get multiple prices
app.get('/api/v1/market/prices', async (c) => {
  const symbolsParam = c.req.query('symbols')
  const symbols = symbolsParam ? symbolsParam.split(',') : POPULAR_SYMBOLS

  try {
    const prices = await getPrices(symbols)
    return c.json({ success: true, data: prices })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Get klines
app.get(`${API_ENDPOINTS.MARKET_KLINES}/:symbol`, async (c) => {
  const symbol = c.req.param('symbol')
  const interval = c.req.query('interval') || '1h'
  const limit = parseInt(c.req.query('limit') || '100', 10)

  try {
    const klines = await getKlines(symbol, interval, limit)
    return c.json({ success: true, data: klines })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// ==================== News ====================

// Get news
app.get('/api/v1/news', async (c) => {
  const limit = parseInt(c.req.query('limit') || '20', 10)
  const config = getConfig()

  try {
    const news = await getNews({
      finnhubApiKey: process.env.FINNHUB_API_KEY,
      limit,
    })
    return c.json({ success: true, data: news })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Search news
app.get('/api/v1/news/search', async (c) => {
  const query = c.req.query('q')
  if (!query) {
    return c.json({ success: false, error: 'Query parameter "q" is required' }, 400)
  }

  try {
    const news = await searchNews(query, {
      finnhubApiKey: process.env.FINNHUB_API_KEY,
    })
    return c.json({ success: true, data: news })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// ==================== RAG ====================

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

// ==================== Server ====================

// Start server
export function startServer() {
  const config = getConfig()
  const { port, host } = config.server

  console.log(`🚀 ${APP_NAME} server starting...`)
  console.log(`📍 http://${host}:${port}`)
  console.log(`📦 Providers: ${getAvailableProviders().join(', ') || 'none'}`)

  return Bun.serve({
    port,
    hostname: host,
    fetch: app.fetch,
  })
}

export { app }

// Auto-start if run directly
if (import.meta.main) {
  startServer()
}
