# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: foreign recovery preserves newer profile draft at 1440x900
- Location: tests/e2e/profile-bindings-accessibility.spec.ts:100:7

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  - 5
+ Received  + 5

  Object {
-   "checked": true,
-   "focused": true,
-   "panelCount": 1,
-   "selectionLabel": 1,
-   "storedProject": "prj-17e74bfe-c756-43eb-b10a-637577e6ccff",
+   "checked": null,
+   "focused": false,
+   "panelCount": 0,
+   "selectionLabel": 0,
+   "storedProject": "prj-e6c97ed1-b416-46ea-bf7e-436773422f96",
  }

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
        - text: Recovered as revision 2. The observed external bytes are preserved in backup rec-3f9d5384-33c4-400e-b767-84339ba07299.
        - button "Dismiss notice" [ref=f1e56] [cursor=pointer]
      - generic [ref=f1e59]:
        - generic [ref=f1e60]:
          - generic [ref=f1e61]:
            - button "Workspace" [ref=f1e62] [cursor=pointer]
            - generic [ref=f1e65]: System
          - generic [ref=f1e66]:
            - heading "Process control reference" [level=1] [ref=f1e73]
            - generic [ref=f1e74]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e75]: Process control terms
            - generic [ref=f1e78]: rev 2
        - generic [ref=f1e79]:
          - 'button "Dependencies: none unresolved" [ref=f1e80] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e81]
          - button "Redo" [disabled] [ref=f1e82]
          - button "Export" [ref=f1e83] [cursor=pointer]
          - button "Validate" [ref=f1e86] [cursor=pointer]
          - button "Preflight & run" [ref=f1e89] [cursor=pointer]
      - tablist "System workflows" [ref=f1e92]:
        - tab "Model" [selected] [ref=f1e93] [cursor=pointer]
        - tab "Connections" [ref=f1e99] [cursor=pointer]
        - tab "Deployment" [ref=f1e104] [cursor=pointer]
        - tab "Experiments" [ref=f1e107] [cursor=pointer]
        - tab "Results" [ref=f1e110] [cursor=pointer]
        - button "XDL source" [active] [ref=f1e114] [cursor=pointer]
      - generic [ref=f1e117]:
        - generic [ref=f1e118]:
          - text: Draft revision
          - code [ref=f1e120]: "2"
        - generic [ref=f1e121]: 3 elements · 2 connections
        - generic [ref=f1e122]:
          - text: Execution scope
          - generic [ref=f1e123]: Owned reference
      - generic [ref=f1e124]:
        - complementary "Structured model navigation" [ref=f1e125]:
          - generic [ref=f1e126]:
            - heading "Process explorer" [level=2] [ref=f1e127]
            - button "View XDL source" [ref=f1e128] [cursor=pointer]
          - textbox "Search elements" [ref=f1e135]:
            - /placeholder: Find an element…
          - generic [ref=f1e136]:
            - strong [ref=f1e142]: reference-loop
            - generic [ref=f1e143]: "3"
            - button "Group by node" [ref=f1e144] [cursor=pointer]
          - generic [ref=f1e145]:
            - button "controller controller" [ref=f1e146] [cursor=pointer]:
              - generic [ref=f1e152]: controller
              - generic [ref=f1e153]: controller
            - button "plant plant" [ref=f1e154] [cursor=pointer]:
              - generic [ref=f1e160]: plant
              - generic [ref=f1e161]: plant
            - button "observer-node observer" [ref=f1e162] [cursor=pointer]:
              - generic [ref=f1e165]: observer-node
              - generic [ref=f1e166]: observer
          - generic [ref=f1e167]:
            - generic [ref=f1e168]: RESOURCES
            - button "reference-controller Component" [ref=f1e169] [cursor=pointer]:
              - generic [ref=f1e172]: reference-controller
              - generic [ref=f1e173]: Component
            - button "reference-plant Component" [ref=f1e174] [cursor=pointer]:
              - generic [ref=f1e177]: reference-plant
              - generic [ref=f1e178]: Component
            - button "reference-loop System" [ref=f1e179] [cursor=pointer]:
              - generic [ref=f1e182]: reference-loop
              - generic [ref=f1e183]: System
            - button "local-reference Deployment" [ref=f1e184] [cursor=pointer]:
              - generic [ref=f1e187]: local-reference
              - generic [ref=f1e188]: Deployment
            - button "reference-response Scenario" [ref=f1e189] [cursor=pointer]:
              - generic [ref=f1e192]: reference-response
              - generic [ref=f1e193]: Scenario
            - button "experiment-lite Profile" [ref=f1e194] [cursor=pointer]:
              - generic [ref=f1e197]: experiment-lite
              - generic [ref=f1e198]: Profile
            - button "studio-experiments Profile" [ref=f1e199] [cursor=pointer]:
              - generic [ref=f1e202]: studio-experiments
              - generic [ref=f1e203]: Profile
          - button "Add element" [ref=f1e205] [cursor=pointer]
        - region "Model canvas" [ref=f1e208]:
          - generic:
            - generic [ref=f1e209]:
              - generic [ref=f1e210]: LOGICAL MODEL
              - generic [ref=f1e211]: 1.0.0
            - generic [ref=f1e212]:
              - button "Table view" [ref=f1e213] [cursor=pointer]
              - button "Auto layout" [ref=f1e214] [cursor=pointer]
              - button "Save layout" [ref=f1e215] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e216]:
            - generic [ref=f1e218]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e219] [cursor=pointer]:
                      - generic [ref=f1e222]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e224] [cursor=pointer]:
                      - generic [ref=f1e227]: state-flow
                - generic:
                  - group [ref=f1e229]:
                    - generic [ref=f1e230]:
                      - generic [ref=f1e232]: controller
                      - strong [ref=f1e241]: controller
                      - code [ref=f1e242]: controller
                      - list "Named ports" [ref=f1e243]:
                        - listitem [ref=f1e244]:
                          - generic [aria-hidden] [ref=f1e245]: ←
                          - code [ref=f1e246]: controller-out
                          - generic [ref=f1e247]: output
                      - generic [ref=f1e248]:
                        - generic [ref=f1e249]: Logical element
                        - generic [ref=f1e250]: 1 ports
                  - group [ref=f1e252]:
                    - generic [ref=f1e253]:
                      - generic [ref=f1e255]: plant
                      - strong [ref=f1e264]: plant
                      - code [ref=f1e265]: plant
                      - list "Named ports" [ref=f1e266]:
                        - listitem [ref=f1e267]:
                          - generic [aria-hidden] [ref=f1e268]: →
                          - code [ref=f1e269]: plant-in
                          - generic [ref=f1e270]: input
                        - listitem [ref=f1e271]:
                          - generic [aria-hidden] [ref=f1e272]: ←
                          - code [ref=f1e273]: plant-out
                          - generic [ref=f1e274]: output
                      - generic [ref=f1e275]:
                        - generic [ref=f1e276]: Logical element
                        - generic [ref=f1e277]: 2 ports
                  - group [ref=f1e279]:
                    - generic [ref=f1e280]:
                      - generic [ref=f1e282]: observer
                      - strong [ref=f1e288]: observer-node
                      - code [ref=f1e289]: observer-node
                      - list "Named ports" [ref=f1e290]:
                        - listitem [ref=f1e291]:
                          - generic [aria-hidden] [ref=f1e292]: →
                          - code [ref=f1e293]: observer-in
                          - generic [ref=f1e294]: input
                      - generic [ref=f1e295]:
                        - generic [ref=f1e296]: Logical element
                        - generic [ref=f1e297]: 1 ports
            - generic "Control Panel" [ref=f1e299]:
              - button "Zoom In" [ref=f1e300] [cursor=pointer]
              - button "Zoom Out" [ref=f1e303] [cursor=pointer]
              - button "Fit View" [ref=f1e306] [cursor=pointer]
            - img "Mini Map" [ref=f1e310]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e315]:
          - heading "System inspector" [level=2] [ref=f1e317]
          - generic [ref=f1e323]:
            - heading "reference-loop" [level=3] [ref=f1e327]
            - paragraph [ref=f1e328]: Authoritative XDL System
            - generic [ref=f1e329]: Draft model
          - navigation "Model location" [ref=f1e330]:
            - button "reference-loop" [ref=f1e331] [cursor=pointer]
          - generic [ref=f1e332]:
            - button "Properties" [ref=f1e333] [cursor=pointer]
            - button "Parameters" [ref=f1e334] [cursor=pointer]
          - generic [ref=f1e335]:
            - paragraph [ref=f1e336]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f1e337]:
              - generic [ref=f1e338]:
                - term [ref=f1e339]: Namespace
                - definition [ref=f1e340]: org.xverse.studio.process-control
              - generic [ref=f1e341]:
                - term [ref=f1e342]: XDL version
                - definition [ref=f1e343]: xverse.io/xdl/v1alpha1
              - generic [ref=f1e344]:
                - term [ref=f1e345]: Resources
                - definition [ref=f1e346]: "7"
              - generic [ref=f1e347]:
                - term [ref=f1e348]: Evidence scope
                - definition [ref=f1e349]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f1e350]
            - generic [ref=f1e351]:
              - group "Setpoint and response" [ref=f1e352]:
                - generic [ref=f1e354]:
                  - generic [ref=f1e355]:
                    - text: Target
                    - generic [ref=f1e356]: "1"
                    - spinbutton "Target 1" [ref=f1e357]: "1"
                  - paragraph [ref=f1e358]: Normalized reference setpoint, dimensionless.
                  - generic [ref=f1e359]:
                    - generic [ref=f1e360]: Scenario XDL extension · default 1
                    - button "Apply" [disabled] [ref=f1e361]
                - generic [ref=f1e362]:
                  - generic [ref=f1e363]:
                    - text: Response gain
                    - generic [ref=f1e364]: "1"
                    - spinbutton "Response gain 1" [ref=f1e365]: "0.8"
                  - paragraph [ref=f1e366]: First-order response coefficient; gain × timestep must be at most one.
                  - generic [ref=f1e367]:
                    - generic [ref=f1e368]: Scenario XDL extension · default 0.8
                    - button "Apply" [disabled] [ref=f1e369]
                - generic [ref=f1e370]:
                  - generic [ref=f1e371]:
                    - text: Initial state
                    - generic [ref=f1e372]: "1"
                    - spinbutton "Initial state 1" [ref=f1e373]: "0"
                  - paragraph [ref=f1e374]: Initial normalized scalar state.
                  - generic [ref=f1e375]:
                    - generic [ref=f1e376]: Scenario XDL extension · default 0
                    - button "Apply" [disabled] [ref=f1e377]
              - group "Run horizon" [ref=f1e378]:
                - generic [ref=f1e380]:
                  - generic [ref=f1e381]:
                    - text: Duration
                    - generic [ref=f1e382]: s
                    - spinbutton "Duration s" [ref=f1e383]: "5"
                  - paragraph [ref=f1e384]: Requested simulation horizon, in seconds; at most 3,000 samples.
                  - generic [ref=f1e385]:
                    - generic [ref=f1e386]: Scenario XDL extension · default 5
                    - button "Apply" [disabled] [ref=f1e387]
                - generic [ref=f1e388]:
                  - generic [ref=f1e389]:
                    - text: Time step
                    - generic [ref=f1e390]: s
                    - spinbutton "Time step s" [ref=f1e391]: "0.1"
                  - paragraph [ref=f1e392]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                  - generic [ref=f1e393]:
                    - generic [ref=f1e394]: Scenario XDL extension · default 0.1
                    - button "Apply" [disabled] [ref=f1e395]
              - group "Instrument faults" [ref=f1e396]:
                - generic [ref=f1e398]:
                  - generic [ref=f1e399]:
                    - text: Reference fault
                    - generic [ref=f1e400]: "1"
                    - combobox "Reference fault 1" [ref=f1e401]:
                      - option "none" [selected]
                      - option "stuck-sensor"
                  - paragraph [ref=f1e402]: Owned model fault only; stuck-sensor freezes the reported observation.
                  - generic [ref=f1e403]:
                    - generic [ref=f1e404]: Scenario XDL extension · default none
                    - button "Apply" [disabled] [ref=f1e405]
          - generic [ref=f1e406]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e411]:
        - generic [ref=f1e412]: Local project · Saved on backend
        - generic [ref=f1e415]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e416]: 1 provider(s) available
