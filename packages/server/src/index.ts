/**
 * @marketpulse/server
 * Hono HTTP Server
 */

import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { streamSSE } from 'hono/streaming'

import { APP_NAME, APP_VERSION, API_ENDPOINTS } from '@marketpulse/shared'
import {
  getConfig,
  loadConfig,
  initProviders,
  createSession,
  getSession,
  streamChat,
  getAvailableProviders,
} from '@marketpulse/core'

// Initialize
loadConfig()
initProviders()

// Create app
const app = new Hono()

// Middleware
app.use('*', cors())
app.use('*', logger())

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

// Create session
app.post('/api/v1/session', (c) => {
  const session = createSession()
  return c.json({
    success: true,
    data: session,
  })
})

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

// Get session
app.get('/api/v1/session/:id', (c) => {
  const session = getSession(c.req.param('id'))
  if (!session) {
    return c.json({ success: false, error: 'Session not found' }, 404)
  }
  return c.json({ success: true, data: session })
})

// Market price (placeholder)
app.get(`${API_ENDPOINTS.MARKET_PRICE}/:symbol`, async (c) => {
  const symbol = c.req.param('symbol')
  // TODO: Implement actual Binance API call
  return c.json({
    success: true,
    data: {
      symbol,
      price: 0,
      change24h: 0,
      timestamp: Date.now(),
    },
  })
})

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
