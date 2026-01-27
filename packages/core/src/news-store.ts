/**
 * News SQLite Store
 * 本地新闻存储，使用 Bun 原生 SQLite
 */

import { Database } from 'bun:sqlite'
import { join } from 'path'

/**
 * 新闻记录
 */
export interface NewsRecord {
  id: string
  title: string
  summary: string | null
  source: string
  url: string
  publishedAt: number // UTC timestamp (ms)
  fetchedAt: number
  category: string | null
}

// 数据库单例
let db: Database | null = null

/**
 * 获取数据库路径
 */
function getDBPath(): string {
  return join(import.meta.dir, '..', 'data', 'news.db')
}

/**
 * 初始化数据库
 */
export function initNewsDB(): Database {
  if (db) return db

  const dbPath = getDBPath()
  db = new Database(dbPath, { create: true })

  // 启用 WAL 模式提升并发性能
  db.run('PRAGMA journal_mode = WAL')

  // 创建主表
  db.run(`
    CREATE TABLE IF NOT EXISTS news (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      summary TEXT,
      source TEXT NOT NULL,
      url TEXT UNIQUE NOT NULL,
      published_at INTEGER NOT NULL,
      fetched_at INTEGER NOT NULL,
      category TEXT
    )
  `)

  // 创建索引
  db.run('CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at DESC)')
  db.run('CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)')

  // 创建 FTS5 虚拟表
  db.run(`
    CREATE VIRTUAL TABLE IF NOT EXISTS news_fts USING fts5(
      title,
      summary,
      content=news,
      content_rowid=rowid
    )
  `)

  // 同步触发器 - 插入
  db.run(`
    CREATE TRIGGER IF NOT EXISTS news_ai AFTER INSERT ON news BEGIN
      INSERT INTO news_fts(rowid, title, summary) VALUES (NEW.rowid, NEW.title, NEW.summary);
    END
  `)

  // 同步触发器 - 删除
  db.run(`
    CREATE TRIGGER IF NOT EXISTS news_ad AFTER DELETE ON news BEGIN
      INSERT INTO news_fts(news_fts, rowid, title, summary) VALUES('delete', OLD.rowid, OLD.title, OLD.summary);
    END
  `)

  console.log('[NewsStore] Database initialized:', dbPath)
  return db
}

/**
 * 获取数据库实例
 */
export function getNewsDB(): Database {
  if (!db) {
    return initNewsDB()
  }
  return db
}

/**
 * 批量插入新闻，返回新增数量
 */
export function insertNews(items: NewsRecord[]): number {
  const database = getNewsDB()
  let inserted = 0

  const stmt = database.prepare(`
    INSERT OR IGNORE INTO news (id, title, summary, source, url, published_at, fetched_at, category)
    VALUES ($id, $title, $summary, $source, $url, $publishedAt, $fetchedAt, $category)
  `)

  const insertMany = database.transaction((newsItems: NewsRecord[]) => {
    for (const item of newsItems) {
      const result = stmt.run({
        $id: item.id,
        $title: item.title,
        $summary: item.summary,
        $source: item.source,
        $url: item.url,
        $publishedAt: item.publishedAt,
        $fetchedAt: item.fetchedAt,
        $category: item.category,
      })
      if (result.changes > 0) {
        inserted++
      }
    }
  })

  insertMany(items)
  return inserted
}

/**
 * FTS5 全文搜索
 */
export function searchNewsInDB(query: string, limit: number = 20): NewsRecord[] {
  const database = getNewsDB()

  // FTS5 搜索
  const rows = database
    .query<
      {
        id: string
        title: string
        summary: string | null
        source: string
        url: string
        published_at: number
        fetched_at: number
        category: string | null
      },
      [string, number]
    >(
      `
    SELECT news.id, news.title, news.summary, news.source, news.url,
           news.published_at, news.fetched_at, news.category
    FROM news_fts
    JOIN news ON news.rowid = news_fts.rowid
    WHERE news_fts MATCH ?
    ORDER BY news.published_at DESC
    LIMIT ?
  `
    )
    .all(query, limit)

  return rows.map((row) => ({
    id: row.id,
    title: row.title,
    summary: row.summary,
    source: row.source,
    url: row.url,
    publishedAt: row.published_at,
    fetchedAt: row.fetched_at,
    category: row.category,
  }))
}

/**
 * 获取最新新闻
 */
export function getLatestNews(limit: number = 20, category?: string): NewsRecord[] {
  const database = getNewsDB()

  let sql = `
    SELECT id, title, summary, source, url, published_at, fetched_at, category
    FROM news
  `
  const params: (string | number)[] = []

  if (category) {
    sql += ' WHERE category = ?'
    params.push(category)
  }

  sql += ' ORDER BY published_at DESC LIMIT ?'
  params.push(limit)

  const rows = database
    .query<
      {
        id: string
        title: string
        summary: string | null
        source: string
        url: string
        published_at: number
        fetched_at: number
        category: string | null
      },
      (string | number)[]
    >(sql)
    .all(...params)

  return rows.map((row) => ({
    id: row.id,
    title: row.title,
    summary: row.summary,
    source: row.source,
    url: row.url,
    publishedAt: row.published_at,
    fetchedAt: row.fetched_at,
    category: row.category,
  }))
}

/**
 * 清理过期新闻
 */
export function cleanupOldNews(retentionDays: number = 30): number {
  const database = getNewsDB()
  const cutoff = Date.now() - retentionDays * 24 * 60 * 60 * 1000

  const result = database.run('DELETE FROM news WHERE published_at < ?', [cutoff])
  return result.changes
}

/**
 * 获取新闻数量统计
 */
export function getNewsStats(): { total: number; byCategory: Record<string, number> } {
  const database = getNewsDB()

  const totalRow = database.query<{ count: number }, []>('SELECT COUNT(*) as count FROM news').get()
  const total = totalRow?.count || 0

  const categoryRows = database
    .query<{ category: string | null; count: number }, []>(
      'SELECT category, COUNT(*) as count FROM news GROUP BY category'
    )
    .all()

  const byCategory: Record<string, number> = {}
  for (const row of categoryRows) {
    byCategory[row.category || 'unknown'] = row.count
  }

  return { total, byCategory }
}

/**
 * 格式化为北京时间 ISO 字符串
 */
export function formatToBeijingTime(timestamp: number): string {
  const date = new Date(timestamp)
  // 北京时间 = UTC + 8 小时
  const beijingOffset = 8 * 60 * 60 * 1000
  const beijingDate = new Date(date.getTime() + beijingOffset)

  const year = beijingDate.getUTCFullYear()
  const month = String(beijingDate.getUTCMonth() + 1).padStart(2, '0')
  const day = String(beijingDate.getUTCDate()).padStart(2, '0')
  const hours = String(beijingDate.getUTCHours()).padStart(2, '0')
  const minutes = String(beijingDate.getUTCMinutes()).padStart(2, '0')
  const seconds = String(beijingDate.getUTCSeconds()).padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}+08:00`
}

/**
 * 关闭数据库
 */
export function closeNewsDB(): void {
  if (db) {
    db.close()
    db = null
  }
}
