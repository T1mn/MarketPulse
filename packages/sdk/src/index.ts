/**
 * @marketpulse/sdk
 * TypeScript SDK for MarketPulse API
 */

import type { ChatMessage, Session, MarketPrice, ApiResponse } from '@marketpulse/shared'

export interface MarketPulseClientOptions {
  baseUrl?: string
}

/**
 * MarketPulse API Client
 */
export class MarketPulseClient {
  private baseUrl: string

  constructor(options: MarketPulseClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? 'http://localhost:3000'
  }

  /**
   * Create a new chat session
   */
  async createSession(): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/api/v1/session`, {
      method: 'POST',
    })
    const result: ApiResponse<Session> = await response.json()
    if (!result.success || !result.data) {
      throw new Error(result.error ?? 'Failed to create session')
    }
    return result.data
  }

  /**
   * Get session by ID
   */
  async getSession(sessionId: string): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/api/v1/session/${sessionId}`)
    const result: ApiResponse<Session> = await response.json()
    if (!result.success || !result.data) {
      throw new Error(result.error ?? 'Session not found')
    }
    return result.data
  }

  /**
   * Send a chat message and get streaming response
   */
  async *chat(
    message: string,
    sessionId?: string
  ): AsyncGenerator<string, Session, unknown> {
    const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message, sessionId }),
    })

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let finalSessionId = sessionId

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.text) {
            yield data.text
          }
          if (data.sessionId) {
            finalSessionId = data.sessionId
          }
        }
      }
    }

    // Return final session
    return this.getSession(finalSessionId!)
  }

  /**
   * Get market price
   */
  async getMarketPrice(symbol: string): Promise<MarketPrice> {
    const response = await fetch(`${this.baseUrl}/api/v1/market/price/${symbol}`)
    const result: ApiResponse<MarketPrice> = await response.json()
    if (!result.success || !result.data) {
      throw new Error(result.error ?? 'Failed to get market price')
    }
    return result.data
  }

  /**
   * Health check
   */
  async health(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${this.baseUrl}/health`)
    return response.json()
  }
}

// Re-export types
export type { ChatMessage, Session, MarketPrice, ApiResponse }

// Default export
export default MarketPulseClient
