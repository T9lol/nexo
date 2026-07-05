/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Backend target for the dev proxy. Sprint 2 talks to the existing FastAPI
// app; override with VITE_API_PROXY_TARGET if it runs elsewhere.
const API_PROXY_TARGET =
  process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8002';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': { target: API_PROXY_TARGET, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    globals: false,
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
