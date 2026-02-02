/**
 * Twitter SQLite Store
 * 本地推文存储，使用 Bun 原生 SQLite
 */

import { Database } from 'bun:sqlite'
import { join } from 'path'
import type { Tweet, TweetSortOptions } from './twitter'
import { DEFAULT_SORT_OPTIONS, calculateWeightedScore } from './twitter'

/**
 * Tweet record in database
 */
export interface TweetRecord {
  id: string
  text: string
  username: string
  name: string
  createdAt: string
  favoriteCount: number
  replyCount: number
  retweetCount: number
  quoteCount: number
  lang: string | null
  url: string | null
  searchQuery: string | null  // 关联的搜索关键词
  fetchedAt: number
}

// 数据库单例
let db: Database | null = null

/**
 * 获取数据库路径
 */
function getDBPath(): string {
  return join(import.meta.dir, '..', 'data', 'twitter.db')
}

/**
 * 初始化数据库
 */
export function initTwitterDB(): Database {
  if (db) return db

  const dbPath = getDBPath()
  db = new Database(dbPath, { create: true })

  // 启用 WAL 模式提升并发性能
  db.run('PRAGMA journal_mode = WAL')

  // 创建主表
  db.run(`
    CREATE TABLE IF NOT EXISTS tweets (
      id TEXT PRIMARY KEY,
      text TEXT NOT NULL,
      username TEXT NOT NULL,
      name TEXT,
      created_at TEXT NOT NULL,
      favorite_count INTEGER DEFAULT 0,
      reply_count INTEGER DEFAULT 0,
      retweet_count INTEGER DEFAULT 0,
      quote_count INTEGER DEFAULT 0,
      lang TEXT,
      url TEXT,
      search_query TEXT,
      fetched_at INTEGER NOT NULL
    )
  `)

  // 创建索引
  db.run('CREATE INDEX IF NOT EXISTS idx_tweets_created ON tweets(created_at DESC)')
  db.run('CREATE INDEX IF NOT EXISTS idx_tweets_username ON tweets(username)')
  db.run('CREATE INDEX IF NOT EXISTS idx_tweets_query ON tweets(search_query)')
  db.run('CREATE INDEX IF NOT EXISTS idx_tweets_fetched ON tweets(fetched_at DESC)')

  // 创建 FTS5 虚拟表用于全文搜索
  db.run(`
    CREATE VIRTUAL TABLE IF NOT EXISTS tweets_fts USING fts5(
      text,
      username,
      name,
      content=tweets,
      content_rowid=rowid
    )
  `)

  // 同步触发器 - 插入
  db.run(`
    CREATE TRIGGER IF NOT EXISTS tweets_ai AFTER INSERT ON tweets BEGIN
      INSERT INTO tweets_fts(rowid, text, username, name)
      VALUES (NEW.rowid, NEW.text, NEW.username, NEW.name);
    END
  `)

  // 同步触发器 - 删除
  db.run(`
    CREATE TRIGGER IF NOT EXISTS tweets_ad AFTER DELETE ON tweets BEGIN
      INSERT INTO tweets_fts(tweets_fts, rowid, text, username, name)
      VALUES('delete', OLD.rowid, OLD.text, OLD.username, OLD.name);
    END
  `)

  // 同步触发器 - 更新
  db.run(`
    CREATE TRIGGER IF NOT EXISTS tweets_au AFTER UPDATE ON tweets BEGIN
      INSERT INTO tweets_fts(tweets_fts, rowid, text, username, name)
      VALUES('delete', OLD.rowid, OLD.text, OLD.username, OLD.name);
      INSERT INTO tweets_fts(rowid, text, username, name)
      VALUES (NEW.rowid, NEW.text, NEW.username, NEW.name);
    END
  `)

  console.log('[TwitterStore] Database initialized:', dbPath)
  return db
}

/**
 * 获取数据库实例
 */
export function getTwitterDB(): Database {
  if (!db) {
    return initTwitterDB()
  }
  return db
}

/**
 * 批量插入推文，返回新增数量
 */
