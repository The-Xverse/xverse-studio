# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: newer head and readiness at 1440x900
- Location: tests/e2e/profile-bindings-accessibility.spec.ts:177:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050', { exact: true })
Expected: visible
Error: strict mode violation: getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050', { exact: true }) resolved to 2 elements:
    1) <code>snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050</code> aka getByRole('code').filter({ hasText: 'snap-f6bba753-fca8-4f8b-b3ee-' })
    2) <dd>snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050</dd> aka getByRole('definition').filter({ hasText: 'snap-f6bba753-fca8-4f8b-b3ee-' })

Call log:
  - Expect "toBeVisible" getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050', { exact: true }) with timeout 10000ms
  - waiting for getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050', { exact: true })

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
            - heading "Profile newer head and readiness 1440" [level=1] [ref=f1e65]
            - generic [ref=f1e66]: Draft
            - generic "Bound domain presentation. Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e67]: Automotive terms
            - generic [ref=f1e70]: rev 3
        - generic [ref=f1e71]:
          - 'button "Dependencies: none unresolved" [ref=f1e72] [cursor=pointer]': Dependencies
          - button "Undo" [ref=f1e73] [cursor=pointer]
          - button "Redo" [disabled] [ref=f1e74]
          - button "Export" [ref=f1e75] [cursor=pointer]
          - button "Validate" [ref=f1e78] [cursor=pointer]
          - button "Preflight & run" [ref=f1e81] [cursor=pointer]
      - tablist "System workflows" [ref=f1e84]:
        - tab "Model" [selected] [ref=f1e85] [cursor=pointer]
        - tab "Connections" [ref=f1e91] [cursor=pointer]
        - tab "Deployment" [ref=f1e96] [cursor=pointer]
        - tab "Experiments" [ref=f1e99] [cursor=pointer]
        - tab "Results" [ref=f1e102] [cursor=pointer]
        - button "XDL source" [ref=f1e106] [cursor=pointer]
      - generic [ref=f1e109]:
        - generic [ref=f1e110]:
          - text: Draft revision
          - code [ref=f1e112]: "3"
        - generic [ref=f1e113]: 3 elements · 2 connections
        - generic [ref=f1e114]:
          - text: Execution scope
          - generic [ref=f1e115]: Owned reference
      - generic [ref=f1e116]:
        - complementary "Structured model navigation" [ref=f1e117]:
          - generic [ref=f1e118]:
            - heading "Vehicle function explorer" [level=2] [ref=f1e119]
            - button "View XDL source" [ref=f1e120] [cursor=pointer]
          - textbox "Search elements" [ref=f1e127]:
            - /placeholder: Find an element…
          - generic [ref=f1e128]:
            - strong [ref=f1e134]: reference-loop
            - generic [ref=f1e135]: "3"
            - button "Group by node" [ref=f1e136] [cursor=pointer]
          - generic [ref=f1e137]:
            - button "controller controller" [ref=f1e138] [cursor=pointer]:
              - generic [ref=f1e144]: controller
              - generic [ref=f1e145]: controller
            - button "plant plant" [ref=f1e146] [cursor=pointer]:
              - generic [ref=f1e152]: plant
              - generic [ref=f1e153]: plant
            - button "observer-node observer" [ref=f1e154] [cursor=pointer]:
              - generic [ref=f1e157]: observer-node
              - generic [ref=f1e158]: observer
          - generic [ref=f1e159]:
            - generic [ref=f1e160]: RESOURCES
            - button "reference-controller Component" [ref=f1e161] [cursor=pointer]:
              - generic [ref=f1e164]: reference-controller
              - generic [ref=f1e165]: Component
            - button "reference-plant Component" [ref=f1e166] [cursor=pointer]:
              - generic [ref=f1e169]: reference-plant
              - generic [ref=f1e170]: Component
            - button "reference-loop System" [ref=f1e171] [cursor=pointer]:
              - generic [ref=f1e174]: reference-loop
              - generic [ref=f1e175]: System
            - button "local-reference Deployment" [ref=f1e176] [cursor=pointer]:
              - generic [ref=f1e179]: local-reference
              - generic [ref=f1e180]: Deployment
            - button "reference-response Scenario" [ref=f1e181] [cursor=pointer]:
              - generic [ref=f1e184]: reference-response
              - generic [ref=f1e185]: Scenario
            - button "experiment-lite Profile" [ref=f1e186] [cursor=pointer]:
              - generic [ref=f1e189]: experiment-lite
              - generic [ref=f1e190]: Profile
            - button "studio-experiments Profile" [ref=f1e191] [cursor=pointer]:
              - generic [ref=f1e194]: studio-experiments
              - generic [ref=f1e195]: Profile
            - button "domain-automotive Profile" [ref=f1e196] [cursor=pointer]:
              - generic [ref=f1e199]: domain-automotive
              - generic [ref=f1e200]: Profile
          - button "Add element" [ref=f1e202] [cursor=pointer]
        - region "Model canvas" [ref=f1e205]:
          - generic:
            - generic [ref=f1e206]:
              - generic [ref=f1e207]: LOGICAL MODEL
              - generic [ref=f1e208]: 1.0.0
            - generic [ref=f1e209]:
              - button "Table view" [ref=f1e210] [cursor=pointer]
              - button "Auto layout" [ref=f1e211] [cursor=pointer]
              - button "Save layout" [ref=f1e212] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e213]:
            - generic [ref=f1e215]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e216] [cursor=pointer]:
                      - generic [ref=f1e219]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e221] [cursor=pointer]:
                      - generic [ref=f1e224]: state-flow
                - generic:
                  - group [ref=f1e226]:
                    - generic [ref=f1e227]:
                      - generic [ref=f1e229]: controller
                      - strong [ref=f1e238]: controller
                      - code [ref=f1e239]: controller
                      - list "Named ports" [ref=f1e240]:
                        - listitem [ref=f1e241]:
                          - generic [aria-hidden] [ref=f1e242]: ←
                          - code [ref=f1e243]: controller-out
                          - generic [ref=f1e244]: output
                      - generic [ref=f1e245]:
                        - generic [ref=f1e246]: Logical element
                        - generic [ref=f1e247]: 1 ports
                  - group [ref=f1e249]:
                    - generic [ref=f1e250]:
                      - generic [ref=f1e252]: plant
                      - strong [ref=f1e261]: plant
                      - code [ref=f1e262]: plant
                      - list "Named ports" [ref=f1e263]:
                        - listitem [ref=f1e264]:
                          - generic [aria-hidden] [ref=f1e265]: →
                          - code [ref=f1e266]: plant-in
                          - generic [ref=f1e267]: input
                        - listitem [ref=f1e268]:
                          - generic [aria-hidden] [ref=f1e269]: ←
                          - code [ref=f1e270]: plant-out
                          - generic [ref=f1e271]: output
                      - generic [ref=f1e272]:
                        - generic [ref=f1e273]: Logical element
                        - generic [ref=f1e274]: 2 ports
                  - group [ref=f1e276]:
                    - generic [ref=f1e277]:
                      - generic [ref=f1e279]: observer
                      - strong [ref=f1e285]: observer-node
                      - code [ref=f1e286]: observer-node
                      - list "Named ports" [ref=f1e287]:
                        - listitem [ref=f1e288]:
                          - generic [aria-hidden] [ref=f1e289]: →
                          - code [ref=f1e290]: observer-in
                          - generic [ref=f1e291]: input
                      - generic [ref=f1e292]:
                        - generic [ref=f1e293]: Logical element
                        - generic [ref=f1e294]: 1 ports
            - generic "Control Panel" [ref=f1e296]:
              - button "Zoom In" [ref=f1e297] [cursor=pointer]
              - button "Zoom Out" [ref=f1e300] [cursor=pointer]
              - button "Fit View" [ref=f1e303] [cursor=pointer]
            - img "Mini Map" [ref=f1e307]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e312]:
          - heading "System inspector" [level=2] [ref=f1e314]
          - generic [ref=f1e320]:
            - heading "reference-loop" [level=3] [ref=f1e324]
            - paragraph [ref=f1e325]: Authoritative XDL System
            - generic [ref=f1e326]: Draft model
          - navigation "Model location" [ref=f1e327]:
            - button "reference-loop" [ref=f1e328] [cursor=pointer]
          - generic [ref=f1e329]:
            - button "Properties" [ref=f1e330] [cursor=pointer]
            - button "Parameters" [ref=f1e331] [cursor=pointer]
          - generic [ref=f1e333]:
            - group "Reference and response" [ref=f1e334]:
              - generic [ref=f1e336]:
                - generic [ref=f1e337]:
                  - text: Target
                  - generic [ref=f1e338]: "1"
                  - spinbutton "Target 1" [ref=f1e339]: "1"
                - paragraph [ref=f1e340]: Normalized reference setpoint, dimensionless.
                - generic [ref=f1e341]:
                  - generic [ref=f1e342]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f1e343]
              - generic [ref=f1e344]:
                - generic [ref=f1e345]:
                  - text: Response gain
                  - generic [ref=f1e346]: "1"
                  - spinbutton "Response gain 1" [ref=f1e347]: "0.8"
                - paragraph [ref=f1e348]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f1e349]:
                  - generic [ref=f1e350]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f1e351]
              - generic [ref=f1e352]:
                - generic [ref=f1e353]:
                  - text: Initial state
                  - generic [ref=f1e354]: "1"
                  - spinbutton "Initial state 1" [ref=f1e355]: "0"
                - paragraph [ref=f1e356]: Initial normalized scalar state.
                - generic [ref=f1e357]:
                  - generic [ref=f1e358]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f1e359]
            - group "Drive horizon" [ref=f1e360]:
              - generic [ref=f1e362]:
                - generic [ref=f1e363]:
                  - text: Duration
                  - generic [ref=f1e364]: s
                  - spinbutton "Duration s" [ref=f1e365]: "6"
                - paragraph [ref=f1e366]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f1e367]:
                  - generic [ref=f1e368]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f1e369]
              - generic [ref=f1e370]:
                - generic [ref=f1e371]:
                  - text: Time step
                  - generic [ref=f1e372]: s
                  - spinbutton "Time step s" [ref=f1e373]: "0.1"
                - paragraph [ref=f1e374]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f1e375]:
                  - generic [ref=f1e376]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f1e377]
            - group "Sensor faults" [ref=f1e378]:
              - generic [ref=f1e380]:
                - generic [ref=f1e381]:
                  - text: Reference fault
                  - generic [ref=f1e382]: "1"
                  - combobox "Reference fault 1" [ref=f1e383]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f1e384]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f1e385]:
                  - generic [ref=f1e386]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f1e387]
          - generic [ref=f1e388]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e393]:
        - generic [ref=f1e394]: Local project · Saved on backend
        - generic [ref=f1e397]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e398]: 1 provider(s) available
  - dialog [ref=f1e400]:
    - banner [ref=f1e401]:
      - heading "Execution preflight" [level=2] [ref=f1e402]
      - button "Close dialog" [ref=f1e403] [cursor=pointer]
    - generic [ref=f1e406]:
      - generic [ref=f1e407]:
        - generic [ref=f1e408]:
          - generic [ref=f1e409]: FROZEN EXECUTION REQUEST
          - 'heading "Admission decision: ready" [level=3] [ref=f1e410]'
        - paragraph [ref=f1e411]: These checks apply to this request and provider. Execution, observations, assertions, cleanup and evidence integrity have separate outcomes.
      - generic [ref=f1e412]:
        - generic [ref=f1e413]:
          - text: Execution provider
          - combobox "Execution provider" [ref=f1e414]:
            - option "Studio executable reference · studio.reference" [selected]
            - option "X-Verse Lite / CARLA · xverse.lite · unavailable"
        - button "Recheck readiness" [ref=f1e415] [cursor=pointer]
      - generic [ref=f1e416]:
        - generic [ref=f1e417]:
          - text: Snapshot
          - code [ref=f1e418]: snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050
        - generic [ref=f1e419]:
          - text: Revision
          - strong [ref=f1e420]: "3"
        - generic [ref=f1e421]:
          - text: Expires
          - strong [ref=f1e422]: 10/27/2026, 12:03:44 AM
        - generic [ref=f1e423]:
          - text: Scope
          - strong [ref=f1e424]: owned_reference
      - group [ref=f1e425]:
        - generic "Frozen request identities" [ref=f1e426] [cursor=pointer]
        - generic [ref=f1e427]:
          - generic [ref=f1e428]:
            - term [ref=f1e429]: Preflight ID
            - definition [ref=f1e430]: pf-2a22eb44-6ff5-46cf-8d94-1d6d190e5a67
          - generic [ref=f1e431]:
            - term [ref=f1e432]: Frozen snapshot
            - definition [ref=f1e433]: snap-f6bba753-fca8-4f8b-b3ee-58ff6aed5050
          - generic [ref=f1e434]:
            - term [ref=f1e435]: Snapshot identity
            - definition [ref=f1e436]: sha256:28dee0fbea8e39e5f7b8fc4c7872c3e967b814e1fae861dd5cb288ee079577ee
          - generic [ref=f1e437]:
            - term [ref=f1e438]: Plan identity
            - definition [ref=f1e439]: sha256:ddabb9d84a31de7aa154ad333fad0098cd175dd88449996a45d68a0b3f2c55fa
          - generic [ref=f1e440]:
            - term [ref=f1e441]: Semantic identity
            - definition [ref=f1e442]: sha256:e33cd8692bcc6b771f46bc148ada97fe2465487657aa84c282d03eb8e09509a1
          - generic [ref=f1e443]:
            - term [ref=f1e444]: Provider
            - definition [ref=f1e445]: studio.reference
          - generic [ref=f1e446]:
            - term [ref=f1e447]: Provider version
            - definition [ref=f1e448]: 1.0.0
          - generic [ref=f1e449]:
            - term [ref=f1e450]: Evidence scope
            - definition [ref=f1e451]: owned_reference
          - generic [ref=f1e452]:
            - term [ref=f1e453]: Capability identity
            - definition [ref=f1e454]: sha256:c16a8f54e1b9276ab1a78399b4948d64ce6e58f7ce1d50b8c56720d389ec952e
          - generic [ref=f1e455]:
            - term [ref=f1e456]: Expires
            - definition [ref=f1e457]: 10/27/2026, 12:03:44 AM
      - generic [ref=f1e458]:
        - heading "Readiness checks" [level=3] [ref=f1e459]
        - table "Independent readiness dimensions" [ref=f1e461]:
          - rowgroup [ref=f1e462]:
            - row [ref=f1e463]:
              - columnheader "Dimension" [ref=f1e464]
              - columnheader "Reported state" [ref=f1e465]
              - columnheader "Evidence and next action" [ref=f1e466]
          - rowgroup [ref=f1e467]:
            - row [ref=f1e468]:
              - rowheader "Studio backend" [ref=f1e469]
              - cell "available" [ref=f1e470]
              - cell [ref=f1e472]:
                - paragraph [ref=f1e473]: The authenticated native Studio backend is responding; no runtime liveness is inferred.
                - list [ref=f1e474]:
                  - listitem [ref=f1e475]:
                    - code [ref=f1e476]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e477]:
                  - generic "Inspect exact data" [ref=f1e478] [cursor=pointer]
            - row [ref=f1e479]:
              - rowheader "Provider / host compatibility" [ref=f1e480]
              - cell "available" [ref=f1e481]
              - cell [ref=f1e483]:
                - paragraph [ref=f1e484]: The installed owned reference provider declares compatibility with this native OS/architecture.
                - list [ref=f1e485]:
                  - listitem [ref=f1e486]:
                    - code [ref=f1e487]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e488]:
                  - generic "Inspect exact data" [ref=f1e489] [cursor=pointer]
            - row [ref=f1e490]:
              - rowheader "Model validity" [ref=f1e491]
              - cell "valid" [ref=f1e492]
              - cell [ref=f1e494]:
                - paragraph [ref=f1e495]: Public XDL validation and declared-intent compilation succeeded.
                - list [ref=f1e496]:
                  - listitem [ref=f1e497]:
                    - code [ref=f1e498]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=f1e499]:
              - rowheader "Artifact availability" [ref=f1e500]
              - cell "available" [ref=f1e501]
              - cell [ref=f1e503]:
                - paragraph [ref=f1e504]: Every selected artifact reference matches the installed owned model contract digest; no external download was performed.
                - list [ref=f1e505]:
                  - listitem [ref=f1e506]:
                    - code [ref=f1e507]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e508]:
                  - generic "Inspect exact data" [ref=f1e509] [cursor=pointer]
            - row [ref=f1e510]:
              - rowheader "Capability compatibility" [ref=f1e511]
              - cell "compatible" [ref=f1e512]
              - cell [ref=f1e514]:
                - paragraph [ref=f1e515]: The exact source/configuration matches the admitted owned reference contract.
                - list [ref=f1e516]:
                  - listitem [ref=f1e517]:
                    - code [ref=f1e518]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=f1e519]:
              - rowheader "Target readiness" [ref=f1e520]
              - cell "ready" [ref=f1e521]
              - cell [ref=f1e523]:
                - paragraph [ref=f1e524]: The owned executable can accept these inputs; it has not been started and no liveness/health is asserted.
                - list [ref=f1e525]:
                  - listitem [ref=f1e526]:
                    - code [ref=f1e527]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=f1e528]:
              - rowheader "Resource availability" [ref=f1e529]
              - cell "available" [ref=f1e530]
              - cell [ref=f1e532]:
                - paragraph [ref=f1e533]: Advertised reference budgets have capacity at this read-only check.
                - list [ref=f1e534]:
                  - listitem [ref=f1e535]:
                    - code [ref=f1e536]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e537]:
                  - generic "Inspect exact data" [ref=f1e538] [cursor=pointer]
            - row [ref=f1e539]:
              - rowheader "Execution ownership" [ref=f1e540]
              - cell "available" [ref=f1e541]
              - cell [ref=f1e543]:
                - paragraph [ref=f1e544]: A new reference run will be owned by the native backend; browser disconnection does not own its lifetime.
                - list [ref=f1e545]:
                  - listitem [ref=f1e546]:
                    - code [ref=f1e547]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e548]:
                  - generic "Inspect exact data" [ref=f1e549] [cursor=pointer]
            - row [ref=f1e550]:
              - rowheader "Clock mappings" [ref=f1e551]
              - cell "compatible" [ref=f1e552]
              - cell [ref=f1e554]:
                - paragraph [ref=f1e555]: The owned simulation clock is declared; no cross-clock mapping or physical synchronization is claimed.
                - list [ref=f1e556]:
                  - listitem [ref=f1e557]:
                    - code [ref=f1e558]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e559]:
                  - generic "Inspect exact data" [ref=f1e560] [cursor=pointer]
            - row [ref=f1e561]:
              - rowheader "Execution authority" [ref=f1e562]
              - cell "available" [ref=f1e563]
              - cell [ref=f1e565]:
                - paragraph [ref=f1e566]: Backend-owned reference execution is admitted; no physical permit is acquired.
                - list [ref=f1e567]:
                  - listitem [ref=f1e568]:
                    - code [ref=f1e569]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e570]:
                  - generic "Inspect exact data" [ref=f1e571] [cursor=pointer]
      - generic [ref=f1e572]:
        - heading "Advertised execution limits" [level=3] [ref=f1e573]
        - paragraph [ref=f1e574]: These are the backend-reported bounds for studio.reference. Limits are rechecked by the backend before execution.
        - table "Advertised execution limits" [ref=f1e576]:
          - rowgroup [ref=f1e577]:
            - row [ref=f1e578]:
              - columnheader "Contract limit" [ref=f1e579]
              - columnheader "Exact advertised value" [ref=f1e580]
          - rowgroup [ref=f1e581]:
            - row [ref=f1e582]:
              - cell [ref=f1e583]:
                - code [ref=f1e584]: maxDurationSeconds
              - cell "30" [ref=f1e585]
            - row [ref=f1e586]:
              - cell [ref=f1e587]:
                - code [ref=f1e588]: maxSamples
              - cell "3000" [ref=f1e589]
            - row [ref=f1e590]:
              - cell [ref=f1e591]:
                - code [ref=f1e592]: maxConcurrentRuns
              - cell "4" [ref=f1e593]
            - row [ref=f1e594]:
              - cell [ref=f1e595]:
                - code [ref=f1e596]: maxElements
              - cell "200" [ref=f1e597]
            - row [ref=f1e598]:
              - cell [ref=f1e599]:
                - code [ref=f1e600]: maxConnections
              - cell "400" [ref=f1e601]
      - region "Readiness diagnostics" [ref=f1e602]:
        - heading "Diagnostic explanations" [level=3] [ref=f1e603]
        - paragraph [ref=f1e604]: No diagnostics reported for this request.
      - region "Readiness explanation" [ref=f1e605]:
        - heading "Readiness explanation" [level=3] [ref=f1e606]
        - paragraph [ref=f1e607]: Facts cite retained evidence. Studio does not infer root causes; hypotheses are unconfirmed and unknowns stay unknown.
        - paragraph [ref=f1e608]: No blocking findings were recorded for this frozen preflight. Readiness is not runtime health.
      - generic [ref=f1e609]:
        - generic [ref=f1e610]:
          - heading "Compiled plan" [level=3] [ref=f1e611]
          - button "Inspect compiled plan" [ref=f1e612] [cursor=pointer]
        - paragraph [ref=f1e613]: Frozen plan identities match
        - paragraph [ref=f1e614]: The identity fields match the backend's frozen preflight. Platform compiler output is read-only. Start rechecks mutable admission facts.
      - generic [ref=f1e615]:
        - button "Back to draft" [ref=f1e616] [cursor=pointer]
        - button "Start frozen snapshot" [active] [ref=f1e617] [cursor=pointer]
