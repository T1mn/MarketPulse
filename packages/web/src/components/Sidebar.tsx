import { Plus, Trash2, MessageSquare, PanelLeftClose, PanelLeft, TrendingUp, Sun, Moon } from 'lucide-react'
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
  theme: 'light' | 'dark'
  onToggleTheme: () => void
}

export function Sidebar({
  isOpen,
  onToggle,
  conversations,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
  theme,
  onToggleTheme,
}: SidebarProps) {
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="manus-sidebar-overlay"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      <aside className={cn('manus-sidebar', isOpen && 'manus-sidebar-expanded')}>
      {/* Logo Area */}
      <div className="manus-sidebar-logo">
        <div className="manus-sidebar-brand">
          <TrendingUp className="manus-sidebar-brand-icon" />
          {isOpen && <span className="manus-sidebar-brand-text">MarketPulse</span>}
        </div>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              className="manus-sidebar-toggle"
              onClick={onToggle}
            >
              {isOpen ? (
                <PanelLeftClose className="manus-sidebar-icon" />
              ) : (
                <PanelLeft className="manus-sidebar-icon" />
              )}
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>{isOpen ? '收起侧边栏' : '展开侧边栏'}</p>
          </TooltipContent>
        </Tooltip>
      </div>

      {/* Action Area */}
      <div className="manus-sidebar-actions">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              className="manus-sidebar-action-btn"
              onClick={onNewChat}
            >
              <Plus className="manus-sidebar-icon" />
              {isOpen && <span>新建对话</span>}
            </button>
          </TooltipTrigger>
          {!isOpen && (
            <TooltipContent side="right">
              <p>新建对话</p>
            </TooltipContent>
          )}
        </Tooltip>
      </div>

      {/* Conversation List */}
      <div className="manus-sidebar-section">
        {isOpen && (
          <div className="manus-sidebar-section-header">
            <span>对话历史</span>
          </div>
        )}
        <nav className="manus-sidebar-nav">
          {conversations.length === 0 ? (
            <div className="manus-sidebar-empty">
              {isOpen ? (
                <>
                  <MessageSquare className="manus-sidebar-empty-icon" />
                  <p>暂无对话</p>
                </>
              ) : (
                <MessageSquare className="manus-sidebar-icon manus-sidebar-empty-icon-collapsed" />
              )}
            </div>
          ) : (
            conversations.map((group) => (
              <div key={group.label} className="manus-sidebar-group">
                {isOpen && (
                  <div className="manus-sidebar-group-label">{group.label}</div>
                )}
                <ul className="manus-sidebar-list">
                  {group.conversations.map((conv) => (
                    <li key={conv.id}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            className={cn(
                              'manus-sidebar-item',
                              currentConversationId === conv.id && 'manus-sidebar-item-active'
                            )}
                            onClick={() => onSelectConversation(conv.id)}
                          >
                            <MessageSquare className="manus-sidebar-icon" />
                            {isOpen && (
                              <>
                                <span className="manus-sidebar-item-title">{conv.title}</span>
                                <button
                                  className="manus-sidebar-item-delete"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onDeleteConversation(conv.id)
                                  }}
                                >
                                  <Trash2 className="manus-sidebar-icon-sm" />
                                </button>
                              </>
                            )}
                          </button>
                        </TooltipTrigger>
                        {!isOpen && (
                          <TooltipContent side="right">
                            <p>{conv.title}</p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </nav>
      </div>

      {/* Bottom Area - Theme Toggle */}
      <div className="manus-sidebar-footer">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              className="manus-sidebar-theme-btn"
              onClick={onToggleTheme}
            >
              {theme === 'dark' ? (
                <Sun className="manus-sidebar-icon" />
              ) : (
                <Moon className="manus-sidebar-icon" />
              )}
              {isOpen && <span>{theme === 'dark' ? '浅色模式' : '深色模式'}</span>}
            </button>
          </TooltipTrigger>
          {!isOpen && (
            <TooltipContent side="right">
              <p>{theme === 'dark' ? '浅色模式' : '深色模式'}</p>
            </TooltipContent>
          )}
        </Tooltip>
      </div>
    </aside>
    </>
  )
}
