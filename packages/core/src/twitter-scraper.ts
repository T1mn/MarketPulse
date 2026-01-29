/**
 * Twitter Playwright Scraper
 * 使用 Playwright 自动抓取 Twitter/X 推文
 * 支持 headless 模式、Cookie 认证、GraphQL 响应拦截
 */

import { chromium, Browser, BrowserContext, Page, Response } from 'playwright'
import { insertTweets } from './twitter-store'
import type { Tweet } from './twitter'

// ==================== Types ====================

export interface ScraperConfig {
  authToken: string
  searchQueries: string[]
  maxTweetsPerQuery: number
  scrollCount: number
  scrollDelay: { min: number; max: number }
  retryAttempts: number
  retryDelay: number
}

export interface ScrapeResult {
  query: string
  total: number
  inserted: number
  error?: string
}

export interface ScraperStatus {
  isRunning: boolean
  lastRunAt: number | null
  lastResults: ScrapeResult[]
  schedulerActive: boolean
  nextRunAt: number | null
  config: Partial<ScraperConfig>
  startedAt: number | null  // 添加：抓取开始时间
}

// ==================== Configuration ====================

const DEFAULT_CONFIG: ScraperConfig = {
  authToken: process.env.TWITTER_AUTH_TOKEN || 'b82beea61ffa1a9841982663051abcb037b9586a',
  searchQueries: (process.env.TWITTER_SEARCH_QUERIES || 'BTC,ETH,crypto').split(',').map(s => s.trim()),
  maxTweetsPerQuery: parseInt(process.env.TWITTER_MAX_TWEETS_PER_QUERY || '100', 10),
  scrollCount: 5,
  scrollDelay: { min: 1000, max: 2000 },  // 加快滚动速度
  retryAttempts: 3,
  retryDelay: 3000,
}

// ==================== Scraper State ====================

let browser: Browser | null = null
let scraperStatus: ScraperStatus = {
  isRunning: false,
  lastRunAt: null,
  lastResults: [],
  schedulerActive: false,
  nextRunAt: null,
  config: {},
  startedAt: null,
}
let schedulerInterval: ReturnType<typeof setInterval> | null = null

// ==================== Browser Management ====================

/**
 * 启动浏览器（headless 模式 + 反检测配置）
 */
async function launchBrowser(): Promise<Browser> {
  if (browser) return browser

  browser = await chromium.launch({
    headless: true,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
      '--log-level=3',  // 只输出严重错误
      '--silent',
    ],
  })

  console.log('[TwitterScraper] Browser launched (headless mode)')
  return browser
}

/**
 * 创建浏览器上下文（Cookie 认证 + 反检测）
 */
async function createContext(authToken: string): Promise<BrowserContext> {
  const browserInstance = await launchBrowser()

  const context = await browserInstance.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 },
    locale: 'en-US',
    timezoneId: 'America/New_York',
    deviceScaleFactor: 1,
    hasTouch: false,
    javaScriptEnabled: true,
  })

  // 注入 auth_token Cookie
  await context.addCookies([
    {
      name: 'auth_token',
      value: authToken,
      domain: '.x.com',
      path: '/',
      secure: true,
      httpOnly: true,
      sameSite: 'None',
    },
    {
      name: 'auth_token',
      value: authToken,
      domain: '.twitter.com',
      path: '/',
      secure: true,
      httpOnly: true,
      sameSite: 'None',
    },
  ])

  // 反检测脚本
  await context.addInitScript(() => {
    // 隐藏 webdriver
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined,
    })
    // 隐藏 plugins
    Object.defineProperty(navigator, 'plugins', {
      get: () => [1, 2, 3, 4, 5],
    })
    // 隐藏自动化标志
    Object.defineProperty(navigator, 'languages', {
      get: () => ['en-US', 'en'],
    })
    // Chrome 属性
    Object.defineProperty(window, 'chrome', {
      get: () => ({
        runtime: {},
      }),
    })
  })

  console.log('[TwitterScraper] Context created with auth_token')
  return context
}

/**
 * 关闭浏览器
 */
async function closeBrowser(): Promise<void> {
  if (browser) {
    await browser.close()
    browser = null
    console.log('[TwitterScraper] Browser closed')
  }
}

// ==================== Tweet Parsing ====================

/**
 * 从 GraphQL SearchTimeline 响应解析推文
 */
