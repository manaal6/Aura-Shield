import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import path from 'path'

// Vite configuration for Aura‑Shield frontend
export default defineConfig({
  plugins: [react()],
  base: '/static/', // Serve assets relative to the FastAPI static mount
  build: {
    // Output built files directly into the FastAPI static directory, so the
    // /static mount serves the hashed assets without a copy step
    outDir: path.resolve(__dirname, '../static'),
    emptyOutDir: false,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
})
