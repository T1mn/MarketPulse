import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { History, Search, Database, X, Trash2, ChevronDown } from 'lucide-react'
import type { SearchHistoryItem } from '@/hooks/useSearchHistory'

interface SearchHistoryDropdownProps {
  history: SearchHistoryItem[]
  onReSearch: (query: string) => void
  onViewCached: (query: string) => void
  onRemove: (id: string) => void
  onClear: () => void
}

export function SearchHistoryDropdown({
  history,
  onReSearch,
  onViewCached,
  onRemove,
  onClear,
}: SearchHistoryDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  // Update position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      // Open upward: position dropdown above the button
      setPosition({
        bottom: window.innerHeight - rect.top + 8,
        right: window.innerWidth - rect.right,
      })
    }
  }, [isOpen])

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return

    const handleClick = (e: MouseEvent) => {
      if (buttonRef.current?.contains(e.target as Node)) return
      setIsOpen(false)
    }

    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [isOpen])

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - timestamp

    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
    if (date.toDateString() === now.toDateString()) return '今天'

    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  return (
    <>
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 12px',
          borderRadius: '8px',
          border: '1px solid rgba(255,255,255,0.1)',
          backgroundColor: isOpen ? 'rgba(255,255,255,0.1)' : 'transparent',
          color: '#9ca3af',
          cursor: 'pointer',
          transition: 'all 0.2s',
          fontSize: '14px',
        }}
        onMouseOver={(e) => {
          if (!isOpen) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'
        }}
        onMouseOut={(e) => {
          if (!isOpen) e.currentTarget.style.backgroundColor = 'transparent'
        }}
      >
        <History style={{ width: '16px', height: '16px' }} />
        <span>搜索历史</span>
        {history.length > 0 && (
          <span
            style={{
              backgroundColor: 'rgba(59, 130, 246, 0.5)',
              color: '#fff',
              fontSize: '12px',
              padding: '2px 6px',
              borderRadius: '10px',
              minWidth: '20px',
              textAlign: 'center',
            }}
          >
            {history.length}
          </span>
        )}
        <ChevronDown
          style={{
            width: '14px',
            height: '14px',
            transition: 'transform 0.2s',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0)',
          }}
        />
      </button>

      {isOpen &&
        createPortal(
          <div
            style={{
              position: 'fixed',
              bottom: position.bottom,
              right: position.right,
              zIndex: 9999,
              width: '320px',
              maxHeight: '400px',
              backgroundColor: '#1f2937',
              borderRadius: '12px',
              boxShadow: '0 -10px 40px rgba(0,0,0,0.5)',
              border: '1px solid rgba(255,255,255,0.1)',
              overflow: 'hidden',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderBottom: '1px solid rgba(255,255,255,0.1)',
              }}
            >
              <span style={{ color: '#fff', fontWeight: 500, fontSize: '14px' }}>
                推文搜索历史
              </span>
              {history.length > 0 && (
                <button
                  onClick={onClear}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    border: 'none',
                    backgroundColor: 'transparent',
                    color: '#ef4444',
                    cursor: 'pointer',
                    fontSize: '12px',
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.backgroundColor = 'rgba(239,68,68,0.1)')}
                  onMouseOut={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <Trash2 style={{ width: '12px', height: '12px' }} />
                  清空
                </button>
              )}
            </div>

            {/* List */}
            <div style={{ maxHeight: '340px', overflowY: 'auto' }}>
              {history.length === 0 ? (
                <div
                  style={{
                    padding: '32px 16px',
                    textAlign: 'center',
                    color: '#6b7280',
                    fontSize: '14px',
                  }}
                >
                  <History style={{ width: '32px', height: '32px', margin: '0 auto 8px', opacity: 0.5 }} />
                  <p>暂无搜索历史</p>
                  <p style={{ fontSize: '12px', marginTop: '4px' }}>
                    抓取推文后会自动保存
                  </p>
                </div>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: '12px 16px',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      transition: 'background 0.2s',
                    }}
                    onMouseOver={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)')}
                    onMouseOut={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ color: '#fff', fontWeight: 500, fontSize: '14px' }}>
                        {item.query}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ color: '#6b7280', fontSize: '12px' }}>
                          {formatTime(item.timestamp)}
                        </span>
                        <button
                          onClick={() => onRemove(item.id)}
                          style={{
                            padding: '2px',
                            borderRadius: '4px',
                            border: 'none',
                            backgroundColor: 'transparent',
                            color: '#6b7280',
                            cursor: 'pointer',
                          }}
                          onMouseOver={(e) => {
                            e.currentTarget.style.color = '#ef4444'
                            e.currentTarget.style.backgroundColor = 'rgba(239,68,68,0.1)'
                          }}
                          onMouseOut={(e) => {
                            e.currentTarget.style.color = '#6b7280'
                            e.currentTarget.style.backgroundColor = 'transparent'
                          }}
                        >
                          <X style={{ width: '14px', height: '14px' }} />
                        </button>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => {
                          onReSearch(item.query)
                          setIsOpen(false)
                        }}
                        style={{
                          flex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          borderRadius: '6px',
                          border: '1px solid rgba(59,130,246,0.3)',
                          backgroundColor: 'rgba(59,130,246,0.1)',
                          color: '#60a5fa',
                          cursor: 'pointer',
                          fontSize: '13px',
                          transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(59,130,246,0.2)'
                          e.currentTarget.style.borderColor = 'rgba(59,130,246,0.5)'
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(59,130,246,0.1)'
                          e.currentTarget.style.borderColor = 'rgba(59,130,246,0.3)'
                        }}
                      >
                        <Search style={{ width: '14px', height: '14px' }} />
                        重新抓取
                      </button>
                      <button
                        onClick={() => {
                          onViewCached(item.query)
                          setIsOpen(false)
                        }}
                        style={{
                          flex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          borderRadius: '6px',
                          border: '1px solid rgba(34,197,94,0.3)',
                          backgroundColor: 'rgba(34,197,94,0.1)',
                          color: '#4ade80',
                          cursor: 'pointer',
                          fontSize: '13px',
                          transition: 'all 0.2s',
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(34,197,94,0.2)'
                          e.currentTarget.style.borderColor = 'rgba(34,197,94,0.5)'
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(34,197,94,0.1)'
                          e.currentTarget.style.borderColor = 'rgba(34,197,94,0.3)'
                        }}
                      >
                        <Database style={{ width: '14px', height: '14px' }} />
                        查看缓存
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>,
          document.body
        )}
    </>
  )
}
