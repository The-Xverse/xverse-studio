import { defineConfig } from "@playwright/test";
import recorded from "./autoverse-recorded-payloads.config";

export default defineConfig({
  ...recorded,
  testMatch: "autoverse-diagnostic-keyboard.spec.ts",
});
