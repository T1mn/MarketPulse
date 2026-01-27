// Types for MarketPulse chat application

export interface Conversation {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  backendSessionId?: string // 后端 session ID，用于保持对话上下文
}

export interface ToolCall {
  toolName: string
  args: unknown
  result?: unknown
  status: 'calling' | 'done'
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  feedback?: 'up' | 'down'
  attachments?: Attachment[]
  isTyping?: boolean
  toolCalls?: ToolCall[]
  // Thinking block fields (for models that use <think> tags)
  thinkingContent?: string
  isThinking?: boolean
  thinkingDuration?: number
}

export interface Attachment {
  id: string
  type: 'image' | 'document'
  name: string
  url: string // base64 or URL
}

// Storage adapter interface for future backend migration
// TODO: When switching to backend storage, implement ApiStorageAdapter
export interface StorageAdapter {
  // Conversation management
  getConversations(): Promise<Conversation[]>
  createConversation(title: string): Promise<Conversation>
  updateConversation(id: string, updates: Partial<Conversation>): Promise<void>
  deleteConversation(id: string): Promise<void>

  // Message management
  getMessages(conversationId: string): Promise<Message[]>
  addMessage(conversationId: string, message: Message): Promise<void>
  updateMessage(conversationId: string, messageId: string, updates: Partial<Message>): Promise<void>
}
