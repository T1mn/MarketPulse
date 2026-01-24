/**
 * Storage Abstraction Layer
 *
 * TODO: 切换后端存储时的修改指南
 * 1. 实现 ApiStorageAdapter 类（参考下方接口）
 * 2. 修改文件底部的 export，将 LocalStorageAdapter 替换为 ApiStorageAdapter
 * 3. 需要实现的后端接口:
 *    - GET    /api/conversations         - 获取对话列表
 *    - POST   /api/conversations         - 创建新对话
 *    - PATCH  /api/conversations/:id     - 更新对话
 *    - DELETE /api/conversations/:id     - 删除对话
 *    - GET    /api/conversations/:id/messages - 获取消息列表
 *    - POST   /api/conversations/:id/messages - 添加消息
 *    - PATCH  /api/conversations/:id/messages/:msgId - 更新消息
 */

import type { Conversation, Message, StorageAdapter } from '@/types'

const CONVERSATIONS_KEY = 'marketpulse-conversations'
const MESSAGES_KEY_PREFIX = 'marketpulse-messages-'

/**
 * LocalStorage implementation of StorageAdapter
 * Used for client-side storage before backend integration
 */
class LocalStorageAdapter implements StorageAdapter {
  async getConversations(): Promise<Conversation[]> {
    const data = localStorage.getItem(CONVERSATIONS_KEY)
    if (!data) return []
    try {
      return JSON.parse(data) as Conversation[]
    } catch {
      return []
    }
  }

  async createConversation(title: string): Promise<Conversation> {
    const conversations = await this.getConversations()
    const newConversation: Conversation = {
      id: crypto.randomUUID(),
      title,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    conversations.unshift(newConversation)
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations))
    return newConversation
  }

  async updateConversation(id: string, updates: Partial<Conversation>): Promise<void> {
    const conversations = await this.getConversations()
    const index = conversations.findIndex(c => c.id === id)
    if (index !== -1) {
      conversations[index] = {
        ...conversations[index],
        ...updates,
        updatedAt: Date.now(),
      }
      localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations))
    }
  }

  async deleteConversation(id: string): Promise<void> {
    const conversations = await this.getConversations()
    const filtered = conversations.filter(c => c.id !== id)
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(filtered))
    // Also delete associated messages
    localStorage.removeItem(`${MESSAGES_KEY_PREFIX}${id}`)
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    const data = localStorage.getItem(`${MESSAGES_KEY_PREFIX}${conversationId}`)
    if (!data) return []
    try {
      return JSON.parse(data) as Message[]
    } catch {
      return []
    }
  }

  async addMessage(conversationId: string, message: Message): Promise<void> {
    const messages = await this.getMessages(conversationId)
    messages.push(message)
    localStorage.setItem(`${MESSAGES_KEY_PREFIX}${conversationId}`, JSON.stringify(messages))

    // Update conversation's updatedAt
    await this.updateConversation(conversationId, {})
  }

  async updateMessage(
    conversationId: string,
    messageId: string,
    updates: Partial<Message>
  ): Promise<void> {
    const messages = await this.getMessages(conversationId)
    const index = messages.findIndex(m => m.id === messageId)
    if (index !== -1) {
      messages[index] = { ...messages[index], ...updates }
      localStorage.setItem(`${MESSAGES_KEY_PREFIX}${conversationId}`, JSON.stringify(messages))
    }
  }
}

/**
 * TODO: ApiStorageAdapter implementation
 *
 * class ApiStorageAdapter implements StorageAdapter {
 *   private baseUrl = '/api'
 *
 *   async getConversations(): Promise<Conversation[]> {
 *     const res = await fetch(`${this.baseUrl}/conversations`)
 *     return res.json()
 *   }
 *
 *   // ... implement other methods
 * }
 */

// TODO: 切换后端时，将下面的 LocalStorageAdapter 替换为 ApiStorageAdapter
export const storage: StorageAdapter = new LocalStorageAdapter()
