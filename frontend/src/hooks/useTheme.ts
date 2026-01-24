import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

const THEME_KEY = 'marketpulse-theme'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // 从 localStorage 读取，默认深色
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(THEME_KEY) as Theme | null
      return stored || 'dark'
    }
    return 'dark'
  })

  useEffect(() => {
    const root = window.document.documentElement

    // 移除旧的主题类
    root.classList.remove('light', 'dark')
    // 添加当前主题类
    root.classList.add(theme)

    // 保存到 localStorage
    localStorage.setItem(THEME_KEY, theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
  }

  return { theme, setTheme, toggleTheme }
}
