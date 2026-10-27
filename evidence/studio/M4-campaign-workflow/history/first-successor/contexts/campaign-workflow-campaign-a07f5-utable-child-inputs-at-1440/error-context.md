# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: campaign-workflow.spec.ts >> campaign workflow: authoritative budgets, scheduling and immutable child inputs at 1440
- Location: tests/e2e/campaign-workflow.spec.ts:77:7

# Error details

```
TimeoutError: locator.selectOption: Timeout 15000ms exceeded.
Call log:
  - waiting for getByLabel('Stop policy', { exact: true })

```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - link "Skip to workspace" [ref=f1e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f1e5]:
    - button "X-Verse Studio home" [ref=f1e6] [cursor=pointer]:
      - generic [ref=f1e7]: X
      - generic [ref=f1e8]: X-VERSE STUDIO
    - generic [ref=f1e10]: Local workspace
    - generic [ref=f1e12]: REFERENCE PREVIEW
    - button "Environment" [ref=f1e13] [cursor=pointer]
    - generic "Local operator" [ref=f1e20]: LO
  - generic [ref=f1e21]:
    - navigation "Main navigation" [ref=f1e22]:
      - button "Workspace" [ref=f1e23] [cursor=pointer]
      - button "Catalog" [ref=f1e30] [cursor=pointer]
      - button "Laboratory" [ref=f1e37] [cursor=pointer]:
        - generic [ref=f1e41]: Lab
      - button "Compatibility and environment" [ref=f1e42] [cursor=pointer]:
        - generic [ref=f1e48]: Settings
      - generic [ref=f1e49]: v0.1
    - main [ref=f1e50]:
      - generic [ref=f1e51]:
        - generic [ref=f1e52]:
          - generic [ref=f1e53]:
            - button "Workspace" [ref=f1e54] [cursor=pointer]
            - generic [ref=f1e57]: System
          - generic [ref=f1e58]:
            - heading "Owned campaign history 1440" [level=1] [ref=f1e65]
            - generic [ref=f1e66]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e67]: Process control terms
            - generic [ref=f1e70]: rev 2
        - generic [ref=f1e71]:
          - 'button "Dependencies: none unresolved" [ref=f1e72] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e73]
          - button "Redo" [disabled] [ref=f1e74]
          - button "Export" [ref=f1e75] [cursor=pointer]
          - button "Validate" [ref=f1e78] [cursor=pointer]
          - button "Preflight & run" [ref=f1e81] [cursor=pointer]
      - tablist "System workflows" [ref=f1e84]:
        - tab "Model" [ref=f1e85] [cursor=pointer]
        - tab "Connections" [ref=f1e91] [cursor=pointer]
        - tab "Deployment" [ref=f1e96] [cursor=pointer]
        - tab "Experiments" [selected] [ref=f1e99] [cursor=pointer]
        - tab "Results" [ref=f1e102] [cursor=pointer]
        - button "XDL source" [ref=f1e106] [cursor=pointer]
      - generic [ref=f1e109]:
        - generic [ref=f1e110]:
          - text: Draft revision
          - code [ref=f1e112]: "2"
        - generic [ref=f1e113]: 3 elements · 2 connections
        - generic [ref=f1e114]:
          - text: Execution scope
          - generic [ref=f1e115]: Owned reference
      - generic [ref=f1e116]:
        - generic [ref=f1e117]:
          - generic [ref=f1e118]:
            - heading "Experiments" [level=2] [ref=f1e119]
            - paragraph [ref=f1e120]: Author bounded intent, inspect actual events, and assess immutable evidence.
          - button "Edit scenario XDL" [ref=f1e121] [cursor=pointer]
        - tablist "Experiment sections" [ref=f1e124]:
          - tab "Scenario" [ref=f1e125] [cursor=pointer]
          - tab "Timeline" [ref=f1e126] [cursor=pointer]
          - tab "Assertions" [ref=f1e127] [cursor=pointer]
          - tab "Campaigns" [selected] [ref=f1e128] [cursor=pointer]
        - generic [ref=f1e129]:
          - region "Campaign planning" [ref=f1e130]:
            - heading "Bounded parameter campaign" [level=3] [ref=f1e131]
            - paragraph [ref=f1e132]: Preview exact frozen inputs before scheduling. The backend owns child admission, budgets, execution and restart reconciliation.
            - paragraph [ref=f1e133]: Only admitted numeric parameter axes are supported. Seeds and physical repetition require a separately admitted provider contract; a campaign does not promise deterministic replay.
            - generic [ref=f1e134]:
              - generic [ref=f1e135]:
                - text: Parameter matrix (JSON)
                - textbox "Parameter matrix (JSON)" [ref=f1e136]: "{\"gain\":[0.5,0.8]}"
              - generic [ref=f1e137]:
                - generic [ref=f1e138]:
                  - text: Maximum runs
                  - spinbutton "Maximum runs" [ref=f1e139]: "2"
                - generic [ref=f1e140]:
                  - text: Maximum total simulated seconds
                  - spinbutton "Maximum total simulated seconds" [active] [ref=f1e141]: "0.3"
                - generic [ref=f1e142]:
                  - text: Concurrency
                  - spinbutton "Concurrency" [ref=f1e143]: "1"
                - generic [ref=f1e144]:
                  - text: Stop policy
                  - combobox "Stop policy" [ref=f1e145]:
                    - option "Continue after a failed child" [selected]
                    - option "Stop pending children after a failure"
              - paragraph [ref=f1e146]: "Advertised limit: 32 runs; concurrency 1. Each child receives an immutable snapshot."
              - generic [ref=f1e147]:
                - button "Preview campaign" [ref=f1e148] [cursor=pointer]
                - button "Create campaign" [disabled] [ref=f1e149]
          - region "Retained campaign history" [ref=f1e150]:
            - generic [ref=f1e151]:
              - heading "Campaign history" [level=3] [ref=f1e152]
              - button "Refresh campaign history" [ref=f1e153] [cursor=pointer]
            - paragraph [ref=f1e154]: Workspace history, 20 records per page. Frozen project identities distinguish other projects. Refresh starts a new list observation; pages may change as history changes.
            - status [ref=f1e155]: History has not been read.
          - region "Selected campaign" [ref=f1e156]:
            - generic [ref=f1e157]:
              - heading "Selected campaign" [level=3] [ref=f1e158]
              - button "Refresh selected campaign" [disabled] [ref=f1e159]
            - status [ref=f1e160]: Open a retained campaign or create one after preview.
      - generic [ref=f1e161]:
        - generic [ref=f1e162]: Local project · Saved on backend
        - generic [ref=f1e165]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e166]: 1 provider(s) available
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
  77  |   test(`campaign workflow: authoritative budgets, scheduling and immutable child inputs at ${width}`, async ({
  78  |     page,
  79  |   }, info) => {
  80  |     await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
  81  |     await connectStudio(page, info);
  82  |     const { project } = await prepare(page, width);
  83  |     await page
  84  |       .getByRole("button", { name: "Preflight & run", exact: true })
  85  |       .click();
  86  |     await expect(
  87  |       page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  88  |     ).toBeEnabled();
  89  |     await page
  90  |       .getByRole("button", { name: "Back to draft", exact: true })
  91  |       .click();
  92  |     await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5,0.8]}');
  93  |     await page.getByLabel("Maximum runs", { exact: true }).fill("2");
  94  |     await page
  95  |       .getByLabel("Maximum total simulated seconds", { exact: true })
  96  |       .fill("0.3");
  97  |     await page
  98  |       .getByLabel("Stop policy", { exact: true })