function parseSearchTimelineResponse(json: Record<string, unknown>): Tweet[] {
  const tweets: Tweet[] = []

  try {
    // Twitter GraphQL 响应结构: data.search_by_raw_query.search_timeline.timeline.instructions
    const instructions = (json as any)?.data?.search_by_raw_query?.search_timeline?.timeline?.instructions || []

    for (const instruction of instructions) {
      const entries = instruction?.entries || []

      for (const entry of entries) {
        // 跳过非推文条目（如广告、推荐用户等）
        if (!entry?.entryId?.startsWith('tweet-')) continue

        const result = entry?.content?.itemContent?.tweet_results?.result
        if (!result) continue

        const tweet = parseTweetResult(result)
        if (tweet) {
          tweets.push(tweet)
        }
      }
    }
  } catch (error) {
    console.warn('[TwitterScraper] Failed to parse SearchTimeline response:', error)
  }

  return tweets
}

/**
 * 解析单条推文结果
 */
function parseTweetResult(result: Record<string, unknown>): Tweet | null {
  try {
    // 处理 TweetWithVisibilityResults 包装
    const tweetData = (result as any).__typename === 'TweetWithVisibilityResults'
      ? (result as any).tweet
      : result

    if (!tweetData?.rest_id) return null

    const legacy = tweetData.legacy || {}
    const userLegacy = tweetData.core?.user_results?.result?.legacy || {}

    const tweet: Tweet = {
      id: tweetData.rest_id,
      text: legacy.full_text || '',
      username: userLegacy.screen_name || 'unknown',
      name: userLegacy.name || '',
      createdAt: legacy.created_at || new Date().toISOString(),
      favoriteCount: legacy.favorite_count || 0,
      replyCount: legacy.reply_count || 0,
      retweetCount: legacy.retweet_count || 0,
      quoteCount: legacy.quote_count || 0,
      lang: legacy.lang,
    }

    // 生成 URL
    if (tweet.username && tweet.id) {
      tweet.url = `https://x.com/${tweet.username}/status/${tweet.id}`
    }

    return tweet
  } catch (error) {
    console.warn('[TwitterScraper] Failed to parse tweet result:', error)
    return null
  }
}

// ==================== Scraping Logic ====================

/**
 * 人类模拟滚动
 */
async function humanScroll(page: Page, config: ScraperConfig): Promise<void> {
  const delay = config.scrollDelay.min + Math.random() * (config.scrollDelay.max - config.scrollDelay.min)

  await page.evaluate(() => {
    window.scrollBy({
      top: 600 + Math.random() * 400, // 随机滚动距离
      behavior: 'smooth',
    })
  })

  await page.waitForTimeout(delay)
}

/**
 * 抓取单个搜索关键词
 */
async function scrapeQuery(
  context: BrowserContext,
  query: string,
  config: ScraperConfig
): Promise<ScrapeResult> {
  const collectedTweets: Tweet[] = []
  const seenIds = new Set<string>()

  const page = await context.newPage()

  try {
    // 监听 GraphQL 响应
    page.on('response', async (response: Response) => {
      const url = response.url()

      // 拦截 SearchTimeline GraphQL 请求（只处理成功的响应）
      if (response.status() === 200 &&
          url.includes('/graphql/') &&
          url.includes('SearchTimeline')) {
        try {
          const json = await response.json()
          const tweets = parseSearchTimelineResponse(json as Record<string, unknown>)

          for (const tweet of tweets) {
            if (!seenIds.has(tweet.id)) {
              seenIds.add(tweet.id)
              collectedTweets.push(tweet)
            }
          }

          console.log(`[TwitterScraper] Collected ${collectedTweets.length} tweets for "${query}"`)
        } catch {
          // 忽略 JSON 解析错误
        }
      }
    })

    // 静默处理页面错误和控制台消息
    page.on('pageerror', () => {})
    page.on('console', () => {})
    page.on('requestfailed', () => {})  // 忽略请求失败

    // 构建搜索 URL（默认 Top 热门排序）
    const searchUrl = `https://x.com/search?q=${encodeURIComponent(query)}&src=typed_query`
    console.log(`[TwitterScraper] Navigating to: ${searchUrl}`)

    // 使用 domcontentloaded 而不是 networkidle（Twitter SPA 永远不会 idle）
    await page.goto(searchUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,  // 缩短超时时间
    })

    // 等待推文列表出现（最多等 5 秒）
    try {
      await page.waitForSelector('[data-testid="tweet"]', { timeout: 5000 })
    } catch {
      console.log(`[TwitterScraper] Tweet elements not found, but continuing...`)
    }

    // 额外等待让 GraphQL 响应完成
    await page.waitForTimeout(1500)

    // 滚动加载更多推文
    for (let i = 0; i < config.scrollCount && collectedTweets.length < config.maxTweetsPerQuery; i++) {
      await humanScroll(page, config)

      // 检查是否达到限制
      if (collectedTweets.length >= config.maxTweetsPerQuery) {
        console.log(`[TwitterScraper] Reached max tweets (${config.maxTweetsPerQuery}) for "${query}"`)
        break
      }
    }

    // 截取最大数量
    const tweetsToInsert = collectedTweets.slice(0, config.maxTweetsPerQuery)

    // 插入数据库
    const inserted = insertTweets(tweetsToInsert, query)

    console.log(`[TwitterScraper] Query "${query}": ${tweetsToInsert.length} collected, ${inserted} inserted`)

    return {
      query,
      total: tweetsToInsert.length,
      inserted,
    }
  } catch (error) {
    console.error(`[TwitterScraper] Error scraping "${query}":`, error)
    return {
      query,
      total: 0,
      inserted: 0,
      error: String(error),
    }
  } finally {
    await page.close()
  }
}

