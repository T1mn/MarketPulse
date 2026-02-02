/**
 * Tool definitions for AI agents
 */

import { tool } from 'ai'
import { z } from 'zod'
import { getPrices } from './market'
import { searchNews, getNews } from './news'
import { getStockPrices, getAllStockPrices } from './stock'
import { getCommoditySymbols, DEFAULT_COMMODITY_SYMBOLS } from './stock-fetcher'
import { searchTweetsInDB, getTopTweetsFromDB, getTwitterStats } from './twitter-store'
import { registerScrapeTask, executeScrapeTask } from './scrape-task-manager'

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
 * Get commodity price tool (Gold, Silver via Yahoo Finance)
 */
export const getCommodityPriceTool = tool({
  description: '获取贵金属（黄金、白银）的实时价格。数据源：Yahoo Finance。当用户询问黄金、白银、贵金属、Gold、Silver 的价格时调用此工具。可用代码：GC=F（黄金期货）、SI=F（白银期货）、GLD（黄金ETF）、SLV（白银ETF）。',
  parameters: z.object({
    symbols: z.array(z.string()).min(1).max(10).optional()
      .describe('贵金属代码数组，如 ["GC=F", "SI=F"]。不提供则返回所有跟踪的贵金属价格。'),
  }),
  execute: async ({ symbols }) => {
    try {
      // 如果没有指定，返回所有默认贵金属
      const querySymbols = symbols && symbols.length > 0 ? symbols : getCommoditySymbols()
      const results = getStockPrices(querySymbols)

      if (results.length === 0) {
        return {
          error: '未找到贵金属数据，可能数据尚未抓取或代码无效。可用代码：GC=F（黄金期货）、SI=F（白银期货）、GLD（黄金ETF）、SLV（白银ETF）',
          results: [],
        }
      }

      return {
        error: null,
        results: results.map(r => ({
          symbol: r.symbol,
          name: getCommodityName(r.symbol),
          price: r.price,
          changePercent: r.changePercent,
          changeAmount: r.changeAmount,
          previousClose: r.previousClose,
          dayHigh: r.dayHigh,
          dayLow: r.dayLow,
          fetchedAt: r.fetchedAt,
        })),
      }
    } catch (error) {
      return {
        error: `获取贵金属价格失败: ${error instanceof Error ? error.message : '未知错误'}`,
        results: [],
      }
    }
  },
})

/**
 * 获取贵金属的中文名称
 */
function getCommodityName(symbol: string): string {
  const names: Record<string, string> = {
    'GC=F': '黄金期货 (COMEX)',
    'SI=F': '白银期货 (COMEX)',
    'GLD': '黄金ETF (SPDR)',
    'SLV': '白银ETF (iShares)',
  }
  return names[symbol] || symbol
}

/**
 * Backward compatibility: getMarketPrice as alias for getCryptoPrice
 */
export const getMarketPriceTool = getCryptoPriceTool

/**
 * Search Twitter/X tool
 * 搜索推文并按加权分数排序
 */
export const searchTwitterTool = tool({
  description: '搜索 Twitter/X 推文，获取社交媒体上关于加密货币、股票、金融话题的讨论。当用户询问 Twitter 上的讨论、社交媒体情绪、推特上怎么说时调用此工具。结果按互动量（点赞、评论、转发）加权排序。',
  parameters: z.object({
    query: z.string().describe('搜索关键词，如 "Bitcoin"、"BTC"、"crypto"'),
    limit: z.number().min(1).max(20).optional().default(10).describe('返回结果数量，默认10条'),
    sortBy: z.enum(['weighted', 'recent']).optional().default('weighted').describe('排序方式：weighted（互动加权）或 recent（最新）'),
  }),
  execute: async ({ query, limit = 10, sortBy = 'weighted' }) => {
    try {
      let results

      if (sortBy === 'weighted') {
        // 使用全文搜索并按加权分数排序
        results = searchTweetsInDB(query, { limit })
      } else {
        // 按时间排序的搜索
        results = searchTweetsInDB(query, {
          limit,
          sortOptions: { likeWeight: 0, replyWeight: 0, retweetWeight: 0, quoteWeight: 0 },
        })
      }

      if (results.length === 0) {
        // 尝试获取热门推文作为备选
        const topTweets = getTopTweetsFromDB({ limit: 5 })
        if (topTweets.length > 0) {
          return {
            error: null,
            query,
            results: [],
            total: 0,
            message: `未找到关于 "${query}" 的推文。数据库中共有 ${getTwitterStats().total} 条推文，请先导入相关推文数据。`,
          }
        }
        return {
          error: null,
          query,
          results: [],
          total: 0,
          message: '推文数据库为空，请先通过 /api/v1/twitter/import 导入推文数据。',
        }
      }

      return {
        error: null,
        query,
        results: results.map(tweet => ({
          id: tweet.id,
          text: tweet.text,
          username: tweet.username,
          name: tweet.name,
          createdAt: tweet.createdAt,
          likes: tweet.favoriteCount,
          replies: tweet.replyCount,
          retweets: tweet.retweetCount,
          quotes: tweet.quoteCount,
          weightedScore: tweet.weightedScore,
          url: tweet.url,
        })),
        total: results.length,
      }
    } catch (error) {
      return {
        error: `搜索推文失败: ${error instanceof Error ? error.message : '未知错误'}`,
        query,
        results: [],
        total: 0,
      }
    }
  },
})

/**
 * Trigger Twitter scrape tool (requires sessionId for SSE notification)
 */
export function createTriggerTwitterScrapeTool(sessionId: string) {
  return tool({
    description: '触发后台抓取 Twitter 推文。当用户询问推特/Twitter 相关内容，但 searchTwitter 返回结果为空或太少（< 3 条），且用户确认需要抓取时调用此工具。调用后推文将在后台抓取，完成后系统会自动通知用户。',
    parameters: z.object({
      queries: z.array(z.string()).min(1).max(5).describe('要搜索的关键词数组，如 ["Solana", "SOL"]'),
    }),
    execute: async ({ queries }) => {
      const taskId = `scrape_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
      registerScrapeTask(taskId, sessionId, queries)
      executeScrapeTask(taskId).catch(err =>
        console.error(`[triggerTwitterScrape] Task ${taskId} error:`, err)
      )
      return {
        success: true,
        taskId,
        queries,
        message: `已启动后台抓取任务（${queries.join(', ')}），完成后会自动通知用户。`,
      }
    },
  })
}

/**
 * All available tools for AI agents
 */
export const tools = {
  getCryptoPrice: getCryptoPriceTool,
  getStockPrice: getStockPriceTool,
  getCommodityPrice: getCommodityPriceTool,
  searchNews: searchNewsTool,
  searchTwitter: searchTwitterTool,
  // Backward compatibility
  getMarketPrice: getMarketPriceTool,
}

/**
 * Create tools with session context (for session-aware tools like triggerTwitterScrape)
 */
export function createSessionTools(sessionId: string) {
  return {
    ...tools,
    triggerTwitterScrape: createTriggerTwitterScrapeTool(sessionId),
  }
}

export type ToolName = keyof typeof tools | 'triggerTwitterScrape'
