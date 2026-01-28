/**
 * Stock Service
 * 美股数据查询服务
 */

import type { StockPrice } from '@marketpulse/shared'
import {
  getLatestStockPrice,
  getLatestStockPrices,
  getAllLatestStockPrices,
  type StockRecord,
} from './stock-store'

/**
 * 将 StockRecord 转换为 StockPrice
 */
function toStockPrice(record: StockRecord): StockPrice {
  return {
    symbol: record.symbol,
    price: record.price,
    changePercent: record.changePercent,
    changeAmount: record.changeAmount,
    previousClose: record.previousClose,
    openPrice: record.openPrice,
    dayHigh: record.dayHigh,
    dayLow: record.dayLow,
    volume: record.volume,
    marketCap: record.marketCap,
    fetchedAt: record.fetchedAt,
  }
}

/**
 * 获取单个股票价格
 */
export function getStockPrice(symbol: string): StockPrice | null {
  const record = getLatestStockPrice(symbol)
  return record ? toStockPrice(record) : null
}

/**
 * 获取多个股票价格
 */
export function getStockPrices(symbols: string[]): StockPrice[] {
  const records = getLatestStockPrices(symbols)
  return records.map(toStockPrice)
}

/**
 * 获取所有股票价格
 */
export function getAllStockPrices(): StockPrice[] {
  const records = getAllLatestStockPrices()
  return records.map(toStockPrice)
}
