/// <reference types="vite/client" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProd = mode === 'production'

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      // Use Render backend in production
      rollupOptions: {
        output: {
          manualChunks: undefined,
        },
      },
    },
    define: {
      // API URLs for different environments
      __API_URL__: JSON.stringify(
        isProd ? 'https://gml-yxf5.onrender.com' : 'http://localhost:8000'
      ),
      __FRONTEND_URL__: JSON.stringify(
        isProd ? 'https://gml-sand.vercel.app' : 'http://localhost:3000'
      ),
    },
  }
})

