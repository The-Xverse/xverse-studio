import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";
export default defineConfig({ ...core, testDir: ".", testMatch: "autoverse-comparison.spec.ts", timeout: 180000 });
