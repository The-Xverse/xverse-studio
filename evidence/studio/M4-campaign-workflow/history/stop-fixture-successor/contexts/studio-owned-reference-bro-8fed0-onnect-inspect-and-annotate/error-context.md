# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: studio.spec.ts >> owned reference browser workflow: author, preflight, execute, reconnect, inspect and annotate
- Location: tests/e2e/studio.spec.ts:7:5

# Error details

```
TimeoutError: locator.fill: Timeout 15000ms exceeded.
Call log:
  - waiting for getByLabel('Duration', { exact: true })

```

# Page snapshot

```yaml
- generic [ref=f2e3]:
  - link "Skip to workspace" [ref=f2e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f2e5]:
    - button "X-Verse Studio home" [ref=f2e6] [cursor=pointer]:
      - generic [ref=f2e7]: X
      - generic [ref=f2e8]: X-VERSE STUDIO
    - generic [ref=f2e10]: Local workspace
    - generic [ref=f2e12]: REFERENCE PREVIEW
    - button "Environment" [ref=f2e13] [cursor=pointer]
    - generic "Local operator" [ref=f2e20]: LO
  - generic [ref=f2e21]:
    - navigation "Main navigation" [ref=f2e22]:
      - button "Workspace" [ref=f2e23] [cursor=pointer]
      - button "Catalog" [ref=f2e30] [cursor=pointer]
      - button "Laboratory" [ref=f2e37] [cursor=pointer]:
        - generic [ref=f2e41]: Lab
      - button "Compatibility and environment" [ref=f2e42] [cursor=pointer]:
        - generic [ref=f2e48]: Settings
      - generic [ref=f2e49]: v0.1
    - main [ref=f2e50]:
      - generic [ref=f2e52]:
        - text: Project created. Review its scope and validate the XDL before running.
        - button "Dismiss notice" [ref=f2e56] [cursor=pointer]
      - generic [ref=f2e59]:
        - generic [ref=f2e60]:
          - generic [ref=f2e61]:
            - button "Workspace" [ref=f2e62] [cursor=pointer]
            - generic [ref=f2e65]: System
          - generic [ref=f2e66]:
            - heading "Automotive reference" [level=1] [ref=f2e73]
            - generic [ref=f2e74]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f2e75]: Automotive terms
            - generic [ref=f2e78]: rev 1
        - generic [ref=f2e79]:
          - 'button "Dependencies: none unresolved" [ref=f2e80] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f2e81]
          - button "Redo" [disabled] [ref=f2e82]
          - button "Export" [ref=f2e83] [cursor=pointer]
          - button "Validate" [ref=f2e86] [cursor=pointer]
          - button "Preflight & run" [ref=f2e89] [cursor=pointer]
      - tablist "System workflows" [ref=f2e92]:
        - tab "Model" [selected] [ref=f2e93] [cursor=pointer]
        - tab "Connections" [ref=f2e99] [cursor=pointer]
        - tab "Deployment" [ref=f2e104] [cursor=pointer]
        - tab "Experiments" [ref=f2e107] [cursor=pointer]
        - tab "Results" [ref=f2e110] [cursor=pointer]
        - button "XDL source" [ref=f2e114] [cursor=pointer]
      - generic [ref=f2e117]:
        - generic [ref=f2e118]:
          - text: Draft revision
          - code [ref=f2e120]: "1"
        - generic [ref=f2e121]: 3 elements · 2 connections
        - generic [ref=f2e122]:
          - text: Execution scope
          - generic [ref=f2e123]: Owned reference
      - generic [ref=f2e124]:
        - complementary "Structured model navigation" [ref=f2e125]:
          - generic [ref=f2e126]:
            - heading "Vehicle function explorer" [level=2] [ref=f2e127]
            - button "View XDL source" [ref=f2e128] [cursor=pointer]
          - textbox "Search elements" [ref=f2e135]:
            - /placeholder: Find an element…
          - generic [ref=f2e136]:
            - strong [ref=f2e142]: reference-loop
            - generic [ref=f2e143]: "3"
            - button "Group by node" [ref=f2e144] [cursor=pointer]
          - generic [ref=f2e145]:
            - button "controller controller" [ref=f2e146] [cursor=pointer]:
              - generic [ref=f2e152]: controller
              - generic [ref=f2e153]: controller
            - button "plant plant" [ref=f2e154] [cursor=pointer]:
              - generic [ref=f2e160]: plant
              - generic [ref=f2e161]: plant
            - button "observer-node observer" [ref=f2e162] [cursor=pointer]:
              - generic [ref=f2e165]: observer-node
              - generic [ref=f2e166]: observer
          - generic [ref=f2e167]:
            - generic [ref=f2e168]: RESOURCES
            - button "reference-controller Component" [ref=f2e169] [cursor=pointer]:
              - generic [ref=f2e172]: reference-controller
              - generic [ref=f2e173]: Component
            - button "reference-plant Component" [ref=f2e174] [cursor=pointer]:
              - generic [ref=f2e177]: reference-plant
              - generic [ref=f2e178]: Component
            - button "reference-loop System" [ref=f2e179] [cursor=pointer]:
              - generic [ref=f2e182]: reference-loop
              - generic [ref=f2e183]: System
            - button "local-reference Deployment" [ref=f2e184] [cursor=pointer]:
              - generic [ref=f2e187]: local-reference
              - generic [ref=f2e188]: Deployment
            - button "reference-response Scenario" [ref=f2e189] [cursor=pointer]:
              - generic [ref=f2e192]: reference-response
              - generic [ref=f2e193]: Scenario
            - button "experiment-lite Profile" [ref=f2e194] [cursor=pointer]:
              - generic [ref=f2e197]: experiment-lite
              - generic [ref=f2e198]: Profile
            - button "studio-experiments Profile" [ref=f2e199] [cursor=pointer]:
              - generic [ref=f2e202]: studio-experiments
              - generic [ref=f2e203]: Profile
          - button "Add element" [ref=f2e205] [cursor=pointer]
        - region "Model canvas" [ref=f2e208]:
          - generic:
            - generic [ref=f2e209]:
              - generic [ref=f2e210]: LOGICAL MODEL
              - generic [ref=f2e211]: 1.0.0
            - generic [ref=f2e212]:
              - button "Table view" [ref=f2e213] [cursor=pointer]
              - button "Auto layout" [ref=f2e214] [cursor=pointer]
              - button "Save layout" [ref=f2e215] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f2e216]:
            - generic [ref=f2e218]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.automotive/system/reference-loop#controller to xdl://org.xverse.studio.automotive/system/reference-loop#plant" [ref=f2e219] [cursor=pointer]:
                      - generic [ref=f2e222]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.automotive/system/reference-loop#plant to xdl://org.xverse.studio.automotive/system/reference-loop#observer-node" [ref=f2e224] [cursor=pointer]:
                      - generic [ref=f2e227]: state-flow
                - generic:
                  - group [ref=f2e229]:
                    - generic [ref=f2e230]:
                      - generic [ref=f2e232]: controller
                      - strong [ref=f2e241]: controller
                      - code [ref=f2e242]: controller
                      - list "Named ports" [ref=f2e243]:
                        - listitem [ref=f2e244]:
                          - generic [aria-hidden] [ref=f2e245]: ←
                          - code [ref=f2e246]: controller-out
                          - generic [ref=f2e247]: output
                      - generic [ref=f2e248]:
                        - generic [ref=f2e249]: Logical element
                        - generic [ref=f2e250]: 1 ports
                  - group [ref=f2e252]:
                    - generic [ref=f2e253]:
                      - generic [ref=f2e255]: plant
                      - strong [ref=f2e264]: plant
                      - code [ref=f2e265]: plant
                      - list "Named ports" [ref=f2e266]:
                        - listitem [ref=f2e267]:
                          - generic [aria-hidden] [ref=f2e268]: →
                          - code [ref=f2e269]: plant-in
                          - generic [ref=f2e270]: input
                        - listitem [ref=f2e271]:
                          - generic [aria-hidden] [ref=f2e272]: ←
                          - code [ref=f2e273]: plant-out
                          - generic [ref=f2e274]: output
                      - generic [ref=f2e275]:
                        - generic [ref=f2e276]: Logical element
                        - generic [ref=f2e277]: 2 ports
                  - group [ref=f2e279]:
                    - generic [ref=f2e280]:
                      - generic [ref=f2e282]: observer
                      - strong [ref=f2e288]: observer-node
                      - code [ref=f2e289]: observer-node
                      - list "Named ports" [ref=f2e290]:
                        - listitem [ref=f2e291]:
                          - generic [aria-hidden] [ref=f2e292]: →
                          - code [ref=f2e293]: observer-in
                          - generic [ref=f2e294]: input
                      - generic [ref=f2e295]:
                        - generic [ref=f2e296]: Logical element
                        - generic [ref=f2e297]: 1 ports
            - generic "Control Panel" [ref=f2e299]:
              - button "Zoom In" [ref=f2e300] [cursor=pointer]
              - button "Zoom Out" [ref=f2e303] [cursor=pointer]
              - button "Fit View" [ref=f2e306] [cursor=pointer]
            - img "Mini Map" [ref=f2e310]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f2e315]:
          - heading "System inspector" [level=2] [ref=f2e317]
          - generic [ref=f2e323]:
            - heading "reference-loop" [level=3] [ref=f2e327]
            - paragraph [ref=f2e328]: Authoritative XDL System
            - generic [ref=f2e329]: Draft model
          - navigation "Model location" [ref=f2e330]:
            - button "reference-loop" [ref=f2e331] [cursor=pointer]
          - generic [ref=f2e332]:
            - button "Properties" [ref=f2e333] [cursor=pointer]
            - button "Parameters" [active] [ref=f2e334] [cursor=pointer]
          - generic [ref=f2e336]:
            - group "Reference and response" [ref=f2e337]:
              - generic [ref=f2e339]:
                - generic [ref=f2e340]:
                  - text: Target
                  - generic [ref=f2e341]: "1"
                  - spinbutton "Target 1" [ref=f2e342]: "1"
                - paragraph [ref=f2e343]: Normalized reference setpoint, dimensionless.
                - generic [ref=f2e344]:
                  - generic [ref=f2e345]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f2e346]
              - generic [ref=f2e347]:
                - generic [ref=f2e348]:
                  - text: Response gain
                  - generic [ref=f2e349]: "1"
                  - spinbutton "Response gain 1" [ref=f2e350]: "0.8"
                - paragraph [ref=f2e351]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f2e352]:
                  - generic [ref=f2e353]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f2e354]
              - generic [ref=f2e355]:
                - generic [ref=f2e356]:
                  - text: Initial state
                  - generic [ref=f2e357]: "1"
                  - spinbutton "Initial state 1" [ref=f2e358]: "0"
                - paragraph [ref=f2e359]: Initial normalized scalar state.
                - generic [ref=f2e360]:
                  - generic [ref=f2e361]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f2e362]
            - group "Drive horizon" [ref=f2e363]:
              - generic [ref=f2e365]:
                - generic [ref=f2e366]:
                  - text: Duration
                  - generic [ref=f2e367]: s
                  - spinbutton "Duration s" [ref=f2e368]: "5"
                - paragraph [ref=f2e369]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f2e370]:
                  - generic [ref=f2e371]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f2e372]
              - generic [ref=f2e373]:
                - generic [ref=f2e374]:
                  - text: Time step
                  - generic [ref=f2e375]: s
                  - spinbutton "Time step s" [ref=f2e376]: "0.1"
                - paragraph [ref=f2e377]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f2e378]:
                  - generic [ref=f2e379]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f2e380]
            - group "Sensor faults" [ref=f2e381]:
              - generic [ref=f2e383]:
                - generic [ref=f2e384]:
                  - text: Reference fault
                  - generic [ref=f2e385]: "1"
                  - combobox "Reference fault 1" [ref=f2e386]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f2e387]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f2e388]:
                  - generic [ref=f2e389]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f2e390]
          - generic [ref=f2e391]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f2e396]:
        - generic [ref=f2e397]: Local project · Saved on backend
        - generic [ref=f2e400]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e401]: 1 provider(s) available
```

