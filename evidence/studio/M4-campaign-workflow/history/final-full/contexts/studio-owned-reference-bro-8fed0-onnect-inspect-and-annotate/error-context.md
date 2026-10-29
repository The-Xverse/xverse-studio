# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: studio.spec.ts >> owned reference browser workflow: author, preflight, execute, reconnect, inspect and annotate
- Location: tests/e2e/studio.spec.ts:7:5

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  getByRole('alert')
Expected: 0
Received: 1
Timeout:  10000ms

Call log:
  - Expect "toHaveCount" getByRole('alert') with timeout 10000ms
  - waiting for getByRole('alert')
    24 × locator resolved to 1 element
       - unexpected value "1"

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
        - text: Run accepted by the backend. Browser disconnection will not duplicate or terminate it.
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
        - tab "Model" [ref=f2e93] [cursor=pointer]
        - tab "Connections" [ref=f2e99] [cursor=pointer]
        - tab "Deployment" [ref=f2e104] [cursor=pointer]
        - tab "Experiments" [ref=f2e107] [cursor=pointer]
        - tab "Results 1" [selected] [ref=f2e110] [cursor=pointer]:
          - text: Results
          - generic [ref=f2e113]: "1"
        - button "XDL source" [ref=f2e115] [cursor=pointer]
      - generic [ref=f2e118]:
        - generic [ref=f2e119]:
          - text: Draft revision
          - code [ref=f2e121]: "1"
        - generic [ref=f2e122]: 3 elements · 2 connections
        - generic [ref=f2e123]:
          - text: Run snapshot
          - code [ref=f2e124]: snap-b0f8436
          - generic [ref=f2e125]: stopped
          - button "Draft matches run inputs" [ref=f2e126] [cursor=pointer]
      - generic [ref=f2e127]:
        - generic [ref=f2e128]:
          - generic [ref=f2e129]:
            - heading "Run results stopped" [level=2] [ref=f2e130]:
              - text: Run results
              - generic [ref=f2e131]: stopped
            - paragraph [ref=f2e132]:
              - code [ref=f2e133]: run-e801dd76-cce8-45ea-955c-25aa74d5a124
              - generic [ref=f2e134]:
                - text: Snapshot
                - code [ref=f2e135]: snap-b0f8436f-9d9d
          - generic [ref=f2e136]:
            - generic [ref=f2e137]:
              - text: Recorded run
              - combobox "Recorded run" [ref=f2e138]:
                - option "run-e801dd76-cce8-45ea-955c-25aa74d5a124 · preparing" [selected]
            - button "Frozen inputs" [ref=f2e139] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f2e142] [cursor=pointer]
            - button "Refresh" [ref=f2e145] [cursor=pointer]
        - region "Run controls" [ref=f2e148]:
          - generic [ref=f2e149]:
            - generic [ref=f2e150]:
              - button "Stop" [disabled] [ref=f2e151]
              - generic [ref=f2e154]: Not available while the run is stopped.
            - generic [ref=f2e155]:
              - button "Cancel" [disabled] [ref=f2e156]
              - generic [ref=f2e157]: Not available while the run is stopped.
            - paragraph [ref=f2e158]: "Not admitted for this run: pause, resume, step, reset, set_parameter. The backend rejects them; absence of a button is not support."
          - alert [ref=f2e159]: Run state changed; refresh before controlling it.
        - generic [ref=f2e160]:
          - generic [ref=f2e161]:
            - text: Execution
            - strong [ref=f2e162]: stopped
            - text: Lifecycle outcome
          - generic [ref=f2e164]:
            - text: Assertion verdict
            - strong [ref=f2e165]: Not evaluated
            - text: Separate assessment result
          - generic [ref=f2e167]:
            - text: Cleanup
            - strong [ref=f2e168]: complete
            - text: Owned-resource release
          - generic [ref=f2e170]:
            - text: Evidence
            - strong [ref=f2e171]: complete
            - text: Integrity and completeness
        - generic [ref=f2e173]:
          - generic [ref=f2e174]: owned_reference
          - generic [ref=f2e175]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f2e176]: Retained history available
        - tablist "Result sections" [ref=f2e178]:
          - tab "Observations" [selected] [ref=f2e179] [cursor=pointer]
          - tab "Events & logs 37" [ref=f2e180] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f2e181]: "37"
          - tab "Diagnosis" [ref=f2e182] [cursor=pointer]
          - tab "Evidence" [ref=f2e183] [cursor=pointer]
          - tab "Compare" [ref=f2e184] [cursor=pointer]
          - tab "Annotations" [ref=f2e185] [cursor=pointer]
        - generic [ref=f2e186]:
          - generic [ref=f2e187]:
            - generic [ref=f2e188]:
              - heading "Recorded observations" [level=3] [ref=f2e189]
              - paragraph [ref=f2e190]: Original source time and quantity semantics are preserved.
            - generic [ref=f2e191]:
              - button "Table view" [ref=f2e192] [cursor=pointer]
              - button "Replay observations" [ref=f2e193] [cursor=pointer]
          - generic [ref=f2e194]:
            - generic [ref=f2e195]:
              - generic [ref=f2e196]:
                - text: Element reference
                - combobox "Element reference" [ref=f2e197]:
                  - option "All elements" [selected]
                  - option "xdl://org.xverse.studio.automotive/system/reference-loop#controller"
                  - option "xdl://org.xverse.studio.automotive/system/reference-loop#plant"
                  - option "xdl://org.xverse.studio.automotive/system/reference-loop#state-flow"
              - generic [ref=f2e198]:
                - text: Emitter provider
                - combobox "Emitter provider" [ref=f2e199]:
                  - option "All reported identities" [selected]
                  - option "studio.reference"
              - generic [ref=f2e200]:
                - text: Observer
                - combobox "Observer" [ref=f2e201]:
                  - option "All reported identities" [selected]
                  - option "state-observer"
              - generic [ref=f2e202]:
                - text: Observation field
                - combobox "Observation field" [ref=f2e203]:
                  - option "All reported fields" [selected]
                  - option "control"
                  - option "measured"
                  - option "target"
                  - option "value"
              - generic [ref=f2e204]:
                - text: Time basis
                - combobox "Time basis" [ref=f2e205]:
                  - option "No time window" [selected]
                  - option "Original source clock"
                  - option "Recorded receipt UTC"
            - paragraph [ref=f2e206]: The field predicate selects records and the returned value field. Original immutable payloads remain inspectable in Events.
            - generic [ref=f2e207]:
              - button "Apply evidence filters" [ref=f2e208] [cursor=pointer]
              - button "Reset evidence filters" [ref=f2e209] [cursor=pointer]
          - status "Evidence read quality" [ref=f2e210]:
            - generic [ref=f2e211]: "Matched: 50 · Returned: 50 · Omitted from page: 0"
            - generic [ref=f2e212]: "missingSourceTime: 0"
            - generic [ref=f2e213]: "malformedSourceTime: 0"
            - generic [ref=f2e214]: "otherClock: 0"
            - generic [ref=f2e215]: "missingReceiptTime: 0"
            - generic [ref=f2e216]: "unsupportedReceiptEncoding: 0"
            - generic [ref=f2e217]: "Reader integrity: valid"
          - generic [ref=f2e218]:
            - paragraph [ref=f2e219]: "Original clock: simulation-time · tick unit: microsecond. Exact endpoint ticks: 0 to 4900000."
            - img "Recorded observation chart in simulation-time. Exact source ticks; missing time is not plotted." [ref=f2e220]:
              - generic [ref=f2e221]: "0.000"
              - generic [ref=f2e223]: "0.2500"
              - generic [ref=f2e225]: "0.5000"
              - generic [ref=f2e227]: "0.7500"
              - generic [ref=f2e229]: "1.000"
              - generic [ref=f2e231]: "0"
              - generic [ref=f2e232]: "4900000"
            - generic [ref=f2e440]:
              - generic [ref=f2e441]: control
              - generic [ref=f2e443]: measured
              - generic [ref=f2e445]: target
              - generic [ref=f2e447]: value
          - generic [ref=f2e449]:
            - button "Previous observation page" [disabled] [ref=f2e450]
            - button "Next observation page" [disabled] [ref=f2e451]
          - generic [ref=f2e452]:
            - generic [ref=f2e453]:
              - text: "Clock:"
              - strong [ref=f2e454]: simulation-time
            - generic [ref=f2e455]:
              - text: "Unit:"
              - strong [ref=f2e456]: 1, 1, 1, 1
            - generic [ref=f2e457]:
              - text: "Reduction:"
              - strong [ref=f2e458]: page
        - generic [ref=f2e459]:
          - heading "Input and evidence provenance" [level=3] [ref=f2e460]
          - generic [ref=f2e461]:
            - generic [ref=f2e462]:
              - term [ref=f2e463]: Snapshot
              - definition [ref=f2e464]: snap-b0f8436f-9d9d-4e61-81fb-c6e066464f3d
            - generic [ref=f2e465]:
              - term [ref=f2e466]: Plan digest
              - definition [ref=f2e467]: sha256:5e56a98f90a2947e221f5163389ddaef8ed1c742f25671fb9fc5e19351e114a6
            - generic [ref=f2e468]:
              - term [ref=f2e469]: Provider
              - definition [ref=f2e470]: studio.reference
            - generic [ref=f2e471]:
              - term [ref=f2e472]: Clock uncertainty
              - definition [ref=f2e473]: Not declared
            - generic [ref=f2e474]:
              - term [ref=f2e475]: Coverage
              - definition [ref=f2e476]: Unknown
          - group [ref=f2e477]:
            - generic "Inspect exact data" [ref=f2e478] [cursor=pointer]
      - generic [ref=f2e479]:
        - generic [ref=f2e480]: Local project · Saved on backend
        - generic [ref=f2e483]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e484]: 1 provider(s) available
