# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: draft-run-isolation.spec.ts >> draft/run isolation: graph undo and redo are new revisions that never change the running snapshot
- Location: tests/e2e/draft-run-isolation.spec.ts:71:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: "20"
Received: "12"

Call Log:
- Timeout 10000ms exceeded while waiting on the predicate
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
      - generic [ref=f1e52]:
        - text: Undid a graph edit as new revision 5. Earlier revisions and run snapshots are unchanged.
        - button "Dismiss notice" [ref=f1e56] [cursor=pointer]
      - generic [ref=f1e59]:
        - generic [ref=f1e60]:
          - generic [ref=f1e61]:
            - button "Workspace" [ref=f1e62] [cursor=pointer]
            - generic [ref=f1e65]: System
          - generic [ref=f1e66]:
            - heading "Undo redo isolation" [level=1] [ref=f1e73]
            - generic [ref=f1e74]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e75]: Process control terms
            - generic [ref=f1e78]: rev 5
        - generic [ref=f1e79]:
          - 'button "Dependencies: none unresolved" [ref=f1e80] [cursor=pointer]': Dependencies
          - button "Undo" [ref=f1e81] [cursor=pointer]
          - button "Redo" [ref=f1e82] [cursor=pointer]
          - button "Export" [ref=f1e83] [cursor=pointer]
          - button "Validate" [ref=f1e86] [cursor=pointer]
          - button "Preflight & run" [ref=f1e89] [cursor=pointer]
      - tablist "System workflows" [ref=f1e92]:
        - tab "Model" [selected] [ref=f1e93] [cursor=pointer]
        - tab "Connections" [ref=f1e99] [cursor=pointer]
        - tab "Deployment" [ref=f1e104] [cursor=pointer]
        - tab "Experiments" [ref=f1e107] [cursor=pointer]
        - tab "Results 1" [ref=f1e110] [cursor=pointer]:
          - text: Results
          - generic [ref=f1e113]: "1"
        - button "XDL source" [ref=f1e115] [cursor=pointer]
      - generic [ref=f1e118]:
        - generic [ref=f1e119]:
          - text: Draft revision
          - code [ref=f1e121]: "5"
        - generic [ref=f1e122]: 3 elements · 2 connections
        - generic [ref=f1e123]:
          - text: Run snapshot
          - code [ref=f1e124]: snap-ee0e7b9
          - generic [ref=f1e125]: running
          - button "Draft differs from run inputs (1 document, 0 elements, 1 parameter)" [ref=f1e126] [cursor=pointer]
      - generic [ref=f1e127]:
        - complementary "Structured model navigation" [ref=f1e128]:
          - generic [ref=f1e129]:
            - heading "Process explorer" [level=2] [ref=f1e130]
            - button "View XDL source" [ref=f1e131] [cursor=pointer]
          - textbox "Search elements" [ref=f1e138]:
            - /placeholder: Find an element…
          - generic [ref=f1e139]:
            - strong [ref=f1e145]: reference-loop
            - generic [ref=f1e146]: "3"
            - button "Group by node" [ref=f1e147] [cursor=pointer]
          - generic [ref=f1e148]:
            - button "controller controller" [ref=f1e149] [cursor=pointer]:
              - generic [ref=f1e155]: controller
              - generic [ref=f1e156]: controller
            - button "plant plant" [ref=f1e157] [cursor=pointer]:
              - generic [ref=f1e163]: plant
              - generic [ref=f1e164]: plant
            - button "observer-node observer" [ref=f1e165] [cursor=pointer]:
              - generic [ref=f1e168]: observer-node
              - generic [ref=f1e169]: observer
          - generic [ref=f1e170]:
            - generic [ref=f1e171]: RESOURCES
            - button "reference-controller Component" [ref=f1e172] [cursor=pointer]:
              - generic [ref=f1e175]: reference-controller
              - generic [ref=f1e176]: Component
            - button "reference-plant Component" [ref=f1e177] [cursor=pointer]:
              - generic [ref=f1e180]: reference-plant
              - generic [ref=f1e181]: Component
            - button "reference-loop System" [ref=f1e182] [cursor=pointer]:
              - generic [ref=f1e185]: reference-loop
              - generic [ref=f1e186]: System
            - button "local-reference Deployment" [ref=f1e187] [cursor=pointer]:
              - generic [ref=f1e190]: local-reference
              - generic [ref=f1e191]: Deployment
            - button "reference-response Scenario" [ref=f1e192] [cursor=pointer]:
              - generic [ref=f1e195]: reference-response
              - generic [ref=f1e196]: Scenario
            - button "experiment-lite Profile" [ref=f1e197] [cursor=pointer]:
              - generic [ref=f1e200]: experiment-lite
              - generic [ref=f1e201]: Profile
            - button "studio-experiments Profile" [ref=f1e202] [cursor=pointer]:
              - generic [ref=f1e205]: studio-experiments
              - generic [ref=f1e206]: Profile
          - button "Add element" [ref=f1e208] [cursor=pointer]
        - region "Model canvas" [ref=f1e211]:
          - generic:
            - generic [ref=f1e212]:
              - generic [ref=f1e213]: LOGICAL MODEL
              - generic [ref=f1e214]: 1.0.0
            - generic [ref=f1e215]:
              - button "Table view" [ref=f1e216] [cursor=pointer]
              - button "Auto layout" [ref=f1e217] [cursor=pointer]
              - button "Save layout" [ref=f1e218] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e219]:
            - generic [ref=f1e221]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e222] [cursor=pointer]:
                      - generic [ref=f1e225]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e227] [cursor=pointer]:
                      - generic [ref=f1e230]: state-flow
                - generic:
                  - group [ref=f1e232]:
                    - generic [ref=f1e233]:
                      - generic [ref=f1e235]: controller
                      - strong [ref=f1e244]: controller
                      - code [ref=f1e245]: controller
                      - list "Named ports" [ref=f1e246]:
                        - listitem [ref=f1e247]:
                          - generic [aria-hidden] [ref=f1e248]: ←
                          - code [ref=f1e249]: controller-out
                          - generic [ref=f1e250]: output
                      - generic [ref=f1e251]:
                        - generic [ref=f1e252]: Logical element
                        - generic [ref=f1e253]: 1 ports
                  - group [ref=f1e255]:
                    - generic [ref=f1e256]:
                      - generic [ref=f1e258]: plant
                      - strong [ref=f1e267]: plant
                      - code [ref=f1e268]: plant
                      - list "Named ports" [ref=f1e269]:
                        - listitem [ref=f1e270]:
                          - generic [aria-hidden] [ref=f1e271]: →
                          - code [ref=f1e272]: plant-in
                          - generic [ref=f1e273]: input
                        - listitem [ref=f1e274]:
                          - generic [aria-hidden] [ref=f1e275]: ←
                          - code [ref=f1e276]: plant-out
                          - generic [ref=f1e277]: output
                      - generic [ref=f1e278]:
                        - generic [ref=f1e279]: Logical element
                        - generic [ref=f1e280]: 2 ports
                  - group [ref=f1e282]:
                    - generic [ref=f1e283]:
                      - generic [ref=f1e285]: observer
                      - strong [ref=f1e291]: observer-node
                      - code [ref=f1e292]: observer-node
                      - list "Named ports" [ref=f1e293]:
                        - listitem [ref=f1e294]:
                          - generic [aria-hidden] [ref=f1e295]: →
                          - code [ref=f1e296]: observer-in
                          - generic [ref=f1e297]: input
                      - generic [ref=f1e298]:
                        - generic [ref=f1e299]: Logical element
                        - generic [ref=f1e300]: 1 ports
            - generic "Control Panel" [ref=f1e302]:
              - button "Zoom In" [ref=f1e303] [cursor=pointer]
              - button "Zoom Out" [ref=f1e306] [cursor=pointer]
              - button "Fit View" [ref=f1e309] [cursor=pointer]
            - img "Mini Map" [ref=f1e313]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e318]:
          - heading "Element inspector" [level=2] [ref=f1e320]
          - generic [ref=f1e326]:
            - heading "plant" [level=3] [ref=f1e333]
            - paragraph [ref=f1e334]: plant
            - generic [ref=f1e335]: Logical identity
          - navigation "Model location" [ref=f1e336]:
            - button "reference-loop" [ref=f1e337] [cursor=pointer]
            - generic [aria-hidden] [ref=f1e338]: ›
            - button "plant-node" [ref=f1e339] [cursor=pointer]
            - generic [aria-hidden] [ref=f1e340]: ›
            - generic [ref=f1e341]: plant
          - generic [ref=f1e342]:
            - button "Properties" [ref=f1e343] [cursor=pointer]
            - button "Parameters" [ref=f1e344] [cursor=pointer]
          - group [ref=f1e347]:
            - generic [ref=f1e348]:
              - generic [ref=f1e349]:
                - text: Target
                - generic [ref=f1e350]: "1"
                - spinbutton "Target 1" [ref=f1e351]: "1"
              - paragraph [ref=f1e352]: Normalized reference setpoint, dimensionless.
              - generic [ref=f1e353]:
                - generic [ref=f1e354]: Scenario XDL extension · default 1
                - button "Apply" [disabled] [ref=f1e355]
            - generic [ref=f1e356]:
              - generic [ref=f1e357]:
                - text: Response gain
                - generic [ref=f1e358]: "1"
                - spinbutton "Response gain 1" [ref=f1e359]: "0.8"
              - paragraph [ref=f1e360]: First-order response coefficient; gain × timestep must be at most one.
              - generic [ref=f1e361]:
                - generic [ref=f1e362]: Scenario XDL extension · default 0.8
                - button "Apply" [disabled] [ref=f1e363]
            - generic [ref=f1e364]:
              - generic [ref=f1e365]:
                - text: Initial state
                - generic [ref=f1e366]: "1"
                - spinbutton "Initial state 1" [ref=f1e367]: "0"
              - paragraph [ref=f1e368]: Initial normalized scalar state.
              - generic [ref=f1e369]:
                - generic [ref=f1e370]: Scenario XDL extension · default 0
                - button "Apply" [disabled] [ref=f1e371]
            - generic [ref=f1e372]:
              - generic [ref=f1e373]:
                - text: Duration
                - generic [ref=f1e374]: s
                - spinbutton "Duration s" [active] [ref=f1e375]: "12"
              - paragraph [ref=f1e376]: Requested simulation horizon, in seconds; at most 3,000 samples.
              - generic [ref=f1e377]:
                - generic [ref=f1e378]: Scenario XDL extension · default 5
                - button "Apply" [disabled] [ref=f1e379]
            - generic [ref=f1e380]:
              - generic [ref=f1e381]:
                - text: Time step
                - generic [ref=f1e382]: s
                - spinbutton "Time step s" [ref=f1e383]: "0.1"
              - paragraph [ref=f1e384]: Fixed simulation step in seconds. Duration must be an integer number of steps.
              - generic [ref=f1e385]:
                - generic [ref=f1e386]: Scenario XDL extension · default 0.1
                - button "Apply" [disabled] [ref=f1e387]
            - generic [ref=f1e388]:
              - generic [ref=f1e389]:
                - text: Reference fault
                - generic [ref=f1e390]: "1"
                - combobox "Reference fault 1" [ref=f1e391]:
                  - option "none" [selected]
                  - option "stuck-sensor"
              - paragraph [ref=f1e392]: Owned model fault only; stuck-sensor freezes the reported observation.
              - generic [ref=f1e393]:
                - generic [ref=f1e394]: Scenario XDL extension · default none
                - button "Apply" [disabled] [ref=f1e395]
          - generic [ref=f1e396]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e401]:
        - generic [ref=f1e402]: Local project · Saved on backend
        - generic [ref=f1e405]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e406]: 1 provider(s) available
