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
 * Market data types
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
 * Config types
 */
export interface AppConfig {
  llm: {
    defaultProvider: LLMProvider
    deepseekApiKey?: string
    openaiApiKey?: string
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
    ollamaBaseUrl: z.string().optional(),
  }),
  server: z.object({
    port: z.number().default(3000),
    host: z.string().default('localhost'),
  }),
})
