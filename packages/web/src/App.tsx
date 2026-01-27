import { useState, useRef, useEffect, useCallback } from 'react'
import { TrendingUp, Menu } from 'lucide-react'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Sidebar } from '@/components/Sidebar'
import { ChatMessage } from '@/components/ChatMessage'
import { ChatInput } from '@/components/ChatInput'
import { useConversations } from '@/hooks/useConversations'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'
import type { Message, ToolCall } from '@/types'
import '@/index.css'

// 新后端 API 地址
const API_URL = 'http://localhost:3000/api/v1/chat'

// Parse <think> tags from streaming text
interface ParsedContent {
  thinkingContent: string
  mainContent: string
  isThinking: boolean
}

function parseThinkTags(text: string): ParsedContent {
  const thinkOpenTag = '<think>'
  const thinkCloseTag = '</think>'

  let thinkingContent = ''
  let mainContent = ''
  let isThinking = false

  let remaining = text

  while (remaining.length > 0) {
    const openIndex = remaining.indexOf(thinkOpenTag)
    const closeIndex = remaining.indexOf(thinkCloseTag)

    if (openIndex === -1 && closeIndex === -1) {
      // No more tags
      if (isThinking) {
        thinkingContent += remaining
      } else {
        mainContent += remaining
      }
      break
    }

    if (openIndex !== -1 && (closeIndex === -1 || openIndex < closeIndex)) {
      // Found open tag
      mainContent += remaining.slice(0, openIndex)
      remaining = remaining.slice(openIndex + thinkOpenTag.length)
      isThinking = true
    } else if (closeIndex !== -1) {
      // Found close tag
      thinkingContent += remaining.slice(0, closeIndex)
      remaining = remaining.slice(closeIndex + thinkCloseTag.length)
      isThinking = false
    }
  }

  // Check for partial tags at the end (streaming edge case)
  // If we have a partial '<' at the end that could be start of a tag, don't include it yet
  const partialTagMatch = mainContent.match(/<(?:t(?:h(?:i(?:n(?:k)?)?)?)?)?$/i)
  if (partialTagMatch) {
    mainContent = mainContent.slice(0, -partialTagMatch[0].length)
  }

  return { thinkingContent, mainContent, isThinking }
}

const SUGGESTIONS = [
  { text: '特斯拉股价', full: '特斯拉现在多少钱？' },
  { text: '分析英伟达', full: '帮我分析一下英伟达的走势' },
  { text: '比特币行情', full: '比特币现在价格是多少' },
  { text: '设置提醒', full: '帮我设置价格提醒' },
]

