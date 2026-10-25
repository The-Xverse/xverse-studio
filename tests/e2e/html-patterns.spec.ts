import { test, expect } from "@playwright/test";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

// Browsers compile the HTML pattern attribute with the Unicode-sets ("v") flag and
// silently ignore a pattern that fails to compile, which disables client validation.
test("every HTML input pattern in the UI compiles with the Unicode-sets flag", () => {
  const root = path.resolve("apps/studio-web/src");
  const files = (readdirSync(root, { recursive: true }) as string[]).filter(
    (f) => f.endsWith(".tsx"),
  );
  const patterns: { file: string; pattern: string }[] = [];
  // Any other dynamic pattern form must be added to this check deliberately.
  for (const file of files)
    expect(
      readFileSync(path.join(root, file), "utf8").match(/pattern=\{(?!")/g),
      file,
    ).toBeNull();
  for (const file of files)
    for (const match of readFileSync(path.join(root, file), "utf8").matchAll(
      /pattern=(?:"([^"]+)"|\{"([^"]+)"\})/g,
    ))
      patterns.push({ file, pattern: match[1] ?? match[2] });
  expect(patterns.length).toBeGreaterThan(3);
  for (const { file, pattern } of patterns)
    expect(
      () => new RegExp(`^(?:${pattern})$`, "v"),
      `${file}: ${pattern}`,
    ).not.toThrow();
  const version = new RegExp(
    `^(?:${patterns.find((p) => p.file.endsWith("ArtifactRegistrationForm.tsx"))!.pattern})$`,
    "v",
  );
  expect(version.test("1.0")).toBe(false);
  expect(version.test("1.0.0-rc.1")).toBe(true);
});
