# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: modal-keyboard.spec.ts >> modal early keyboard: async Preflight dialog handles Escape immediately after mount
- Location: tests/e2e/modal-keyboard.spec.ts:93:5

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  getByRole('dialog', { name: 'Execution preflight' })
Expected: 0
Received: 1
Timeout:  10000ms

Call log:
  - Expect "toHaveCount" getByRole('dialog', { name: 'Execution preflight' }) with timeout 10000ms
  - waiting for getByRole('dialog', { name: 'Execution preflight' })
    21 × locator resolved to 1 element
       - unexpected value "1"

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to workspace" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=e5]:
    - button "X-Verse Studio home" [ref=e6] [cursor=pointer]:
      - generic [ref=e7]: X
      - generic [ref=e8]: X-VERSE STUDIO
    - generic [ref=e10]: Local workspace
    - generic [ref=e12]: REFERENCE PREVIEW
    - button "Environment" [ref=e13] [cursor=pointer]
    - generic "Local operator" [ref=e20]: LO
  - generic [ref=e21]:
    - complementary "Main navigation" [ref=e22]:
      - button "Workspace" [ref=e23] [cursor=pointer]
      - button "Catalog" [ref=e30] [cursor=pointer]
      - button "Laboratory" [ref=e37] [cursor=pointer]:
        - generic [ref=e41]: Lab
      - button "Compatibility and environment" [ref=e42] [cursor=pointer]:
        - generic [ref=e48]: Settings
      - generic [ref=e49]: v0.1
    - main [ref=e50]:
      - generic [ref=e51]:
        - generic [ref=e52]:
          - generic [ref=e53]:
            - button "Workspace" [ref=e54] [cursor=pointer]
            - generic [ref=e57]: System
          - generic [ref=e58]:
            - heading "Process control reference" [level=1] [ref=e65]
            - generic [ref=e66]: Draft
            - generic [ref=e67]: rev 1
        - generic [ref=e68]:
          - button "Export" [ref=e69] [cursor=pointer]
          - button "Validate" [ref=e72] [cursor=pointer]
          - button "Preflight & run" [ref=e75] [cursor=pointer]
      - tablist "System workflows" [ref=e78]:
        - tab "Model" [selected] [ref=e79] [cursor=pointer]
        - tab "Connections" [ref=e85] [cursor=pointer]
        - tab "Deployment" [ref=e90] [cursor=pointer]
        - tab "Experiments" [ref=e93] [cursor=pointer]
        - tab "Results" [ref=e96] [cursor=pointer]
        - button "XDL source" [ref=e100] [cursor=pointer]
      - generic [ref=e103]:
        - generic [ref=e104]:
          - text: Draft revision
          - code [ref=e106]: "1"
        - generic [ref=e107]: 3 elements · 2 connections
        - generic [ref=e108]:
          - text: Execution scope
          - generic [ref=e109]: Owned reference
      - generic [ref=e110]:
        - complementary "Structured model navigation" [ref=e111]:
          - generic [ref=e112]:
            - heading "System explorer" [level=2] [ref=e113]
            - button "View XDL source" [ref=e114] [cursor=pointer]
          - textbox "Search elements" [ref=e121]:
            - /placeholder: Find an element…
          - generic [ref=e122]:
            - strong [ref=e128]: reference-loop
            - generic [ref=e129]: "3"
          - generic [ref=e130]:
            - button "controller controller" [ref=e131] [cursor=pointer]:
              - generic [ref=e137]: controller
              - generic [ref=e138]: controller
            - button "plant plant" [ref=e139] [cursor=pointer]:
              - generic [ref=e145]: plant
              - generic [ref=e146]: plant
            - button "observer-node observer" [ref=e147] [cursor=pointer]:
              - generic [ref=e150]: observer-node
              - generic [ref=e151]: observer
          - generic [ref=e152]:
            - generic [ref=e153]: RESOURCES
            - button "reference-controller Component" [ref=e154] [cursor=pointer]:
              - generic [ref=e157]: reference-controller
              - generic [ref=e158]: Component
            - button "reference-plant Component" [ref=e159] [cursor=pointer]:
              - generic [ref=e162]: reference-plant
              - generic [ref=e163]: Component
            - button "reference-loop System" [ref=e164] [cursor=pointer]:
              - generic [ref=e167]: reference-loop
              - generic [ref=e168]: System
            - button "local-reference Deployment" [ref=e169] [cursor=pointer]:
              - generic [ref=e172]: local-reference
              - generic [ref=e173]: Deployment
            - button "reference-response Scenario" [ref=e174] [cursor=pointer]:
              - generic [ref=e177]: reference-response
              - generic [ref=e178]: Scenario
            - button "experiment-lite Profile" [ref=e179] [cursor=pointer]:
              - generic [ref=e182]: experiment-lite
              - generic [ref=e183]: Profile
            - button "studio-experiments Profile" [ref=e184] [cursor=pointer]:
              - generic [ref=e187]: studio-experiments
              - generic [ref=e188]: Profile
          - button "Add element" [ref=e190] [cursor=pointer]
        - region "Model canvas" [ref=e193]:
          - generic:
            - generic [ref=e194]:
              - generic [ref=e195]: LOGICAL MODEL
              - generic [ref=e196]: 1.0.0
            - generic [ref=e197]:
              - button "Table view" [ref=e198] [cursor=pointer]
              - button "Auto layout" [ref=e199] [cursor=pointer]
              - button "Save layout" [ref=e200] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=e201]:
            - generic [ref=e203]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=e204] [cursor=pointer]:
                      - generic [ref=e205]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=e207] [cursor=pointer]:
                      - generic [ref=e208]: state-flow
                - generic:
                  - group [ref=e210]:
                    - generic [ref=e211]:
                      - generic [ref=e213]: controller
                      - strong [ref=e222]: controller
                      - code [ref=e223]: controller
                      - generic [ref=e224]:
                        - generic [ref=e225]: Logical element
                        - generic [ref=e226]: 1 ports
                  - group [ref=e228]:
                    - generic [ref=e229]:
                      - generic [ref=e231]: plant
                      - strong [ref=e240]: plant
                      - code [ref=e241]: plant
                      - generic [ref=e242]:
                        - generic [ref=e243]: Logical element
                        - generic [ref=e244]: 2 ports
                  - group [ref=e246]:
                    - generic [ref=e247]:
                      - generic [ref=e249]: observer
                      - strong [ref=e255]: observer-node
                      - code [ref=e256]: observer-node
                      - generic [ref=e257]:
                        - generic [ref=e258]: Logical element
                        - generic [ref=e259]: 1 ports
            - generic "Control Panel" [ref=e261]:
              - button "Zoom In" [ref=e262] [cursor=pointer]
              - button "Zoom Out" [ref=e265] [cursor=pointer]
              - button "Fit View" [ref=e268] [cursor=pointer]
            - img "Mini Map" [ref=e272]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=e277]:
          - heading "System inspector" [level=2] [ref=e279]
          - generic [ref=e285]:
            - heading "reference-loop" [level=3] [ref=e289]
            - paragraph [ref=e290]: Authoritative XDL System
            - generic [ref=e291]: Draft model
          - generic [ref=e292]:
            - button "Properties" [ref=e293] [cursor=pointer]
            - button "Parameters" [ref=e294] [cursor=pointer]
          - generic [ref=e295]:
            - paragraph [ref=e296]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=e297]:
              - generic [ref=e298]:
                - term [ref=e299]: Namespace
                - definition [ref=e300]: org.xverse.studio.process-control
              - generic [ref=e301]:
                - term [ref=e302]: XDL version
                - definition [ref=e303]: xverse.io/xdl/v1alpha1
              - generic [ref=e304]:
                - term [ref=e305]: Resources
                - definition [ref=e306]: "7"
              - generic [ref=e307]:
                - term [ref=e308]: Evidence scope
                - definition [ref=e309]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=e310]
            - generic [ref=e311]:
              - generic [ref=e312]:
                - generic [ref=e313]:
                  - text: Target
                  - generic [ref=e314]: "1"
                  - spinbutton "Target 1" [ref=e315]: "1"
                - paragraph [ref=e316]: Normalized reference setpoint, dimensionless.
                - generic [ref=e317]:
                  - generic [ref=e318]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=e319]
              - generic [ref=e320]:
                - generic [ref=e321]:
                  - text: Response gain
                  - generic [ref=e322]: "1"
                  - spinbutton "Response gain 1" [ref=e323]: "0.8"
                - paragraph [ref=e324]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=e325]:
                  - generic [ref=e326]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=e327]
              - generic [ref=e328]:
                - generic [ref=e329]:
                  - text: Initial state
                  - generic [ref=e330]: "1"
                  - spinbutton "Initial state 1" [ref=e331]: "0"
                - paragraph [ref=e332]: Initial normalized scalar state.
                - generic [ref=e333]:
                  - generic [ref=e334]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=e335]
              - generic [ref=e336]:
                - generic [ref=e337]:
                  - text: Duration
                  - generic [ref=e338]: s
                  - spinbutton "Duration s" [ref=e339]: "5"
                - paragraph [ref=e340]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=e341]:
                  - generic [ref=e342]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=e343]
              - generic [ref=e344]:
                - generic [ref=e345]:
                  - text: Time step
                  - generic [ref=e346]: s
                  - spinbutton "Time step s" [ref=e347]: "0.1"
                - paragraph [ref=e348]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=e349]:
                  - generic [ref=e350]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=e351]
              - generic [ref=e352]:
                - generic [ref=e353]:
                  - text: Reference fault
                  - generic [ref=e354]: "1"
                  - combobox "Reference fault 1" [ref=e355]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=e356]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=e357]:
                  - generic [ref=e358]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=e359]
          - generic [ref=e360]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=e365]:
        - generic [ref=e366]: Local project · Saved on backend
        - generic [ref=e369]: Authoritative XDL · Layout stored separately
        - generic [ref=e370]: 1 provider(s) available
  - dialog [ref=e372]:
    - banner [ref=e373]:
      - heading "Execution preflight" [level=2] [ref=e374]
      - button "Close dialog" [active] [ref=e375] [cursor=pointer]
    - generic [ref=e378]:
      - generic [ref=e379]:
        - generic [ref=e380]:
          - generic [ref=e381]: FROZEN EXECUTION REQUEST
          - 'heading "Admission decision: ready" [level=3] [ref=e382]'
        - paragraph [ref=e383]: These checks apply to this request and provider. Execution, observations, assertions, cleanup and evidence integrity have separate outcomes.
      - generic [ref=e384]:
        - generic [ref=e385]:
          - text: Execution provider
          - combobox "Execution provider" [ref=e386]:
            - option "Studio executable reference · studio.reference" [selected]
            - option "X-Verse Lite / CARLA · xverse.lite · unavailable"
        - button "Recheck readiness" [ref=e387] [cursor=pointer]
      - generic [ref=e388]:
        - generic [ref=e389]:
          - text: Snapshot
          - code [ref=e390]: snap-6e32acbc-b899-482e-852d-559a25d7fc96
        - generic [ref=e391]:
          - text: Revision
          - strong [ref=e392]: "1"
        - generic [ref=e393]:
          - text: Expires
          - strong [ref=e394]: 10/25/2026, 4:01:32 PM
        - generic [ref=e395]:
          - text: Scope
          - strong [ref=e396]: owned_reference
      - group [ref=e397]:
        - generic "Frozen request identities" [ref=e398] [cursor=pointer]
      - generic [ref=e399]:
        - heading "Readiness checks" [level=3] [ref=e400]
        - table "Independent readiness dimensions" [ref=e402]:
          - rowgroup [ref=e403]:
            - row [ref=e404]:
              - columnheader "Dimension" [ref=e405]
              - columnheader "Reported state" [ref=e406]
              - columnheader "Evidence and next action" [ref=e407]
          - rowgroup [ref=e408]:
            - row [ref=e409]:
              - rowheader "Studio backend" [ref=e410]
              - cell "available" [ref=e411]
              - cell [ref=e413]:
                - paragraph [ref=e414]: The authenticated native Studio backend is responding; no runtime liveness is inferred.
                - list [ref=e415]:
                  - listitem [ref=e416]:
                    - code [ref=e417]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e418]:
                  - generic "Inspect exact data" [ref=e419] [cursor=pointer]
            - row [ref=e420]:
              - rowheader "Provider / host compatibility" [ref=e421]
              - cell "available" [ref=e422]
              - cell [ref=e424]:
                - paragraph [ref=e425]: The installed owned reference provider declares compatibility with this native OS/architecture.
                - list [ref=e426]:
                  - listitem [ref=e427]:
                    - code [ref=e428]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e429]:
                  - generic "Inspect exact data" [ref=e430] [cursor=pointer]
            - row [ref=e431]:
              - rowheader "Model validity" [ref=e432]
              - cell "valid" [ref=e433]
              - cell [ref=e435]:
                - paragraph [ref=e436]: Public XDL validation and declared-intent compilation succeeded.
                - list [ref=e437]:
                  - listitem [ref=e438]:
                    - code [ref=e439]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=e440]:
              - rowheader "Artifact availability" [ref=e441]
              - cell "available" [ref=e442]
              - cell [ref=e444]:
                - paragraph [ref=e445]: Every selected artifact reference matches the installed owned model contract digest; no external download was performed.
                - list [ref=e446]:
                  - listitem [ref=e447]:
                    - code [ref=e448]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e449]:
                  - generic "Inspect exact data" [ref=e450] [cursor=pointer]
            - row [ref=e451]:
              - rowheader "Capability compatibility" [ref=e452]
              - cell "compatible" [ref=e453]
              - cell [ref=e455]:
                - paragraph [ref=e456]: The exact source/configuration matches the admitted owned reference contract.
                - list [ref=e457]:
                  - listitem [ref=e458]:
                    - code [ref=e459]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=e460]:
              - rowheader "Target readiness" [ref=e461]
              - cell "ready" [ref=e462]
              - cell [ref=e464]:
                - paragraph [ref=e465]: The owned executable can accept these inputs; it has not been started and no liveness/health is asserted.
                - list [ref=e466]:
                  - listitem [ref=e467]:
                    - code [ref=e468]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=e469]:
              - rowheader "Resource availability" [ref=e470]
              - cell "available" [ref=e471]
              - cell [ref=e473]:
                - paragraph [ref=e474]: Advertised reference budgets have capacity at this read-only check.
                - list [ref=e475]:
                  - listitem [ref=e476]:
                    - code [ref=e477]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e478]:
                  - generic "Inspect exact data" [ref=e479] [cursor=pointer]
            - row [ref=e480]:
              - rowheader "Execution ownership" [ref=e481]
              - cell "available" [ref=e482]
              - cell [ref=e484]:
                - paragraph [ref=e485]: A new reference run will be owned by the native backend; browser disconnection does not own its lifetime.
                - list [ref=e486]:
                  - listitem [ref=e487]:
                    - code [ref=e488]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e489]:
                  - generic "Inspect exact data" [ref=e490] [cursor=pointer]
            - row [ref=e491]:
              - rowheader "Clock mappings" [ref=e492]
              - cell "compatible" [ref=e493]
              - cell [ref=e495]:
                - paragraph [ref=e496]: The owned simulation clock is declared; no cross-clock mapping or physical synchronization is claimed.
                - list [ref=e497]:
                  - listitem [ref=e498]:
                    - code [ref=e499]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e500]:
                  - generic "Inspect exact data" [ref=e501] [cursor=pointer]
            - row [ref=e502]:
              - rowheader "Execution authority" [ref=e503]
              - cell "available" [ref=e504]
              - cell [ref=e506]:
                - paragraph [ref=e507]: Backend-owned reference execution is admitted; no physical permit is acquired.
                - list [ref=e508]:
                  - listitem [ref=e509]:
                    - code [ref=e510]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=e511]:
                  - generic "Inspect exact data" [ref=e512] [cursor=pointer]
      - generic [ref=e513]:
        - heading "Advertised execution limits" [level=3] [ref=e514]
        - paragraph [ref=e515]: These are the backend-reported bounds for studio.reference. Limits are rechecked by the backend before execution.
        - table "Advertised execution limits" [ref=e517]:
          - rowgroup [ref=e518]:
            - row [ref=e519]:
              - columnheader "Contract limit" [ref=e520]
              - columnheader "Exact advertised value" [ref=e521]
          - rowgroup [ref=e522]:
            - row [ref=e523]:
              - cell [ref=e524]:
                - code [ref=e525]: maxDurationSeconds
              - cell "30" [ref=e526]
            - row [ref=e527]:
              - cell [ref=e528]:
                - code [ref=e529]: maxSamples
              - cell "3000" [ref=e530]
            - row [ref=e531]:
              - cell [ref=e532]:
                - code [ref=e533]: maxConcurrentRuns
              - cell "4" [ref=e534]
            - row [ref=e535]:
              - cell [ref=e536]:
                - code [ref=e537]: maxElements
              - cell "200" [ref=e538]
            - row [ref=e539]:
              - cell [ref=e540]:
                - code [ref=e541]: maxConnections
              - cell "400" [ref=e542]
      - region "Readiness diagnostics" [ref=e543]:
        - heading "Diagnostic explanations" [level=3] [ref=e544]
        - paragraph [ref=e545]: No diagnostics reported for this request.
      - generic [ref=e546]:
        - generic [ref=e547]:
          - heading "Compiled plan" [level=3] [ref=e548]
          - button "Inspect compiled plan" [ref=e549] [cursor=pointer]
        - paragraph [ref=e550]: Frozen plan identities match
        - paragraph [ref=e551]: The identity fields match the backend's frozen preflight. Platform compiler output is read-only. Start rechecks mutable admission facts.
      - generic [ref=e552]:
        - button "Back to draft" [ref=e553] [cursor=pointer]
        - button "Start frozen snapshot" [ref=e554] [cursor=pointer]
