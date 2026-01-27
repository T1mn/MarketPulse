import { Copy, Check, ThumbsUp, ThumbsDown, RefreshCw, Wrench, Loader2, ChevronRight, Sparkles } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

// Tool name mapping for display
const TOOL_DISPLAY_NAMES: Record<string, string> = {
  getMarketPrice: '获取价格',
  searchNews: '搜索新闻',
}

// Thinking block component
function ThinkingBlock({ message }: { message: Message }) {
  const [expanded, setExpanded] = useState(false)
  const hasThinkingContent = message.thinkingContent && message.thinkingContent.trim().length > 0

  if (!hasThinkingContent && !message.isThinking) return null

  // During thinking - pulsing indicator
  if (message.isThinking) {
    return (
      <div className="thinking-block">
        <div className="thinking-indicator">
          <Sparkles className="thinking-indicator-icon" />
          <span>
            正在思考{message.thinkingDuration && message.thinkingDuration > 0 ? ` · ${message.thinkingDuration}秒` : ''}
          </span>
        </div>
      </div>
    )
  }

  // After thinking - collapsible block
  if (!hasThinkingContent) return null

  return (
    <div className="thinking-block">
      <div className="thinking-header" onClick={() => setExpanded(!expanded)}>
        <ChevronRight className={cn('thinking-chevron', expanded && 'thinking-chevron-expanded')} />
        <span>已深度思考（用时 {message.thinkingDuration || 0} 秒）</span>
      </div>
      <div className={cn(
        'thinking-content-wrapper',
        expanded ? 'thinking-content-expanded' : 'thinking-content-collapsed'
      )}>
        <div className="thinking-content">
          {message.thinkingContent}
        </div>
      </div>
    </div>
  )
}

interface ChatMessageProps {
  message: Message
  onFeedback?: (messageId: string, feedback: 'up' | 'down') => void
  onRegenerate?: (messageId: string) => void
}

export function ChatMessage({ message, onFeedback, onRegenerate }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  return (
    <div className={cn('message', message.role)}>
      {/* Tool calls display - inline chips for assistant messages */}
      {isAssistant && message.toolCalls && message.toolCalls.length > 0 && (
        <div className="tool-calls">
          {message.toolCalls.map((tc, index) => (
            <span key={index} className="tool-call">
              {tc.status === 'calling' ? (
                <Loader2 className="tool-call-icon animate-spin" />
              ) : (
                <Wrench className="tool-call-icon" />
              )}
              <span className="tool-call-name">
                {TOOL_DISPLAY_NAMES[tc.toolName] || tc.toolName}
              </span>
            </span>
          ))}
        </div>
      )}

      {/* Thinking block - ChatGPT-style collapsible */}
      {isAssistant && <ThinkingBlock message={message} />}

      <div className="message-content">
        {message.isTyping && !message.content && !message.isThinking ? (
          <span className="loading-text">正在思考...</span>
        ) : (
          <>
            {isAssistant ? (
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const inline = !match && !String(children).includes('\n')
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={oneDark as Record<string, React.CSSProperties>}
                        language={match[1]}
                        PreTag="div"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              message.content
            )}
            {message.isTyping && <span className="cursor" />}
          </>
        )}
      </div>

      {/* Action buttons - always reserve space, show on hover */}
      <div className={cn(
        'message-actions',
        isUser ? 'message-actions-user' : 'message-actions-assistant',
        message.isTyping && 'message-actions-hidden'
      )}>
        {/* Copy button */}
        <button
          className="message-action-btn"
          onClick={handleCopy}
          title={copied ? '已复制' : '复制'}
        >
          {copied ? (
            <Check className="action-icon" />
          ) : (
            <Copy className="action-icon" />
          )}
        </button>

        {/* Assistant-only buttons */}
        {isAssistant && (
          <>
            {onRegenerate && (
              <button
                className="message-action-btn"
                onClick={() => onRegenerate(message.id)}
                title="重新生成"
              >
                <RefreshCw className="action-icon" />
              </button>
            )}

            {onFeedback && (
              <>
                <button
                  className={cn(
                    'message-action-btn',
                    message.feedback === 'up' && 'message-action-btn-active'
                  )}
                  onClick={() => onFeedback(message.id, 'up')}
                  title="有帮助"
                >
                  <ThumbsUp className="action-icon" />
                </button>
                <button
                  className={cn(
                    'message-action-btn',
                    message.feedback === 'down' && 'message-action-btn-active'
                  )}
                  onClick={() => onFeedback(message.id, 'down')}
                  title="没帮助"
                >
                  <ThumbsDown className="action-icon" />
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}
