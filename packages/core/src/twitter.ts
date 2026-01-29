/**
 * Twitter/X Tweet Module
 * 推文抓取与加权排序
 */

import { z } from 'zod'

/**
 * Tweet interface matching tweet-harvest CSV output
 */
export interface Tweet {
  id: string
  text: string
  username: string
  name: string
  createdAt: string
  // Metrics for weighted sorting
  favoriteCount: number  // 点赞数
  replyCount: number     // 评论数
  retweetCount: number   // 转发数
  quoteCount: number     // 引用数
  // Computed
  weightedScore?: number
  // Additional metadata
  lang?: string
  url?: string
}

/**
 * Zod schema for tweet validation
 */
export const TweetSchema = z.object({
  id: z.string(),
  text: z.string(),
  username: z.string(),
  name: z.string(),
  createdAt: z.string(),
  favoriteCount: z.number().default(0),
  replyCount: z.number().default(0),
  retweetCount: z.number().default(0),
  quoteCount: z.number().default(0),
  weightedScore: z.number().optional(),
  lang: z.string().optional(),
  url: z.string().optional(),
})

/**
 * Sort options for weighted scoring
 */
export interface TweetSortOptions {
  likeWeight: number      // 点赞权重
  replyWeight: number     // 评论权重
  retweetWeight: number   // 转发权重
  quoteWeight: number     // 引用权重
}

/**
 * Default sort weights
 * 评论权重高于点赞，因为评论代表更高的参与度
 */
export const DEFAULT_SORT_OPTIONS: TweetSortOptions = {
  likeWeight: 1,
  replyWeight: 2,
  retweetWeight: 1.5,
  quoteWeight: 1.5,
}

/**
 * Calculate weighted score for a tweet
 */
export function calculateWeightedScore(tweet: Tweet, options: TweetSortOptions = DEFAULT_SORT_OPTIONS): number {
  return (
    tweet.favoriteCount * options.likeWeight +
    tweet.replyCount * options.replyWeight +
    tweet.retweetCount * options.retweetWeight +
    tweet.quoteCount * options.quoteWeight
  )
}

/**
 * Sort tweets by weighted score
 */
export function sortByWeightedScore(tweets: Tweet[], options: TweetSortOptions = DEFAULT_SORT_OPTIONS): Tweet[] {
  return tweets
    .map(tweet => ({
      ...tweet,
      weightedScore: calculateWeightedScore(tweet, options),
    }))
    .sort((a, b) => (b.weightedScore || 0) - (a.weightedScore || 0))
}

/**
 * Parse tweet-harvest CSV output
 * tweet-harvest outputs: id, text, created_at, username, reply_count, retweet_count, favorite_count, quote_count
 */
export function parseTweetHarvestCSV(csvContent: string): Tweet[] {
  const lines = csvContent.trim().split('\n')
  if (lines.length < 2) return []

  // Parse header
  const header = parseCSVLine(lines[0])
  const headerMap = new Map<string, number>()
  header.forEach((col, idx) => headerMap.set(col.toLowerCase().trim(), idx))

  // Parse rows
  const tweets: Tweet[] = []
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    try {
      const values = parseCSVLine(line)

      const tweet: Tweet = {
        id: getCSVValue(values, headerMap, ['id', 'tweet_id']) || `tweet-${i}`,
        text: getCSVValue(values, headerMap, ['text', 'full_text', 'content']) || '',
        username: getCSVValue(values, headerMap, ['username', 'screen_name', 'user']) || 'unknown',
        name: getCSVValue(values, headerMap, ['name', 'display_name']) || '',
        createdAt: getCSVValue(values, headerMap, ['created_at', 'createdat', 'date']) || new Date().toISOString(),
        favoriteCount: parseInt(getCSVValue(values, headerMap, ['favorite_count', 'favoritecount', 'likes', 'like_count']) || '0', 10) || 0,
        replyCount: parseInt(getCSVValue(values, headerMap, ['reply_count', 'replycount', 'replies']) || '0', 10) || 0,
        retweetCount: parseInt(getCSVValue(values, headerMap, ['retweet_count', 'retweetcount', 'retweets']) || '0', 10) || 0,
        quoteCount: parseInt(getCSVValue(values, headerMap, ['quote_count', 'quotecount', 'quotes']) || '0', 10) || 0,
        lang: getCSVValue(values, headerMap, ['lang', 'language']) || undefined,
      }

      // Generate URL
      if (tweet.username && tweet.id) {
        tweet.url = `https://x.com/${tweet.username}/status/${tweet.id}`
      }

      tweets.push(tweet)
    } catch (error) {
      console.warn(`[Twitter] Failed to parse row ${i}:`, error)
    }
  }

  return tweets
}

