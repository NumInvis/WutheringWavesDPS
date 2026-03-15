import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  base: '/WutheringWavesDPS/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    target: 'es2015',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-element': ['element-plus']
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    port: 14877,
    strictPort: true,
    host: '0.0.0.0',
    proxy: {
      '/WutheringWavesDPS/api': {
        target: 'http://localhost:14876',
        changeOrigin: true
      },
      '/WutheringWavesDPS/uploads': {
        target: 'http://localhost:14876',
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 14876,
    host: '0.0.0.0'
  }
})
