/**
 * Stock SQLite Store
 * 美股数据存储，使用 Bun 原生 SQLite
 */

import { Database } from 'bun:sqlite'
import { join } from 'path'

/**
 * 股票价格记录
 */
export interface StockRecord {
  symbol: string
  price: number
  changePercent: number | null
  changeAmount: number | null
  previousClose: number | null
  openPrice: number | null
  dayHigh: number | null
  dayLow: number | null
  volume: number | null
  marketCap: number | null
  fetchedAt: number // UTC timestamp (ms)
}

// 数据库单例
let db: Database | null = null

/**
 * 获取数据库路径
 */
function getDBPath(): string {
  return join(import.meta.dir, '..', 'data', 'stocks.db')
}

/**
 * 初始化数据库
 */
export function initStockDB(): Database {
  if (db) return db

  const dbPath = getDBPath()
  db = new Database(dbPath, { create: true })

  // 启用 WAL 模式提升并发性能
  db.run('PRAGMA journal_mode = WAL')

  // 创建股票价格历史表（时序数据）
  db.run(`
    CREATE TABLE IF NOT EXISTS stock_prices (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      symbol TEXT NOT NULL,
      price REAL NOT NULL,
      change_percent REAL,
      change_amount REAL,
      previous_close REAL,
      open_price REAL,
      day_high REAL,
      day_low REAL,
      volume INTEGER,
      market_cap INTEGER,
      fetched_at INTEGER NOT NULL,
      UNIQUE(symbol, fetched_at)
    )
  `)

  // 创建最新价格表（快速查询）
  db.run(`
    CREATE TABLE IF NOT EXISTS stock_latest (
      symbol TEXT PRIMARY KEY,
      price REAL NOT NULL,
      change_percent REAL,
      change_amount REAL,
      previous_close REAL,
      open_price REAL,
      day_high REAL,
      day_low REAL,
      volume INTEGER,
      market_cap INTEGER,
      fetched_at INTEGER NOT NULL
    )
  `)

  // 创建索引
  db.run('CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock_prices(symbol)')
  db.run('CREATE INDEX IF NOT EXISTS idx_stock_fetched ON stock_prices(fetched_at DESC)')

  console.log('[StockStore] Database initialized:', dbPath)
  return db
}

/**
 * 获取数据库实例
 */
export function getStockDB(): Database {
  if (!db) {
    return initStockDB()
  }
  return db
}

/**
 * 批量插入股票价格，返回新增数量
 */
export function insertStockPrices(items: StockRecord[]): number {
  const database = getStockDB()
  let inserted = 0

  // 插入历史记录
  const historyStmt = database.prepare(`
    INSERT OR IGNORE INTO stock_prices
    (symbol, price, change_percent, change_amount, previous_close, open_price, day_high, day_low, volume, market_cap, fetched_at)
    VALUES ($symbol, $price, $changePercent, $changeAmount, $previousClose, $openPrice, $dayHigh, $dayLow, $volume, $marketCap, $fetchedAt)
  `)

  // 更新最新价格（使用 REPLACE）
  const latestStmt = database.prepare(`
    INSERT OR REPLACE INTO stock_latest
    (symbol, price, change_percent, change_amount, previous_close, open_price, day_high, day_low, volume, market_cap, fetched_at)
    VALUES ($symbol, $price, $changePercent, $changeAmount, $previousClose, $openPrice, $dayHigh, $dayLow, $volume, $marketCap, $fetchedAt)
  `)

  const insertMany = database.transaction((stockItems: StockRecord[]) => {
    for (const item of stockItems) {
      const params = {
        $symbol: item.symbol,
        $price: item.price,
        $changePercent: item.changePercent,
        $changeAmount: item.changeAmount,
        $previousClose: item.previousClose,
        $openPrice: item.openPrice,
        $dayHigh: item.dayHigh,
        $dayLow: item.dayLow,
        $volume: item.volume,
        $marketCap: item.marketCap,
        $fetchedAt: item.fetchedAt,
      }

      const result = historyStmt.run(params)
      if (result.changes > 0) {
        inserted++
      }

      // 更新最新价格
      latestStmt.run(params)
    }
  })

  insertMany(items)
  return inserted
}

/**
 * 获取单个股票最新价格
 */
