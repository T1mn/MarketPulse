/**
 * Application configuration
 */

import type { AppConfig, LLMProvider } from '@marketpulse/shared'
import { AppConfigSchema, DEFAULT_LLM_PROVIDER, DEFAULT_PORT, DEFAULT_HOST } from '@marketpulse/shared'

let config: AppConfig | null = null

/**
 * Load configuration from environment
 */
export function loadConfig(): AppConfig {
  const rawConfig = {
    llm: {
      defaultProvider: (process.env.LLM_PROVIDER as LLMProvider) ?? DEFAULT_LLM_PROVIDER,
      deepseekApiKey: process.env.DEEPSEEK_API_KEY,
      openaiApiKey: process.env.OPENAI_API_KEY,
      ollamaBaseUrl: process.env.OLLAMA_BASE_URL,
    },
    server: {
      port: parseInt(process.env.PORT ?? String(DEFAULT_PORT), 10),
      host: process.env.HOST ?? DEFAULT_HOST,
    },
  }

  config = AppConfigSchema.parse(rawConfig)
  return config
}

/**
 * Get current configuration
 */
export function getConfig(): AppConfig {
  if (!config) {
    return loadConfig()
  }
  return config
}

/**
 * Update configuration
 */
export function updateConfig(updates: Partial<AppConfig>): AppConfig {
  const current = getConfig()
  config = {
    ...current,
    ...updates,
    llm: {
      ...current.llm,
      ...updates.llm,
    },
    server: {
      ...current.server,
      ...updates.server,
    },
  }
  return config
}
