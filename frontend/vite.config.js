import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const DEBUG_PROXY = ['1', 'true', 'yes', 'on'].includes(
  (process.env.DEBUG_PROXY || '').toLowerCase(),
)

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        proxyTimeout: 3600000,
        timeout: 3600000,
        secure: false,
        ws: false,
        configure: (proxy) => {
          proxy.on('error', (err, _req, _res) => {
            console.error('Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            if (DEBUG_PROXY) console.log('Proxying request to:', req.url);
          });
        }
      }
    }
  }
})
