import { defineConfig } from "@playwright/test";
import recorded from "./autoverse-recorded-payloads.config";
export default defineConfig({
  ...recorded,
  testDir: "../e2e",
  testMatch: "lab-inventory-accessibility.spec.ts",
});
