import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";
export default defineConfig({ ...core, testDir: ".", testMatch: process.env.STUDIO_AUTOVERSE_BROWSER_STAGE === "timeline" ? "autoverse-fault-timeline.spec.ts" : "autoverse-fault-authoring.spec.ts", timeout: 180000 });
