/**
 * Embedding service for RAG
 * 使用 Vercel AI SDK + OpenAI text-embedding-3-small
 */

import { embed, embedMany } from 'ai'
import { openai } from '@ai-sdk/openai'

const EMBEDDING_MODEL = 'text-embedding-3-small'

/**
 * 检查 OpenAI API Key 是否可用
 */
export function isEmbeddingAvailable(): boolean {
  return !!process.env.OPENAI_API_KEY
}

/**
 * 生成单个文本的嵌入向量
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  if (!isEmbeddingAvailable()) {
    throw new Error('OPENAI_API_KEY is required for embedding generation')
  }

  const { embedding } = await embed({
    model: openai.embedding(EMBEDDING_MODEL),
    value: text,
  })

  return embedding
}

/**
 * 批量生成嵌入向量
 */
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  if (!isEmbeddingAvailable()) {
    throw new Error('OPENAI_API_KEY is required for embedding generation')
  }

  if (texts.length === 0) {
    return []
  }

  const { embeddings } = await embedMany({
    model: openai.embedding(EMBEDDING_MODEL),
    values: texts,
  })

  return embeddings
}
