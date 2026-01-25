/**
 * Tool definitions for AI agents
 */

import { tool } from 'ai'
import { z } from 'zod'
import { getPrices } from './market'

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
  description: '搜索金融新闻',
  parameters: z.object({
    query: z.string().describe('搜索关键词'),
    limit: z.number().optional().default(5).describe('返回结果数量'),
  }),
  execute: async ({ query, limit }) => {
    // TODO: Implement actual news search
    return {
      query,
      results: [],
      total: 0,
    }
  },
})

/**
 * Analyze sentiment tool
 */
export const analyzeSentimentTool = tool({
  description: '分析文本的市场情绪',
  parameters: z.object({
    text: z.string().describe('待分析的文本'),
  }),
  execute: async ({ text }) => {
    // TODO: Implement actual sentiment analysis
    return {
      sentiment: 'neutral' as 'positive' | 'negative' | 'neutral',
      confidence: 0.5,
      text,
    }
  },
})

/**
 * All available tools
 */
export const tools = {
  getMarketPrice: getMarketPriceTool,
  searchNews: searchNewsTool,
  analyzeSentiment: analyzeSentimentTool,
}

export type ToolName = keyof typeof tools