# Test source

```ts
  149 |   await page.getByRole("tab", { name: "Assertions", exact: true }).click();
  150 |   await expect(
  151 |     page.getByLabel("Snapshot definition reference").locator("option"),
  152 |   ).toHaveCount(2);
  153 |   await page
  154 |     .getByLabel("Snapshot definition reference")
  155 |     .selectOption({ index: 1 });
  156 |   await page
  157 |     .getByRole("button", { name: "Evaluate assertion", exact: true })
  158 |     .click();
  159 |   await expect(page.getByText("indeterminate", { exact: true })).toBeVisible();
  160 |   await page
  161 |     .getByRole("button", { name: "Preflight & run", exact: true })
  162 |     .click();
  163 |   await expect(
  164 |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  165 |   ).toBeEnabled();
  166 |   await page
  167 |     .getByRole("button", { name: "Back to draft", exact: true })
  168 |     .click();
  169 |   await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  170 |   await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5,0.8]}');
  171 |   await page.getByLabel("Maximum runs", { exact: true }).fill("2");
  172 |   await page
  173 |     .getByRole("button", { name: "Preview campaign", exact: true })
  174 |     .click();
  175 |   await expect(
  176 |     page.getByRole("heading", {
  177 |       name: "Authoritative campaign preview",
  178 |       exact: true,
  179 |     }),
  180 |   ).toBeVisible();
  181 |   await page
  182 |     .getByRole("button", { name: "Create campaign", exact: true })
  183 |     .click();
  184 |   await expect(
  185 |     page.locator(".section-heading").getByText("complete", { exact: true }),
  186 |   ).toBeVisible({ timeout: 30000 });
  187 |   await page.screenshot({
  188 |     path: testInfo.outputPath("campaign.png"),
  189 |     fullPage: true,
  190 |   });
  191 |   await exerciseComposition(page, testInfo);
  192 |   await exerciseFrozenRerun(page, testInfo);
  193 |   for (const viewport of [
  194 |     { width: 1024, height: 768 },
  195 |     { width: 1440, height: 900 },
  196 |   ]) {
  197 |     await page.setViewportSize(viewport);
  198 |     await page.getByRole("tab", { name: "Model", exact: true }).click();
  199 |     const horizontalOverflow = await page.evaluate(
  200 |       () => document.documentElement.scrollWidth > window.innerWidth + 1,
  201 |     );
  202 |     expect(horizontalOverflow).toBe(false);
  203 |     await page.getByRole("button", { name: "Table view", exact: true }).focus();
  204 |     await page.keyboard.press("Enter");
  205 |     await expect(
  206 |       page.getByRole("button", { name: "plant", exact: true }),
  207 |     ).toBeVisible();
  208 |     await page.getByRole("button", { name: "Graph view", exact: true }).click();
  209 |     await page.screenshot({
  210 |       path: testInfo.outputPath(`workspace-${viewport.width}.png`),
  211 |       fullPage: true,
  212 |     });
  213 |   }
  214 |   await page.getByRole("button", { name: "Laboratory", exact: true }).click();
  215 |   await expect(
  216 |     page.getByRole("heading", { name: "No physical provider admitted" }),
  217 |   ).toBeVisible();
  218 |   expect(errors).toEqual([]);
  219 |   const keyboardActivate = async (
  220 |     target: ReturnType<typeof page.getByRole>,
  221 |   ) => {
  222 |     await expect(target).toBeVisible();
  223 |     for (let step = 0; step < 130; step++) {
  224 |       if (
  225 |         await target.evaluate((element) => document.activeElement === element)
  226 |       ) {
  227 |         await page.keyboard.press("Enter");
  228 |         return;
  229 |       }
  230 |       await page.keyboard.press("Tab");
  231 |     }
  232 |     throw new Error(
  233 |       "Keyboard target is not reachable through native Tab order.",
  234 |     );
  235 |   };
  236 |   await keyboardActivate(
  237 |     page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
  238 |   );
  239 |   await keyboardActivate(
  240 |     page
  241 |       .locator(".example-grid")
  242 |       .getByRole("button", { name: /Automotive reference/ }),
  243 |   );
  244 |   await expect(
  245 |     page.getByRole("heading", { name: "Automotive reference", exact: true }),
  246 |   ).toBeVisible();
  247 |   // Keep the worker active for the native Tab traversal; prove actual Stop execution below.
  248 |   await page.getByRole("button", { name: "Parameters", exact: true }).click();
> 249 |   await page.getByLabel("Duration", { exact: true }).fill("30");
      |                                                      ^ TimeoutError: locator.fill: Timeout 15000ms exceeded.
  250 |   await page
  251 |     .getByLabel("Duration", { exact: true })
  252 |     .locator("xpath=ancestor::form")
  253 |     .getByRole("button", { name: "Apply", exact: true })
  254 |     .click();
  255 |   await expect(
  256 |     page.getByText("Draft saved. Existing run snapshots remain unchanged.", {
  257 |       exact: true,
  258 |     }),
  259 |   ).toBeVisible();
  260 |   await keyboardActivate(
  261 |     page.getByRole("button", { name: "Validate", exact: true }),
  262 |   );
  263 |   await expect(
  264 |     page.getByText("Authoritative platform validation passed.", {
  265 |       exact: false,
  266 |     }),
  267 |   ).toBeVisible();
  268 |   await keyboardActivate(
  269 |     page.getByRole("button", { name: "Preflight & run", exact: true }),
  270 |   );
  271 |   await expect(
  272 |     page.getByRole("heading", { name: "Execution preflight" }),
  273 |   ).toBeVisible();
  274 |   await page.keyboard.press("Escape");
  275 |   await expect(
  276 |     page.getByRole("button", { name: "Preflight & run", exact: true }),
  277 |   ).toBeFocused();
  278 |   await page.keyboard.press("Enter");
  279 |   await keyboardActivate(
  280 |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  281 |   );
  282 |   await expect(
  283 |     page.getByRole("heading", { name: /Run results/ }),
  284 |   ).toBeVisible();
  285 |   await expect(page.getByText("running", { exact: true }).first()).toBeVisible({
  286 |     timeout: 10000,
  287 |   });
  288 |   const activeRunId = await page.evaluate(() =>
  289 |     localStorage.getItem("studio.lastRun"),
  290 |   );
  291 |   expect(activeRunId).toBeTruthy();
  292 |   const frozen = await page.evaluate(async (id) => {
  293 |     const response = await fetch(`/api/v1/runs/${id}/snapshot`);
  294 |     if (!response.ok)
  295 |       throw new Error("Owned keyboard snapshot could not be read.");
  296 |     return response.json();
  297 |   }, activeRunId);
  298 |   expect(frozen.snapshot.configuration.duration).toBe(30);
  299 |   const stopTiming: any[] = [];
  300 |   const recordStop = (value: any) => {
  301 |     if (stopTiming.length < 64)
  302 |       stopTiming.push({ at: performance.now(), ...value });
  303 |   };
  304 |   page.on("request", (request) => {
  305 |     if (
  306 |       request.method() === "POST" &&
  307 |       new URL(request.url()).pathname === `/api/v1/runs/${activeRunId}/commands`
  308 |     ) {
  309 |       const body = request.postDataJSON();
  310 |       recordStop({
  311 |         event: "command-request",
  312 |         kind: body.kind,
  313 |         expectedStateVersion: body.expectedStateVersion,
  314 |       });
  315 |     }
  316 |   });
  317 |   const acknowledgement = page.waitForResponse(
  318 |     (response) =>
  319 |       response.request().method() === "POST" &&
  320 |       new URL(response.url()).pathname ===
  321 |         `/api/v1/runs/${activeRunId}/commands`,
  322 |     { timeout: 15000 },
  323 |   );
  324 |   // Observe a rejected wait without creating an unhandled rejection if an earlier assertion fails.
  325 |   void acknowledgement.catch(() => {});
  326 |   try {
  327 |     recordStop({ event: "keyboard-stop-begin", configuredDuration: 30 });
  328 |     await keyboardActivate(
  329 |       page.getByRole("button", { name: "Stop", exact: true }),
  330 |     );
  331 |     await expect(
  332 |       page.getByText("stopped", { exact: true }).first(),
  333 |     ).toBeVisible({
  334 |       timeout: 15000,
  335 |     });
  336 |     const stopResponse = await acknowledgement;
  337 |     const stopReceipt = await stopResponse.json();
  338 |     recordStop({
  339 |       event: "command-response",
  340 |       status: stopResponse.status(),
  341 |       code: stopReceipt.code,
  342 |       operationId: stopReceipt.operationId,
  343 |     });
  344 |     expect(stopResponse.status()).toBe(202);
  345 |     expect(stopReceipt.operationId).toBeTruthy();
  346 |     await expect
  347 |       .poll(
  348 |         async () =>
  349 |           page.evaluate(async (id) => {
```
