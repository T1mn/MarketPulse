/**
 * Tool definitions for AI agents
 */

import { tool } from 'ai'
import { z } from 'zod'
import { getPrices } from './market'
import { searchNews, getNews } from './news'

/**
 * Get current market price tool
 */
export const getMarketPriceTool = tool({
  description: '获取指定加密货币的当前市场价格。支持单个或多个交易对（最多10个）。',
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
 * All available tools for AI agents
 */
export const tools = {
  getMarketPrice: getMarketPriceTool,
  searchNews: searchNewsTool,
}

export type ToolName = keyof typeof tools
