/**
 * Scrape Task Manager
 * 管理 Twitter 按需抓取任务，提供 SSE 通知机制
 */

import { scrapeTwitter } from './twitter-scraper'
import type { ScrapeResult } from './twitter-scraper'

// ==================== Types ====================

export interface ScrapeTask {
  id: string
  sessionId: string
  queries: string[]
  status: 'pending' | 'running' | 'completed' | 'failed'
  startedAt: number
  completedAt?: number
  results?: ScrapeResult[]
  error?: string
}

export type SSEWriter = (event: string, data: unknown) => void

// ==================== State ====================

const tasks = new Map<string, ScrapeTask>()
const sseSubscribers = new Map<string, Set<SSEWriter>>()

// ==================== SSE Subscription ====================

/**
 * 订阅 SSE 事件
 */
export function subscribeSSE(sessionId: string, writer: SSEWriter): void {
  if (!sseSubscribers.has(sessionId)) {
    sseSubscribers.set(sessionId, new Set())
  }
  sseSubscribers.get(sessionId)!.add(writer)
}

/**
 * 取消 SSE 订阅
 */
export function unsubscribeSSE(sessionId: string, writer: SSEWriter): void {
  const subscribers = sseSubscribers.get(sessionId)
  if (subscribers) {
    subscribers.delete(writer)
    if (subscribers.size === 0) {
      sseSubscribers.delete(sessionId)
    }
  }
}

/**
 * 向指定 session 的所有订阅者推送事件
 */
function notifySubscribers(sessionId: string, event: string, data: unknown): void {
  const subscribers = sseSubscribers.get(sessionId)
  if (!subscribers) return

  for (const writer of subscribers) {
    try {
      writer(event, data)
    } catch (error) {
      console.warn('[ScrapeTaskManager] Failed to notify subscriber:', error)
    }
  }
}

// ==================== Task Management ====================

/**
 * 注册新的抓取任务
 */
export function registerScrapeTask(taskId: string, sessionId: string, queries: string[]): ScrapeTask {
  const task: ScrapeTask = {
    id: taskId,
    sessionId,
    queries,
    status: 'pending',
    startedAt: Date.now(),
  }
  tasks.set(taskId, task)
  return task
}

/**
 * 执行抓取任务（异步，完成后通过 SSE 通知）
 */
export async function executeScrapeTask(taskId: string): Promise<void> {
  const task = tasks.get(taskId)
  if (!task) {
    console.error(`[ScrapeTaskManager] Task not found: ${taskId}`)
    return
  }

  task.status = 'running'

  try {
    const results = await scrapeTwitter(task.queries)
    task.status = 'completed'
    task.completedAt = Date.now()
    task.results = results

    const totalCollected = results.reduce((sum, r) => sum + r.total, 0)
    const totalInserted = results.reduce((sum, r) => sum + r.inserted, 0)

    notifySubscribers(task.sessionId, 'scrape-complete', {
      taskId: task.id,
      queries: task.queries,
      totalCollected,
      totalInserted,
      duration: task.completedAt - task.startedAt,
      results,
    })

    console.log(`[ScrapeTaskManager] Task ${taskId} completed: ${totalCollected} collected, ${totalInserted} inserted`)
  } catch (error) {
    task.status = 'failed'
    task.completedAt = Date.now()
    task.error = String(error)

    notifySubscribers(task.sessionId, 'scrape-error', {
      taskId: task.id,
      queries: task.queries,
      error: task.error,
    })

    console.error(`[ScrapeTaskManager] Task ${taskId} failed:`, error)
  }
}

/**
 * 获取任务状态
 */
export function getScrapeTask(taskId: string): ScrapeTask | undefined {
  return tasks.get(taskId)
}
