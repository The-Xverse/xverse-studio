# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: foreign recovery preserves newer profile draft at 1024x768
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
-   "storedProject": "prj-0e03367e-c3e0-4c73-9365-db99e4fd40b6",
+   "checked": null,
+   "focused": false,
+   "panelCount": 0,
+   "selectionLabel": 0,
+   "storedProject": "prj-ceec3bdd-c548-41f4-8094-56cdd7d8998b",
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
    - button "Environment" [ref=f1e12] [cursor=pointer]
    - generic "Local operator" [ref=f1e19]: LO
  - generic [ref=f1e20]:
    - navigation "Main navigation" [ref=f1e21]:
      - button "Workspace" [ref=f1e22] [cursor=pointer]
      - button "Catalog" [ref=f1e29] [cursor=pointer]
      - button "Laboratory" [ref=f1e36] [cursor=pointer]:
        - generic [ref=f1e40]: Lab
      - button "Compatibility and environment" [ref=f1e41] [cursor=pointer]:
        - generic [ref=f1e47]: Settings
      - generic [ref=f1e48]: v0.1
    - main [ref=f1e49]:
      - generic [ref=f1e51]:
        - text: Recovered as revision 2. The observed external bytes are preserved in backup rec-acc762a2-a994-4d0f-aedc-bab9b8e5e692.
        - button "Dismiss notice" [ref=f1e55] [cursor=pointer]
      - generic [ref=f1e58]:
        - generic [ref=f1e59]:
          - generic [ref=f1e60]:
            - button "Workspace" [ref=f1e61] [cursor=pointer]
            - generic [ref=f1e64]: System
          - generic [ref=f1e65]:
            - heading "Process control reference" [level=1] [ref=f1e72]
            - generic [ref=f1e73]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e74]: Process control terms
        - generic [ref=f1e77]:
          - 'button "Dependencies: none unresolved" [ref=f1e78] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e79]
          - button "Redo" [disabled] [ref=f1e80]
          - button "Export" [ref=f1e81] [cursor=pointer]
          - button "Validate" [ref=f1e84] [cursor=pointer]
          - button "Preflight & run" [ref=f1e87] [cursor=pointer]
      - tablist "System workflows" [ref=f1e90]:
        - tab "Model" [selected] [ref=f1e91] [cursor=pointer]
        - tab "Connections" [ref=f1e97] [cursor=pointer]
        - tab "Deployment" [ref=f1e102] [cursor=pointer]
        - tab "Experiments" [ref=f1e105] [cursor=pointer]
        - tab "Results" [ref=f1e108] [cursor=pointer]
        - button "XDL source" [active] [ref=f1e112] [cursor=pointer]
      - generic [ref=f1e115]:
        - generic [ref=f1e116]:
          - text: Draft revision
          - code [ref=f1e118]: "2"
        - generic [ref=f1e119]: 3 elements · 2 connections
        - generic [ref=f1e120]:
          - text: Execution scope
          - generic [ref=f1e121]: Owned reference
      - generic [ref=f1e122]:
        - complementary "Structured model navigation" [ref=f1e123]:
          - generic [ref=f1e124]:
            - heading "Process explorer" [level=2] [ref=f1e125]
            - button "View XDL source" [ref=f1e126] [cursor=pointer]
          - textbox "Search elements" [ref=f1e133]:
            - /placeholder: Find an element…
          - generic [ref=f1e134]:
            - strong [ref=f1e140]: reference-loop
            - generic [ref=f1e141]: "3"
            - button "Group by node" [ref=f1e142] [cursor=pointer]
          - generic [ref=f1e143]:
            - button "controller controller" [ref=f1e144] [cursor=pointer]:
              - generic [ref=f1e150]: controller
              - generic [ref=f1e151]: controller
            - button "plant plant" [ref=f1e152] [cursor=pointer]:
              - generic [ref=f1e158]: plant
              - generic [ref=f1e159]: plant
            - button "observer-node observer" [ref=f1e160] [cursor=pointer]:
              - generic [ref=f1e163]: observer-node
              - generic [ref=f1e164]: observer
          - generic [ref=f1e165]:
            - generic [ref=f1e166]: RESOURCES
            - button "reference-controller Component" [ref=f1e167] [cursor=pointer]:
              - generic [ref=f1e170]: reference-controller
              - generic [ref=f1e171]: Component
            - button "reference-plant Component" [ref=f1e172] [cursor=pointer]:
              - generic [ref=f1e175]: reference-plant
              - generic [ref=f1e176]: Component
            - button "reference-loop System" [ref=f1e177] [cursor=pointer]:
              - generic [ref=f1e180]: reference-loop
              - generic [ref=f1e181]: System
            - button "local-reference Deployment" [ref=f1e182] [cursor=pointer]:
              - generic [ref=f1e185]: local-reference
              - generic [ref=f1e186]: Deployment
            - button "reference-response Scenario" [ref=f1e187] [cursor=pointer]:
              - generic [ref=f1e190]: reference-response
              - generic [ref=f1e191]: Scenario
            - button "experiment-lite Profile" [ref=f1e192] [cursor=pointer]:
              - generic [ref=f1e195]: experiment-lite
              - generic [ref=f1e196]: Profile
            - button "studio-experiments Profile" [ref=f1e197] [cursor=pointer]:
              - generic [ref=f1e200]: studio-experiments
              - generic [ref=f1e201]: Profile
          - button "Add element" [ref=f1e203] [cursor=pointer]
        - region "Model canvas" [ref=f1e206]:
          - generic:
            - generic [ref=f1e207]:
              - generic [ref=f1e208]: LOGICAL MODEL
              - generic [ref=f1e209]: 1.0.0
            - generic [ref=f1e210]:
              - button "Table view" [ref=f1e211] [cursor=pointer]
              - button "Auto layout" [ref=f1e212] [cursor=pointer]
              - button "Save layout" [ref=f1e213] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e214]:
            - generic [ref=f1e216]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e217] [cursor=pointer]:
                      - generic [ref=f1e220]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e222] [cursor=pointer]:
                      - generic [ref=f1e225]: state-flow
                - generic:
                  - group [ref=f1e227]:
                    - generic [ref=f1e228]:
                      - generic [ref=f1e230]: controller
                      - strong [ref=f1e239]: controller
                      - code [ref=f1e240]: controller
                      - list "Named ports" [ref=f1e241]:
                        - listitem [ref=f1e242]:
                          - generic [aria-hidden] [ref=f1e243]: ←
                          - code [ref=f1e244]: controller-out
                          - generic [ref=f1e245]: output
                      - generic [ref=f1e246]:
                        - generic [ref=f1e247]: Logical element
                        - generic [ref=f1e248]: 1 ports
                  - group [ref=f1e250]:
                    - generic [ref=f1e251]:
                      - generic [ref=f1e253]: plant
                      - strong [ref=f1e262]: plant
                      - code [ref=f1e263]: plant
                      - list "Named ports" [ref=f1e264]:
                        - listitem [ref=f1e265]:
                          - generic [aria-hidden] [ref=f1e266]: →
                          - code [ref=f1e267]: plant-in
                          - generic [ref=f1e268]: input
                        - listitem [ref=f1e269]:
                          - generic [aria-hidden] [ref=f1e270]: ←
                          - code [ref=f1e271]: plant-out
                          - generic [ref=f1e272]: output
                      - generic [ref=f1e273]:
                        - generic [ref=f1e274]: Logical element
                        - generic [ref=f1e275]: 2 ports
                  - group [ref=f1e277]:
                    - generic [ref=f1e278]:
                      - generic [ref=f1e280]: observer
                      - strong [ref=f1e286]: observer-node
                      - code [ref=f1e287]: observer-node
                      - list "Named ports" [ref=f1e288]:
                        - listitem [ref=f1e289]:
                          - generic [aria-hidden] [ref=f1e290]: →
                          - code [ref=f1e291]: observer-in
                          - generic [ref=f1e292]: input
                      - generic [ref=f1e293]:
                        - generic [ref=f1e294]: Logical element
                        - generic [ref=f1e295]: 1 ports
            - generic "Control Panel" [ref=f1e297]:
              - button "Zoom In" [ref=f1e298] [cursor=pointer]
              - button "Zoom Out" [ref=f1e301] [cursor=pointer]
              - button "Fit View" [ref=f1e304] [cursor=pointer]
            - img "Mini Map" [ref=f1e308]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e313]:
          - heading "System inspector" [level=2] [ref=f1e315]
          - generic [ref=f1e321]:
            - heading "reference-loop" [level=3] [ref=f1e325]
            - paragraph [ref=f1e326]: Authoritative XDL System
            - generic [ref=f1e327]: Draft model
          - navigation "Model location" [ref=f1e328]:
            - button "reference-loop" [ref=f1e329] [cursor=pointer]
          - generic [ref=f1e330]:
            - button "Properties" [ref=f1e331] [cursor=pointer]
            - button "Parameters" [ref=f1e332] [cursor=pointer]
          - generic [ref=f1e333]:
            - paragraph [ref=f1e334]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f1e335]:
              - generic [ref=f1e336]:
                - term [ref=f1e337]: Namespace
                - definition [ref=f1e338]: org.xverse.studio.process-control
              - generic [ref=f1e339]:
                - term [ref=f1e340]: XDL version
                - definition [ref=f1e341]: xverse.io/xdl/v1alpha1
              - generic [ref=f1e342]:
                - term [ref=f1e343]: Resources
                - definition [ref=f1e344]: "7"
              - generic [ref=f1e345]:
                - term [ref=f1e346]: Evidence scope
                - definition [ref=f1e347]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f1e348]
            - generic [ref=f1e349]:
              - group "Setpoint and response" [ref=f1e350]:
                - generic [ref=f1e352]:
                  - generic [ref=f1e353]:
                    - text: Target
                    - generic [ref=f1e354]: "1"
                    - spinbutton "Target 1" [ref=f1e355]: "1"
                  - paragraph [ref=f1e356]: Normalized reference setpoint, dimensionless.
                  - generic [ref=f1e357]:
                    - generic [ref=f1e358]: Scenario XDL extension · default 1
                    - button "Apply" [disabled] [ref=f1e359]
                - generic [ref=f1e360]:
                  - generic [ref=f1e361]:
                    - text: Response gain
                    - generic [ref=f1e362]: "1"
                    - spinbutton "Response gain 1" [ref=f1e363]: "0.8"
                  - paragraph [ref=f1e364]: First-order response coefficient; gain × timestep must be at most one.
                  - generic [ref=f1e365]:
                    - generic [ref=f1e366]: Scenario XDL extension · default 0.8
                    - button "Apply" [disabled] [ref=f1e367]
                - generic [ref=f1e368]:
                  - generic [ref=f1e369]:
                    - text: Initial state
                    - generic [ref=f1e370]: "1"
                    - spinbutton "Initial state 1" [ref=f1e371]: "0"
                  - paragraph [ref=f1e372]: Initial normalized scalar state.
                  - generic [ref=f1e373]:
                    - generic [ref=f1e374]: Scenario XDL extension · default 0
                    - button "Apply" [disabled] [ref=f1e375]
              - group "Run horizon" [ref=f1e376]:
                - generic [ref=f1e378]:
                  - generic [ref=f1e379]:
                    - text: Duration
                    - generic [ref=f1e380]: s
                    - spinbutton "Duration s" [ref=f1e381]: "5"
                  - paragraph [ref=f1e382]: Requested simulation horizon, in seconds; at most 3,000 samples.
                  - generic [ref=f1e383]:
                    - generic [ref=f1e384]: Scenario XDL extension · default 5
                    - button "Apply" [disabled] [ref=f1e385]
                - generic [ref=f1e386]:
                  - generic [ref=f1e387]:
                    - text: Time step
                    - generic [ref=f1e388]: s
                    - spinbutton "Time step s" [ref=f1e389]: "0.1"
                  - paragraph [ref=f1e390]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                  - generic [ref=f1e391]:
                    - generic [ref=f1e392]: Scenario XDL extension · default 0.1
                    - button "Apply" [disabled] [ref=f1e393]
              - group "Instrument faults" [ref=f1e394]:
                - generic [ref=f1e396]:
                  - generic [ref=f1e397]:
                    - text: Reference fault
                    - generic [ref=f1e398]: "1"
                    - combobox "Reference fault 1" [ref=f1e399]:
                      - option "none" [selected]
                      - option "stuck-sensor"
                  - paragraph [ref=f1e400]: Owned model fault only; stuck-sensor freezes the reported observation.
                  - generic [ref=f1e401]:
                    - generic [ref=f1e402]: Scenario XDL extension · default none
                    - button "Apply" [disabled] [ref=f1e403]
          - generic [ref=f1e404]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e409]:
        - generic [ref=f1e410]: Local project · Saved on backend
        - generic [ref=f1e413]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e414]: 1 provider(s) available
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