export function insertTweets(tweets: Tweet[], searchQuery?: string): number {
  const database = getTwitterDB()
  let inserted = 0

  const stmt = database.prepare(`
    INSERT OR REPLACE INTO tweets
    (id, text, username, name, created_at, favorite_count, reply_count, retweet_count, quote_count, lang, url, search_query, fetched_at)
    VALUES ($id, $text, $username, $name, $createdAt, $favoriteCount, $replyCount, $retweetCount, $quoteCount, $lang, $url, $searchQuery, $fetchedAt)
  `)

  const fetchedAt = Date.now()

  const insertMany = database.transaction((items: Tweet[]) => {
    for (const tweet of items) {
      const result = stmt.run({
        $id: tweet.id,
        $text: tweet.text,
        $username: tweet.username,
        $name: tweet.name || '',
        $createdAt: tweet.createdAt,
        $favoriteCount: tweet.favoriteCount,
        $replyCount: tweet.replyCount,
        $retweetCount: tweet.retweetCount,
        $quoteCount: tweet.quoteCount,
        $lang: tweet.lang || null,
        $url: tweet.url || null,
        $searchQuery: searchQuery || null,
        $fetchedAt: fetchedAt,
      })
      if (result.changes > 0) {
        inserted++
      }
    }
  })

  insertMany(tweets)
  return inserted
}

/**
 * FTS5 全文搜索推文
 */
export function searchTweetsInDB(
  query: string,
  options: {
    limit?: number
    sortOptions?: TweetSortOptions
  } = {}
): Tweet[] {
  const { limit = 20, sortOptions = DEFAULT_SORT_OPTIONS } = options
  const database = getTwitterDB()

  // FTS5 搜索
  const rows = database
    .query<TweetDBRow, [string, number]>(
      `
    SELECT tweets.id, tweets.text, tweets.username, tweets.name, tweets.created_at,
           tweets.favorite_count, tweets.reply_count, tweets.retweet_count, tweets.quote_count,
           tweets.lang, tweets.url
    FROM tweets_fts
    JOIN tweets ON tweets.rowid = tweets_fts.rowid
    WHERE tweets_fts MATCH ?
    ORDER BY tweets.created_at DESC
    LIMIT ?
  `
    )
    .all(query, limit * 2) // Fetch more for sorting

  const tweets = rows.map(rowToTweet)

  // Apply weighted sorting
  return tweets
    .map(tweet => ({
      ...tweet,
      weightedScore: calculateWeightedScore(tweet, sortOptions),
    }))
    .sort((a, b) => (b.weightedScore || 0) - (a.weightedScore || 0))
    .slice(0, limit)
}

/**
 * 按搜索关键词获取推文
 */
export function getTweetsByQuery(
  searchQuery: string,
  options: {
    limit?: number
    sortOptions?: TweetSortOptions
  } = {}
): Tweet[] {
  const { limit = 20, sortOptions = DEFAULT_SORT_OPTIONS } = options
  const database = getTwitterDB()

  const rows = database
    .query<TweetDBRow, [string, number]>(
      `
    SELECT id, text, username, name, created_at, favorite_count, reply_count,
           retweet_count, quote_count, lang, url
    FROM tweets
    WHERE search_query = ?
    ORDER BY created_at DESC
    LIMIT ?
  `
    )
    .all(searchQuery, limit * 2)

  const tweets = rows.map(rowToTweet)

  // Apply weighted sorting
  return tweets
    .map(tweet => ({
      ...tweet,
      weightedScore: calculateWeightedScore(tweet, sortOptions),
    }))
    .sort((a, b) => (b.weightedScore || 0) - (a.weightedScore || 0))
    .slice(0, limit)
}

/**
 * 获取最新推文
 */
export function getLatestTweets(
  options: {
    limit?: number
    username?: string
    sortOptions?: TweetSortOptions
  } = {}
): Tweet[] {
  const { limit = 20, username, sortOptions = DEFAULT_SORT_OPTIONS } = options
  const database = getTwitterDB()

  let sql = `
    SELECT id, text, username, name, created_at, favorite_count, reply_count,
           retweet_count, quote_count, lang, url
    FROM tweets
  `
  const params: (string | number)[] = []

  if (username) {
    sql += ' WHERE username = ?'
    params.push(username)
  }

  sql += ' ORDER BY created_at DESC LIMIT ?'
  params.push(limit * 2)

  const rows = database.query<TweetDBRow, (string | number)[]>(sql).all(...params)

  const tweets = rows.map(rowToTweet)

  // Apply weighted sorting
  return tweets
    .map(tweet => ({
      ...tweet,
      weightedScore: calculateWeightedScore(tweet, sortOptions),
    }))
    .sort((a, b) => (b.weightedScore || 0) - (a.weightedScore || 0))
    .slice(0, limit)
}

