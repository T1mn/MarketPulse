/**
 * News Aggregation Service
 * 聚合金融新闻数据
 */

/**
 * 新闻条目
 */
export interface NewsItem {
  id: string
  title: string
  summary: string
  source: string
  url: string
  publishedAt: number
  category?: string
}

/**
 * RSS Feed 源
 */
const RSS_FEEDS = [
  {
    name: 'CoinDesk',
    url: 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    category: 'crypto',
  },
  {
    name: 'Cointelegraph',
    url: 'https://cointelegraph.com/rss',
    category: 'crypto',
  },
]

/**
 * 解析 RSS Feed
 */
async function parseRSSFeed(feedUrl: string, source: string, category: string): Promise<NewsItem[]> {
  try {
    const response = await fetch(feedUrl)
    if (!response.ok) {
      console.error(`Failed to fetch RSS feed from ${source}`)
      return []
    }

    const xml = await response.text()

    // 简单的 XML 解析（不依赖外部库）
    const items: NewsItem[] = []
    const itemMatches = xml.match(/<item>([\s\S]*?)<\/item>/g) || []

    for (const itemXml of itemMatches.slice(0, 10)) {
      const title = itemXml.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/)?.[1]
        || itemXml.match(/<title>(.*?)<\/title>/)?.[1]
        || ''

      const link = itemXml.match(/<link>(.*?)<\/link>/)?.[1] || ''

      const description = itemXml.match(/<description><!\[CDATA\[(.*?)\]\]><\/description>/)?.[1]
        || itemXml.match(/<description>(.*?)<\/description>/)?.[1]
        || ''

      const pubDate = itemXml.match(/<pubDate>(.*?)<\/pubDate>/)?.[1]

      if (title && link) {
        items.push({
          id: Buffer.from(link).toString('base64').slice(0, 16),
          title: title.trim(),
          summary: description.replace(/<[^>]*>/g, '').trim().slice(0, 200),
          source,
          url: link,
          publishedAt: pubDate ? new Date(pubDate).getTime() : Date.now(),
          category,
        })
      }
    }

    return items
  } catch (error) {
    console.error(`Error parsing RSS feed from ${source}:`, error)
    return []
  }
}

/**
 * 从 Finnhub 获取新闻（需要 API key）
 */
async function fetchFinnhubNews(apiKey: string): Promise<NewsItem[]> {
  if (!apiKey) return []

  try {
    const response = await fetch(
      `https://finnhub.io/api/v1/news?category=crypto&token=${apiKey}`
    )

    if (!response.ok) return []

    const data: any[] = await response.json()

    return data.slice(0, 10).map((item) => ({
      id: String(item.id),
      title: item.headline,
      summary: item.summary?.slice(0, 200) || '',
      source: item.source,
      url: item.url,
      publishedAt: item.datetime * 1000,
      category: 'crypto',
    }))
  } catch (error) {
    console.error('Error fetching Finnhub news:', error)
    return []
  }
}

/**
 * 获取所有新闻
 */
export async function getNews(options?: {
  finnhubApiKey?: string
  limit?: number
}): Promise<NewsItem[]> {
  const { finnhubApiKey, limit = 20 } = options || {}

  // 并行获取所有源
  const promises: Promise<NewsItem[]>[] = [
    ...RSS_FEEDS.map((feed) => parseRSSFeed(feed.url, feed.name, feed.category)),
  ]

  if (finnhubApiKey) {
    promises.push(fetchFinnhubNews(finnhubApiKey))
  }

  const results = await Promise.all(promises)
  const allNews = results.flat()

  // 按时间排序，去重
  const seen = new Set<string>()
  const uniqueNews = allNews
    .sort((a, b) => b.publishedAt - a.publishedAt)
    .filter((item) => {
      if (seen.has(item.title)) return false
      seen.add(item.title)
      return true
    })
    .slice(0, limit)

  return uniqueNews
}

/**
 * 搜索新闻
 */
export async function searchNews(
  query: string,
  options?: { finnhubApiKey?: string }
): Promise<NewsItem[]> {
  const news = await getNews(options)
  const lowerQuery = query.toLowerCase()

  return news.filter(
    (item) =>
      item.title.toLowerCase().includes(lowerQuery) ||
      item.summary.toLowerCase().includes(lowerQuery)
  )
}
