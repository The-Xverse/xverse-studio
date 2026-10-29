# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: source-accessibility.spec.ts >> source accessibility: native undo redo and button save at 1024x768
- Location: tests/e2e/source-accessibility.spec.ts:219:9

# Error details

```
Error: page.waitForResponse: Test ended.
```

```
Error: locator.evaluate: Test ended.
Call log:
  - waiting for getByRole('button', { name: 'Validate', exact: true })
    - locator resolved to visible <button class="button">…</button>

```

# Test source

```ts
  1   | import { test, expect, type Locator, type Page } from "@playwright/test";
  2   | import { createHash } from "node:crypto";
  3   | import { connectStudio } from "./connect-studio";
  4   | import { renderedContrast } from "./contrast";
  5   |
  6   | async function tabTo(page: Page, target: Locator) {
  7   |   await expect(target).toBeVisible();
  8   |   for (let i = 0; i < 200; i++) {
> 9   |     if (await target.evaluate((n) => document.activeElement === n)) return;
      |                      ^ Error: locator.evaluate: Test ended.
  10  |     await page.keyboard.press("Tab");
  11  |   }
  12  |   throw Error("Source control is unreachable through native Tab order");
  13  | }
  14  | async function activate(page: Page, target: Locator) {
  15  |   await tabTo(page, target);
  16  |   await page.keyboard.press("Enter");
  17  | }
  18  | async function choose(page: Page, target: Locator, value: string) {
  19  |   const enabled = await target
  20  |     .locator("option")
  21  |     .evaluateAll((nodes) =>
  22  |       nodes
  23  |         .filter((n) => !(n as HTMLOptionElement).disabled)
  24  |         .map((n) => (n as HTMLOptionElement).value),
  25  |     );
  26  |   const index = enabled.indexOf(value);
  27  |   expect(index).toBeGreaterThanOrEqual(0);
  28  |   await tabTo(page, target);
  29  |   await page.keyboard.press("Home");
  30  |   for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  31  |   await expect(target).toHaveValue(value);
  32  | }
  33  | const dialog = (page: Page) =>
  34  |   page.getByRole("dialog", { name: "Authored XDL source", exact: true });
  35  | const text = (page: Page) =>
  36  |   dialog(page).getByRole("textbox", { name: /^(XDL source|Edited draft)$/ });
  37  | const save = (page: Page) =>
  38  |   dialog(page).getByRole("button", {
  39  |     name: "Save source revision",
  40  |     exact: true,
  41  |   });
  42  | async function read(page: Page, id: string) {
  43  |   return page.request.get(`/api/v1/projects/${id}`).then((r) => r.json());
  44  | }
  45  | async function runIds(page: Page, id: string) {
  46  |   return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
  47  |     .filter((r: any) => r.projectId === id)
  48  |     .map((r: any) => r.runId)
  49  |     .sort();
  50  | }
  51  | const docId = (project: any, suffix: string): string =>
  52  |   Object.keys(project.documents).find((id) =>
  53  |     project.documents[id].path.endsWith("/" + suffix),
  54  |   )!;
  55  | const cache = (page: Page, projectId: string, id: string) =>
  56  |   page.evaluate(
  57  |     ({ projectId, id }) =>
  58  |       sessionStorage.getItem(`studio.draft.${projectId}.${id}`),
  59  |     { projectId, id },
  60  |   );
  61  | async function create(page: Page, name: string) {
  62  |   const project = await page.evaluate(async (name) => {
  63  |     const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
  64  |     const r = await fetch("/api/v1/projects", {
  65  |       method: "POST",
  66  |       headers: {
  67  |         "Content-Type": "application/json",
  68  |         "X-CSRF-Token": csrfToken,
  69  |       },
  70  |       body: JSON.stringify({ name }),
  71  |     });
  72  |     if (!r.ok) throw Error("Owned source fixture creation failed");
  73  |     const p = await r.json();
  74  |     localStorage.setItem("studio.projectId", p.projectId);
  75  |     return p;
  76  |   }, name);
  77  |   await page.reload();
  78  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  79  |   return project;
  80  | }
  81  | async function open(page: Page, id: string) {
  82  |   await activate(
  83  |     page,
  84  |     page.getByRole("button", { name: "XDL source", exact: true }),
  85  |   );
  86  |   await choose(page, dialog(page).getByLabel("Resource", { exact: true }), id);
  87  |   await expect(text(page)).toBeEnabled();
  88  | }
  89  | async function append(page: Page, comment: string) {
  90  |   await tabTo(page, text(page));
  91  |   await page.keyboard.press("ControlOrMeta+End");
  92  |   await page.keyboard.insertText(`\n# ${comment}\n`);
  93  |   return text(page).inputValue();
  94  | }
  95  | async function holdPut(page: Page, projectId: string, id: string) {
  96  |   const pattern = `**/api/v1/projects/${projectId}/documents/${id}`;
  97  |   const started = performance.now(),
  98  |     observations: Record<string, unknown>[] = [];
  99  |   const observe = (stage: string, details: Record<string, unknown> = {}) => {
  100 |     if (observations.length < 64)
  101 |       observations.push({
  102 |         stage,
  103 |         elapsedMs: Math.round(performance.now() - started),
  104 |         ...details,
  105 |       });
  106 |   };
  107 |   let release!: () => void,
  108 |     ready = false,
  109 |     seen = false,
```
