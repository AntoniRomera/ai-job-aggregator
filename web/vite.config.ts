/// <reference types="vitest/config" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Tailwind v4 is config-less: the plugin reads the single `@import "tailwindcss"`
// in src/index.css and the @theme block there. No tailwind.config.js / postcss.
export default defineConfig({
  // "/" for local dev; the GitHub Pages demo build sets BASE_PATH=/ai-job-aggregator/.
  base: process.env.BASE_PATH || "/",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
