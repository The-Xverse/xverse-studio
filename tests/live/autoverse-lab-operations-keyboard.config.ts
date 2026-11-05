import { defineConfig } from "@playwright/test";
import recorded from "./autoverse-recorded-payloads.config";
export default defineConfig({
  ...recorded,
  testDir: "../e2e",
  testMatch: [
    "lab-reservations.spec.ts",
    "lab-keyboard-fields.spec.ts",
    "lab-probes.spec.ts",
    "lab-probes-configured.spec.ts",
    "lab-probes-recovery.spec.ts",
  ],
});
