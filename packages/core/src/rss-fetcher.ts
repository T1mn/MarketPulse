/**
 * RSS Fetcher Service
 * 定时抓取 RSS 源并存储到本地
 */

import { insertNews, cleanupOldNews, type NewsRecord } from './news-store'
import { proxyFetch } from './proxy-fetch'

/**
 * RSS 源配置
 */
export interface RSSSource {
  name: string
  url: string
  category: string
}

/**
 * 默认 RSS 源
 */
const DEFAULT_RSS_SOURCES: RSSSource[] = [
  { name: 'Investing', url: 'https://www.investing.com/rss/news.rss', category: 'general' },
  { name: 'CNBC', url: 'https://www.cnbc.com/id/100003114/device/rss/rss.html', category: 'general' },
  {
    name: 'Yahoo Finance',
    url: `https://feeds.finance.yahoo.com/rss/2.0/headline?s=${process.env.YAHOO_SYMBOLS || 'AAPL,TSLA,MSFT,GOOGL,AMZN,NVDA,META'}`,
    category: 'stocks',
  },
  { name: 'CoinDesk', url: 'https://www.coindesk.com/arc/outboundfeeds/rss/', category: 'crypto' },
]

// 定时器引用
let schedulerInterval: ReturnType<typeof setInterval> | null = null

/**
 * 解析 RSS 时间格式为 UTC timestamp
 * 支持多种常见格式：RFC 822, ISO 8601 等
 */
function parseRSSDate(dateStr: string | undefined): number {
  if (!dateStr) return Date.now()

  try {
    const timestamp = Date.parse(dateStr)
    if (!isNaN(timestamp)) {
      return timestamp
    }
  } catch {
    // 解析失败，使用当前时间
  }

  return Date.now()
}

/**
 * 生成新闻 ID（基于 URL 的 hash）
 */
function generateNewsId(url: string): string {
  // 使用 Bun 的 hash 函数
  const hash = Bun.hash(url)
  return hash.toString(16).slice(0, 16)
}

/**
 * 清理 HTML 标签和多余空白
 */
function cleanText(text: string): string {
  return text
    .replace(/<[^>]*>/g, '') // 移除 HTML 标签
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ') // 合并多余空白
    .trim()
}

/**
 * 解析单个 RSS Feed
 */
