/**
 * Binance Market Data Service
 * 提供加密货币行情数据
 */

import type { MarketPrice } from '@marketpulse/shared'
import { proxyFetch } from './proxy-fetch'

const BINANCE_API = 'https://api.binance.com/api/v3'

/**
 * 获取单个交易对价格
 */
export async function getPrice(symbol: string): Promise<MarketPrice> {
  const response = await proxyFetch(`${BINANCE_API}/ticker/24hr?symbol=${symbol.toUpperCase()}`)

  if (!response.ok) {
    throw new Error(`Failed to fetch price for ${symbol}: ${response.statusText}`)
  }

  const data = await response.json()

  return {
    symbol: data.symbol,
    price: parseFloat(data.lastPrice),
    change24h: parseFloat(data.priceChangePercent),
    timestamp: Date.now(),
  }
}

/**
 * 获取多个交易对价格
 */
export async function getPrices(symbols: string[]): Promise<MarketPrice[]> {
  const promises = symbols.map((s) => getPrice(s))
  return Promise.all(promises)
}

/**
 * K 线数据类型
 */
export interface Kline {
  openTime: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  closeTime: number
}

/**
 * 获取 K 线数据
 */
export async function getKlines(
  symbol: string,
  interval: string = '1h',
  limit: number = 100
): Promise<Kline[]> {
  const response = await proxyFetch(
    `${BINANCE_API}/klines?symbol=${symbol.toUpperCase()}&interval=${interval}&limit=${limit}`
  )

  if (!response.ok) {
    throw new Error(`Failed to fetch klines for ${symbol}: ${response.statusText}`)
  }

  const data = await response.json() as (string | number)[][]

  return data.map((k) => ({
    openTime: k[0],
    open: parseFloat(k[1]),
    high: parseFloat(k[2]),
    low: parseFloat(k[3]),
    close: parseFloat(k[4]),
    volume: parseFloat(k[5]),
    closeTime: k[6],
  }))
}

/**
 * 获取交易所信息（支持的交易对列表）
 */
export async function getExchangeInfo(): Promise<string[]> {
  const response = await proxyFetch(`${BINANCE_API}/exchangeInfo`)

  if (!response.ok) {
    throw new Error('Failed to fetch exchange info')
  }

  const data = await response.json()
  return data.symbols.map((s: any) => s.symbol)
}

/**
 * 常用交易对
 */
export const POPULAR_SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'BNBUSDT',
  'SOLUSDT',
  'XRPUSDT',
  'DOGEUSDT',
  'ADAUSDT',
  'AVAXUSDT',
]
