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
  initNewsDB,
  getNewsStats,
  fetchAllRSS,
  startRSSScheduler,
  getRSSSources,
  initStockDB,
  getStockStats,
  fetchAllStocks,
  startStockScheduler,
  getStockSymbols,
  getStockPrice,
  getStockPrices,
  getAllStockPrices,
} from '@marketpulse/core'

// Initialize
loadConfig()

// Async initialization for RAG and RSS
async function initialize() {
  // Initialize LLM providers
  initProviders()

  // Initialize News SQLite database
  try {
    initNewsDB()
    console.log('[Server] News database initialized')

    // Initial RSS fetch
    const result = await fetchAllRSS()
    console.log(`[Server] Initial RSS fetch: ${result.total} parsed, ${result.inserted} new`)

    // Start RSS scheduler
    startRSSScheduler()
  } catch (error) {
    console.error('[Server] News initialization failed:', error)
  }

  // Initialize Stock SQLite database
  try {
    initStockDB()
    console.log('[Server] Stock database initialized')

    // Initial stock fetch
    const stockResult = await fetchAllStocks()
    console.log(`[Server] Initial stock fetch: ${stockResult.total} fetched, ${stockResult.inserted} new`)

    // Start stock scheduler
    startStockScheduler()
  } catch (error) {
    console.error('[Server] Stock initialization failed:', error)
  }

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
      stock: {
        price: '/api/v1/stock/price/:symbol',
        prices: '/api/v1/stock/prices',
        stats: '/api/v1/stock/stats',
        refresh: '/api/v1/stock/refresh',
      },
      news: {
        list: '/api/v1/news',
        search: '/api/v1/news/search',
        stats: '/api/v1/news/stats',
        refresh: '/api/v1/news/refresh',
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
      for await (const event of streamChat(sessionId, message)) {
        if (event.type === 'text') {
          await stream.writeSSE({
            event: 'message',
            data: JSON.stringify({ text: event.content }),
          })
        } else if (event.type === 'tool-call') {
          await stream.writeSSE({
            event: 'tool-call',
            data: JSON.stringify({ toolName: event.toolName, args: event.args }),
          })
        } else if (event.type === 'tool-result') {
          await stream.writeSSE({
            event: 'tool-result',
            data: JSON.stringify({ toolName: event.toolName, result: event.result }),
          })
        }
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
  const category = c.req.query('category')

  try {
    const news = await getNews({ limit, category })
    return c.json({ success: true, data: news })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Search news
app.get('/api/v1/news/search', async (c) => {
  const query = c.req.query('q')
  const limit = parseInt(c.req.query('limit') || '20', 10)

  if (!query) {
    return c.json({ success: false, error: 'Query parameter "q" is required' }, 400)
  }

  try {
    const news = await searchNews(query, { limit })
    return c.json({ success: true, data: news })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// News stats
app.get('/api/v1/news/stats', (c) => {
  try {
    const stats = getNewsStats()
    const sources = getRSSSources()
    return c.json({
      success: true,
      data: {
        ...stats,
        sources: sources.map((s) => ({ name: s.name, category: s.category })),
        fetchInterval: parseInt(process.env.RSS_FETCH_INTERVAL || '15', 10),
        retentionDays: parseInt(process.env.RSS_RETENTION_DAYS || '30', 10),
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Manual refresh
app.post('/api/v1/news/refresh', async (c) => {
  try {
    const result = await fetchAllRSS()
    return c.json({
      success: true,
      data: {
        total: result.total,
        inserted: result.inserted,
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// ==================== Stock ====================

// Get single stock price
app.get('/api/v1/stock/price/:symbol', (c) => {
  const symbol = c.req.param('symbol')
  try {
    const price = getStockPrice(symbol)
    if (!price) {
      return c.json({ success: false, error: `Stock ${symbol} not found` }, 404)
    }
    return c.json({ success: true, data: price })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Get multiple stock prices
app.get('/api/v1/stock/prices', (c) => {
  const symbolsParam = c.req.query('symbols')

  try {
    let prices
    if (symbolsParam) {
      const symbols = symbolsParam.split(',').map((s) => s.trim())
      prices = getStockPrices(symbols)
    } else {
      prices = getAllStockPrices()
    }
    return c.json({ success: true, data: prices })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Stock stats
app.get('/api/v1/stock/stats', (c) => {
  try {
    const stats = getStockStats()
    const symbols = getStockSymbols()
    return c.json({
      success: true,
      data: {
        ...stats,
        trackedSymbols: symbols,
        fetchInterval: parseInt(process.env.STOCK_FETCH_INTERVAL || '5', 10),
        retentionDays: parseInt(process.env.STOCK_RETENTION_DAYS || '7', 10),
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Manual stock refresh
app.post('/api/v1/stock/refresh', async (c) => {
  try {
    const result = await fetchAllStocks()
    return c.json({
      success: true,
      data: {
        total: result.total,
        inserted: result.inserted,
        failed: result.failed,
      },
    })
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
