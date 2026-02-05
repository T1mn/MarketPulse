import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    allowedHosts: ['chat.tonwork.fun'],
    // 本地开发时代理 API 请求到线上服务器
    proxy: {
      '/api': {
        target: 'https://chat.tonwork.fun',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
