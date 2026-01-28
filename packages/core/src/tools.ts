/**
 * Tool definitions for AI agents
 */

import { tool } from 'ai'
import { z } from 'zod'
import { getPrices } from './market'
import { searchNews, getNews } from './news'
import { getStockPrices, getAllStockPrices } from './stock'

/**
 * Get crypto price tool (Binance)
 */
export const getCryptoPriceTool = tool({
  description: '获取加密货币的实时价格（如 BTC、ETH）。数据源：Binance。当用户询问比特币、以太坊等加密货币的价格时调用此工具。',
  parameters: z.object({
    symbols: z.array(z.string()).min(1).max(10).describe('交易对符号数组，如 ["BTCUSDT", "ETHUSDT"]'),
  }),
  execute: async ({ symbols }) => {
    if (symbols.length > 10) {
      return {
        error: '一次最多查询 10 个交易对，请分批查询',
        results: [],
      }
    }

    try {
      const results = await getPrices(symbols)
      return {
        error: null,
        results: results.map(r => ({
          symbol: r.symbol,
          price: r.price,
          change24h: r.change24h,
          timestamp: r.timestamp,
        })),
      }
    } catch (error) {
      return {
        error: `获取价格失败: ${error instanceof Error ? error.message : '未知错误'}`,
        results: [],
      }
    }
  },
})

/**
 * Get stock price tool (Yahoo Finance)
 */
export const getStockPriceTool = tool({
  description: '获取美股股票的实时价格（如 AAPL、MSFT、GOOGL）。数据源：Yahoo Finance。当用户询问苹果、微软、谷歌等美股公司的股票价格时调用此工具。',
  parameters: z.object({
    symbols: z.array(z.string()).min(1).max(10).describe('股票代码数组，如 ["AAPL", "MSFT", "GOOGL"]'),
  }),
  execute: async ({ symbols }) => {
    if (symbols.length > 10) {
      return {
        error: '一次最多查询 10 个股票，请分批查询',
        results: [],
      }
    }

    try {
      // 如果没有指定股票，返回所有跟踪的股票
      const results = symbols.length > 0 ? getStockPrices(symbols) : getAllStockPrices()

      if (results.length === 0) {
        return {
          error: '未找到股票数据，可能数据尚未抓取或股票代码无效',
          results: [],
        }
      }

      return {
        error: null,
        results: results.map(r => ({
          symbol: r.symbol,
          price: r.price,
          changePercent: r.changePercent,
          changeAmount: r.changeAmount,
          previousClose: r.previousClose,
          dayHigh: r.dayHigh,
          dayLow: r.dayLow,
          volume: r.volume,
          marketCap: r.marketCap,
          fetchedAt: r.fetchedAt,
        })),
      }
    } catch (error) {
      return {
        error: `获取股票价格失败: ${error instanceof Error ? error.message : '未知错误'}`,
        results: [],
      }
    }
  },
})

/**
 * Search news tool
 */
export const searchNewsTool = tool({
  description: '搜索和获取最新金融新闻、加密货币资讯、市场动态。当用户询问新闻、资讯、最新消息、市场动态、发生了什么时调用此工具。',
  parameters: z.object({
    query: z.string().optional().describe('搜索关键词，如 "比特币"、"以太坊"、"crypto"（可选，不提供则返回最新新闻）'),
    limit: z.number().min(1).max(20).optional().default(5).describe('返回结果数量，默认5条'),
  }),
  execute: async ({ query, limit = 5 }) => {
    try {
      let results
      if (query && query.trim()) {
        results = await searchNews(query, { limit })
      } else {
        results = await getNews({ limit })
      }

      return {
        error: null,
        query: query || null,
        results: results.slice(0, limit).map(item => ({
          title: item.title,
          summary: item.summary,
          source: item.source,
          url: item.url,
          publishedAt: item.publishedAt,
          category: item.category,
        })),
        total: results.length,
      }
    } catch (error) {
      return {
        error: `获取新闻失败: ${error instanceof Error ? error.message : '未知错误'}`,
        query: query || null,
        results: [],
        total: 0,
      }
    }
  },
})

/**
 * Backward compatibility: getMarketPrice as alias for getCryptoPrice
 */
export const getMarketPriceTool = getCryptoPriceTool

/**
 * All available tools for AI agents
 */
export const tools = {
  getCryptoPrice: getCryptoPriceTool,
  getStockPrice: getStockPriceTool,
  searchNews: searchNewsTool,
  // Backward compatibility
  getMarketPrice: getMarketPriceTool,
}

export type ToolName = keyof typeof tools
