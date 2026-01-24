import { useState, useRef, useEffect } from 'react'
import './index.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  isTyping?: boolean
}

const API_URL = 'http://127.0.0.1:8000/api/v1/chat'

const SUGGESTIONS = [
  { text: '特斯拉股价', full: '特斯拉现在多少钱？' },
  { text: '分析英伟达', full: '帮我分析一下英伟达的走势' },
  { text: '比特币行情', full: '比特币现在价格是多少' },
  { text: '设置提醒', full: '帮我设置价格提醒' },
]

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const typeText = async (text: string, index: number) => {
    const chars = text.split('')
    let current = ''
    for (let i = 0; i < chars.length; i++) {
      current += chars[i]
      setMessages(prev => {
        const updated = [...prev]
        updated[index] = { ...updated[index], content: current, isTyping: true }
        return updated
      })
      await new Promise(r => setTimeout(r, 8))
    }
    setMessages(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], isTyping: false }
      return updated
    })
  }

  const send = async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || isLoading) return

    setInput('')
    setIsLoading(true)

    const newMessages = [...messages, { role: 'user' as const, content: msg }]
    setMessages(newMessages)

    const aiIndex = newMessages.length
    setMessages([...newMessages, { role: 'assistant', content: '', isTyping: true }])

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, user_id: 'user', language: 'zh-CN' })
      })

      if (!res.ok) throw new Error('Request failed')

      const data = await res.json()
      await typeText(data.content, aiIndex)
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[aiIndex] = {
          role: 'assistant',
          content: '无法连接服务器，请确保后端已启动',
          isTyping: false
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="app">
      {/* Messages Area */}
      <main className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="welcome-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M7 16l4-6 4 4 5-8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1>MarketPulse</h1>
            <p>智能金融助手</p>
          </div>
        ) : (
          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content}
                  {msg.isTyping && <span className="cursor" />}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
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

          <div className="input-box">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息..."
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || isLoading}
              className="send-btn"
              aria-label="发送"
            >
              {isLoading ? (
                <div className="loader" />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </button>
          </div>

          <p className="footer-text">MarketPulse 可能会出错，请核实重要信息</p>
        </div>
      </footer>
    </div>
  )
}

export default App
