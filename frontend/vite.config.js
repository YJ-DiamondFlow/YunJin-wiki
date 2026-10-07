import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前端构建配置：开发时把 /api 代理到纯 Python 后端
export default defineConfig({
  plugins: [vue()],
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
