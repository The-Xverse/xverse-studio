import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";

// Explicitly owned native Autoverse execution, never generic fixture collection.
export default defineConfig({
  ...core,
  testDir: ".",
  testMatch: "autoverse-reconnect.spec.ts",
  timeout: 180000,
});
