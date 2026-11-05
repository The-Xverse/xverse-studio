import { defineConfig } from "@playwright/test";
import recorded from "./autoverse-recorded-payloads.config";
export default defineConfig({
  ...recorded,
  testMatch: "autoverse-authoring-keyboard.spec.ts",
});
