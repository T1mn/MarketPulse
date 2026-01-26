/**
 * RAG (Retrieval-Augmented Generation) Service
 * 使用 ChromaDB 存储和检索金融知识
 */

import { ChromaClient, Collection } from 'chromadb'
import { generateEmbedding, generateEmbeddings, isEmbeddingAvailable } from './embedding'
import * as fs from 'fs'
import * as path from 'path'

const COLLECTION_NAME = 'financial_knowledge'
const CHROMA_HOST = process.env.CHROMA_HOST || 'http://localhost:8000'

let client: ChromaClient | null = null
let collection: Collection | null = null

/**
 * 初始化 ChromaDB 客户端
 */
export async function initRAG(): Promise<void> {
  if (client && collection) return

  if (!isEmbeddingAvailable()) {
    throw new Error('OPENAI_API_KEY is required for RAG embedding generation')
  }

  client = new ChromaClient({ path: CHROMA_HOST })

  // 获取或创建集合（不使用 embeddingFunction，我们自己生成 embedding）
  collection = await client.getOrCreateCollection({
    name: COLLECTION_NAME,
    metadata: { description: 'MarketPulse 金融知识库' },
  })

  console.log(`[RAG] Initialized collection: ${COLLECTION_NAME}`)
}

/**
 * 知识片段结构
 */
export interface KnowledgeChunk {
  id: string
  content: string
  metadata: {
    source: string
    title: string
    category: string
  }
}

/**
 * 从 Markdown 文件解析知识片段
 * 按 ## 标题分块
 */
export function parseMarkdownToChunks(
  filePath: string,
  category: string
): KnowledgeChunk[] {
  const content = fs.readFileSync(filePath, 'utf-8')
  const fileName = path.basename(filePath, '.md')
  const chunks: KnowledgeChunk[] = []

  // 按 ## 分割
  const sections = content.split(/^## /m).filter(Boolean)

  for (let i = 0; i < sections.length; i++) {
    const section = sections[i].trim()
    if (!section) continue

    const lines = section.split('\n')
    const title = lines[0].trim()
    const body = lines.slice(1).join('\n').trim()

    if (body.length > 50) {  // 忽略太短的片段
      chunks.push({
        id: `${fileName}-${i}`,
        content: `## ${title}\n\n${body}`,
        metadata: {
          source: filePath,
          title,
          category,
        },
      })
    }
  }

  return chunks
}

/**
 * 加载知识库目录下的所有 Markdown 文件
 */
export async function loadKnowledgeBase(knowledgeDir: string): Promise<number> {
  await initRAG()
  if (!collection) throw new Error('Collection not initialized')

  // 检查是否已有数据，避免重复加载
  const existingCount = await collection.count()
  if (existingCount > 0) {
    console.log(`[RAG] Collection already has ${existingCount} chunks, skipping load`)
    return existingCount
  }

  const files = fs.readdirSync(knowledgeDir).filter(f => f.endsWith('.md'))
  let totalChunks = 0

  for (const file of files) {
    const filePath = path.join(knowledgeDir, file)
    const category = file.replace('.md', '').replace(/-/g, '_')
    const chunks = parseMarkdownToChunks(filePath, category)

    if (chunks.length > 0) {
      // 生成 embeddings
      const embeddings = await generateEmbeddings(chunks.map(c => c.content))

      await collection.add({
        ids: chunks.map(c => c.id),
        documents: chunks.map(c => c.content),
        embeddings: embeddings,
        metadatas: chunks.map(c => c.metadata),
      })
      totalChunks += chunks.length
      console.log(`[RAG] Loaded ${chunks.length} chunks from ${file}`)
    }
  }

  console.log(`[RAG] Total chunks loaded: ${totalChunks}`)
  return totalChunks
}

/**
 * 检索相关知识片段
 */
export async function retrieveKnowledge(
  query: string,
  topK: number = 3
): Promise<KnowledgeChunk[]> {
  await initRAG()
  if (!collection) throw new Error('Collection not initialized')

  // 生成查询的 embedding
  const queryEmbedding = await generateEmbedding(query)

  const results = await collection.query({
    queryEmbeddings: [queryEmbedding],
    nResults: topK,
  })

  if (!results.documents?.[0]) return []

  return results.documents[0].map((doc, i) => ({
    id: results.ids[0][i],
    content: doc || '',
    metadata: (results.metadatas?.[0]?.[i] || {}) as KnowledgeChunk['metadata'],
  }))
}

/**
 * 获取集合统计信息
 */
export async function getRAGStats(): Promise<{ count: number }> {
  await initRAG()
  if (!collection) throw new Error('Collection not initialized')

  const count = await collection.count()
  return { count }
}

/**
 * 清空知识库
 */
export async function clearKnowledgeBase(): Promise<void> {
  if (!client) return

  try {
    await client.deleteCollection({ name: COLLECTION_NAME })
    collection = null
    console.log(`[RAG] Collection ${COLLECTION_NAME} deleted`)
  } catch (error) {
    // Collection may not exist
  }
}