```

# Test source

```ts
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
  247 |   await keyboardActivate(
  248 |     page.getByRole("button", { name: "Validate", exact: true }),
  249 |   );
  250 |   await expect(
  251 |     page.getByText("Authoritative platform validation passed.", {
  252 |       exact: false,
  253 |     }),
  254 |   ).toBeVisible();
  255 |   await keyboardActivate(
  256 |     page.getByRole("button", { name: "Preflight & run", exact: true }),
  257 |   );
  258 |   await expect(
  259 |     page.getByRole("heading", { name: "Execution preflight" }),
  260 |   ).toBeVisible();
  261 |   await page.keyboard.press("Escape");
  262 |   await expect(
  263 |     page.getByRole("button", { name: "Preflight & run", exact: true }),
  264 |   ).toBeFocused();
  265 |   await page.keyboard.press("Enter");
  266 |   await keyboardActivate(
  267 |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  268 |   );
  269 |   await expect(
  270 |     page.getByRole("heading", { name: /Run results/ }),
  271 |   ).toBeVisible();
  272 |   await expect(page.getByText("running", { exact: true }).first()).toBeVisible({
  273 |     timeout: 10000,
  274 |   });
  275 |   await keyboardActivate(
  276 |     page.getByRole("button", { name: "Stop", exact: true }),
  277 |   );
  278 |   await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
  279 |     timeout: 15000,
  280 |   });
> 281 |   await expect(page.getByRole("alert")).toHaveCount(0);
      |                                         ^ Error: expect(locator).toHaveCount(expected) failed
  282 |   expect(errors).toEqual([]);
  283 |   if (
  284 |     process.env.STUDIO_MEASURE_PERFORMANCE === "1" ||
  285 |     process.env.STUDIO_PERFORMANCE === "1"
  286 |   ) {
  287 |     const referenceProjectId = await page.evaluate(() =>
  288 |       localStorage.getItem("studio.projectId"),
  289 |     );
  290 |     await measureModel(page, testInfo);
  291 |     await measureHistory(page, testInfo, referenceProjectId || undefined);
  292 |   }
  293 |   expect(errors).toEqual([]);
  294 | });
  295 |
```
