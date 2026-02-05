import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, CheckCircle, AlertCircle, Twitter, RefreshCw } from 'lucide-react'
import type { ScrapeCompleteEvent, ScrapeErrorEvent } from '@/hooks/useSSEEvents'

interface ScrapeNotificationProps {
  event: ScrapeCompleteEvent | ScrapeErrorEvent | null
  onDismiss: () => void
  onViewResults: (queries: string[]) => void
}

export function ScrapeNotification({ event, onDismiss, onViewResults }: ScrapeNotificationProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (event) {
      setVisible(true)
      // Auto-dismiss after 15 seconds
      const timer = setTimeout(() => {
        setVisible(false)
        setTimeout(onDismiss, 300) // Wait for animation
      }, 15000)
      return () => clearTimeout(timer)
    }
  }, [event, onDismiss])

  if (!event) return null

  const isSuccess = 'totalCollected' in event
  const queries = event.queries.join(', ')

  const handleViewResults = () => {
    onViewResults(event.queries)
    setVisible(false)
    setTimeout(onDismiss, 300)
  }

  const handleDismiss = () => {
    setVisible(false)
    setTimeout(onDismiss, 300)
  }

  // Use Portal to render at document body level (avoids CSS transform issues)
  return createPortal(
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        maxWidth: '384px',
        transition: 'all 0.3s ease-out',
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(16px)',
        pointerEvents: visible ? 'auto' : 'none',
      }}
    >
      <div
        style={{
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
          border: `1px solid ${isSuccess ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          padding: '16px',
          backgroundColor: isSuccess ? 'rgba(20, 83, 45, 0.95)' : 'rgba(127, 29, 29, 0.95)',
          backdropFilter: 'blur(8px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div
            style={{
              flexShrink: 0,
              borderRadius: '50%',
              padding: '6px',
              backgroundColor: isSuccess ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            }}
          >
            {isSuccess ? (
              <CheckCircle style={{ width: '20px', height: '20px', color: '#4ade80' }} />
            ) : (
              <AlertCircle style={{ width: '20px', height: '20px', color: '#f87171' }} />
            )}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Twitter style={{ width: '16px', height: '16px', color: '#38bdf8' }} />
              <h4
                style={{
                  fontSize: '14px',
                  fontWeight: 500,
                  margin: 0,
                  color: isSuccess ? '#bbf7d0' : '#fecaca',
                }}
              >
                {isSuccess ? '推文抓取完成' : '推文抓取失败'}
              </h4>
            </div>

            <p style={{ marginTop: '4px', fontSize: '14px', color: '#d1d5db' }}>
              {isSuccess ? (
                <>
                  已抓取 <span style={{ fontWeight: 500, color: '#fff' }}>{(event as ScrapeCompleteEvent).totalCollected}</span> 条关于「{queries}」的推文
                  {(event as ScrapeCompleteEvent).totalInserted > 0 && (
                    <>，新增 <span style={{ fontWeight: 500, color: '#fff' }}>{(event as ScrapeCompleteEvent).totalInserted}</span> 条</>
                  )}
                </>
              ) : (
                <>抓取「{queries}」失败: {(event as ScrapeErrorEvent).error}</>
              )}
            </p>

            {isSuccess && (event as ScrapeCompleteEvent).totalCollected > 0 && (
              <button
                onClick={handleViewResults}
                style={{
                  marginTop: '12px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  fontSize: '14px',
                  fontWeight: 500,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: 'rgba(34, 197, 94, 0.3)',
                  color: '#bbf7d0',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(34, 197, 94, 0.5)'
                  e.currentTarget.style.color = '#fff'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(34, 197, 94, 0.3)'
                  e.currentTarget.style.color = '#bbf7d0'
                }}
              >
                <RefreshCw style={{ width: '14px', height: '14px' }} />
                查看结果
              </button>
            )}
          </div>

          <button
            onClick={handleDismiss}
            style={{
              flexShrink: 0,
              padding: '4px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.2s',
              backgroundColor: 'transparent',
              color: '#9ca3af',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(75, 85, 99, 0.5)'
              e.currentTarget.style.color = '#fff'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
              e.currentTarget.style.color = '#9ca3af'
            }}
          >
            <X style={{ width: '16px', height: '16px' }} />
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