```

# Test source

```ts
  135 |       expect(response.status()).toBe(201);
  136 |       const other = await response.json(),
  137 |         id = Object.keys(other.documents).find(
  138 |           (id) => parse(other.documents[id].content).kind === "System",
  139 |         )!,
  140 |         document = other.documents[id];
  141 |       expect(process.env.STUDIO_BROWSER_DATA).toBeTruthy();
  142 |       const root = realpathSync(process.env.STUDIO_BROWSER_DATA!),
  143 |         file = path.resolve(
  144 |           root,
  145 |           "projects",
  146 |           other.projectId,
  147 |           "revisions",
  148 |           String(other.revision),
  149 |           document.path,
  150 |         );
  151 |       expect(file.startsWith(root + path.sep)).toBe(true);
  152 |       expect(realpathSync(file)).toBe(file);
  153 |       expect(readFileSync(file, "utf8")).toBe(document.content);
  154 |       fixture = { project: other, file, original: document.content };
  155 |       writeFileSync(file, Buffer.from([0xff, 0xfe, 0x00, 0x64]));
  156 |       await route.fulfill({ response });
  157 |     });
  158 |     await page.route(recoveryPattern, async (route) => {
  159 |       if (
  160 |         route.request().method() !== "POST" ||
  161 |         !fixture ||
  162 |         new URL(route.request().url()).pathname !==
  163 |           `/api/v1/projects/${fixture.project.projectId}/recoveries`
  164 |       ) {
  165 |         await route.continue();
  166 |         return;
  167 |       }
  168 |       let finish!: () => void;
  169 |       finished = new Promise<void>((r) => (finish = r));
  170 |       try {
  171 |         const response = await route.fetch();
  172 |         expect(response.status()).toBe(200);
  173 |         committed = await response.json();
  174 |         ready = true;
  175 |         await gate;
  176 |         await route.fulfill({ response });
  177 |       } finally {
  178 |         finish();
  179 |       }
  180 |     });
  181 |     try {
  182 |       await activate(
  183 |         page,
  184 |         page
  185 |           .getByRole("article")
  186 |           .filter({
  187 |             has: page.getByRole("heading", { name: entry.name, exact: true }),
  188 |           })
  189 |           .getByRole("button", { name: "Open as project", exact: true }),
  190 |       );
  191 |       const recovery = page.getByRole("group", {
  192 |         name: "Source recovery",
  193 |         exact: true,
  194 |       });
  195 |       await expect(recovery).toBeVisible();
  196 |       expect(fixture).toBeDefined();
  197 |       await environment(page);
  198 |       const checkbox = panel(page).getByRole("checkbox", {
  199 |         name: "Select profile Automotive terminology",
  200 |         exact: true,
  201 |       });
  202 |       await expect(checkbox).toBeVisible();
  203 |       await activate(
  204 |         page,
  205 |         recovery.getByRole("button", {
  206 |           name: `Restore committed revision ${fixture!.project.revision}`,
  207 |           exact: true,
  208 |         }),
  209 |       );
  210 |       await expect.poll(() => ready).toBe(true);
  211 |       await tabTo(page, checkbox);
  212 |       await page.keyboard.press("Space");
  213 |       await expect(checkbox).toBeChecked();
  214 |       release();
  215 |       await finished;
  216 |       await settle(page);
  217 |       const current = async () => ({
  218 |         panelCount: await panel(page).count(),
  219 |         checked: (await checkbox.count()) ? await checkbox.isChecked() : null,
  220 |         focused: (await checkbox.count())
  221 |           ? await checkbox.evaluate((n) => document.activeElement === n)
  222 |           : false,
  223 |         selectionLabel: await panel(page)
  224 |           .getByText(
  225 |             `Selected project: ${project.name} · revision ${project.revision}`,
  226 |             { exact: true },
  227 |           )
  228 |           .count(),
  229 |         storedProject: await page.evaluate(() =>
  230 |           localStorage.getItem("studio.projectId"),
  231 |         ),
  232 |       });
  233 |       await expect.soft
  234 |         .poll(current)
> 235 |         .toEqual({
      |          ^ Error: expect(received).toEqual(expected) // deep equality
  236 |           panelCount: 1,
  237 |           checked: true,
  238 |           focused: true,
  239 |           selectionLabel: 1,
  240 |           storedProject: project.projectId,
  241 |         });
  242 |       const saved = await request(page, `/projects/${project.projectId}`),
  243 |         recovered = await request(
  244 |           page,
  245 |           `/projects/${fixture!.project.projectId}`,
  246 |         );
  247 |       expect(saved.revision).toBe(project.revision);
  248 |       expect(saved.documents).toEqual(project.documents);
  249 |       expect(saved.manifest.profiles).toEqual(project.manifest.profiles);
  250 |       expect(committed.project.projectId).toBe(fixture!.project.projectId);
  251 |       expect(recovered.revision).toBe(fixture!.project.revision + 1);
  252 |       for (const [id, document] of Object.entries<any>(
  253 |         fixture!.project.documents,
  254 |       ))
  255 |         expect(recovered.documents[id].content).toBe(document.content);
  256 |       expect(await runs(page, project.projectId)).toEqual(beforeRuns);
  257 |       expect(await runs(page, recovered.projectId)).toEqual([]);
  258 |       await info.attach("profile-foreign-recovery.json", {
  259 |         body: JSON.stringify({
  260 |           viewport,
  261 |           activeProjectId: project.projectId,
  262 |           recoveredProjectId: recovered.projectId,
  263 |           measuredContext: await current(),
  264 |           backendRecoveryCommitted: true,
  265 |           profileDraftUnsubmitted: true,
  266 |           activeCanonicalUnchanged: true,
  267 |           noStart: true,
  268 |           scope:
  269 |             "Only newly owned test source made unreadable; real foreign recovery held after commit while active Environment profile checkbox changes",
  270 |         }),
  271 |         contentType: "application/json",
  272 |       });
  273 |     } finally {
  274 |       release();
  275 |       await finished;
  276 |       await page.unroute(createPattern);
  277 |       await page.unroute(recoveryPattern);
  278 |       if (fixture) writeFileSync(fixture.file, fixture.original);
  279 |     }
  280 |   });
  281 |   test(`profile bindings: discovery failure stays unknown and retries actual registry at ${viewport.width}x${viewport.height}`, async ({
  282 |     page,
  283 |   }, info) => {
  284 |     test.setTimeout(60000);
  285 |     await page.setViewportSize(viewport);
  286 |     await connectStudio(page, info);
  287 |     const project = await create(page, `Profile discovery ${viewport.width}`),
  288 |       beforeRuns = await runs(page, project.projectId);
  289 |     let reads = 0,
  290 |       writes = 0;
  291 |     page.on("request", (r) => {
  292 |       if (
  293 |         r.method() === "POST" &&
  294 |         new URL(r.url()).pathname.endsWith("/profile-bindings")
  295 |       )
  296 |         writes++;
  297 |     });
  298 |     const pattern = "**/api/v1/profiles";
  299 |     await page.route(pattern, async (route) => {
  300 |       reads++;
  301 |       if (reads === 1)
  302 |         await route.fulfill({
  303 |           status: 503,
  304 |           contentType: "application/json",
  305 |           body: JSON.stringify({
  306 |             code: "PROFILE_DISCOVERY_UNAVAILABLE",
  307 |             message: "Controlled registry transport failure",
  308 |             retryable: true,
  309 |           }),
  310 |         });
  311 |       else {
  312 |         const response = await route.fetch();
  313 |         expect(response.status()).toBe(200);
  314 |         await route.fulfill({ response });
  315 |       }
  316 |     });
  317 |     try {
  318 |       await environment(page);
  319 |       await expect.poll(() => reads).toBe(1);
  320 |       await expect(panel(page).getByRole("alert")).toContainText(
  321 |         /unknown|unavailable|could not/i,
  322 |       );
  323 |       await expect(panel(page).getByRole("checkbox")).toHaveCount(0);
  324 |       await expect(bind(page)).toBeDisabled();
  325 |       await activate(
  326 |         page,
  327 |         panel(page).getByRole("button", {
  328 |           name: "Retry profile discovery",
  329 |           exact: true,
  330 |         }),
  331 |       );
  332 |       await expect(
  333 |         panel(page).getByRole("checkbox", {
  334 |           name: "Select profile Automotive terminology",
  335 |           exact: true,
```
