import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";

// Explicitly owned native Autoverse execution, never generic fixture collection.
export default defineConfig({
  ...core,
  testDir: ".",
  testMatch: process.env.STUDIO_AUTOVERSE_RECONNECT_CASE?.startsWith("session-")
    ? "autoverse-session.spec.ts" : "autoverse-reconnect.spec.ts",
  timeout: 180000,
});