```

# Test source

```ts
  25  |         document.querySelectorAll('[role="dialog"]'),
  26  |       ).find((node) => node.getAttribute("aria-label") === expectedTitle);
  27  |       if (!dialog || state.fired) return;
  28  |       observer.disconnect();
  29  |       queueMicrotask(() => {
  30  |         state.mounted = dialog.isConnected;
  31  |         state.activeElement = document.activeElement?.tagName || null;
  32  |         const escape = new KeyboardEvent("keydown", {
  33  |           key: "Escape",
  34  |           code: "Escape",
  35  |           bubbles: true,
  36  |           cancelable: true,
  37  |         });
  38  |         // Deliberate earliest post-mount input in actual Chromium. No listener
  39  |         // replacement, application patch, mocked modal or fixed timing delay.
  40  |         dialog.dispatchEvent(escape);
  41  |         state.prevented = escape.defaultPrevented;
  42  |         state.fired = true;
  43  |       });
  44  |     });
  45  |     observer.observe(document.body, { childList: true, subtree: true });
  46  |   }, title);
  47  | }
  48  |
  49  | async function observedEscape(
  50  |   page: Page,
  51  |   testInfo: TestInfo,
  52  | ): Promise<EarlyEscape> {
  53  |   await expect
  54  |     .poll(() =>
  55  |       page.evaluate(
  56  |         () =>
  57  |           (window as unknown as { earlyModalEscape: EarlyEscape })
  58  |             .earlyModalEscape?.fired,
  59  |       ),
  60  |     )
  61  |     .toBe(true);
  62  |   const observation = await page.evaluate(
  63  |     () =>
  64  |       (window as unknown as { earlyModalEscape: EarlyEscape }).earlyModalEscape,
  65  |   );
  66  |   await testInfo.attach("early-escape-observation", {
  67  |     body: JSON.stringify(observation, null, 2),
  68  |     contentType: "application/json",
  69  |   });
  70  |   expect(observation.mounted).toBe(true);
  71  |   return observation;
  72  | }
  73  |
  74  | test("modal early keyboard: New dialog handles Escape immediately after mount", async ({
  75  |   page,
  76  | }, testInfo) => {
  77  |   await connectStudio(page, testInfo);
  78  |   const trigger = page.getByRole("button", {
  79  |     name: "New project",
  80  |     exact: true,
  81  |   });
  82  |   await trigger.focus();
  83  |   await armEarlyEscape(page, "Create a System workspace");
  84  |   await trigger.click();
  85  |   const observation = await observedEscape(page, testInfo);
  86  |   await expect(
  87  |     page.getByRole("dialog", { name: "Create a System workspace" }),
  88  |   ).toHaveCount(0);
  89  |   expect(observation.prevented).toBe(true);
  90  |   await expect(trigger).toBeFocused();
  91  | });
  92  |
  93  | test("modal early keyboard: async Preflight dialog handles Escape immediately after mount", async ({
  94  |   page,
  95  | }, testInfo) => {
  96  |   const starts: string[] = [];
  97  |   page.on("request", (request) => {
  98  |     if (
  99  |       request.method() === "POST" &&
  100 |       /\/api\/v1\/runs$/.test(new URL(request.url()).pathname)
  101 |     )
  102 |       starts.push(request.url());
  103 |   });
  104 |   await connectStudio(page, testInfo);
  105 |   await page
  106 |     .locator(".example-grid")
  107 |     .getByRole("button", { name: /Process control reference/ })
  108 |     .click();
  109 |   await expect(
  110 |     page.getByRole("heading", {
  111 |       name: "Process control reference",
  112 |       exact: true,
  113 |     }),
  114 |   ).toBeVisible();
  115 |   const trigger = page.getByRole("button", {
  116 |     name: "Preflight & run",
  117 |     exact: true,
  118 |   });
  119 |   await trigger.focus();
  120 |   await armEarlyEscape(page, "Execution preflight");
  121 |   await trigger.click();
  122 |   const observation = await observedEscape(page, testInfo);
  123 |   await expect(
  124 |     page.getByRole("dialog", { name: "Execution preflight" }),
> 125 |   ).toHaveCount(0);
      |     ^ Error: expect(locator).toHaveCount(expected) failed
  126 |   expect(observation.prevented).toBe(true);
  127 |   await expect(trigger).toBeFocused();
  128 |   expect(starts).toEqual([]);
  129 | });
  130 |
```