/**
 * 执行完整抓取（带重试）
 */
async function executeScrape(config: ScraperConfig = DEFAULT_CONFIG): Promise<ScrapeResult[]> {
  const results: ScrapeResult[] = []
  let context: BrowserContext | null = null

  try {
    scraperStatus.isRunning = true
    scraperStatus.startedAt = Date.now()
    context = await createContext(config.authToken)

    for (const query of config.searchQueries) {
      let lastError: string | undefined
      let result: ScrapeResult | null = null

      // 重试逻辑
      for (let attempt = 1; attempt <= config.retryAttempts; attempt++) {
        try {
          result = await scrapeQuery(context, query, config)

          if (!result.error) {
            break // 成功，跳出重试循环
          }

          lastError = result.error
          console.warn(`[TwitterScraper] Attempt ${attempt}/${config.retryAttempts} failed for "${query}": ${lastError}`)

          if (attempt < config.retryAttempts) {
            // 指数退避
            const backoff = config.retryDelay * Math.pow(2, attempt - 1)
            console.log(`[TwitterScraper] Waiting ${backoff}ms before retry...`)
            await new Promise(resolve => setTimeout(resolve, backoff))
          }
        } catch (error) {
          lastError = String(error)
          console.error(`[TwitterScraper] Attempt ${attempt}/${config.retryAttempts} threw error for "${query}":`, error)
        }
      }

      if (result) {
        results.push(result)
      } else {
        results.push({
          query,
          total: 0,
          inserted: 0,
          error: lastError || 'Unknown error',
        })
      }

      // 每个 query 之间等待，避免被限流
      if (config.searchQueries.indexOf(query) < config.searchQueries.length - 1) {
        const queryDelay = 2000 + Math.random() * 2000 // 2-4秒
        console.log(`[TwitterScraper] Waiting ${Math.round(queryDelay / 1000)}s before next query...`)
        await new Promise(resolve => setTimeout(resolve, queryDelay))
      }
    }

    scraperStatus.lastRunAt = Date.now()
    scraperStatus.lastResults = results

    return results
  } finally {
    scraperStatus.isRunning = false
    scraperStatus.startedAt = null

    if (context) {
      await context.close()
    }
  }
}

// ==================== Scheduler ====================

/**
 * 启动定时抓取调度器
 */
