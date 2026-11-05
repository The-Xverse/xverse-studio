import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";
export default defineConfig({
  ...core,
  testDir: ".",
  testMatch: "autoverse-comparison.spec.ts",
  timeout: 180000,
  globalSetup: "./recorded-browser-device-setup.ts",
  use: {
    ...core.use,
    ...(process.env.STUDIO_BROWSER_CPU_ONLY === "1"
      ? { launchOptions: { args: ["--disable-gpu", "--disable-gpu-rasterization"] } }
      : {}),
  },
});
