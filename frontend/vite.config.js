import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The proxy target is set via env var so Docker can point to the API container
// by its service name (http://documind-api:8000), while local dev uses localhost.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 8501,
    strictPort: true,
    proxy: {
      // All /api/v1/* requests are forwarded to the backend container
      '/api/v1': {
        target: API_PROXY_TARGET,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
