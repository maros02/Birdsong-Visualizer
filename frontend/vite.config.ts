import { defineConfig } from "vite";

// During `npm run dev`, proxy /api and /audio to the FastAPI backend.
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