/**
 * 获取热门推文（按加权分数排序）
 */
export function getTopTweetsFromDB(
  options: {
    limit?: number
    sortOptions?: TweetSortOptions
    searchQuery?: string
  } = {}
): Tweet[] {
  const { limit = 10, sortOptions = DEFAULT_SORT_OPTIONS, searchQuery } = options
  const database = getTwitterDB()

  let sql = `
    SELECT id, text, username, name, created_at, favorite_count, reply_count,
           retweet_count, quote_count, lang, url
    FROM tweets
  `
  const params: (string | number)[] = []

  if (searchQuery) {
    sql += ' WHERE search_query = ?'
    params.push(searchQuery)
  }

  // Fetch more and sort in memory for accurate weighted scoring
  sql += ' LIMIT 1000'

  const rows = database.query<TweetDBRow, (string | number)[]>(sql).all(...params)

  const tweets = rows.map(rowToTweet)

  // Apply weighted sorting
  return tweets
    .map(tweet => ({
      ...tweet,
      weightedScore: calculateWeightedScore(tweet, sortOptions),
    }))
    .sort((a, b) => (b.weightedScore || 0) - (a.weightedScore || 0))
    .slice(0, limit)
}

/**
 * 清理过期推文
 */
export function cleanupOldTweets(retentionDays: number = 7): number {
  const database = getTwitterDB()
  const cutoff = Date.now() - retentionDays * 24 * 60 * 60 * 1000

  const result = database.run('DELETE FROM tweets WHERE fetched_at < ?', [cutoff])
  return result.changes
}

/**
 * 获取推文数量统计
 */
export function getTwitterStats(): {
  total: number
  byQuery: Record<string, number>
  byUsername: { username: string; count: number }[]
  lastFetchedAt: number | null
} {
  const database = getTwitterDB()

  const totalRow = database.query<{ count: number }, []>('SELECT COUNT(*) as count FROM tweets').get()
  const total = totalRow?.count || 0

  // By search query
  const queryRows = database
    .query<{ search_query: string | null; count: number }, []>(
      'SELECT search_query, COUNT(*) as count FROM tweets GROUP BY search_query'
    )
    .all()

  const byQuery: Record<string, number> = {}
  for (const row of queryRows) {
    byQuery[row.search_query || 'unknown'] = row.count
  }

  // By username (top 10)
  const userRows = database
    .query<{ username: string; count: number }, []>(
      'SELECT username, COUNT(*) as count FROM tweets GROUP BY username ORDER BY count DESC LIMIT 10'
    )
    .all()

  const byUsername = userRows.map(row => ({ username: row.username, count: row.count }))

  // Last fetched
  const lastRow = database
    .query<{ fetched_at: number }, []>('SELECT MAX(fetched_at) as fetched_at FROM tweets')
    .get()

  return {
    total,
    byQuery,
    byUsername,
    lastFetchedAt: lastRow?.fetched_at || null,
  }
}

/**
 * 获取所有搜索关键词
 */
export function getSearchQueries(): string[] {
  const database = getTwitterDB()

  const rows = database
    .query<{ search_query: string }, []>(
      'SELECT DISTINCT search_query FROM tweets WHERE search_query IS NOT NULL ORDER BY search_query'
    )
    .all()

  return rows.map(row => row.search_query)
}

/**
 * 关闭数据库
 */
export function closeTwitterDB(): void {
  if (db) {
    db.close()
    db = null
  }
}

// Internal types
interface TweetDBRow {
  id: string
  text: string
  username: string
  name: string | null
  created_at: string
  favorite_count: number
  reply_count: number
  retweet_count: number
  quote_count: number
  lang: string | null
  url: string | null
}

function rowToTweet(row: TweetDBRow): Tweet {
  return {
    id: row.id,
    text: row.text,
    username: row.username,
    name: row.name ?? '',
    createdAt: row.created_at,
    favoriteCount: row.favorite_count,
    replyCount: row.reply_count,
    retweetCount: row.retweet_count,
    quoteCount: row.quote_count,
    lang: row.lang || undefined,
    url: row.url || undefined,
  }
}
