import { defineConfig } from 'vite';

export default defineConfig({
  base: '/carnage3d-typescript-port/',
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
  "build": {
    target: "es2022",
  },
});