export function getLatestStockPrice(symbol: string): StockRecord | null {
  const database = getStockDB()

  const row = database
    .query<
      {
        symbol: string
        price: number
        change_percent: number | null
        change_amount: number | null
        previous_close: number | null
        open_price: number | null
        day_high: number | null
        day_low: number | null
        volume: number | null
        market_cap: number | null
        fetched_at: number
      },
      [string]
    >(`
      SELECT symbol, price, change_percent, change_amount, previous_close,
             open_price, day_high, day_low, volume, market_cap, fetched_at
      FROM stock_latest
      WHERE symbol = ?
    `)
    .get(symbol.toUpperCase())

  if (!row) return null

  return {
    symbol: row.symbol,
    price: row.price,
    changePercent: row.change_percent,
    changeAmount: row.change_amount,
    previousClose: row.previous_close,
    openPrice: row.open_price,
    dayHigh: row.day_high,
    dayLow: row.day_low,
    volume: row.volume,
    marketCap: row.market_cap,
    fetchedAt: row.fetched_at,
  }
}

/**
 * 获取多个股票最新价格
 */
export function getLatestStockPrices(symbols: string[]): StockRecord[] {
  const database = getStockDB()

  const upperSymbols = symbols.map((s) => s.toUpperCase())
  const placeholders = upperSymbols.map(() => '?').join(',')

  const rows = database
    .query<
      {
        symbol: string
        price: number
        change_percent: number | null
        change_amount: number | null
        previous_close: number | null
        open_price: number | null
        day_high: number | null
        day_low: number | null
        volume: number | null
        market_cap: number | null
        fetched_at: number
      },
      string[]
    >(`
      SELECT symbol, price, change_percent, change_amount, previous_close,
             open_price, day_high, day_low, volume, market_cap, fetched_at
      FROM stock_latest
      WHERE symbol IN (${placeholders})
    `)
    .all(...upperSymbols)

  return rows.map((row) => ({
    symbol: row.symbol,
    price: row.price,
    changePercent: row.change_percent,
    changeAmount: row.change_amount,
    previousClose: row.previous_close,
    openPrice: row.open_price,
    dayHigh: row.day_high,
    dayLow: row.day_low,
    volume: row.volume,
    marketCap: row.market_cap,
    fetchedAt: row.fetched_at,
  }))
}

/**
 * 获取所有最新股票价格
 */
export function getAllLatestStockPrices(): StockRecord[] {
  const database = getStockDB()

  const rows = database
    .query<
      {
        symbol: string
        price: number
        change_percent: number | null
        change_amount: number | null
        previous_close: number | null
        open_price: number | null
        day_high: number | null
        day_low: number | null
        volume: number | null
        market_cap: number | null
        fetched_at: number
      },
      []
    >(`
      SELECT symbol, price, change_percent, change_amount, previous_close,
             open_price, day_high, day_low, volume, market_cap, fetched_at
      FROM stock_latest
      ORDER BY symbol
    `)
    .all()

  return rows.map((row) => ({
    symbol: row.symbol,
    price: row.price,
    changePercent: row.change_percent,
    changeAmount: row.change_amount,
    previousClose: row.previous_close,
    openPrice: row.open_price,
    dayHigh: row.day_high,
    dayLow: row.day_low,
    volume: row.volume,
    marketCap: row.market_cap,
    fetchedAt: row.fetched_at,
  }))
}

/**
 * 清理过期股票数据
 */
export function cleanupOldStocks(retentionDays: number = 7): number {
  const database = getStockDB()
  const cutoff = Date.now() - retentionDays * 24 * 60 * 60 * 1000

  const result = database.run('DELETE FROM stock_prices WHERE fetched_at < ?', [cutoff])
  return result.changes
}

/**
 * 获取股票数据统计
 */
export function getStockStats(): {
  totalRecords: number
  uniqueSymbols: number
  latestCount: number
  oldestFetch: number | null
  newestFetch: number | null
} {
  const database = getStockDB()

  const totalRow = database.query<{ count: number }, []>('SELECT COUNT(*) as count FROM stock_prices').get()
  const uniqueRow = database.query<{ count: number }, []>('SELECT COUNT(DISTINCT symbol) as count FROM stock_prices').get()
  const latestRow = database.query<{ count: number }, []>('SELECT COUNT(*) as count FROM stock_latest').get()
  const timeRow = database.query<{ oldest: number | null; newest: number | null }, []>(
    'SELECT MIN(fetched_at) as oldest, MAX(fetched_at) as newest FROM stock_prices'
  ).get()

  return {
    totalRecords: totalRow?.count || 0,
    uniqueSymbols: uniqueRow?.count || 0,
    latestCount: latestRow?.count || 0,
    oldestFetch: timeRow?.oldest || null,
    newestFetch: timeRow?.newest || null,
  }
}

/**
 * 关闭数据库
 */
export function closeStockDB(): void {
  if (db) {
    db.close()
    db = null
  }
}
