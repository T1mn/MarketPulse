interface LogoProps {
  size?: number
  className?: string
  theme?: 'light' | 'dark'
}

export function Logo({ size = 24, className = '', theme }: LogoProps) {
  // 浅色模式：深色背景 + 白色折线
  // 深色模式：浅色背景 + 深色折线（背景比页面背景稍暗一点形成色差）
  const isDark = theme === 'dark'

  const bgColor = isDark ? '#e5e5e5' : '#1a1a1a'
  const lineColor = isDark ? '#1a1a1a' : '#ffffff'

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={size}
      height={size}
      className={className}
    >
      <rect width="32" height="32" rx="6" fill={bgColor} />
      <path
        d="M4 18 L8 18 L10 12 L13 22 L16 8 L19 24 L22 14 L24 18 L28 18"
        fill="none"
        stroke={lineColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
