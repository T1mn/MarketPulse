/**
 * LLM Provider implementations
 */

import { createOpenAI } from '@ai-sdk/openai'
import type { LLMProvider } from '@marketpulse/shared'
import { getConfig } from './config'

export interface ProviderInstance {
  id: LLMProvider
  client: ReturnType<typeof createOpenAI>
  model: string
}

/**
 * Create DeepSeek provider
 */
export function createDeepSeekProvider(): ProviderInstance | null {
  const config = getConfig()
  const apiKey = config.llm.deepseekApiKey

  if (!apiKey) {
    return null
  }

  const client = createOpenAI({
    apiKey,
    baseURL: 'https://api.deepseek.com/v1',
  })

  return {
    id: 'deepseek',
    client,
    model: 'deepseek-chat',
  }
}

/**
 * Create OpenAI provider
 */
export function createOpenAIProvider(): ProviderInstance | null {
  const config = getConfig()
  const apiKey = config.llm.openaiApiKey

  if (!apiKey) {
    return null
  }

  const client = createOpenAI({
    apiKey,
  })

  return {
    id: 'openai',
    client,
    model: 'gpt-4o-mini',
  }
}

/**
 * Create Ollama provider
 */
export function createOllamaProvider(): ProviderInstance | null {
  const config = getConfig()
  const baseURL = config.llm.ollamaBaseUrl

  if (!baseURL) {
    return null
  }

  const client = createOpenAI({
    apiKey: 'ollama', // Ollama doesn't need a real API key
    baseURL: `${baseURL}/v1`,
  })

  return {
    id: 'ollama',
    client,
    model: 'llama3.2',
  }
}

/**
 * Provider registry
 */
const providers = new Map<LLMProvider, ProviderInstance>()

/**
 * Initialize all available providers
 */
export function initProviders(): void {
  const deepseek = createDeepSeekProvider()
  if (deepseek) {
    providers.set('deepseek', deepseek)
  }

  const openai = createOpenAIProvider()
  if (openai) {
    providers.set('openai', openai)
  }

  const ollama = createOllamaProvider()
  if (ollama) {
    providers.set('ollama', ollama)
  }
}

/**
 * Get provider by ID
 */
export function getProvider(id: LLMProvider): ProviderInstance | undefined {
  return providers.get(id)
}

/**
 * Get all available providers
 */
export function getAvailableProviders(): LLMProvider[] {
  return Array.from(providers.keys())
}

/**
 * Get default provider (first available in priority order)
 */
export function getDefaultProvider(): ProviderInstance | undefined {
  const priority: LLMProvider[] = ['deepseek', 'ollama', 'openai']

  for (const id of priority) {
    const provider = providers.get(id)
    if (provider) {
      return provider
    }
  }

  return undefined
}
