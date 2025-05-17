import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: ['.']
    }
  },
  build: {
    outDir: 'dist',
  },
  // 👇 This is the fix
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  // 👇 This handles React Router on refresh
  base: '/',
  server: {
    historyApiFallback: true
  }
})