async function parseRSSFeed(source: RSSSource): Promise<NewsRecord[]> {
  try {
    const response = await proxyFetch(source.url, {
      headers: {
        'User-Agent': 'MarketPulse/2.0 RSS Reader',
        Accept: 'application/rss+xml, application/xml, text/xml',
      },
    })

    if (!response.ok) {
      console.error(`[RSSFetcher] Failed to fetch ${source.name}: ${response.status}`)
      return []
    }

    const xml = await response.text()
    const items: NewsRecord[] = []
    const now = Date.now()

    // 解析 RSS 2.0 格式的 <item>
    const itemMatches = xml.match(/<item>([\s\S]*?)<\/item>/gi) || []

    for (const itemXml of itemMatches) {
      // 提取标题
      const titleMatch =
        itemXml.match(/<title><!\[CDATA\[([\s\S]*?)\]\]><\/title>/i) ||
        itemXml.match(/<title>([\s\S]*?)<\/title>/i)
      const title = titleMatch ? cleanText(titleMatch[1]) : ''

      // 提取链接
      const linkMatch = itemXml.match(/<link>([\s\S]*?)<\/link>/i)
      const url = linkMatch ? linkMatch[1].trim() : ''

      // 提取描述/摘要
      const descMatch =
        itemXml.match(/<description><!\[CDATA\[([\s\S]*?)\]\]><\/description>/i) ||
        itemXml.match(/<description>([\s\S]*?)<\/description>/i)
      const summary = descMatch ? cleanText(descMatch[1]).slice(0, 500) : ''

      // 提取发布时间
      const pubDateMatch = itemXml.match(/<pubDate>([\s\S]*?)<\/pubDate>/i)
      const publishedAt = parseRSSDate(pubDateMatch?.[1])

      if (title && url) {
        items.push({
          id: generateNewsId(url),
          title,
          summary: summary || null,
          source: source.name,
          url,
          publishedAt,
          fetchedAt: now,
          category: source.category,
        })
      }
    }

    // 如果没有找到 RSS 2.0 格式，尝试 Atom 格式
    if (items.length === 0) {
      const entryMatches = xml.match(/<entry>([\s\S]*?)<\/entry>/gi) || []

      for (const entryXml of entryMatches) {
        const titleMatch = entryXml.match(/<title[^>]*>([\s\S]*?)<\/title>/i)
        const title = titleMatch ? cleanText(titleMatch[1]) : ''

        const linkMatch = entryXml.match(/<link[^>]*href=["']([^"']+)["'][^>]*\/?>/i)
        const url = linkMatch ? linkMatch[1].trim() : ''

        const summaryMatch =
          entryXml.match(/<summary[^>]*>([\s\S]*?)<\/summary>/i) ||
          entryXml.match(/<content[^>]*>([\s\S]*?)<\/content>/i)
        const summary = summaryMatch ? cleanText(summaryMatch[1]).slice(0, 500) : ''

        const updatedMatch =
          entryXml.match(/<updated>([\s\S]*?)<\/updated>/i) ||
          entryXml.match(/<published>([\s\S]*?)<\/published>/i)
        const publishedAt = parseRSSDate(updatedMatch?.[1])

        if (title && url) {
          items.push({
            id: generateNewsId(url),
            title,
            summary: summary || null,
            source: source.name,
            url,
            publishedAt,
            fetchedAt: now,
            category: source.category,
          })
        }
      }
    }

    console.log(`[RSSFetcher] Parsed ${items.length} items from ${source.name}`)
    return items
  } catch (error) {
    console.error(`[RSSFetcher] Error fetching ${source.name}:`, error)
    return []
  }
}

/**
 * 抓取所有 RSS 源
 */
export async function fetchAllRSS(
  sources: RSSSource[] = DEFAULT_RSS_SOURCES
): Promise<{ total: number; inserted: number }> {
  console.log(`[RSSFetcher] Starting fetch for ${sources.length} sources...`)

  const results = await Promise.allSettled(sources.map((source) => parseRSSFeed(source)))

  const allItems: NewsRecord[] = []
  for (const result of results) {
    if (result.status === 'fulfilled') {
      allItems.push(...result.value)
    }
  }

  const inserted = insertNews(allItems)

  // 清理过期数据
  const retentionDays = parseInt(process.env.RSS_RETENTION_DAYS || '30', 10)
  const deleted = cleanupOldNews(retentionDays)

  console.log(
    `[RSSFetcher] Fetch complete: ${allItems.length} parsed, ${inserted} new, ${deleted} expired removed`
  )

  return { total: allItems.length, inserted }
}

/**
 * 启动定时抓取
 */
export function startRSSScheduler(intervalMinutes?: number): void {
  if (schedulerInterval) {
    console.log('[RSSFetcher] Scheduler already running')
    return
  }

  const interval = intervalMinutes || parseInt(process.env.RSS_FETCH_INTERVAL || '15', 10)
  const intervalMs = interval * 60 * 1000

  console.log(`[RSSFetcher] Starting scheduler with ${interval} minute interval`)

  schedulerInterval = setInterval(async () => {
    try {
      await fetchAllRSS()
    } catch (error) {
      console.error('[RSSFetcher] Scheduled fetch error:', error)
    }
  }, intervalMs)
}

/**
 * 停止定时抓取
 */
export function stopRSSScheduler(): void {
  if (schedulerInterval) {
    clearInterval(schedulerInterval)
    schedulerInterval = null
    console.log('[RSSFetcher] Scheduler stopped')
  }
}

/**
 * 获取 RSS 源列表
 */
export function getRSSSources(): RSSSource[] {
  return [...DEFAULT_RSS_SOURCES]
}
