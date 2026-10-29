import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: ".", testMatch: "autoverse.spec.ts", workers: 1, retries: 0,
  timeout: 720000, expect: { timeout: 15000 },
  reporter: [["list"], ["json", { outputFile: process.env.STUDIO_BROWSER_REPORT }]],
  outputDir: process.env.STUDIO_BROWSER_OUTPUT || "test-results/autoverse-live",
  use: { baseURL: process.env.STUDIO_BASE_URL, browserName: "chromium", headless: true,
    viewport: { width: 1440, height: 1000 }, screenshot: "only-on-failure", trace: "off", video: "off" },
});
