import { defineConfig } from "@playwright/test";
import recorded from "./autoverse-recorded-payloads.config";
export default defineConfig({
  ...recorded,
  testMatch: "autoverse-exports-keyboard.spec.ts",
});
