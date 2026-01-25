/**
 * Embedding service for RAG
 * 使用 @chroma-core/default-embed 提供的默认嵌入
 */

import { DefaultEmbeddingFunction } from '@chroma-core/default-embed'

let embeddingFunction: DefaultEmbeddingFunction | null = null

/**
 * 获取嵌入函数实例（单例）
 */
export function getEmbeddingFunction(): DefaultEmbeddingFunction {
  if (!embeddingFunction) {
    embeddingFunction = new DefaultEmbeddingFunction()
  }
  return embeddingFunction
}

/**
 * 生成文本嵌入向量
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  const fn = getEmbeddingFunction()
  const embeddings = await fn.generate([text])
  return embeddings[0]
}

/**
 * 批量生成嵌入向量
 */
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  const fn = getEmbeddingFunction()
  return fn.generate(texts)
}
