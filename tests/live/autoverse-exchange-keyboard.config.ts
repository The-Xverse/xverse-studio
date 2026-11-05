import { defineConfig } from "@playwright/test";
import core from "./autoverse-exchange.config";
export default defineConfig({ ...core, testMatch: "autoverse-exchange-keyboard.spec.ts" });
