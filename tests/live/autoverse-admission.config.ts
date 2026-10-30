import { defineConfig } from "@playwright/test";
import core from "../e2e/playwright.config";

// Explicit enrolled-demo verification. Ordinary browser collection must not
// pretend a workstation or CI host has this native installation.
export default defineConfig({ ...core, testDir: ".", testMatch: ["autoverse-admission.spec.ts", "autoverse-security.spec.ts"] });
