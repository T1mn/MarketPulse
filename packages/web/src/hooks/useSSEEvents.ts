import { useEffect, useRef, useCallback } from 'react'

export interface ScrapeCompleteEvent {
  taskId: string
  queries: string[]
  totalCollected: number
  totalInserted: number
  duration: number
}

export interface ScrapeErrorEvent {
  taskId: string
  queries: string[]
  error: string
}

interface UseSSEEventsOptions {
  sessionId: string | undefined
  onScrapeComplete?: (data: ScrapeCompleteEvent) => void
  onScrapeError?: (data: ScrapeErrorEvent) => void
}

export function useSSEEvents({ sessionId, onScrapeComplete, onScrapeError }: UseSSEEventsOptions) {
  const eventSourceRef = useRef<EventSource | null>(null)
  const callbacksRef = useRef({ onScrapeComplete, onScrapeError })

  // Keep callbacks ref in sync
  callbacksRef.current = { onScrapeComplete, onScrapeError }

  const connect = useCallback(() => {
    if (!sessionId) return

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const eventSource = new EventSource(`${baseUrl}/api/v1/events/${sessionId}`)
    eventSourceRef.current = eventSource

    eventSource.addEventListener('scrape-complete', (e) => {
      try {
        const data = JSON.parse(e.data) as ScrapeCompleteEvent
        callbacksRef.current.onScrapeComplete?.(data)
      } catch {
        // Ignore parse errors
      }
    })

    eventSource.addEventListener('scrape-error', (e) => {
      try {
        const data = JSON.parse(e.data) as ScrapeErrorEvent
        callbacksRef.current.onScrapeError?.(data)
      } catch {
        // Ignore parse errors
      }
    })

    eventSource.onerror = () => {
      // EventSource will auto-reconnect
    }
  }, [sessionId])

  useEffect(() => {
    connect()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [connect])
}
