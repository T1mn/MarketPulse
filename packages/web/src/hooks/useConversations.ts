import { useState, useEffect, useCallback, useRef } from 'react'
import { storage } from '@/lib/storage'
import type { Conversation, Message } from '@/types'

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Flag to skip loading messages after creating a new conversation
  const skipNextLoadRef = useRef(false)

  // Load conversations on mount
  useEffect(() => {
    const loadConversations = async () => {
      const data = await storage.getConversations()
      setConversations(data)
      setIsLoading(false)
    }
    loadConversations()
  }, [])

  // Load messages when conversation changes (but skip for newly created conversations)
  useEffect(() => {
    const loadMessages = async () => {
      // Skip loading for newly created conversations - caller manages messages
      if (skipNextLoadRef.current) {
        skipNextLoadRef.current = false
        return
      }

      if (currentConversationId) {
        const data = await storage.getMessages(currentConversationId)
        setMessages(data)
      } else {
        setMessages([])
      }
    }
    loadMessages()
  }, [currentConversationId])

  const createConversation = useCallback(async (firstMessage: string) => {
    // Generate title from first message (truncate to 30 chars)
    const title = firstMessage.length > 30
      ? firstMessage.slice(0, 30) + '...'
      : firstMessage

    const conversation = await storage.createConversation(title)
    setConversations(prev => [conversation, ...prev])

    // Mark to skip next message load - caller will manage messages for new conversation
    skipNextLoadRef.current = true
    setCurrentConversationId(conversation.id)

    return conversation
  }, [])

  const deleteConversation = useCallback(async (id: string) => {
    await storage.deleteConversation(id)
    setConversations(prev => prev.filter(c => c.id !== id))

    // If deleting current conversation, clear it
    if (currentConversationId === id) {
      setCurrentConversationId(null)
      setMessages([])
    }
  }, [currentConversationId])

  const selectConversation = useCallback((id: string | null) => {
    setCurrentConversationId(id)
  }, [])

  const addMessage = useCallback(async (message: Message, conversationId?: string) => {
    const targetId = conversationId || currentConversationId
    if (!targetId) return

    await storage.addMessage(targetId, message)
    // Note: Don't call setMessages here - caller handles UI state
  }, [currentConversationId])

  const updateMessage = useCallback(async (messageId: string, updates: Partial<Message>) => {
    if (!currentConversationId) return

    await storage.updateMessage(currentConversationId, messageId, updates)
    setMessages(prev =>
      prev.map(m => (m.id === messageId ? { ...m, ...updates } : m))
    )
  }, [currentConversationId])

  const updateConversation = useCallback(async (id: string, updates: Partial<Conversation>) => {
    await storage.updateConversation(id, updates)
    setConversations(prev =>
      prev.map(c => (c.id === id ? { ...c, ...updates, updatedAt: Date.now() } : c))
    )
  }, [])

  const startNewChat = useCallback(() => {
    setCurrentConversationId(null)
    setMessages([])
  }, [])

  // Group conversations by date
  const groupedConversations = useCallback(() => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
    const yesterday = today - 24 * 60 * 60 * 1000

    const groups: { label: string; conversations: Conversation[] }[] = [
      { label: '今天', conversations: [] },
      { label: '昨天', conversations: [] },
      { label: '更早', conversations: [] },
    ]

    for (const conv of conversations) {
      if (conv.updatedAt >= today) {
        groups[0].conversations.push(conv)
      } else if (conv.updatedAt >= yesterday) {
        groups[1].conversations.push(conv)
      } else {
        groups[2].conversations.push(conv)
      }
    }

    // Filter out empty groups
    return groups.filter(g => g.conversations.length > 0)
  }, [conversations])

  return {
    conversations,
    currentConversationId,
    messages,
    isLoading,
    groupedConversations,
    createConversation,
    updateConversation,
    deleteConversation,
    selectConversation,
    addMessage,
    updateMessage,
    startNewChat,
    setMessages,
  }
}
