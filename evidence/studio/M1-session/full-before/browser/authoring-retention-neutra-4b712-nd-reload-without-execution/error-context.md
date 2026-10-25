# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: authoring-retention.spec.ts >> neutral logical assets: keyboard author, inspect, source anchor and reload without execution
- Location: tests/e2e/authoring-retention.spec.ts:5:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: 'Neutral asset authoring', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('heading', { name: 'Neutral asset authoring', exact: true }) with timeout 10000ms
  - waiting for getByRole('heading', { name: 'Neutral asset authoring', exact: true })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace REFERENCE PREVIEW
  - button "Environment"
  - text: LO
- complementary "Main navigation":
  - button "Workspace"
  - button "Catalog"
  - button "Laboratory": Lab
  - button "Compatibility and environment": Settings
  - text: v0.1
- main:
  - text: LOCAL WORKSPACE
  - heading "Build understanding. One System at a time." [level=1]
  - paragraph: Model, connect, and explore cyber-physical systems. Keep every experiment connected to its evidence.
  - button "New project"
  - button "Import project"
  - button "Import evidence"
  - button "Import evidence archive"
  - button "Import project archive"
  - heading "Start with an example" [level=2]
  - paragraph: A guided path from a model to a recorded result.
  - text: OWNED REFERENCE PROVIDER
  - button "fixture Process control reference Explore a normalized process response, tune the setpoint and compare measured reference observations. Guided example owned_reference":
    - text: fixture
    - heading "Process control reference" [level=3]
    - paragraph: Explore a normalized process response, tune the setpoint and compare measured reference observations.
    - text: Guided example owned_reference
  - button "fixture Automotive reference Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim. Guided example owned_reference":
    - text: fixture
    - heading "Automotive reference" [level=3]
    - paragraph: Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim.
    - text: Guided example owned_reference
  - paragraph: Reference runs verify Studio workflows. Their results do not establish external simulator or physical-device integration.
  - heading "Recent projects" [level=2]
  - paragraph: Continue from your last saved draft.
  - text: 1 project
  - button "Annotation context reference System workspace · rev 2 Local":
    - strong: Annotation context reference
    - text: System workspace · rev 2 Local
  - button "Review retention for project Annotation context reference": Retention
- dialog "Create a System workspace":
  - banner:
    - heading "Create a System workspace" [level=2]
    - button "Close dialog"
  - paragraph: Begin with the owned reference blueprint. You can inspect and edit its XDL before execution.
  - text: Project name
  - textbox "Project name":
    - /placeholder: My System
    - text: Neutral asset authoring
  - button "Cancel"
  - button "Create project"
