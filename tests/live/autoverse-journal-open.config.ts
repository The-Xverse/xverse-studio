import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";

export default defineConfig({ ...core, testDir: ".", testMatch: "autoverse-journal-open.spec.ts", timeout: 60000 });
