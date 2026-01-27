/**
 * News Service
 * 新闻查询服务（从本地 SQLite 读取）
 */

import {
  getLatestNews,
  searchNewsInDB,
  formatToBeijingTime,
  type NewsRecord,
} from './news-store'

/**
 * 新闻条目（对外接口）
 */
export interface NewsItem {
  id: string
  title: string
  summary: string
  source: string
  url: string
  publishedAt: string // 北京时间 ISO 字符串
  category?: string
}

/**
 * 将内部记录转换为对外接口
 */
function toNewsItem(record: NewsRecord): NewsItem {
  return {
    id: record.id,
    title: record.title,
    summary: record.summary || '',
    source: record.source,
    url: record.url,
    publishedAt: formatToBeijingTime(record.publishedAt),
    category: record.category || undefined,
  }
}

/**
 * 获取最新新闻
 */
export async function getNews(options?: {
  limit?: number
  category?: string
}): Promise<NewsItem[]> {
  const { limit = 20, category } = options || {}

  const records = getLatestNews(limit, category)
  return records.map(toNewsItem)
}

/**
 * 搜索新闻
 */
export async function searchNews(
  query: string,
  options?: { limit?: number }
): Promise<NewsItem[]> {
  const { limit = 20 } = options || {}

  if (!query || !query.trim()) {
    return getNews({ limit })
  }

  // 中英文关键词映射（用于扩展搜索）
  const keywordMap: Record<string, string[]> = {
    '比特币': ['bitcoin', 'btc'],
    '以太坊': ['ethereum', 'eth'],
    '加密货币': ['crypto', 'cryptocurrency'],
    '区块链': ['blockchain'],
    '币安': ['binance'],
    '交易所': ['exchange'],
    '苹果': ['apple', 'aapl'],
    '特斯拉': ['tesla', 'tsla'],
    '微软': ['microsoft', 'msft'],
    '谷歌': ['google', 'googl'],
    '亚马逊': ['amazon', 'amzn'],
    '英伟达': ['nvidia', 'nvda'],
  }

  // 构建 FTS5 查询
  const keywords = query.toLowerCase().split(/\s+/).filter(k => k.length > 0)
  const expandedKeywords = new Set<string>()

  for (const keyword of keywords) {
    expandedKeywords.add(keyword)
    // 如果是中文关键词，添加对应的英文
    if (keywordMap[keyword]) {
      keywordMap[keyword].forEach(k => expandedKeywords.add(k))
    }
  }

  // FTS5 OR 查询
  const ftsQuery = Array.from(expandedKeywords).join(' OR ')

  try {
    const records = searchNewsInDB(ftsQuery, limit)
    return records.map(toNewsItem)
  } catch (error) {
    // FTS5 查询失败时，回退到简单查询
    console.error('[News] FTS5 search error, falling back to latest:', error)
    return getNews({ limit })
  }
}