> 99  |       .selectOption("stop_on_failure");
      |        ^ TimeoutError: locator.selectOption: Timeout 15000ms exceeded.
  100 |     const before = (await request(page, "/campaigns")).items.map(
  101 |       (c: any) => c.campaignId,
  102 |     );
  103 |     const preview = page.getByRole("button", {
  104 |       name: "Preview campaign",
  105 |       exact: true,
  106 |     });
  107 |     await preview.focus();
  108 |     await page.keyboard.press("Enter");
  109 |     await expect(page.getByRole("alert")).toContainText("CAMPAIGN_BUDGET");
  110 |     expect(
  111 |       (await request(page, "/campaigns")).items.map((c: any) => c.campaignId),
  112 |     ).toEqual(before);
  113 |     expect((await request(page, "/runs")).items).toEqual([]);
  114 |     await page
  115 |       .getByLabel("Maximum total simulated seconds", { exact: true })
  116 |       .fill("1");
  117 |     await preview.focus();
  118 |     await page.keyboard.press("Enter");
  119 |     await expect(
  120 |       page.getByRole("heading", {
  121 |         name: "Authoritative campaign preview",
  122 |         exact: true,
  123 |       }),
  124 |     ).toBeFocused();
  125 |     expect(
  126 |       (await request(page, "/campaigns")).items.map((c: any) => c.campaignId),
  127 |     ).toEqual(before);
  128 |     const created: any[] = [];
  129 |     page.on("request", (r) => {
  130 |       if (
  131 |         r.method() === "POST" &&
  132 |         new URL(r.url()).pathname === "/api/v1/campaigns"
  133 |       )
  134 |         created.push(r.postDataJSON());
  135 |     });
  136 |     const create = page.getByRole("button", {
  137 |       name: "Create campaign",
  138 |       exact: true,
  139 |     });
  140 |     await create.focus();
  141 |     await page.keyboard.press("Enter");
  142 |     await page.keyboard.press("Enter");
  143 |     const panel = page.getByRole("region", {
  144 |       name: "Selected campaign",
  145 |       exact: true,
  146 |     });
  147 |     await expect(
  148 |       panel.locator(".section-heading").getByText("complete", { exact: true }),
  149 |     ).toBeVisible({ timeout: 30000 });
  150 |     expect(created).toHaveLength(1);
  151 |     expect(created[0].budget).toEqual({ maxRuns: 2, maxTotalSeconds: 1 });
  152 |     expect(created[0].stopPolicy).toBe("stop_on_failure");
  153 |     const records = (await request(page, "/campaigns")).items.filter(
  154 |       (c: any) => !before.includes(c.campaignId),
  155 |     );
  156 |     expect(records).toHaveLength(1);
  157 |     const campaign = records[0];
  158 |     expect(campaign.baseInput.projectId).toBe(project.projectId);
  159 |     expect(campaign.children.map((c: any) => c.state)).toEqual([
  160 |       "stopped",
  161 |       "stopped",
  162 |     ]);
  163 |     const child = campaign.children[0];
  164 |     await panel
  165 |       .getByRole("button", {
  166 |         name: `Inspect child inputs ${child.runId}`,
  167 |         exact: true,
  168 |       })
  169 |       .focus();
  170 |     await page.keyboard.press("Enter");
  171 |     await expect(
  172 |       panel.getByRole("heading", {
  173 |         name: "Verified child inputs",
  174 |         exact: true,
  175 |       }),
  176 |     ).toBeVisible();
  177 |     const run = await request(page, `/runs/${child.runId}`);
  178 |     const snapshot = (await request(page, `/runs/${child.runId}/snapshot`))
  179 |       .snapshot;
  180 |     expect(snapshot.snapshotId).toBe(run.snapshotId);
  181 |     expect(snapshot.parentSnapshotId).toBe(campaign.baseSnapshotId);
  182 |     expect(snapshot.configuration.gain).toBe(child.parameters.gain);
  183 |     await expect(panel).toContainText(snapshot.snapshotDigest);
  184 |     expect(await request(page, `/campaigns/${campaign.campaignId}`)).toEqual(
  185 |       campaign,
  186 |     );
  187 |     expect(
  188 |       await page.evaluate(
  189 |         () => document.documentElement.scrollWidth <= innerWidth + 1,
  190 |       ),
  191 |     ).toBe(true);
  192 |     await info.attach("actual-campaign-preview-and-children", {
  193 |       contentType: "application/json",
  194 |       body: JSON.stringify({
  195 |         campaign,
  196 |         childSnapshotId: snapshot.snapshotId,
  197 |         childDigest: snapshot.snapshotDigest,
  198 |         inspectionCreatesNoChildren: true,
  199 |       }),
```
