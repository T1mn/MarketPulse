import { Plus, Trash2, MessageSquare, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { Conversation } from '@/types'
import { cn } from '@/lib/utils'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  conversations: { label: string; conversations: Conversation[] }[]
  currentConversationId: string | null
  onSelectConversation: (id: string) => void
  onDeleteConversation: (id: string) => void
  onNewChat: () => void
}

export function Sidebar({
  isOpen,
  onClose,
  conversations,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
}: SidebarProps) {
  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="sidebar-overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside className={cn('sidebar', isOpen && 'sidebar-open')}>
        <div className="sidebar-header">
          <Button
            variant="outline"
            className="new-chat-btn"
            onClick={() => {
              onNewChat()
              onClose()
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            新对话
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="sidebar-close-btn"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="sidebar-content">
          {conversations.length === 0 ? (
            <div className="sidebar-empty">
              <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
              <p>暂无对话记录</p>
            </div>
          ) : (
            conversations.map((group) => (
              <div key={group.label} className="conversation-group">
                <h3 className="conversation-group-label">{group.label}</h3>
                <ul className="conversation-list">
                  {group.conversations.map((conv) => (
                    <li key={conv.id}>
                      <button
                        className={cn(
                          'conversation-item',
                          currentConversationId === conv.id && 'conversation-item-active'
                        )}
                        onClick={() => {
                          onSelectConversation(conv.id)
                          onClose()
                        }}
                      >
                        <MessageSquare className="h-4 w-4 flex-shrink-0" />
                        <span className="conversation-title">{conv.title}</span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              className="conversation-delete"
                              onClick={(e) => {
                                e.stopPropagation()
                                onDeleteConversation(conv.id)
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>删除对话</p>
                          </TooltipContent>
                        </Tooltip>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </nav>
      </aside>
    </>
  )
}
