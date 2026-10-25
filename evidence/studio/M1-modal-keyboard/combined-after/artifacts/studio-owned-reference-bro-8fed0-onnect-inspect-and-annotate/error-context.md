# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: studio.spec.ts >> owned reference browser workflow: author, preflight, execute, reconnect, inspect and annotate
- Location: tests/e2e/studio.spec.ts:7:5

# Error details

```
TimeoutError: locator.click: Timeout 15000ms exceeded.
Call log:
  - waiting for getByLabel('Duration').locator('xpath=ancestor::form').getByRole('button', { name: 'Apply', exact: true })
    - locator resolved to <button class="small-button">Apply</button>
  - attempting click action
    - waiting for element to be visible, enabled and stable
    - element is visible, enabled and stable
    - scrolling into view if needed
    - done scrolling
    - performing click action

```

# Test source

```ts
  1   | import { test, expect } from "@playwright/test";
  2   | import { connectStudio } from "./connect-studio";
  3   | import { measureModel } from "../performance/browser-model";
  4   | import { measureHistory } from "../performance/browser-history";
  5   | import { exerciseComposition } from "./composition-flow";
  6   | import { exerciseFrozenRerun } from "./frozen-rerun-flow";
  7   | test("owned reference browser workflow: author, preflight, execute, reconnect, inspect and annotate", async ({
  8   |   page,
  9   | }, testInfo) => {
  10  |   test.setTimeout(240000);
  11  |   const errors: string[] = [];
  12  |   page.on("pageerror", (e) => errors.push(e.message));
  13  |   await connectStudio(page, testInfo);
  14  |   await page.screenshot({
  15  |     path: testInfo.outputPath("home.png"),
  16  |     fullPage: true,
  17  |   });
  18  |   await page
  19  |     .locator(".example-grid")
  20  |     .getByRole("button", { name: /Process control reference/ })
  21  |     .click();
  22  |   await expect(
  23  |     page.getByRole("heading", {
  24  |       name: "Process control reference",
  25  |       exact: true,
  26  |     }),
  27  |   ).toBeVisible();
  28  |   await expect(page.getByRole("button", { name: "plant plant" })).toBeVisible();
  29  |   await page.getByRole("button", { name: "plant plant" }).click();
  30  |   await expect(page.locator(".inspector .key-values")).toContainText(
  31  |     "reference-response",
  32  |   );
  33  |   await expect(
  34  |     page.getByRole("heading", { name: "Element inspector" }),
  35  |   ).toBeVisible();
  36  |   await page.getByRole("button", { name: "Parameters", exact: true }).click();
  37  |   await page.getByLabel("Duration").fill("1");
  38  |   await page
  39  |     .getByLabel("Duration")
  40  |     .locator("xpath=ancestor::form")
  41  |     .getByRole("button", { name: "Apply", exact: true })
> 42  |     .click();
      |      ^ TimeoutError: locator.click: Timeout 15000ms exceeded.
  43  |   await expect(
  44  |     page.getByText("Draft saved. Existing run snapshots remain unchanged."),
  45  |   ).toBeVisible();
  46  |   await page.getByRole("button", { name: "Validate", exact: true }).click();
  47  |   await expect(
  48  |     page.getByText("Authoritative platform validation passed.", {
  49  |       exact: false,
  50  |     }),
  51  |   ).toBeVisible();
  52  |   await page.screenshot({
  53  |     path: testInfo.outputPath("model.png"),
  54  |     fullPage: true,
  55  |   });
  56  |   await page.getByRole("button", { name: "Table view", exact: true }).click();
  57  |   await expect(
  58  |     page.getByRole("table").getByRole("button", { name: "plant", exact: true }),
  59  |   ).toBeVisible();
  60  |   await page.getByRole("button", { name: "Graph view", exact: true }).click();
  61  |   await page.getByRole("tab", { name: "Connections", exact: true }).click();
  62  |   await expect(
  63  |     page.getByRole("heading", { name: "Endpoint contracts" }),
  64  |   ).toBeVisible();
  65  |   await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  66  |   await expect(
  67  |     page.getByRole("heading", { name: "Inspect and update a binding" }),
  68  |   ).toBeVisible();
  69  |   await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  70  |   await expect(
  71  |     page.getByRole("heading", { name: "Scheduled actions" }),
  72  |   ).toBeVisible();
  73  |   await page.getByRole("button", { name: "XDL source", exact: true }).click();
  74  |   await page
  75  |     .getByRole("combobox", { name: "Resource", exact: true })
  76  |     .selectOption({ index: 0 });
  77  |   const before = await page
  78  |     .getByLabel("XDL source", { exact: true })
  79  |     .inputValue();
  80  |   await page
  81  |     .getByLabel("XDL source", { exact: true })
  82  |     .fill(before + "\n# Browser round-trip verification\n");
  83  |   await page
  84  |     .getByRole("button", { name: "Compare changes", exact: true })
  85  |     .click();
  86  |   await expect(page.getByText("Edited draft", { exact: true })).toBeVisible();
  87  |   await page
  88  |     .getByRole("button", { name: "Save source revision", exact: true })
  89  |     .click();
  90  |   await expect(page.getByText("Saved revision", { exact: true })).toBeVisible();
  91  |   await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  92  |   await page
  93  |     .getByRole("button", { name: "Preflight & run", exact: true })
  94  |     .click();
  95  |   await expect(
  96  |     page.getByRole("heading", { name: "Execution preflight" }),
  97  |   ).toBeVisible();
  98  |   await expect(
  99  |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  100 |   ).toBeEnabled();
  101 |   await page
  102 |     .getByRole("button", { name: "Start frozen snapshot", exact: true })
  103 |     .click();
  104 |   await expect(
  105 |     page.getByRole("heading", { name: /Run results/ }),
  106 |   ).toBeVisible();
  107 |   await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
  108 |     timeout: 20000,
  109 |   });
  110 |   const runIds = await page.evaluate(() =>
  111 |     localStorage.getItem("studio.lastRun"),
  112 |   );
  113 |   expect(runIds).toBeTruthy();
  114 |   await page.reload();
  115 |   await expect(
  116 |     page.getByRole("heading", {
  117 |       name: "Process control reference",
  118 |       exact: true,
  119 |     }),
  120 |   ).toBeVisible();
  121 |   await page.getByRole("tab", { name: "Results", exact: false }).click();
  122 |   await expect(page.getByText(runIds!, { exact: true }).first()).toBeVisible();
  123 |   await page.getByRole("button", { name: "Refresh", exact: true }).click();
  124 |   await expect(
  125 |     page.getByRole("img", { name: /Recorded observation chart/ }),
  126 |   ).toBeVisible();
  127 |   await page.screenshot({
  128 |     path: testInfo.outputPath("results.png"),
  129 |     fullPage: true,
  130 |   });
  131 |   await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  132 |   await expect(
  133 |     page.getByRole("heading", { name: "Events and permitted logs" }),
  134 |   ).toBeVisible();
  135 |   await page.getByRole("tab", { name: "Annotations", exact: true }).click();
  136 |   await page
  137 |     .getByLabel("Comment", { exact: true })
  138 |     .fill("Browser verification note; separate from immutable evidence.");
  139 |   await page
  140 |     .getByRole("button", { name: "Save separate annotation", exact: true })
  141 |     .click();
  142 |   await expect(
```
