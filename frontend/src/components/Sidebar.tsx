import { Plus, Trash2, MessageSquare, PanelLeftClose, PanelLeft } from 'lucide-react'
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
  onToggle: () => void
  conversations: { label: string; conversations: Conversation[] }[]
  currentConversationId: string | null
  onSelectConversation: (id: string) => void
  onDeleteConversation: (id: string) => void
  onNewChat: () => void
}

export function Sidebar({
  isOpen,
  onToggle,
  conversations,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
}: SidebarProps) {
  return (
    <div className="sidebar-wrapper">
      {/* Collapsed sidebar strip */}
      <div className={cn('sidebar-collapsed', isOpen && 'sidebar-collapsed-hidden')}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="sidebar-toggle-btn"
              onClick={onToggle}
            >
              <PanelLeft className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>展开侧边栏</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="sidebar-toggle-btn"
              onClick={onNewChat}
            >
              <Plus className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>新对话</p>
          </TooltipContent>
        </Tooltip>
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="sidebar-overlay"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      {/* Expanded sidebar */}
      <aside className={cn('sidebar', isOpen && 'sidebar-open')}>
        <div className="sidebar-header">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="sidebar-toggle-btn"
                onClick={onToggle}
              >
                <PanelLeftClose className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>收起侧边栏</p>
            </TooltipContent>
          </Tooltip>

          <Button
            variant="ghost"
            size="icon"
            className="sidebar-toggle-btn"
            onClick={() => {
              onNewChat()
            }}
          >
            <Plus className="h-5 w-5" />
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
    </div>
  )
}
