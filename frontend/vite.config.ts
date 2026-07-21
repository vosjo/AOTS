import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig(({ command }) => ({
  plugins: [vue(), tailwindcss()],
  // Dev server: same URL layout as production (/w/…). Production assets: /static/dist/.
  base: command === 'serve' ? '/' : '/static/dist/',
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  build: {
    outDir: '../site_static/dist',
    emptyOutDir: true,
    // Content hashes prevent stale chunk mixes after deploy (cached index.js + new
    // DashboardView.js caused cryptic runtime errors like undefined.join).
    manifest: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/accounts': 'http://127.0.0.1:8000',
      '/users': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000',
      '/django-admin': 'http://127.0.0.1:8000',
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
}))
