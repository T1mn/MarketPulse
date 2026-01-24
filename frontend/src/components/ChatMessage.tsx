import { useState } from 'react'
import { Copy, Check, ThumbsUp, ThumbsDown, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import type { Message } from '@/types'

interface ChatMessageProps {
  message: Message
  onFeedback?: (messageId: string, feedback: 'up' | 'down') => void
  onRegenerate?: (messageId: string) => void
}

export function ChatMessage({ message, onFeedback, onRegenerate }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  return (
    <div
      className={cn('message', message.role)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="message-content">
        {message.content}
        {message.isTyping && <span className="cursor" />}
      </div>

      {/* Action buttons - show on hover, hide during typing */}
      {!message.isTyping && isHovered && (
        <div className={cn('message-actions', isUser ? 'message-actions-user' : 'message-actions-assistant')}>
          {/* Copy button - for all messages */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="message-action-btn"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{copied ? '已复制' : '复制'}</p>
            </TooltipContent>
          </Tooltip>

          {/* Assistant-only buttons */}
          {isAssistant && (
            <>
              {/* Regenerate button */}
              {onRegenerate && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="message-action-btn"
                      onClick={() => onRegenerate(message.id)}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>重新生成</p>
                  </TooltipContent>
                </Tooltip>
              )}

              {/* Thumbs up */}
              {onFeedback && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        'message-action-btn',
                        message.feedback === 'up' && 'message-action-btn-active'
                      )}
                      onClick={() => onFeedback(message.id, 'up')}
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>有帮助</p>
                  </TooltipContent>
                </Tooltip>
              )}

              {/* Thumbs down */}
              {onFeedback && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        'message-action-btn',
                        message.feedback === 'down' && 'message-action-btn-active'
                      )}
                      onClick={() => onFeedback(message.id, 'down')}
                    >
                      <ThumbsDown className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>没帮助</p>
                  </TooltipContent>
                </Tooltip>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
