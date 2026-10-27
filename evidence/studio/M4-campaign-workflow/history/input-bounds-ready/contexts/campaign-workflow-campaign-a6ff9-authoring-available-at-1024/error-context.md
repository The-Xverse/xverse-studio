# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: campaign-workflow.spec.ts >> campaign input bounds: deep imported matrix keeps authoring available at 1024
- Location: tests/e2e/campaign-workflow.spec.ts:77:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByLabel('Parameter matrix (JSON)')
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByLabel('Parameter matrix (JSON)') with timeout 10000ms
  - waiting for getByLabel('Parameter matrix (JSON)')

```

# Test source

```ts
  1   | import { test, expect, type Page } from "@playwright/test";
  2   | import { parse, stringify } from "yaml";
  3   | import { connectStudio } from "./connect-studio";
  4   |
  5   | async function request(
  6   |   page: Page,
  7   |   path: string,
  8   |   method = "GET",
  9   |   body?: any,
  10  |   revision?: number,
  11  | ) {
  12  |   return page.evaluate(
  13  |     async ({ path, method, body, revision }) => {
  14  |       const { csrfToken } = await fetch("/api/v1/session").then((r) =>
  15  |         r.json(),
  16  |       );
  17  |       const r = await fetch("/api/v1" + path, {
  18  |         method,
  19  |         headers: {
  20  |           "Content-Type": "application/json",
  21  |           "X-CSRF-Token": csrfToken,
  22  |           ...(revision ? { "If-Match": String(revision) } : {}),
  23  |           ...(method === "POST"
  24  |             ? { "Idempotency-Key": crypto.randomUUID() }
  25  |             : {}),
  26  |         },
  27  |         ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  28  |       });
  29  |       const v = await r.json();
  30  |       if (!r.ok) throw new Error(`Owned campaign setup ${r.status} ${v.code}`);
  31  |       return v;
  32  |     },
  33  |     { path, method, body, revision },
  34  |   );
  35  | }
  36  | async function prepare(page: Page, width: number) {
  37  |   let project = await request(page, "/projects", "POST", {
  38  |     name: `Owned campaign history ${width}`,
  39  |   });
  40  |   const [docId, doc]: any = Object.entries(project.documents).find(
  41  |     ([, d]: any) => parse(d.content).kind === "Scenario",
  42  |   )!;
  43  |   const source = parse(doc.content);
  44  |   source.extensions["io.xverse.experiment"].parameters.find(
  45  |     (p: any) => p.id === "duration",
  46  |   ).value = 0.2;
  47  |   project = await request(
  48  |     page,
  49  |     `/projects/${project.projectId}/documents/${docId}`,
  50  |     "PUT",
  51  |     { content: stringify(source), format: "yaml" },
  52  |     project.revision,
  53  |   );
  54  |   const pf = await request(
  55  |     page,
  56  |     `/projects/${project.projectId}/preflights`,
  57  |     "POST",
  58  |     { revision: project.revision },
  59  |   );
  60  |   expect(pf.status).toBe("ready");
  61  |   await page.evaluate(
  62  |     ({ project, pf }) => {
  63  |       localStorage.setItem("studio.projectId", project.projectId);
  64  |       localStorage.setItem(
  65  |         "studio.selection." + project.projectId,
  66  |         JSON.stringify(pf.selection),
  67  |       );
  68  |     },
  69  |     { project, pf },
  70  |   );
  71  |   await page.reload();
  72  |   await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  73  |   await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  74  |   return { project, pf };
  75  | }
  76  | for (const width of [1024, 1440]) {
  77  |   test(`campaign input bounds: deep imported matrix keeps authoring available at ${width}`, async ({ page }, info) => {
  78  |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  79  |     await connectStudio(page, info);
  80  |     await prepare(page, width);
  81  |     await page.getByRole("button", { name: "Preflight & run", exact: true }).click();
  82  |     await expect(page.getByRole("button", { name: "Start frozen snapshot", exact: true })).toBeEnabled();
  83  |     await page.getByRole("button", { name: "Back to draft", exact: true }).click();
  84  |     const errors: string[] = [], writes: string[] = [];
  85  |     page.on("pageerror", e => errors.push(e.message));
  86  |     page.on("request", r => { if (r.method() === "POST" && /\/campaigns(?:\/preview)?$/.test(new URL(r.url()).pathname)) writes.push(r.url()); });
  87  |     const field = page.getByLabel("Parameter matrix (JSON)");
  88  |     const deep = '{"gain":[' + '['.repeat(12000) + '0' + ']'.repeat(12000) + ']}';
  89  |     expect(deep.length).toBeLessThan(32768);
  90  |     await field.fill(deep);
> 91  |     await expect(field).toBeVisible();
      |                         ^ Error: expect(locator).toBeVisible() failed
  92  |     await expect(page.getByRole("button", { name: "Create campaign", exact: true })).toBeDisabled();
  93  |     await expect(page.getByRole("button", { name: "Preview campaign", exact: true })).toBeDisabled();
  94  |     expect(errors).toEqual([]);
  95  |     expect(writes).toEqual([]);
  96  |     await field.fill('{"gain":[0.5,0.8]}');
  97  |     await expect(field).toHaveValue('{"gain":[0.5,0.8]}');
  98  |   });
  99  |   test(`campaign workflow: authoritative budgets, scheduling and immutable child inputs at ${width}`, async ({
  100 |     page,
  101 |   }, info) => {
  102 |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  103 |     await connectStudio(page, info);
  104 |     const { project } = await prepare(page, width);
  105 |     await page
  106 |       .getByRole("button", { name: "Preflight & run", exact: true })
  107 |       .click();
  108 |     await expect(
  109 |       page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  110 |     ).toBeEnabled();
  111 |     await page
  112 |       .getByRole("button", { name: "Back to draft", exact: true })
  113 |       .click();
  114 |     await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5,0.8]}');
  115 |     await page.getByLabel("Maximum runs", { exact: true }).fill("2");
  116 |     await page
  117 |       .getByLabel("Maximum total simulated seconds", { exact: true })
  118 |       .fill("0.3");
  119 |     await page
  120 |       .getByLabel("Stop policy", { exact: true })
  121 |       .selectOption("stop_on_failure");
  122 |     const before = (await request(page, "/campaigns")).items.map(
  123 |       (c: any) => c.campaignId,
  124 |     );
  125 |     const preview = page.getByRole("button", {
  126 |       name: "Preview campaign",
  127 |       exact: true,
  128 |     });
  129 |     await preview.focus();
  130 |     await page.keyboard.press("Enter");
  131 |     await expect(page.getByRole("alert")).toContainText("CAMPAIGN_BUDGET");
  132 |     expect(
  133 |       (await request(page, "/campaigns")).items.map((c: any) => c.campaignId),
  134 |     ).toEqual(before);
  135 |     expect((await request(page, "/runs")).items).toEqual([]);
  136 |     await page
  137 |       .getByLabel("Maximum total simulated seconds", { exact: true })
  138 |       .fill("1");
  139 |     await preview.focus();
  140 |     await page.keyboard.press("Enter");
  141 |     await expect(
  142 |       page.getByRole("heading", {
  143 |         name: "Authoritative campaign preview",
  144 |         exact: true,
  145 |       }),
  146 |     ).toBeFocused();
  147 |     expect(
  148 |       (await request(page, "/campaigns")).items.map((c: any) => c.campaignId),
  149 |     ).toEqual(before);
  150 |     const created: any[] = [];
  151 |     page.on("request", (r) => {
  152 |       if (
  153 |         r.method() === "POST" &&
  154 |         new URL(r.url()).pathname === "/api/v1/campaigns"
  155 |       )
  156 |         created.push(r.postDataJSON());
  157 |     });
  158 |     const create = page.getByRole("button", {
  159 |       name: "Create campaign",
  160 |       exact: true,
  161 |     });
  162 |     await create.focus();
  163 |     await page.keyboard.press("Enter");
  164 |     await page.keyboard.press("Enter");
  165 |     const panel = page.getByRole("region", {
  166 |       name: "Selected campaign",
  167 |       exact: true,
  168 |     });
  169 |     await expect(
  170 |       panel.locator(".section-heading").getByText("complete", { exact: true }),
  171 |     ).toBeVisible({ timeout: 30000 });
  172 |     expect(created).toHaveLength(1);
  173 |     expect(created[0].budget).toEqual({ maxRuns: 2, maxTotalSeconds: 1 });
  174 |     expect(created[0].stopPolicy).toBe("stop_on_failure");
  175 |     const records = (await request(page, "/campaigns")).items.filter(
  176 |       (c: any) => !before.includes(c.campaignId),
  177 |     );
  178 |     expect(records).toHaveLength(1);
  179 |     const campaign = records[0];
  180 |     expect(campaign.baseInput.projectId).toBe(project.projectId);
  181 |     expect(campaign.children.map((c: any) => c.state)).toEqual([
  182 |       "stopped",
  183 |       "stopped",
  184 |     ]);
  185 |     const child = campaign.children[0];
  186 |     await panel
  187 |       .getByRole("button", {
  188 |         name: `Inspect child inputs ${child.runId}`,
  189 |         exact: true,
  190 |       })
  191 |       .focus();
```
