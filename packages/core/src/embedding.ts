/**
 * Embedding service for RAG
 * 支持 Ollama (本地) 或 OpenAI (云端)
 */

import { embed, embedMany } from 'ai'
import { openai } from '@ai-sdk/openai'
import { ollama } from 'ollama-ai-provider'

// 优先使用 Ollama (本地)，其次 OpenAI (云端)
type EmbeddingProvider = 'ollama' | 'openai' | null

function getEmbeddingProvider(): EmbeddingProvider {
  if (process.env.OLLAMA_BASE_URL) {
    return 'ollama'
  }
  if (process.env.OPENAI_API_KEY) {
    return 'openai'
  }
  return null
}

function getEmbeddingModel() {
  const provider = getEmbeddingProvider()

  if (provider === 'ollama') {
    return ollama.embedding('nomic-embed-text')
  }

  if (provider === 'openai') {
    return openai.embedding('text-embedding-3-small')
  }

  return null
}

/**
 * 检查 Embedding 是否可用
 */
export function isEmbeddingAvailable(): boolean {
  return getEmbeddingProvider() !== null
}

/**
 * 获取当前使用的 Embedding 提供商
 */
export function getEmbeddingProviderName(): string | null {
  return getEmbeddingProvider()
}

/**
 * 生成单个文本的嵌入向量
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  const model = getEmbeddingModel()
  if (!model) {
    throw new Error('No embedding provider available. Set OLLAMA_BASE_URL or OPENAI_API_KEY.')
  }

  const { embedding } = await embed({
    model,
    value: text,
  })

  return embedding
}

/**
 * 批量生成嵌入向量
 */
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  const model = getEmbeddingModel()
  if (!model) {
    throw new Error('No embedding provider available. Set OLLAMA_BASE_URL or OPENAI_API_KEY.')
  }

  if (texts.length === 0) {
    return []
  }

  const { embeddings } = await embedMany({
    model,
    values: texts,
  })

  return embeddings
}
