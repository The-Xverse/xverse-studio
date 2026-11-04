import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";
export default defineConfig({ ...core, testDir: ".", testMatch: "autoverse-performance.spec.ts", timeout: 600000 });
