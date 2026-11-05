import { defineConfig } from "@playwright/test";
import core from "./autoverse-recorded-payloads.config";
export default defineConfig({
  ...core,
  testDir: ".",
  testMatch: "autoverse-assessments.spec.ts",
});
