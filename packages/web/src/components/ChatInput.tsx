import { useRef, useEffect, useState } from 'react'
import { Paperclip, ArrowRight, Square, X, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { generateUUID } from '@/lib/storage'
import type { Attachment } from '@/types'

const MAX_CHARS = 8000

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (attachments?: Attachment[]) => void
  onStop?: () => void
  isLoading: boolean
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({
  value,
  onChange,
  onSend,
  onStop,
  isLoading,
  disabled = false,
  placeholder = '输入消息...',
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [attachments, setAttachments] = useState<Attachment[]>([])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '24px'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSend = () => {
    if ((!value.trim() && attachments.length === 0) || isLoading) return
    onSend(attachments.length > 0 ? attachments : undefined)
    setAttachments([])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach(file => {
      const reader = new FileReader()
      reader.onload = () => {
        const attachment: Attachment = {
          id: generateUUID(),
          type: file.type.startsWith('image/') ? 'image' : 'document',
          name: file.name,
          url: reader.result as string,
        }
        setAttachments(prev => [...prev, attachment])
      }
      reader.readAsDataURL(file)
    })

    // Reset input
    e.target.value = ''
  }

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(a => a.id !== id))
  }

  const charCount = value.length
  const isOverLimit = charCount > MAX_CHARS
  const canSend = (value.trim() || attachments.length > 0) && !isOverLimit && !disabled

  return (
    <div className="chat-input-container">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="attachments-preview">
          {attachments.map(attachment => (
            <div key={attachment.id} className="attachment-item">
              {attachment.type === 'image' ? (
                <img src={attachment.url} alt={attachment.name} className="attachment-image" />
              ) : (
                <div className="attachment-file">
                  <FileText className="h-6 w-6" />
                </div>
              )}
              <span className="attachment-name">{attachment.name}</span>
              <button
                className="attachment-remove"
                onClick={() => removeAttachment(attachment.id)}
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Box */}
      <div className={cn('input-box', isOverLimit && 'input-box-error')}>
        {/* Attachment Button */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="input-action-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || disabled}
            >
              <Paperclip className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>添加附件</p>
          </TooltipContent>
        </Tooltip>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf,.doc,.docx,.txt"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={isLoading || disabled}
        />

        {/* Send/Stop Button */}
        {isLoading ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="send-btn send-btn-stop"
                onClick={onStop}
              >
                <Square className="h-4 w-4 fill-current" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>停止生成</p>
            </TooltipContent>
          </Tooltip>
        ) : (
          <button
            onClick={handleSend}
            disabled={!canSend}
            className="send-btn"
            aria-label="发送"
          >
            <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Footer with character count */}
      <div className="input-footer">
        <p className="footer-text">MarketPulse 可能会出错，请核实重要信息</p>
        <span className={cn('char-count', isOverLimit && 'char-count-error')}>
          {charCount}/{MAX_CHARS}
        </span>
      </div>
    </div>
  )
}
