import { useState, useEffect, useCallback } from 'react'

export interface SearchHistoryItem {
  id: string
  query: string
  timestamp: number
}

const STORAGE_KEY = 'marketpulse-twitter-search-history'
const MAX_HISTORY_ITEMS = 20

export function useSearchHistory() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([])

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        setHistory(JSON.parse(stored))
      }
    } catch {
      // Ignore parse errors
    }
  }, [])

  // Save to localStorage
  const saveToStorage = useCallback((items: SearchHistoryItem[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
    } catch {
      // Ignore storage errors
    }
  }, [])

  // Add a search query to history
  const addSearch = useCallback((query: string) => {
    setHistory(prev => {
      // Remove duplicate if exists
      const filtered = prev.filter(item => item.query.toLowerCase() !== query.toLowerCase())

      // Add new item at the beginning
      const newItem: SearchHistoryItem = {
        id: `search_${Date.now()}`,
        query,
        timestamp: Date.now(),
      }

      const updated = [newItem, ...filtered].slice(0, MAX_HISTORY_ITEMS)
      saveToStorage(updated)
      return updated
    })
  }, [saveToStorage])

  // Remove a search from history
  const removeSearch = useCallback((id: string) => {
    setHistory(prev => {
      const updated = prev.filter(item => item.id !== id)
      saveToStorage(updated)
      return updated
    })
  }, [saveToStorage])

  // Clear all history
  const clearHistory = useCallback(() => {
    setHistory([])
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return {
    history,
    addSearch,
    removeSearch,
    clearHistory,
  }
}