```

# Test source

```ts
  1   | import { parse } from "yaml";
  2   | import { expect, type Page, type TestInfo } from "@playwright/test";
  3   | export async function exerciseNeutralAssets(page: Page, testInfo: TestInfo) {
  4   |   await page
  5   |     .getByRole("button", { name: "X-Verse Studio home", exact: true })
  6   |     .click();
  7   |   await page.getByRole("button", { name: "New project", exact: true }).focus();
  8   |   await page.keyboard.press("Enter");
  9   |   await page
  10  |     .getByLabel("Project name", { exact: true })
  11  |     .fill("Neutral asset authoring");
  12  |   await page
  13  |     .getByRole("button", { name: "Create project", exact: true })
  14  |     .focus();
  15  |   await page.keyboard.press("Enter");
  16  |   await expect(
  17  |     page.getByRole("heading", { name: "Neutral asset authoring", exact: true }),
> 18  |   ).toBeVisible();
      |     ^ Error: expect(locator).toBeVisible() failed
  19  |   const before = await page.evaluate(async () => ({
  20  |     projectId: localStorage.getItem("studio.projectId"),
  21  |     runs: (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  22  |   }));
  23  |   async function add(kind: string, id: string, configure: () => Promise<void>) {
  24  |     await page
  25  |       .getByRole("button", { name: "Add element", exact: true })
  26  |       .focus();
  27  |     await page.keyboard.press("Enter");
  28  |     await page
  29  |       .getByLabel("Element family", { exact: true })
  30  |       .selectOption("logical");
  31  |     await page
  32  |       .getByLabel("Logical asset kind", { exact: true })
  33  |       .selectOption(kind);
  34  |     await page.getByLabel("Element identifier", { exact: true }).fill(id);
  35  |     await configure();
  36  |     await page
  37  |       .getByRole("button", { name: "Add logical asset", exact: true })
  38  |       .focus();
  39  |     await page.keyboard.press("Enter");
  40  |     await expect(page.getByRole("dialog")).toHaveCount(0);
  41  |     const entry = page
  42  |       .locator(".tree-list")
  43  |       .getByRole("button", { name: `${id} ${kind}`, exact: true });
  44  |     await entry.focus();
  45  |     await page.keyboard.press("Enter");
  46  |     await expect(
  47  |       page
  48  |         .locator(".inspector")
  49  |         .getByRole("heading", { name: id, exact: true }),
  50  |     ).toBeVisible();
  51  |   }
  52  |   await add("device", "measurement-device", async () => {
  53  |     await page
  54  |       .getByLabel("Logical containing node", { exact: true })
  55  |       .selectOption("plant-node");
  56  |     await page.getByLabel("physical", { exact: true }).check();
  57  |     await page
  58  |       .getByLabel("Optional new device port", { exact: true })
  59  |       .selectOption("output");
  60  |     await page
  61  |       .getByLabel("New port identifier", { exact: true })
  62  |       .fill("measurement-out");
  63  |     await page
  64  |       .getByLabel("New port interface", { exact: true })
  65  |       .selectOption("state");
  66  |   });
  67  |   await expect(
  68  |     page.locator(".inspector").getByText("simulated", { exact: false }).first(),
  69  |   ).toBeVisible();
  70  |   await page
  71  |     .getByRole("button", { name: "Edit logical asset", exact: true })
  72  |     .focus();
  73  |   await page.keyboard.press("Enter");
  74  |   await page
  75  |     .getByLabel("Logical containing node", { exact: true })
  76  |     .selectOption("");
  77  |   await page
  78  |     .getByRole("button", { name: "Save logical asset", exact: true })
  79  |     .focus();
  80  |   await page.keyboard.press("Enter");
  81  |   await expect(page.getByRole("dialog")).toHaveCount(0);
  82  |   await expect(
  83  |     page.locator(".inspector").getByText("Unplaced", { exact: true }),
  84  |   ).toBeVisible();
  85  |   await add("sensor", "state-sensor", async () => {
  86  |     await page
  87  |       .getByLabel("Associated logical device", { exact: true })
  88  |       .selectOption("measurement-device");
  89  |     await page
  90  |       .getByLabel("Output endpoint", { exact: true })
  91  |       .selectOption("measurement-out");
  92  |   });
  93  |   await add("actuator", "command-actuator", async () => {
  94  |     await page
  95  |       .getByLabel("Associated logical device", { exact: true })
  96  |       .selectOption("measurement-device");
  97  |     await page
  98  |       .getByLabel("Controlled quantity", { exact: true })
  99  |       .fill("command");
  100 |     await page
  101 |       .getByLabel("Input endpoint", { exact: true })
  102 |       .selectOption("plant-in");
  103 |   });
  104 |   await add("model", "logical-model", async () => {
  105 |     await page
  106 |       .getByRole("group", { name: "Input interfaces", exact: true })
  107 |       .getByLabel("command", { exact: true })
  108 |       .check();
  109 |     await page
  110 |       .getByRole("group", { name: "Output interfaces", exact: true })
  111 |       .getByLabel("state", { exact: true })
  112 |       .check();
  113 |     await page
  114 |       .getByLabel("Maturity", { exact: true })
  115 |       .selectOption("architectural-target");
  116 |   });
  117 |   await page
  118 |     .getByRole("button", { name: "View selected declaration", exact: true })
```
