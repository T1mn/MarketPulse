import { z } from 'zod'

/**
 * LLM Provider types
 */
export type LLMProvider = 'deepseek' | 'openai' | 'ollama'

export const LLMProviderSchema = z.enum(['deepseek', 'openai', 'ollama'])

/**
 * Chat message types
 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export const ChatMessageSchema = z.object({
  id: z.string(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  timestamp: z.number(),
})

/**
 * Session types
 */
export interface Session {
  id: string
  messages: ChatMessage[]
  provider: LLMProvider
  createdAt: number
  updatedAt: number
}

export const SessionSchema = z.object({
  id: z.string(),
  messages: z.array(ChatMessageSchema),
  provider: LLMProviderSchema,
  createdAt: z.number(),
  updatedAt: z.number(),
})

/**
 * API Response types
 */
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z.string().optional(),
  })

/**
 * Market data types (Crypto - Binance)
 */
export interface MarketPrice {
  symbol: string
  price: number
  change24h: number
  timestamp: number
}

export const MarketPriceSchema = z.object({
  symbol: z.string(),
  price: z.number(),
  change24h: z.number(),
  timestamp: z.number(),
})

/**
 * Stock price types (US Stocks - Yahoo Finance)
 */
export interface StockPrice {
  symbol: string
  price: number
  changePercent: number | null
  changeAmount: number | null
  previousClose: number | null
  openPrice: number | null
  dayHigh: number | null
  dayLow: number | null
  volume: number | null
  marketCap: number | null
  fetchedAt: number
}

export const StockPriceSchema = z.object({
  symbol: z.string(),
  price: z.number(),
  changePercent: z.number().nullable(),
  changeAmount: z.number().nullable(),
  previousClose: z.number().nullable(),
  openPrice: z.number().nullable(),
  dayHigh: z.number().nullable(),
  dayLow: z.number().nullable(),
  volume: z.number().nullable(),
  marketCap: z.number().nullable(),
  fetchedAt: z.number(),
})

/**
 * Config types
 */
export interface AppConfig {
  llm: {
    defaultProvider: LLMProvider
    deepseekApiKey?: string
    openaiApiKey?: string
    openaiBaseUrl?: string      // 自定义 OpenAI 兼容服务地址（vLLM / LocalAI 等）
    openaiModelName?: string    // 自定义模型名称
    ollamaBaseUrl?: string
  }
  server: {
    port: number
    host: string
  }
}

export const AppConfigSchema = z.object({
  llm: z.object({
    defaultProvider: LLMProviderSchema,
    deepseekApiKey: z.string().optional(),
    openaiApiKey: z.string().optional(),
    openaiBaseUrl: z.string().optional(),      // 自定义 OpenAI 兼容服务地址
    openaiModelName: z.string().optional(),    // 自定义模型名称
    ollamaBaseUrl: z.string().optional(),
  }),
  server: z.object({
    port: z.number().default(3000),
    host: z.string().default('localhost'),
  }),
})