```

# Test source

```ts
  27  |         body: JSON.stringify({
  28  |           baseRevision: project.revision,
  29  |           edits: [
  30  |             { kind: "set_parameter", parameterId: "duration", value: duration },
  31  |           ],
  32  |         }),
  33  |       });
  34  |       if (!r.ok) throw Error(await r.text());
  35  |       project = await r.json();
  36  |       localStorage.setItem("studio.projectId", project.projectId);
  37  |       return project;
  38  |     },
  39  |     { name, duration },
  40  |   );
  41  | }
  42  | async function readProject(page: Page, projectId: string) {
  43  |   return page.request
  44  |     .get(`/api/v1/projects/${projectId}`)
  45  |     .then((r) => r.json());
  46  | }
  47  | function parameter(project: any, id: string) {
  48  |   const scenario = Object.values(project.documents).find((d: any) =>
  49  |     d.content.includes("kind: Scenario"),
  50  |   ) as any;
  51  |   const match = scenario.content.match(
  52  |     new RegExp(`- id: ${id}\\n(?:\\s+.*\\n)*?\\s+value: ([^\\n]+)`),
  53  |   );
  54  |   return match?.[1];
  55  | }
  56  | async function applyDuration(page: Page, value: string) {
  57  |   await page.getByRole("tab", { name: /Model/ }).click();
  58  |   await page.getByRole("button", { name: "plant plant" }).click();
  59  |   await page.getByRole("button", { name: "Parameters", exact: true }).click();
  60  |   await page.getByLabel("Duration").fill(value);
  61  |   await page
  62  |     .getByLabel("Duration")
  63  |     .locator("xpath=ancestor::form")
  64  |     .getByRole("button", { name: "Apply", exact: true })
  65  |     .click();
  66  |   await expect(
  67  |     page.getByText("Draft saved. Existing run snapshots remain unchanged."),
  68  |   ).toBeVisible();
  69  | }
  70  |
  71  | test("draft/run isolation: graph undo and redo are new revisions that never change the running snapshot", async ({
  72  |   page,
  73  |   context,
  74  | }, testInfo) => {
  75  |   test.setTimeout(90000);
  76  |   await connectStudio(page, testInfo);
  77  |   const project = await makeProject(page, "Undo redo isolation", 20);
  78  |   await page.reload();
  79  |   await page
  80  |     .getByRole("button", { name: "Preflight & run", exact: true })
  81  |     .click();
  82  |   await page
  83  |     .getByRole("button", { name: "Start frozen snapshot", exact: true })
  84  |     .click();
  85  |   await expect(
  86  |     page.getByRole("heading", { name: /Run results/ }),
  87  |   ).toContainText("running", { timeout: 15000 });
  88  |   const runId = (await page.evaluate(() =>
  89  |     localStorage.getItem("studio.lastRun"),
  90  |   ))!;
  91  |   const run = await page.request
  92  |     .get(`/api/v1/runs/${runId}`)
  93  |     .then((r) => r.json());
  94  |   const snapshotFile = path.join(
  95  |       data(),
  96  |       "snapshots",
  97  |       run.snapshotId,
  98  |       "snapshot.json",
  99  |     ),
  100 |     sha = () =>
  101 |       createHash("sha256").update(readFileSync(snapshotFile)).digest("hex"),
  102 |     snapshotBefore = sha();
  103 |   const starts: string[] = [];
  104 |   page.on("request", (r) => {
  105 |     if (r.method() === "POST" && new URL(r.url()).pathname === "/api/v1/runs")
  106 |       starts.push(r.url());
  107 |   });
  108 |   await applyDuration(page, "12");
  109 |   await applyDuration(page, "8");
  110 |   const undo = page.getByRole("button", { name: "Undo", exact: true }),
  111 |     redo = page.getByRole("button", { name: "Redo", exact: true });
  112 |   await expect(redo).toBeDisabled();
  113 |   await undo.click();
  114 |   await expect(
  115 |     page.getByText(/Undid a graph edit as new revision/),
  116 |   ).toBeVisible();
  117 |   let current = await readProject(page, project.projectId);
  118 |   expect(parameter(current, "duration")).toBe("12");
  119 |   // Keyboard undo applies outside text fields.
  120 |   await page.locator(".project-header h1").click();
  121 |   await expect(undo).toBeEnabled();
  122 |   await page.keyboard.press("Control+z");
  123 |   await expect
  124 |     .poll(async () =>
  125 |       parameter(await readProject(page, project.projectId), "duration"),
  126 |     )
> 127 |     .toBe("20");
      |      ^ Error: expect(received).toBe(expected) // Object.is equality
  128 |   // A shortcut is ignored while another action is busy; wait as a user would.
  129 |   await expect(redo).toBeEnabled();
  130 |   await page.keyboard.press("Control+Shift+z");
  131 |   await expect
  132 |     .poll(async () =>
  133 |       parameter(await readProject(page, project.projectId), "duration"),
  134 |     )
  135 |     .toBe("12");
  136 |   current = await readProject(page, project.projectId);
  137 |   const history = await page.request
  138 |     .get(`/api/v1/projects/${project.projectId}/revisions`)
  139 |     .then((r) => r.json());
  140 |   expect(history.items[0].revision).toBe(current.revision);
  141 |   expect(history.items[0].origin.kind).toBe("restore");
  142 |   expect(history.items.length).toBe(current.revision);
  143 |   // The active run keeps its frozen inputs while the draft moves on.
  144 |   expect(sha()).toBe(snapshotBefore);
  145 |   const frozen = await page.request
  146 |     .get(`/api/v1/runs/${runId}/snapshot`)
  147 |     .then((r) => r.json());
  148 |   expect(frozen.snapshot.revision).toBe(project.revision);
  149 |   expect(starts).toEqual([]);
  150 |   // A change from another tab makes this tab's next step a conflict, never an overwrite.
  151 |   const other = await context.newPage();
  152 |   await other.goto("/");
  153 |   await other.evaluate(
  154 |     async ({ projectId, revision }) => {
  155 |       const { csrfToken } = await fetch("/api/v1/session").then((r) =>
  156 |         r.json(),
  157 |       );
  158 |       const r = await fetch(`/api/v1/projects/${projectId}/edits`, {
  159 |         method: "POST",
  160 |         headers: {
  161 |           "Content-Type": "application/json",
  162 |           "X-CSRF-Token": csrfToken,
  163 |           "If-Match": String(revision),
  164 |         },
  165 |         body: JSON.stringify({
  166 |           baseRevision: revision,
  167 |           edits: [{ kind: "set_parameter", parameterId: "gain", value: 0.5 }],
  168 |         }),
  169 |       });
  170 |       if (!r.ok) throw Error(await r.text());
  171 |     },
  172 |     { projectId: project.projectId, revision: current.revision },
  173 |   );
  174 |   await other.close();
  175 |   await undo.click();
  176 |   await expect(page.getByRole("alert")).toContainText("REVISION_CONFLICT");
  177 |   const after = await readProject(page, project.projectId);
  178 |   expect(after.revision).toBe(current.revision + 1);
  179 |   expect(parameter(after, "gain")).toBe("0.5");
  180 |   expect(sha()).toBe(snapshotBefore);
  181 |   await page.screenshot({
  182 |     path: testInfo.outputPath("undo-redo-isolation.png"),
  183 |   });
  184 | });
  185 |
  186 | test("draft/run isolation: externally modified sources are preserved before an explicit recovery", async ({
  187 |   page,
  188 | }, testInfo) => {
  189 |   test.setTimeout(60000);
  190 |   await connectStudio(page, testInfo);
  191 |   const project = await makeProject(page, "External source recovery", 5);
  192 |   const [documentId, document] = Object.entries(project.documents).find(
  193 |     ([, d]: any) => d.path.endsWith("/plant.xdl.yaml"),
  194 |   ) as [string, any];
  195 |   const file = path.join(
  196 |     data(),
  197 |     "projects",
  198 |     project.projectId,
  199 |     "revisions",
  200 |     String(project.revision),
  201 |     document.path,
  202 |   );
  203 |   const external = document.content.replace(
  204 |     "Studio-owned reference fixture.",
  205 |     "Edited outside Studio.",
  206 |   );
  207 |   writeFileSync(file, external);
  208 |   await page.reload();
  209 |   const notice = page
  210 |     .getByRole("alert")
  211 |     .filter({ hasText: "Source files changed outside Studio" });
  212 |   await expect(notice).toBeVisible();
  213 |   await notice
  214 |     .getByRole("button", {
  215 |       name: "Adopt external changes as a new revision",
  216 |       exact: true,
  217 |     })
  218 |     .click();
  219 |   await expect(page.getByText(/Recovered as revision \d+/)).toBeVisible();
  220 |   await expect(notice).toHaveCount(0);
  221 |   const recovered = await readProject(page, project.projectId);
  222 |   expect(recovered.sourceIntegrity).toBe("intact");
  223 |   expect(recovered.revision).toBe(project.revision + 1);
  224 |   expect(recovered.documents[documentId].content).toBe(external);
  225 |   const backups = await page.request
  226 |     .get(`/api/v1/projects/${project.projectId}/recoveries`)
  227 |     .then((r) => r.json());
```
