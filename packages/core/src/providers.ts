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
 * Create OpenAI-compatible provider
 *
 * 支持任何 OpenAI 兼容服务（OpenAI / vLLM / LocalAI 等）
 *
 * 环境变量：
 *   OPENAI_API_KEY     - API 密钥（vLLM/LocalAI 可设任意值或留空）
 *   OPENAI_BASE_URL    - 服务地址（可选，不设则使用 OpenAI 官方）
 *   OPENAI_MODEL_NAME  - 模型名称（可选，默认 gpt-4o-mini）
 *
 * 示例 - 使用 vLLM 部署的 Qwen：
 *   OPENAI_BASE_URL=http://172.26.190.100:1995
 *   OPENAI_MODEL_NAME=qwen2.5-vl-7b
 *
 * 示例 - 使用 OpenAI 官方：
 *   OPENAI_API_KEY=sk-xxx
 */
export function createOpenAIProvider(): ProviderInstance | null {
  const config = getConfig()
  const apiKey = config.llm.openaiApiKey
  const baseURL = config.llm.openaiBaseUrl
  const modelName = config.llm.openaiModelName

  // 需要 API Key 或自定义 baseURL（vLLM 等不需要真实 key）
  if (!apiKey && !baseURL) {
    return null
  }

  const client = createOpenAI({
    apiKey: apiKey || 'no-key-required',  // vLLM 等不需要真实 API Key
    ...(baseURL && { baseURL: baseURL.endsWith('/v1') ? baseURL : `${baseURL}/v1` }),
  })

  return {
    id: 'openai',
    client,
    model: modelName || 'gpt-4o-mini',
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
 *
 * 优先级：openai（支持自定义 vLLM 等）> deepseek > ollama
 */
export function getDefaultProvider(): ProviderInstance | undefined {
  const priority: LLMProvider[] = ['openai', 'deepseek', 'ollama']

  for (const id of priority) {
    const provider = providers.get(id)
    if (provider) {
      return provider
    }
  }

  return undefined
}
