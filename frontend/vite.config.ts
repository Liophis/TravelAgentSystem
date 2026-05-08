import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 1300,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined
          }

          if (id.includes('ant-design-vue')) {
            return 'ant-design-vue'
          }

          if (id.includes('@ant-design/icons-vue')) {
            return 'ant-design-icons'
          }

          if (id.includes('vue-i18n')) {
            return 'vue-i18n'
          }

          if (id.includes('vue-router')) {
            return 'vue-router'
          }

          if (id.includes('dayjs')) {
            return 'dayjs'
          }

          if (id.includes('axios')) {
            return 'axios'
          }

          return 'vendor'
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Proxy API requests to local backend during development
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
})
