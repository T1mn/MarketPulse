import { useState, useRef, useEffect } from 'react'
import { TrendingUp } from 'lucide-react'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Sidebar } from '@/components/Sidebar'
import { ChatMessage } from '@/components/ChatMessage'
import { ChatInput } from '@/components/ChatInput'
import { useConversations } from '@/hooks/useConversations'
import type { Message } from '@/types'
import '@/index.css'

const API_URL = 'http://127.0.0.1:8000/api/v1/chat'

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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const {
    messages,
    currentConversationId,
    groupedConversations,
    createConversation,
    deleteConversation,
    selectConversation,
    addMessage,
    updateMessage,
    startNewChat,
    setMessages,
  } = useConversations()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const typeText = async (text: string, messageId: string) => {
    // Use requestAnimationFrame for smooth typing even when tab is not focused
    const chars = text.split('')
    let current = ''
    let i = 0

    const typeNextChunk = () => {
      // Type multiple chars per frame for better performance
      const charsPerFrame = document.hidden ? 10 : 3
      for (let j = 0; j < charsPerFrame && i < chars.length; j++, i++) {
        current += chars[i]
      }

      setMessages(prev =>
        prev.map(m =>
          m.id === messageId ? { ...m, content: current, isTyping: true } : m
        )
      )

      if (i < chars.length) {
        requestAnimationFrame(typeNextChunk)
      } else {
        // Typing complete
        updateMessage(messageId, { content: text, isTyping: false })
        setMessages(prev =>
          prev.map(m =>
            m.id === messageId ? { ...m, isTyping: false } : m
          )
        )
      }
    }

    requestAnimationFrame(typeNextChunk)
  }

  const send = async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || isLoading) return

    setInput('')
    setIsLoading(true)

    // Create conversation if this is the first message
    let conversationId = currentConversationId
    if (!conversationId) {
      const conversation = await createConversation(msg)
      conversationId = conversation.id
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: msg,
      timestamp: Date.now(),
    }

    await addMessage(userMessage)

    const aiMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isTyping: true,
    }

    // Add AI message to local state immediately for typing effect
    setMessages(prev => [...prev, aiMessage])

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, user_id: 'user', language: 'zh-CN' })
      })

      if (!res.ok) throw new Error('Request failed')

      const data = await res.json()
      await typeText(data.content, aiMessage.id)

      // Update the message in storage (not add again)
      aiMessage.content = data.content
      aiMessage.isTyping = false
    } catch {
      const errorContent = '无法连接服务器，请确保后端已启动'
      setMessages(prev =>
        prev.map(m =>
          m.id === aiMessage.id
            ? { ...m, content: errorContent, isTyping: false }
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
    // Find the message to regenerate and the previous user message
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex <= 0) return

    const userMessage = messages[messageIndex - 1]
    if (userMessage.role !== 'user') return

    // Remove the old AI response
    setMessages(prev => prev.filter(m => m.id !== messageId))

    // Create new AI message
    const aiMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isTyping: true,
    }

    setMessages(prev => [...prev, aiMessage])
    setIsLoading(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content, user_id: 'user', language: 'zh-CN' })
      })

      if (!res.ok) throw new Error('Request failed')

      const data = await res.json()
      await typeText(data.content, aiMessage.id)

      aiMessage.content = data.content
      aiMessage.isTyping = false
      await addMessage(aiMessage)
    } catch {
      const errorContent = '无法连接服务器，请确保后端已启动'
      setMessages(prev =>
        prev.map(m =>
          m.id === aiMessage.id
            ? { ...m, content: errorContent, isTyping: false }
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
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          conversations={groupedConversations()}
          currentConversationId={currentConversationId}
          onSelectConversation={selectConversation}
          onDeleteConversation={deleteConversation}
          onNewChat={startNewChat}
        />

        {/* Main Container */}
        <div className="app-container">
          {/* Theme Toggle - Fixed position */}
          <div className="theme-toggle-fixed">
            <ThemeToggle />
          </div>

          {/* Main Content */}
          <div className="main-content">
            {/* Messages Area */}
            <main className="messages-container">
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

            {/* Input Area */}
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
