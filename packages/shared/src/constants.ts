/**
 * Application constants
 */

export const APP_NAME = 'MarketPulse'
export const APP_VERSION = '2.0.0-alpha.0'

export const DEFAULT_PORT = 3000
export const DEFAULT_HOST = 'localhost'

/**
 * LLM Provider defaults
 */
export const LLM_PROVIDERS = {
  DEEPSEEK: 'deepseek',
  OPENAI: 'openai',
  OLLAMA: 'ollama',
} as const

export const DEFAULT_LLM_PROVIDER = LLM_PROVIDERS.DEEPSEEK

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  CHAT: '/api/v1/chat',
  MARKET_PRICE: '/api/v1/market/price',
  MARKET_KLINES: '/api/v1/market/klines',
  HEALTH: '/health',
  EVENTS: '/events',
} as const

/**
 * SSE event types
 */
export const SSE_EVENTS = {
  MESSAGE: 'message',
  ERROR: 'error',
  DONE: 'done',
  PING: 'ping',
} as const
