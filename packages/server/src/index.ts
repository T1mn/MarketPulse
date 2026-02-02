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
  // Twitter
  initTwitterDB,
  getTwitterStats,
  searchTweetsInDB,
  getTopTweetsFromDB,
  getLatestTweets,
  getSearchQueries,
  insertTweets,
  parseTweetHarvestCSV,
  DEFAULT_SORT_OPTIONS,
  // Twitter Scraper
  initTwitterScraper,
  scrapeTwitter,
  getTwitterScraperStatus,
  startTwitterScrapeScheduler,
  stopTwitterScrapeScheduler,
  forceResetScraper,
  // Scrape Task Manager (SSE)
  subscribeSSE,
  unsubscribeSSE,
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

  // Initialize Twitter SQLite database
  try {
    initTwitterDB()
    const twitterStats = getTwitterStats()
    console.log(`[Server] Twitter database initialized with ${twitterStats.total} tweets`)

    // Initialize Twitter scraper (will auto-start scheduler if configured)
    initTwitterScraper()
  } catch (error) {
    console.error('[Server] Twitter initialization failed:', error)
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
      twitter: {
        search: '/api/v1/twitter/search',
        top: '/api/v1/twitter/top',
        stats: '/api/v1/twitter/stats',
        import: '/api/v1/twitter/import',
        scrape: '/api/v1/twitter/scrape',
        scraperStatus: '/api/v1/twitter/scraper/status',
        scraperStart: '/api/v1/twitter/scraper/start',
        scraperStop: '/api/v1/twitter/scraper/stop',
        scraperReset: '/api/v1/twitter/scraper/reset',
      },
      events: '/api/v1/events/:sessionId',
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

// ==================== Twitter ====================

// Search tweets with weighted scoring
app.get('/api/v1/twitter/search', (c) => {
  const query = c.req.query('q')
  const limit = parseInt(c.req.query('limit') || '20', 10)
  const likeWeight = parseFloat(c.req.query('likeWeight') || String(DEFAULT_SORT_OPTIONS.likeWeight))
  const replyWeight = parseFloat(c.req.query('replyWeight') || String(DEFAULT_SORT_OPTIONS.replyWeight))
  const retweetWeight = parseFloat(c.req.query('retweetWeight') || String(DEFAULT_SORT_OPTIONS.retweetWeight))
  const quoteWeight = parseFloat(c.req.query('quoteWeight') || String(DEFAULT_SORT_OPTIONS.quoteWeight))

  if (!query) {
    return c.json({ success: false, error: 'Query parameter "q" is required' }, 400)
  }

  try {
    const tweets = searchTweetsInDB(query, {
      limit,
      sortOptions: { likeWeight, replyWeight, retweetWeight, quoteWeight },
    })
    return c.json({
      success: true,
      data: tweets,
      query,
      total: tweets.length,
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Get top tweets by weighted score
app.get('/api/v1/twitter/top', (c) => {
  const limit = parseInt(c.req.query('limit') || '10', 10)
  const searchQuery = c.req.query('searchQuery')
  const likeWeight = parseFloat(c.req.query('likeWeight') || String(DEFAULT_SORT_OPTIONS.likeWeight))
  const replyWeight = parseFloat(c.req.query('replyWeight') || String(DEFAULT_SORT_OPTIONS.replyWeight))
  const retweetWeight = parseFloat(c.req.query('retweetWeight') || String(DEFAULT_SORT_OPTIONS.retweetWeight))
  const quoteWeight = parseFloat(c.req.query('quoteWeight') || String(DEFAULT_SORT_OPTIONS.quoteWeight))

  try {
    const tweets = getTopTweetsFromDB({
      limit,
      searchQuery,
      sortOptions: { likeWeight, replyWeight, retweetWeight, quoteWeight },
    })
    return c.json({
      success: true,
      data: tweets,
      total: tweets.length,
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Get latest tweets
app.get('/api/v1/twitter/latest', (c) => {
  const limit = parseInt(c.req.query('limit') || '20', 10)
  const username = c.req.query('username')

  try {
    const tweets = getLatestTweets({ limit, username })
    return c.json({
      success: true,
      data: tweets,
      total: tweets.length,
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Twitter stats
app.get('/api/v1/twitter/stats', (c) => {
  try {
    const stats = getTwitterStats()
    const queries = getSearchQueries()
    return c.json({
      success: true,
      data: {
        ...stats,
        searchQueries: queries,
        retentionDays: parseInt(process.env.TWITTER_RETENTION_DAYS || '7', 10),
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Import tweets from CSV (tweet-harvest format)
app.post('/api/v1/twitter/import', async (c) => {
  try {
    const contentType = c.req.header('content-type') || ''

    let csvContent: string
    let searchQuery: string | undefined

    if (contentType.includes('multipart/form-data')) {
      // Handle file upload
      const formData = await c.req.formData()
      const file = formData.get('file') as File | null
      searchQuery = formData.get('searchQuery') as string | null || undefined

      if (!file) {
        return c.json({ success: false, error: 'No file provided. Send CSV file as "file" field.' }, 400)
      }

      csvContent = await file.text()
    } else if (contentType.includes('application/json')) {
      // Handle JSON with CSV content
      const body = await c.req.json<{ csv: string; searchQuery?: string }>()
      if (!body.csv) {
        return c.json({ success: false, error: 'Missing "csv" field in JSON body' }, 400)
      }
      csvContent = body.csv
      searchQuery = body.searchQuery
    } else {
      // Handle raw CSV
      csvContent = await c.req.text()
      searchQuery = c.req.query('searchQuery')
    }

    // Parse CSV
    const tweets = parseTweetHarvestCSV(csvContent)

    if (tweets.length === 0) {
      return c.json({
        success: false,
        error: 'No valid tweets found in CSV. Ensure it has columns: id, text, username, favorite_count, reply_count, etc.',
      }, 400)
    }

    // Insert into database
    const inserted = insertTweets(tweets, searchQuery)

    return c.json({
      success: true,
      data: {
        parsed: tweets.length,
        inserted,
        searchQuery: searchQuery || null,
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Manual trigger scrape
app.post('/api/v1/twitter/scrape', async (c) => {
  try {
    const body = await c.req.json<{ queries?: string[] }>().catch(() => ({}))
    const queries = body.queries

    console.log('[Server] Manual Twitter scrape triggered', queries ? `for: ${queries.join(', ')}` : '')

    const results = await scrapeTwitter(queries)

    const totalCollected = results.reduce((sum, r) => sum + r.total, 0)
    const totalInserted = results.reduce((sum, r) => sum + r.inserted, 0)
    const errors = results.filter(r => r.error)

    return c.json({
      success: errors.length === 0,
      data: {
        results,
        summary: {
          queries: results.length,
          totalCollected,
          totalInserted,
          errors: errors.length,
        },
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Get scraper status
app.get('/api/v1/twitter/scraper/status', (c) => {
  try {
    const status = getTwitterScraperStatus()
    return c.json({
      success: true,
      data: status,
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Start scraper scheduler
app.post('/api/v1/twitter/scraper/start', async (c) => {
  try {
    const body = await c.req.json<{ intervalMinutes?: number }>().catch(() => ({}))

    startTwitterScrapeScheduler(body.intervalMinutes)

    const status = getTwitterScraperStatus()
    return c.json({
      success: true,
      data: {
        message: 'Scheduler started',
        status,
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Stop scraper scheduler
app.post('/api/v1/twitter/scraper/stop', (c) => {
  try {
    stopTwitterScrapeScheduler()

    const status = getTwitterScraperStatus()
    return c.json({
      success: true,
      data: {
        message: 'Scheduler stopped',
        status,
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// Force reset scraper (for stuck recovery)
app.post('/api/v1/twitter/scraper/reset', async (c) => {
  try {
    await forceResetScraper()

    const status = getTwitterScraperStatus()
    return c.json({
      success: true,
      data: {
        message: 'Scraper state reset',
        status,
      },
    })
  } catch (error) {
    return c.json({ success: false, error: String(error) }, 500)
  }
})

// ==================== SSE Events ====================

// SSE endpoint for real-time events (scrape notifications, etc.)
app.get('/api/v1/events/:sessionId', async (c) => {
  const sessionId = c.req.param('sessionId')

  return streamSSE(c, async (stream) => {
    let running = true

    // SSE writer for scrape task manager
    const writer = (event: string, data: unknown) => {
      if (!running) return
      stream.writeSSE({
        event,
        data: JSON.stringify(data),
      }).catch(() => { running = false })
    }

    // Subscribe to events
    subscribeSSE(sessionId, writer)

    // Send connected event
    await stream.writeSSE({
      event: 'connected',
      data: JSON.stringify({ sessionId, timestamp: Date.now() }),
    })

    // Keep stream alive with heartbeat loop (every 5s to stay within idle timeout)
    while (running) {
      await new Promise(r => setTimeout(r, 5000))
      if (!running) break
      try {
        await stream.writeSSE({
          event: 'heartbeat',
          data: JSON.stringify({ timestamp: Date.now() }),
        })
      } catch {
        running = false
      }
    }

    // Cleanup
    unsubscribeSSE(sessionId, writer)
  })
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
    idleTimeout: 255, // Max value for SSE long-lived connections
  })
}

export { app }

// Auto-start if run directly
if (import.meta.main) {
  startServer()
}