/**
 * Parse a single CSV line, handling quoted fields
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    const nextChar = line[i + 1]

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // Escaped quote
        current += '"'
        i++
      } else {
        // Toggle quote mode
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }

  result.push(current.trim())
  return result
}

/**
 * Get value from CSV row by trying multiple column names
 */
function getCSVValue(values: string[], headerMap: Map<string, number>, possibleNames: string[]): string {
  for (const name of possibleNames) {
    const idx = headerMap.get(name.toLowerCase())
    if (idx !== undefined && values[idx] !== undefined) {
      return values[idx]
    }
  }
  return ''
}

/**
 * Filter tweets by text content
 */
export function filterTweets(tweets: Tweet[], query: string): Tweet[] {
  const queryLower = query.toLowerCase()
  return tweets.filter(tweet =>
    tweet.text.toLowerCase().includes(queryLower) ||
    tweet.username.toLowerCase().includes(queryLower) ||
    tweet.name.toLowerCase().includes(queryLower)
  )
}

/**
 * Get top tweets by engagement
 */
export function getTopTweets(tweets: Tweet[], limit: number = 10, options: TweetSortOptions = DEFAULT_SORT_OPTIONS): Tweet[] {
  return sortByWeightedScore(tweets, options).slice(0, limit)
}

/**
 * Format tweet for display
 */
export function formatTweetForDisplay(tweet: Tweet): string {
  const score = tweet.weightedScore?.toFixed(1) || '0'
  const metrics = `${tweet.favoriteCount} likes | ${tweet.replyCount} replies | ${tweet.retweetCount} RTs`
  return `@${tweet.username} (score: ${score})
${tweet.text}
${metrics}
${tweet.url || ''}`
}

/**
 * Aggregate tweet statistics
 */
export function getTweetStats(tweets: Tweet[]): {
  total: number
  totalLikes: number
  totalReplies: number
  totalRetweets: number
  totalQuotes: number
  avgLikes: number
  avgReplies: number
  topAuthors: { username: string; count: number }[]
} {
  const total = tweets.length
  if (total === 0) {
    return {
      total: 0,
      totalLikes: 0,
      totalReplies: 0,
      totalRetweets: 0,
      totalQuotes: 0,
      avgLikes: 0,
      avgReplies: 0,
      topAuthors: [],
    }
  }

  const totalLikes = tweets.reduce((sum, t) => sum + t.favoriteCount, 0)
  const totalReplies = tweets.reduce((sum, t) => sum + t.replyCount, 0)
  const totalRetweets = tweets.reduce((sum, t) => sum + t.retweetCount, 0)
  const totalQuotes = tweets.reduce((sum, t) => sum + t.quoteCount, 0)

  // Count by author
  const authorCounts = new Map<string, number>()
  for (const tweet of tweets) {
    authorCounts.set(tweet.username, (authorCounts.get(tweet.username) || 0) + 1)
  }

  const topAuthors = Array.from(authorCounts.entries())
    .map(([username, count]) => ({ username, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  return {
    total,
    totalLikes,
    totalReplies,
    totalRetweets,
    totalQuotes,
    avgLikes: Math.round(totalLikes / total),
    avgReplies: Math.round(totalReplies / total),
    topAuthors,
  }
}
