/**
 * Stock Fetcher Service
 * 定时抓取美股数据并存储到本地
 */

import YahooFinance from 'yahoo-finance2'
import { insertStockPrices, cleanupOldStocks, type StockRecord } from './stock-store'

// Initialize Yahoo Finance client
// Note: yahoo-finance2 uses native fetch, proxy is handled via HTTP_PROXY env var
const yahooFinance = new YahooFinance({
  suppressNotices: ['yahooSurvey'],
})

/**
 * 默认股票列表（12 只科技股）
 */
export const DEFAULT_STOCK_SYMBOLS = [
  'AAPL',   // Apple
  'MSFT',   // Microsoft
  'GOOGL',  // Alphabet (Google)
  'AMZN',   // Amazon
  'NVDA',   // NVIDIA
  'TSLA',   // Tesla
  'META',   // Meta (Facebook)
  'AMD',    // AMD
  'INTC',   // Intel
  'NFLX',   // Netflix
  'CRM',    // Salesforce
  'ORCL',   // Oracle
]

/**
 * 默认贵金属/大宗商品列表
 */
export const DEFAULT_COMMODITY_SYMBOLS = [
  'GC=F',   // Gold Futures (黄金期货)
  'SI=F',   // Silver Futures (白银期货)
  'GLD',    // SPDR Gold Shares (黄金 ETF)
  'SLV',    // iShares Silver Trust (白银 ETF)
]

// 定时器引用
let schedulerInterval: ReturnType<typeof setInterval> | null = null

/**
 * 获取配置的股票列表
 */
export function getStockSymbols(): string[] {
  const envSymbols = process.env.STOCK_SYMBOLS
  if (envSymbols) {
    return envSymbols.split(',').map((s) => s.trim().toUpperCase())
  }
  return DEFAULT_STOCK_SYMBOLS
}

/**
 * 获取贵金属/大宗商品列表
 */
export function getCommoditySymbols(): string[] {
  const envSymbols = process.env.COMMODITY_SYMBOLS
  if (envSymbols) {
    return envSymbols.split(',').map((s) => s.trim().toUpperCase())
  }
  return DEFAULT_COMMODITY_SYMBOLS
}

/**
 * 获取所有需要抓取的符号（股票 + 贵金属）
 */
export function getAllSymbols(): string[] {
  return [...getStockSymbols(), ...getCommoditySymbols()]
}

/**
 * 从 Yahoo Finance 抓取股票数据
 */
async function fetchSingleStock(symbol: string): Promise<StockRecord | null> {
  try {
    const quote = await yahooFinance.quote(symbol)

    if (!quote || !quote.regularMarketPrice) {
      console.warn(`[StockFetcher] No data for ${symbol}`)
      return null
    }

    return {
      symbol: quote.symbol || symbol,
      price: quote.regularMarketPrice,
      changePercent: quote.regularMarketChangePercent ?? null,
      changeAmount: quote.regularMarketChange ?? null,
      previousClose: quote.regularMarketPreviousClose ?? null,
      openPrice: quote.regularMarketOpen ?? null,
      dayHigh: quote.regularMarketDayHigh ?? null,
      dayLow: quote.regularMarketDayLow ?? null,
      volume: quote.regularMarketVolume ?? null,
      marketCap: quote.marketCap ?? null,
      fetchedAt: Date.now(),
    }
  } catch (error) {
    console.error(`[StockFetcher] Error fetching ${symbol}:`, error)
    return null
  }
}

/**
 * 抓取所有配置的股票和贵金属
 */
export async function fetchAllStocks(
  symbols: string[] = getAllSymbols()
): Promise<{ total: number; inserted: number; failed: string[] }> {
  console.log(`[StockFetcher] Starting fetch for ${symbols.length} symbols...`)

  const results = await Promise.allSettled(symbols.map((symbol) => fetchSingleStock(symbol)))

  const stockRecords: StockRecord[] = []
  const failed: string[] = []

  results.forEach((result, index) => {
    if (result.status === 'fulfilled' && result.value) {
      stockRecords.push(result.value)
    } else {
      failed.push(symbols[index])
    }
  })

  let inserted = 0
  if (stockRecords.length > 0) {
    inserted = insertStockPrices(stockRecords)
  }

  // 清理过期数据
  const retentionDays = parseInt(process.env.STOCK_RETENTION_DAYS || '7', 10)
  const deleted = cleanupOldStocks(retentionDays)

  console.log(
    `[StockFetcher] Fetch complete: ${stockRecords.length}/${symbols.length} success, ${inserted} new records, ${deleted} expired removed`
  )

  if (failed.length > 0) {
    console.warn(`[StockFetcher] Failed symbols: ${failed.join(', ')}`)
  }

  return { total: stockRecords.length, inserted, failed }
}

/**
 * 启动定时抓取
 */
export function startStockScheduler(intervalMinutes?: number): void {
  if (schedulerInterval) {
    console.log('[StockFetcher] Scheduler already running')
    return
  }

  const interval = intervalMinutes || parseInt(process.env.STOCK_FETCH_INTERVAL || '5', 10)
  const intervalMs = interval * 60 * 1000

  console.log(`[StockFetcher] Starting scheduler with ${interval} minute interval`)

  schedulerInterval = setInterval(async () => {
    try {
      await fetchAllStocks()
    } catch (error) {
      console.error('[StockFetcher] Scheduled fetch error:', error)
    }
  }, intervalMs)
}

/**
 * 停止定时抓取
 */
export function stopStockScheduler(): void {
  if (schedulerInterval) {
    clearInterval(schedulerInterval)
    schedulerInterval = null
    console.log('[StockFetcher] Scheduler stopped')
  }
}

/**
 * 检查调度器是否运行
 */
export function isStockSchedulerRunning(): boolean {
  return schedulerInterval !== null
}
