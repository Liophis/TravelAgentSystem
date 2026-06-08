import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: true,
    timeout: 60_000,
    env: {
      VITE_API_BASE_URL: process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",
      VITE_AMAP_KEY: process.env.VITE_AMAP_KEY ?? "",
    },
  },
});
