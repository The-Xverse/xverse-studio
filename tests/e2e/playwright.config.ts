import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120000,
  expect: { timeout: 10000 },
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile:
          process.env.STUDIO_BROWSER_REPORT ||
          "test-results/browser-report.json",
      },
    ],
  ],
  outputDir: process.env.STUDIO_BROWSER_OUTPUT || "test-results/browser",
  use: {
    baseURL: process.env.STUDIO_BASE_URL || "http://127.0.0.1:8876",
    browserName: "chromium",
    actionTimeout: 15000,
    viewport: { width: 1440, height: 900 },
    trace: "off",
    screenshot: "only-on-failure",
    video: "off",
  },
});
