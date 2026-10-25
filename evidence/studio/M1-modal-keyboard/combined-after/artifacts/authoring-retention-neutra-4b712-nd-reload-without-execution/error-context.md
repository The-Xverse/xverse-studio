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
  - text: Creating project… LOCAL WORKSPACE
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
  - text: 0 projects Your projects will appear here. Explore an example to get started.
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
  - button "Create project" [disabled]
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
  12  |   const createProject = page.getByRole("button", {
  13  |     name: "Create project",
  14  |     exact: true,
  15  |   });
  16  |   await expect(createProject).toBeEnabled();
  17  |   await createProject.focus();
  18  |   await expect(createProject).toBeFocused();
  19  |   await page.keyboard.press("Enter");
  20  |   await expect(
  21  |     page.getByRole("heading", { name: "Neutral asset authoring", exact: true }),
> 22  |   ).toBeVisible();
      |     ^ Error: expect(locator).toBeVisible() failed
  23  |   const before = await page.evaluate(async () => ({
  24  |     projectId: localStorage.getItem("studio.projectId"),
  25  |     runs: (await fetch("/api/v1/runs").then((r) => r.json())).items.length,
  26  |   }));
  27  |   async function add(kind: string, id: string, configure: () => Promise<void>) {
  28  |     await page
  29  |       .getByRole("button", { name: "Add element", exact: true })
  30  |       .focus();
  31  |     await page.keyboard.press("Enter");
  32  |     await page
  33  |       .getByLabel("Element family", { exact: true })
  34  |       .selectOption("logical");
  35  |     await page
  36  |       .getByLabel("Logical asset kind", { exact: true })
  37  |       .selectOption(kind);
  38  |     await page.getByLabel("Element identifier", { exact: true }).fill(id);
  39  |     await configure();
  40  |     await page
  41  |       .getByRole("button", { name: "Add logical asset", exact: true })
  42  |       .focus();
  43  |     await page.keyboard.press("Enter");
  44  |     await expect(page.getByRole("dialog")).toHaveCount(0);
  45  |     const entry = page
  46  |       .locator(".tree-list")
  47  |       .getByRole("button", { name: `${id} ${kind}`, exact: true });
  48  |     await entry.focus();
  49  |     await page.keyboard.press("Enter");
  50  |     await expect(
  51  |       page
  52  |         .locator(".inspector")
  53  |         .getByRole("heading", { name: id, exact: true }),
  54  |     ).toBeVisible();
  55  |   }
  56  |   await add("device", "measurement-device", async () => {
  57  |     await page
  58  |       .getByLabel("Logical containing node", { exact: true })
  59  |       .selectOption("plant-node");
  60  |     await page.getByLabel("physical", { exact: true }).check();
  61  |     await page
  62  |       .getByLabel("Optional new device port", { exact: true })
  63  |       .selectOption("output");
  64  |     await page
  65  |       .getByLabel("New port identifier", { exact: true })
  66  |       .fill("measurement-out");
  67  |     await page
  68  |       .getByLabel("New port interface", { exact: true })
  69  |       .selectOption("state");
  70  |   });
  71  |   await expect(
  72  |     page.locator(".inspector").getByText("simulated", { exact: false }).first(),
  73  |   ).toBeVisible();
  74  |   await page
  75  |     .getByRole("button", { name: "Edit logical asset", exact: true })
  76  |     .focus();
  77  |   await page.keyboard.press("Enter");
  78  |   await page
  79  |     .getByLabel("Logical containing node", { exact: true })
  80  |     .selectOption("");
  81  |   await page
  82  |     .getByRole("button", { name: "Save logical asset", exact: true })
  83  |     .focus();
  84  |   await page.keyboard.press("Enter");
  85  |   await expect(page.getByRole("dialog")).toHaveCount(0);
  86  |   await expect(
  87  |     page.locator(".inspector").getByText("Unplaced", { exact: true }),
  88  |   ).toBeVisible();
  89  |   await add("sensor", "state-sensor", async () => {
  90  |     await page
  91  |       .getByLabel("Associated logical device", { exact: true })
  92  |       .selectOption("measurement-device");
  93  |     await page
  94  |       .getByLabel("Output endpoint", { exact: true })
  95  |       .selectOption("measurement-out");
  96  |   });
  97  |   await add("actuator", "command-actuator", async () => {
  98  |     await page
  99  |       .getByLabel("Associated logical device", { exact: true })
  100 |       .selectOption("measurement-device");
  101 |     await page
  102 |       .getByLabel("Controlled quantity", { exact: true })
  103 |       .fill("command");
  104 |     await page
  105 |       .getByLabel("Input endpoint", { exact: true })
  106 |       .selectOption("plant-in");
  107 |   });
  108 |   await add("model", "logical-model", async () => {
  109 |     await page
  110 |       .getByRole("group", { name: "Input interfaces", exact: true })
  111 |       .getByLabel("command", { exact: true })
  112 |       .check();
  113 |     await page
  114 |       .getByRole("group", { name: "Output interfaces", exact: true })
  115 |       .getByLabel("state", { exact: true })
  116 |       .check();
  117 |     await page
  118 |       .getByLabel("Maturity", { exact: true })
  119 |       .selectOption("architectural-target");
  120 |   });
  121 |   await page
  122 |     .getByRole("button", { name: "View selected declaration", exact: true })
```
