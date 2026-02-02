/**
 * Utility functions
 */

/**
 * Generate a unique ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
}

/**
 * Sleep for a given number of milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Format timestamp to ISO string
 */
export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toISOString()
}

/**
 * Parse environment variable with fallback
 */
export function getEnv(key: string, fallback?: string): string | undefined {
  return process.env[key] ?? fallback
}

/**
 * Check if running in development mode
 */
export function isDev(): boolean {
  return process.env.NODE_ENV === 'development'
}

/**
 * Check if running in production mode
 */
export function isProd(): boolean {
  return process.env.NODE_ENV === 'production'
}

/**
 * Safely parse JSON with error handling
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json) as T
  } catch {
    return fallback
  }
}