export function startTwitterScrapeScheduler(intervalMinutes?: number): void {
  if (schedulerInterval) {
    console.log('[TwitterScraper] Scheduler already running')
    return
  }

  const interval = (intervalMinutes ?? parseInt(process.env.TWITTER_SCRAPE_INTERVAL || '30', 10)) * 60 * 1000

  console.log(`[TwitterScraper] Starting scheduler with ${interval / 60000} minute interval`)

  // 是否启动时立即抓取
  if (process.env.TWITTER_SCRAPE_ON_STARTUP === 'true') {
    console.log('[TwitterScraper] Running initial scrape on startup...')
    scrapeTwitter().catch(err => console.error('[TwitterScraper] Initial scrape failed:', err))
  }

  schedulerInterval = setInterval(async () => {
    // 超时保护：如果运行超过 10 分钟，强制重置状态
    const SCRAPE_TIMEOUT = 10 * 60 * 1000 // 10 分钟
    if (scraperStatus.isRunning && scraperStatus.startedAt) {
      const runningTime = Date.now() - scraperStatus.startedAt
      if (runningTime > SCRAPE_TIMEOUT) {
        console.warn(`[TwitterScraper] Scraper stuck for ${Math.round(runningTime / 1000)}s, force resetting...`)
        await forceResetScraper()
      }
    }

    if (scraperStatus.isRunning) {
      console.log('[TwitterScraper] Skipping scheduled run, scraper is already running')
      return
    }

    console.log('[TwitterScraper] Starting scheduled scrape...')
    try {
      await scrapeTwitter()
    } catch (error) {
      console.error('[TwitterScraper] Scheduled scrape failed:', error)
    }
  }, interval)

  scraperStatus.schedulerActive = true
  scraperStatus.nextRunAt = Date.now() + interval
  scraperStatus.config = {
    searchQueries: DEFAULT_CONFIG.searchQueries,
    maxTweetsPerQuery: DEFAULT_CONFIG.maxTweetsPerQuery,
  }

  console.log('[TwitterScraper] Scheduler started')
}

/**
 * 停止定时抓取调度器
 */
export function stopTwitterScrapeScheduler(): void {
  if (schedulerInterval) {
    clearInterval(schedulerInterval)
    schedulerInterval = null
    scraperStatus.schedulerActive = false
    scraperStatus.nextRunAt = null
    console.log('[TwitterScraper] Scheduler stopped')
  }
}

/**
 * 强制重置抓取器状态（用于卡死恢复）
 */
export async function forceResetScraper(): Promise<void> {
  console.log('[TwitterScraper] Force resetting scraper state...')

  // 重置状态
  scraperStatus.isRunning = false
  scraperStatus.startedAt = null

  // 强制关闭浏览器
  try {
    await closeBrowser()
  } catch (error) {
    console.error('[TwitterScraper] Error closing browser during reset:', error)
  }

  console.log('[TwitterScraper] Scraper state reset complete')
}

// ==================== Public API ====================

/**
 * 手动触发抓取
 */
export async function scrapeTwitter(queries?: string[]): Promise<ScrapeResult[]> {
  if (scraperStatus.isRunning) {
    console.warn('[TwitterScraper] Scraper is already running')
    return [{
      query: 'all',
      total: 0,
      inserted: 0,
      error: 'Scraper is already running',
    }]
  }

  const config: ScraperConfig = {
    ...DEFAULT_CONFIG,
    searchQueries: queries || DEFAULT_CONFIG.searchQueries,
  }

  console.log(`[TwitterScraper] Starting manual scrape for queries: ${config.searchQueries.join(', ')}`)

  try {
    const results = await executeScrape(config)
    return results
  } catch (error) {
    console.error('[TwitterScraper] Manual scrape failed:', error)
    return [{
      query: 'all',
      total: 0,
      inserted: 0,
      error: String(error),
    }]
  } finally {
    // 清理浏览器资源
    await closeBrowser()
  }
}

/**
 * 获取抓取器状态
 */
export function getTwitterScraperStatus(): ScraperStatus {
  // 更新 nextRunAt
  if (schedulerInterval && scraperStatus.lastRunAt) {
    const interval = parseInt(process.env.TWITTER_SCRAPE_INTERVAL || '30', 10) * 60 * 1000
    scraperStatus.nextRunAt = scraperStatus.lastRunAt + interval
  }

  return { ...scraperStatus }
}

/**
 * 初始化 Twitter 抓取器（服务器启动时调用）
 */
export function initTwitterScraper(): void {
  const authToken = process.env.TWITTER_AUTH_TOKEN

  if (!authToken) {
    console.warn('[TwitterScraper] TWITTER_AUTH_TOKEN not set, scraper disabled')
    return
  }

  console.log('[TwitterScraper] Initialized')

  // 自动启动调度器（如果配置了）
  if (process.env.TWITTER_SCRAPE_INTERVAL) {
    startTwitterScrapeScheduler()
  }
}

/**
 * 清理资源（服务器关闭时调用）
 */
export async function cleanupTwitterScraper(): Promise<void> {
  stopTwitterScrapeScheduler()
  await closeBrowser()
  console.log('[TwitterScraper] Cleanup complete')
}