function App() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { theme, toggleTheme } = useTheme()

  const {
    conversations,
    messages,
    currentConversationId,
    groupedConversations,
    createConversation,
    updateConversation,
    deleteConversation,
    selectConversation,
    addMessage,
    updateMessage,
    startNewChat,
    setMessages,
  } = useConversations()

  // Get current conversation's backend session ID
  const currentConversation = conversations.find(c => c.id === currentConversationId)
  const backendSessionId = currentConversation?.backendSessionId

  // Smart scroll: only auto-scroll if user is near bottom
  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
    setShouldAutoScroll(isNearBottom)
  }, [])

  // Auto-scroll only when shouldAutoScroll is true
  useEffect(() => {
    if (shouldAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, shouldAutoScroll])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const send = async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || isLoading) return

    setInput('')
    setIsLoading(true)
    setShouldAutoScroll(true) // Reset auto-scroll when sending new message

    // Create conversation if this is the first message
    let conversationId = currentConversationId
    let sessionId = backendSessionId
    if (!conversationId) {
      const conversation = await createConversation(msg)
      conversationId = conversation.id
      sessionId = conversation.backendSessionId // will be undefined for new conversation
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: msg,
      timestamp: Date.now(),
    }

    // Add user message to local state immediately
    setMessages(prev => [...prev, userMessage])
    // Persist to storage with explicit conversationId
    await addMessage(userMessage, conversationId)

    const aiMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isTyping: true,
      toolCalls: [],
      thinkingContent: '',
      isThinking: false,
      thinkingDuration: 0,
    }

    // Add AI message to local state
    setMessages(prev => [...prev, aiMessage])

    // Timer for tracking thinking duration
    let thinkingStartTime: number | null = null
    let thinkingDurationMs = 0

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, message: msg })
      })

      // Handle session not found (404) - session expired on server restart
      if (res.status === 404) {
        // Clear the invalid sessionId
        if (conversationId) {
          await updateConversation(conversationId, { backendSessionId: undefined })
        }
        throw new Error('SESSION_EXPIRED')
      }

      if (!res.ok) throw new Error('Request failed')

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let fullText = ''
      let currentToolCalls: ToolCall[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('event: ')) continue
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.text) {
                fullText += data.text
                const parsed = parseThinkTags(fullText)

                // Track thinking duration
                if (parsed.isThinking && thinkingStartTime === null) {
                  thinkingStartTime = Date.now()
                }
                if (!parsed.isThinking && thinkingStartTime !== null) {
                  thinkingDurationMs = Date.now() - thinkingStartTime
                }

                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessage.id ? {
                      ...m,
                      content: parsed.mainContent,
                      thinkingContent: parsed.thinkingContent,
                      isThinking: parsed.isThinking,
                      thinkingDuration: parsed.isThinking && thinkingStartTime
                        ? Math.round((Date.now() - thinkingStartTime) / 1000)
                        : Math.round(thinkingDurationMs / 1000),
                      isTyping: true
                    } : m
                  )
                )
              }

              if (data.toolName && data.args !== undefined) {
                const newToolCall: ToolCall = {
                  toolName: data.toolName,
                  args: data.args,
                  status: 'calling',
                }
                currentToolCalls = [...currentToolCalls, newToolCall]
                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessage.id ? { ...m, toolCalls: currentToolCalls } : m
                  )
                )
              }

              if (data.toolName && data.result !== undefined) {
                currentToolCalls = currentToolCalls.map(tc =>
                  tc.toolName === data.toolName && tc.status === 'calling'
                    ? { ...tc, result: data.result, status: 'done' as const }
                    : tc
                )
                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessage.id ? { ...m, toolCalls: currentToolCalls } : m
                  )
                )
              }

              // Handle done event - store backend sessionId for context continuity
              if (data.sessionId && conversationId) {
                await updateConversation(conversationId, { backendSessionId: data.sessionId })
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }

      // Finalize message
      const finalParsed = parseThinkTags(fullText)
      const finalMessage = {
        ...aiMessage,
        content: finalParsed.mainContent,
        thinkingContent: finalParsed.thinkingContent,
        isThinking: false,
        thinkingDuration: thinkingStartTime ? Math.round((thinkingDurationMs || (Date.now() - thinkingStartTime)) / 1000) : 0,
        isTyping: false,
        toolCalls: currentToolCalls,
      }
      setMessages(prev =>
        prev.map(m => m.id === aiMessage.id ? finalMessage : m)
      )
      // Persist AI message
      await addMessage(finalMessage, conversationId)
    } catch (error) {
      const isSessionExpired = error instanceof Error && error.message === 'SESSION_EXPIRED'
      const errorContent = isSessionExpired
        ? '对话已失效（服务器重启），请点击左上角开始新对话'
        : '无法连接服务器，请确保后端已启动'
      setMessages(prev =>
        prev.map(m =>
          m.id === aiMessage.id
            ? { ...m, content: errorContent, isTyping: false, isThinking: false }
            : m
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleFeedback = async (messageId: string, feedback: 'up' | 'down') => {
    await updateMessage(messageId, { feedback })
  }

  const handleRegenerate = async (messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex <= 0) return

    const userMessage = messages[messageIndex - 1]
    if (userMessage.role !== 'user') return

    setMessages(prev => prev.filter(m => m.id !== messageId))

    const aiMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isTyping: true,
      toolCalls: [],
      thinkingContent: '',
      isThinking: false,
      thinkingDuration: 0,
    }

    setMessages(prev => [...prev, aiMessage])
    setIsLoading(true)
    setShouldAutoScroll(true)

    // Timer for tracking thinking duration
    let thinkingStartTime: number | null = null
    let thinkingDurationMs = 0

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId: backendSessionId, message: userMessage.content })
      })

      // Handle session not found (404) - session expired on server restart
      if (res.status === 404) {
        // Clear the invalid sessionId
        if (currentConversationId) {
          await updateConversation(currentConversationId, { backendSessionId: undefined })
        }
        throw new Error('SESSION_EXPIRED')
      }

      if (!res.ok) throw new Error('Request failed')

      const reader = res.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let fullText = ''
      let currentToolCalls: ToolCall[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('event: ')) continue
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.text) {
                fullText += data.text
                const parsed = parseThinkTags(fullText)

                // Track thinking duration
                if (parsed.isThinking && thinkingStartTime === null) {
                  thinkingStartTime = Date.now()
                }
                if (!parsed.isThinking && thinkingStartTime !== null) {
                  thinkingDurationMs = Date.now() - thinkingStartTime
                }

                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessage.id ? {
                      ...m,
                      content: parsed.mainContent,
                      thinkingContent: parsed.thinkingContent,
                      isThinking: parsed.isThinking,
                      thinkingDuration: parsed.isThinking && thinkingStartTime
                        ? Math.round((Date.now() - thinkingStartTime) / 1000)
                        : Math.round(thinkingDurationMs / 1000),
                      isTyping: true
                    } : m
                  )
                )
              }
              if (data.toolName && data.args !== undefined) {
                const newToolCall: ToolCall = {
                  toolName: data.toolName,
                  args: data.args,
                  status: 'calling',
                }
                currentToolCalls = [...currentToolCalls, newToolCall]
                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessage.id ? { ...m, toolCalls: currentToolCalls } : m
                  )
                )
              }
              if (data.toolName && data.result !== undefined) {
                currentToolCalls = currentToolCalls.map(tc =>
                  tc.toolName === data.toolName && tc.status === 'calling'
                    ? { ...tc, result: data.result, status: 'done' as const }
                    : tc
                )
                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessage.id ? { ...m, toolCalls: currentToolCalls } : m
                  )
                )
              }

              // Handle done event - store backend sessionId for context continuity
              if (data.sessionId && currentConversationId) {
                await updateConversation(currentConversationId, { backendSessionId: data.sessionId })
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }

      const finalParsed = parseThinkTags(fullText)
      const finalMessage = {
        ...aiMessage,
        content: finalParsed.mainContent,
        thinkingContent: finalParsed.thinkingContent,
        isThinking: false,
        thinkingDuration: thinkingStartTime ? Math.round((thinkingDurationMs || (Date.now() - thinkingStartTime)) / 1000) : 0,
        isTyping: false,
        toolCalls: currentToolCalls,
      }
      setMessages(prev =>
        prev.map(m => m.id === aiMessage.id ? finalMessage : m)
      )
      if (currentConversationId) {
        await addMessage(finalMessage, currentConversationId)
      }
    } catch (error) {
      const isSessionExpired = error instanceof Error && error.message === 'SESSION_EXPIRED'
      const errorContent = isSessionExpired
        ? '对话已失效（服务器重启），请点击左上角开始新对话'
        : '无法连接服务器，请确保后端已启动'
      setMessages(prev =>
        prev.map(m =>
          m.id === aiMessage.id
            ? { ...m, content: errorContent, isTyping: false, isThinking: false }
            : m
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <TooltipProvider>
      <div className="app">
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          conversations={groupedConversations()}
          currentConversationId={currentConversationId}
          onSelectConversation={selectConversation}
          onDeleteConversation={deleteConversation}
          onNewChat={startNewChat}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        {/* Mobile Toggle Button */}
        <button
          className={cn('mobile-sidebar-toggle', sidebarOpen && 'mobile-sidebar-toggle-hidden')}
          onClick={() => setSidebarOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className={cn('app-container', sidebarOpen && 'app-container-sidebar-expanded')}>
          <div className="main-content">
            <main
              className="messages-container"
              ref={messagesContainerRef}
              onScroll={handleScroll}
            >
              <div className="messages-wrapper">
                {messages.length === 0 ? (
                  <div className="welcome">
                    <div className="welcome-icon">
                      <TrendingUp strokeWidth={1.5} />
                    </div>
                    <h1>MarketPulse</h1>
                    <p>智能金融助手</p>
                  </div>
                ) : (
                  <div className="messages">
                    {messages.map((msg) => (
                      <ChatMessage
                        key={msg.id}
                        message={msg}
                        onFeedback={handleFeedback}
                        onRegenerate={handleRegenerate}
                      />
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
            </main>

            <footer className="input-area">
              <div className="input-wrapper">
                {messages.length === 0 && (
                  <div className="suggestions">
                    {SUGGESTIONS.map((s, i) => (
                      <button key={i} onClick={() => send(s.full)} className="suggestion">
                        {s.text}
                      </button>
                    ))}
                  </div>
                )}

                <ChatInput
                  value={input}
                  onChange={setInput}
                  onSend={() => send()}
                  isLoading={isLoading}
                />
              </div>
            </footer>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}

export default App
