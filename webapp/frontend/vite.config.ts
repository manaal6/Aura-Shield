import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import path from 'path'

// Vite configuration for Aura‑Shield frontend
export default defineConfig({
  plugins: [react()],
  base: '/static/', // Serve assets relative to the FastAPI static mount
  build: {
    // Output built files to the FastAPI static directory
    outDir: path.resolve(__dirname, '../static/dist'),
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
})