```

# Test source

```ts
  261 |           expect(JSON.parse(history!).undo).toHaveLength(1);
  262 |           const ready = page.waitForResponse(
  263 |             (r) =>
  264 |               new URL(r.url()).pathname ===
  265 |                 `/api/v1/projects/${project.projectId}/preflights` &&
  266 |               r.request().method() === "POST",
  267 |           );
  268 |           await activate(
  269 |             page,
  270 |             page.getByRole("button", { name: "Preflight & run", exact: true }),
  271 |           );
  272 |           const report = await (await ready).json();
  273 |           expect(report.status).toBe("ready");
  274 |           readyId = report.preflightId;
  275 |           readySnapshot = report.snapshotId;
  276 |           await activate(
  277 |             page,
  278 |             page.getByText("Frozen request identities", { exact: true }),
  279 |           );
  280 |           await expect(
  281 |             page.getByRole("dialog").getByText(readyId!, { exact: true }),
  282 |           ).toBeVisible();
  283 |           await tabTo(
  284 |             page,
  285 |             page.getByRole("button", {
  286 |               name: "Start frozen snapshot",
  287 |               exact: true,
  288 |             }),
  289 |           );
  290 |         }
  291 |         await pending.release();
  292 |         await settle(page);
  293 |         expect(pending.writes).toHaveLength(1);
  294 |         const saved = await request(page, `/projects/${project.projectId}`);
  295 |         if (mode === "current pending") {
  296 |           await expect(panel(page)).toHaveCount(0);
  297 |           await expect(page.locator(".project-header h1")).toHaveText(
  298 |             project.name,
  299 |           );
  300 |           await expect(
  301 |             page.getByText(
  302 |               "Profile locks saved with exact schema and presentation identities.",
  303 |               { exact: true },
  304 |             ),
  305 |           ).toBeVisible();
  306 |           const source = page.getByRole("button", {
  307 |             name: "XDL source",
  308 |             exact: true,
  309 |           });
  310 |           await expect(source).toBeFocused();
  311 |           const box = await source.boundingBox();
  312 |           expect(box!.y).toBeGreaterThanOrEqual(0);
  313 |           expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height);
  314 |           expect(saved.revision).toBe(committed.revision);
  315 |         } else if (mode === "newer selection" || mode === "deliberate focus") {
  316 |           await expect(panel(page)).toBeVisible();
  317 |           await expect(checkbox).toBeChecked();
  318 |           await expect(
  319 |             panel(page).getByText(
  320 |               `Selected project: ${project.name} · revision ${committed.revision}`,
  321 |               { exact: true },
  322 |             ),
  323 |           ).toBeVisible();
  324 |           await expect(panel(page).getByRole("status")).toContainText(
  325 |             "Saved the submitted profile locks",
  326 |           );
  327 |           if (newerChoice) {
  328 |             await expect(newerChoice).toBeChecked();
  329 |             await expect(newerChoice).toBeFocused();
  330 |             expect(
  331 |               saved.manifest.profiles.some(
  332 |                 (p: any) =>
  333 |                   p.namespace === "io.xverse.studio.domain.process-control",
  334 |               ),
  335 |             ).toBe(false);
  336 |           } else
  337 |             await expect(
  338 |               page.getByRole("button", {
  339 |                 name: "X-Verse Studio home",
  340 |                 exact: true,
  341 |               }),
  342 |             ).toBeFocused();
  343 |         } else {
  344 |           expect(saved.documents).toEqual(newest.documents);
  345 |           expect(saved.revision).toBe(newest.revision);
  346 |           expect(
  347 |             await page.evaluate(
  348 |               (pid) => sessionStorage.getItem("studio.graphHistory." + pid),
  349 |               project.projectId,
  350 |             ),
  351 |           ).toBe(history);
  352 |           const dialog = page.getByRole("dialog", {
  353 |             name: "Execution preflight",
  354 |             exact: true,
  355 |           });
  356 |           await expect(
  357 |             dialog.getByText(readyId!, { exact: true }),
  358 |           ).toBeVisible();
  359 |           await expect(
  360 |             dialog.getByText(readySnapshot!, { exact: true }),
> 361 |           ).toBeVisible();
      |             ^ Error: expect(locator).toBeVisible() failed
  362 |           await expect(
  363 |             dialog.getByRole("button", {
  364 |               name: "Start frozen snapshot",
  365 |               exact: true,
  366 |             }),
  367 |           ).toBeEnabled();
  368 |           await expect(
  369 |             dialog.getByRole("button", {
  370 |               name: "Start frozen snapshot",
  371 |               exact: true,
  372 |             }),
  373 |           ).toBeFocused();
  374 |         }
  375 |         expect(await runs(page, project.projectId)).toEqual(beforeRuns);
  376 |         await info.attach("profile-completion.json", {
  377 |           body: JSON.stringify({
  378 |             viewport,
  379 |             mode,
  380 |             projectId: project.projectId,
  381 |             committedRevision: committed.revision,
  382 |             currentRevision: saved.revision,
  383 |             actualPendingPosts: pending.writes.length,
  384 |             readyId,
  385 |             readySnapshot,
  386 |             measurements: [guidance],
  387 |             noStart: true,
  388 |             scope:
  389 |               "Actual immutable profile transaction; preserve current navigation, checkbox/focus intent, newer canonical history and real ready preflight",
  390 |           }),
  391 |           contentType: "application/json",
  392 |         });
  393 |       } finally {
  394 |         await pending.close();
  395 |       }
  396 |     });
  397 |   }
  398 |   for (const departed of [false, true]) {
  399 |     test(`profile bindings: actual stale refusal ${departed ? "after departure" : "current"} at ${viewport.width}x${viewport.height}`, async ({
  400 |       page,
  401 |     }, info) => {
  402 |       test.setTimeout(90000);
  403 |       await page.setViewportSize(viewport);
  404 |       await connectStudio(page, info);
  405 |       const project = await create(
  406 |           page,
  407 |           `Stale profile ${departed} ${viewport.width}`,
  408 |         ),
  409 |         entries = (await request(page, "/profiles")).items,
  410 |         other = entries.find(
  411 |           (p: any) => p.namespace === "io.xverse.studio.domain.process-control",
  412 |         ),
  413 |         beforeRuns = await runs(page, project.projectId);
  414 |       await environment(page);
  415 |       const checkbox = await choose(page, "Automotive terminology");
  416 |       const advanced = await request(
  417 |         page,
  418 |         `/projects/${project.projectId}/profile-bindings`,
  419 |         { baseRevision: project.revision, profiles: [identity(other)] },
  420 |         project.revision,
  421 |       );
  422 |       const pending = await holdBinding(page, project.projectId, 412);
  423 |       try {
  424 |         await activate(page, bind(page));
  425 |         const rejected = await pending.ready();
  426 |         expect(rejected.code).toBe("REVISION_CONFLICT");
  427 |         if (departed)
  428 |           await activate(
  429 |             page,
  430 |             page.getByRole("button", {
  431 |               name: "X-Verse Studio home",
  432 |               exact: true,
  433 |             }),
  434 |           );
  435 |         await pending.release();
  436 |         await settle(page);
  437 |         if (departed) {
  438 |           await expect(
  439 |             page.getByRole("heading", { name: "Recent projects", exact: true }),
  440 |           ).toBeVisible();
  441 |           await expect(page.locator(".alerts .notice.error")).toHaveCount(0);
  442 |         } else {
  443 |           await expect(checkbox).toBeChecked();
  444 |           await expect(bind(page)).toBeEnabled();
  445 |           const error = page.getByRole("alert", {
  446 |             name: "Operation error",
  447 |             exact: true,
  448 |           });
  449 |           await expect(error).toContainText("REVISION_CONFLICT");
  450 |           await expect(error).toBeFocused();
  451 |           await activate(
  452 |             page,
  453 |             error.getByRole("button", {
  454 |               name: "Load current revision",
  455 |               exact: true,
  456 |             }),
  457 |           );
  458 |           await expect(page.locator(".workspace-context")).toContainText(
  459 |             `Draft revision ${advanced.revision}`,
  460 |           );
  461 |         }
```
