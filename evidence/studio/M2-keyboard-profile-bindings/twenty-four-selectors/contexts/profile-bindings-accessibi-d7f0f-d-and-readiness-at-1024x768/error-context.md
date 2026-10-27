# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: newer head and readiness at 1024x768
- Location: tests/e2e/profile-bindings-accessibility.spec.ts:177:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-790a16f5-21ac-4b6c-81df-171e1a92c81c', { exact: true })
Expected: visible
Error: strict mode violation: getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-790a16f5-21ac-4b6c-81df-171e1a92c81c', { exact: true }) resolved to 2 elements:
    1) <code>snap-790a16f5-21ac-4b6c-81df-171e1a92c81c</code> aka getByRole('code').filter({ hasText: 'snap-790a16f5-21ac-4b6c-81df-' })
    2) <dd>snap-790a16f5-21ac-4b6c-81df-171e1a92c81c</dd> aka getByRole('definition').filter({ hasText: 'snap-790a16f5-21ac-4b6c-81df-' })

Call log:
  - Expect "toBeVisible" getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-790a16f5-21ac-4b6c-81df-171e1a92c81c', { exact: true }) with timeout 10000ms
  - waiting for getByRole('dialog', { name: 'Execution preflight', exact: true }).getByText('snap-790a16f5-21ac-4b6c-81df-171e1a92c81c', { exact: true })

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
      - generic [ref=f1e50]:
        - generic [ref=f1e51]:
          - generic [ref=f1e52]:
            - button "Workspace" [ref=f1e53] [cursor=pointer]
            - generic [ref=f1e56]: System
          - generic [ref=f1e57]:
            - heading "Profile newer head and readiness 1024" [level=1] [ref=f1e64]
            - generic [ref=f1e65]: Draft
            - generic "Bound domain presentation. Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e66]: Automotive terms
        - generic [ref=f1e69]:
          - 'button "Dependencies: none unresolved" [ref=f1e70] [cursor=pointer]': Dependencies
          - button "Undo" [ref=f1e71] [cursor=pointer]
          - button "Redo" [disabled] [ref=f1e72]
          - button "Export" [ref=f1e73] [cursor=pointer]
          - button "Validate" [ref=f1e76] [cursor=pointer]
          - button "Preflight & run" [ref=f1e79] [cursor=pointer]
      - tablist "System workflows" [ref=f1e82]:
        - tab "Model" [selected] [ref=f1e83] [cursor=pointer]
        - tab "Connections" [ref=f1e89] [cursor=pointer]
        - tab "Deployment" [ref=f1e94] [cursor=pointer]
        - tab "Experiments" [ref=f1e97] [cursor=pointer]
        - tab "Results" [ref=f1e100] [cursor=pointer]
        - button "XDL source" [ref=f1e104] [cursor=pointer]
      - generic [ref=f1e107]:
        - generic [ref=f1e108]:
          - text: Draft revision
          - code [ref=f1e110]: "3"
        - generic [ref=f1e111]: 3 elements · 2 connections
        - generic [ref=f1e112]:
          - text: Execution scope
          - generic [ref=f1e113]: Owned reference
      - generic [ref=f1e114]:
        - complementary "Structured model navigation" [ref=f1e115]:
          - generic [ref=f1e116]:
            - heading "Vehicle function explorer" [level=2] [ref=f1e117]
            - button "View XDL source" [ref=f1e118] [cursor=pointer]
          - textbox "Search elements" [ref=f1e125]:
            - /placeholder: Find an element…
          - generic [ref=f1e126]:
            - strong [ref=f1e132]: reference-loop
            - generic [ref=f1e133]: "3"
            - button "Group by node" [ref=f1e134] [cursor=pointer]
          - generic [ref=f1e135]:
            - button "controller controller" [ref=f1e136] [cursor=pointer]:
              - generic [ref=f1e142]: controller
              - generic [ref=f1e143]: controller
            - button "plant plant" [ref=f1e144] [cursor=pointer]:
              - generic [ref=f1e150]: plant
              - generic [ref=f1e151]: plant
            - button "observer-node observer" [ref=f1e152] [cursor=pointer]:
              - generic [ref=f1e155]: observer-node
              - generic [ref=f1e156]: observer
          - generic [ref=f1e157]:
            - generic [ref=f1e158]: RESOURCES
            - button "reference-controller Component" [ref=f1e159] [cursor=pointer]:
              - generic [ref=f1e162]: reference-controller
              - generic [ref=f1e163]: Component
            - button "reference-plant Component" [ref=f1e164] [cursor=pointer]:
              - generic [ref=f1e167]: reference-plant
              - generic [ref=f1e168]: Component
            - button "reference-loop System" [ref=f1e169] [cursor=pointer]:
              - generic [ref=f1e172]: reference-loop
              - generic [ref=f1e173]: System
            - button "local-reference Deployment" [ref=f1e174] [cursor=pointer]:
              - generic [ref=f1e177]: local-reference
              - generic [ref=f1e178]: Deployment
            - button "reference-response Scenario" [ref=f1e179] [cursor=pointer]:
              - generic [ref=f1e182]: reference-response
              - generic [ref=f1e183]: Scenario
            - button "experiment-lite Profile" [ref=f1e184] [cursor=pointer]:
              - generic [ref=f1e187]: experiment-lite
              - generic [ref=f1e188]: Profile
            - button "studio-experiments Profile" [ref=f1e189] [cursor=pointer]:
              - generic [ref=f1e192]: studio-experiments
              - generic [ref=f1e193]: Profile
            - button "domain-automotive Profile" [ref=f1e194] [cursor=pointer]:
              - generic [ref=f1e197]: domain-automotive
              - generic [ref=f1e198]: Profile
          - button "Add element" [ref=f1e200] [cursor=pointer]
        - region "Model canvas" [ref=f1e203]:
          - generic:
            - generic [ref=f1e204]:
              - generic [ref=f1e205]: LOGICAL MODEL
              - generic [ref=f1e206]: 1.0.0
            - generic [ref=f1e207]:
              - button "Table view" [ref=f1e208] [cursor=pointer]
              - button "Auto layout" [ref=f1e209] [cursor=pointer]
              - button "Save layout" [ref=f1e210] [cursor=pointer]
          - application "Logical System graph. Use the System explorer for keyboard selection." [ref=f1e211]:
            - generic [ref=f1e213]:
              - generic:
                - generic:
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#controller to xdl://org.xverse.studio.process-control/system/reference-loop#plant" [ref=f1e214] [cursor=pointer]:
                      - generic [ref=f1e217]: command-flow
                  - img:
                    - group "Edge from xdl://org.xverse.studio.process-control/system/reference-loop#plant to xdl://org.xverse.studio.process-control/system/reference-loop#observer-node" [ref=f1e219] [cursor=pointer]:
                      - generic [ref=f1e222]: state-flow
                - generic:
                  - group [ref=f1e224]:
                    - generic [ref=f1e225]:
                      - generic [ref=f1e227]: controller
                      - strong [ref=f1e236]: controller
                      - code [ref=f1e237]: controller
                      - list "Named ports" [ref=f1e238]:
                        - listitem [ref=f1e239]:
                          - generic [aria-hidden] [ref=f1e240]: ←
                          - code [ref=f1e241]: controller-out
                          - generic [ref=f1e242]: output
                      - generic [ref=f1e243]:
                        - generic [ref=f1e244]: Logical element
                        - generic [ref=f1e245]: 1 ports
                  - group [ref=f1e247]:
                    - generic [ref=f1e248]:
                      - generic [ref=f1e250]: plant
                      - strong [ref=f1e259]: plant
                      - code [ref=f1e260]: plant
                      - list "Named ports" [ref=f1e261]:
                        - listitem [ref=f1e262]:
                          - generic [aria-hidden] [ref=f1e263]: →
                          - code [ref=f1e264]: plant-in
                          - generic [ref=f1e265]: input
                        - listitem [ref=f1e266]:
                          - generic [aria-hidden] [ref=f1e267]: ←
                          - code [ref=f1e268]: plant-out
                          - generic [ref=f1e269]: output
                      - generic [ref=f1e270]:
                        - generic [ref=f1e271]: Logical element
                        - generic [ref=f1e272]: 2 ports
                  - group [ref=f1e274]:
                    - generic [ref=f1e275]:
                      - generic [ref=f1e277]: observer
                      - strong [ref=f1e283]: observer-node
                      - code [ref=f1e284]: observer-node
                      - list "Named ports" [ref=f1e285]:
                        - listitem [ref=f1e286]:
                          - generic [aria-hidden] [ref=f1e287]: →
                          - code [ref=f1e288]: observer-in
                          - generic [ref=f1e289]: input
                      - generic [ref=f1e290]:
                        - generic [ref=f1e291]: Logical element
                        - generic [ref=f1e292]: 1 ports
            - generic "Control Panel" [ref=f1e294]:
              - button "Zoom In" [ref=f1e295] [cursor=pointer]
              - button "Zoom Out" [ref=f1e298] [cursor=pointer]
              - button "Fit View" [ref=f1e301] [cursor=pointer]
            - img "Mini Map" [ref=f1e305]
          - generic:
            - generic: Declared communication
            - generic: Logical element
            - generic: Graph positions are presentation only
        - complementary "Element inspector" [ref=f1e310]:
          - heading "System inspector" [level=2] [ref=f1e312]
          - generic [ref=f1e318]:
            - heading "reference-loop" [level=3] [ref=f1e322]
            - paragraph [ref=f1e323]: Authoritative XDL System
            - generic [ref=f1e324]: Draft model
          - navigation "Model location" [ref=f1e325]:
            - button "reference-loop" [ref=f1e326] [cursor=pointer]
          - generic [ref=f1e327]:
            - button "Properties" [ref=f1e328] [cursor=pointer]
            - button "Parameters" [ref=f1e329] [cursor=pointer]
          - generic [ref=f1e331]:
            - group "Reference and response" [ref=f1e332]:
              - generic [ref=f1e334]:
                - generic [ref=f1e335]:
                  - text: Target
                  - generic [ref=f1e336]: "1"
                  - spinbutton "Target 1" [ref=f1e337]: "1"
                - paragraph [ref=f1e338]: Normalized reference setpoint, dimensionless.
                - generic [ref=f1e339]:
                  - generic [ref=f1e340]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f1e341]
              - generic [ref=f1e342]:
                - generic [ref=f1e343]:
                  - text: Response gain
                  - generic [ref=f1e344]: "1"
                  - spinbutton "Response gain 1" [ref=f1e345]: "0.8"
                - paragraph [ref=f1e346]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f1e347]:
                  - generic [ref=f1e348]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f1e349]
              - generic [ref=f1e350]:
                - generic [ref=f1e351]:
                  - text: Initial state
                  - generic [ref=f1e352]: "1"
                  - spinbutton "Initial state 1" [ref=f1e353]: "0"
                - paragraph [ref=f1e354]: Initial normalized scalar state.
                - generic [ref=f1e355]:
                  - generic [ref=f1e356]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f1e357]
            - group "Drive horizon" [ref=f1e358]:
              - generic [ref=f1e360]:
                - generic [ref=f1e361]:
                  - text: Duration
                  - generic [ref=f1e362]: s
                  - spinbutton "Duration s" [ref=f1e363]: "6"
                - paragraph [ref=f1e364]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f1e365]:
                  - generic [ref=f1e366]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f1e367]
              - generic [ref=f1e368]:
                - generic [ref=f1e369]:
                  - text: Time step
                  - generic [ref=f1e370]: s
                  - spinbutton "Time step s" [ref=f1e371]: "0.1"
                - paragraph [ref=f1e372]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f1e373]:
                  - generic [ref=f1e374]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f1e375]
            - group "Sensor faults" [ref=f1e376]:
              - generic [ref=f1e378]:
                - generic [ref=f1e379]:
                  - text: Reference fault
                  - generic [ref=f1e380]: "1"
                  - combobox "Reference fault 1" [ref=f1e381]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f1e382]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f1e383]:
                  - generic [ref=f1e384]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f1e385]
          - generic [ref=f1e386]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e391]:
        - generic [ref=f1e392]: Local project · Saved on backend
        - generic [ref=f1e395]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e396]: 1 provider(s) available
  - dialog [ref=f1e398]:
    - banner [ref=f1e399]:
      - heading "Execution preflight" [level=2] [ref=f1e400]
      - button "Close dialog" [ref=f1e401] [cursor=pointer]
    - generic [ref=f1e404]:
      - generic [ref=f1e405]:
        - generic [ref=f1e406]:
          - generic [ref=f1e407]: FROZEN EXECUTION REQUEST
          - 'heading "Admission decision: ready" [level=3] [ref=f1e408]'
        - paragraph [ref=f1e409]: These checks apply to this request and provider. Execution, observations, assertions, cleanup and evidence integrity have separate outcomes.
      - generic [ref=f1e410]:
        - generic [ref=f1e411]:
          - text: Execution provider
          - combobox "Execution provider" [ref=f1e412]:
            - option "Studio executable reference · studio.reference" [selected]
            - option "X-Verse Lite / CARLA · xverse.lite · unavailable"
        - button "Recheck readiness" [ref=f1e413] [cursor=pointer]
      - generic [ref=f1e414]:
        - generic [ref=f1e415]:
          - text: Snapshot
          - code [ref=f1e416]: snap-790a16f5-21ac-4b6c-81df-171e1a92c81c
        - generic [ref=f1e417]:
          - text: Revision
          - strong [ref=f1e418]: "3"
        - generic [ref=f1e419]:
          - text: Expires
          - strong [ref=f1e420]: 10/27/2026, 12:03:05 AM
        - generic [ref=f1e421]:
          - text: Scope
          - strong [ref=f1e422]: owned_reference
      - group [ref=f1e423]:
        - generic "Frozen request identities" [ref=f1e424] [cursor=pointer]
        - generic [ref=f1e425]:
          - generic [ref=f1e426]:
            - term [ref=f1e427]: Preflight ID
            - definition [ref=f1e428]: pf-ff28e133-ffa5-4fcc-975c-24c70f500e50
          - generic [ref=f1e429]:
            - term [ref=f1e430]: Frozen snapshot
            - definition [ref=f1e431]: snap-790a16f5-21ac-4b6c-81df-171e1a92c81c
          - generic [ref=f1e432]:
            - term [ref=f1e433]: Snapshot identity
            - definition [ref=f1e434]: sha256:3f29ce68078dba350c71769832427e69837fb6ded111779397c8689f083fe6f5
          - generic [ref=f1e435]:
            - term [ref=f1e436]: Plan identity
            - definition [ref=f1e437]: sha256:ddabb9d84a31de7aa154ad333fad0098cd175dd88449996a45d68a0b3f2c55fa
          - generic [ref=f1e438]:
            - term [ref=f1e439]: Semantic identity
            - definition [ref=f1e440]: sha256:e33cd8692bcc6b771f46bc148ada97fe2465487657aa84c282d03eb8e09509a1
          - generic [ref=f1e441]:
            - term [ref=f1e442]: Provider
            - definition [ref=f1e443]: studio.reference
          - generic [ref=f1e444]:
            - term [ref=f1e445]: Provider version
            - definition [ref=f1e446]: 1.0.0
          - generic [ref=f1e447]:
            - term [ref=f1e448]: Evidence scope
            - definition [ref=f1e449]: owned_reference
          - generic [ref=f1e450]:
            - term [ref=f1e451]: Capability identity
            - definition [ref=f1e452]: sha256:c16a8f54e1b9276ab1a78399b4948d64ce6e58f7ce1d50b8c56720d389ec952e
          - generic [ref=f1e453]:
            - term [ref=f1e454]: Expires
            - definition [ref=f1e455]: 10/27/2026, 12:03:05 AM
      - generic [ref=f1e456]:
        - heading "Readiness checks" [level=3] [ref=f1e457]
        - table "Independent readiness dimensions" [ref=f1e459]:
          - rowgroup [ref=f1e460]:
            - row [ref=f1e461]:
              - columnheader "Dimension" [ref=f1e462]
              - columnheader "Reported state" [ref=f1e463]
              - columnheader "Evidence and next action" [ref=f1e464]
          - rowgroup [ref=f1e465]:
            - row [ref=f1e466]:
              - rowheader "Studio backend" [ref=f1e467]
              - cell "available" [ref=f1e468]
              - cell [ref=f1e470]:
                - paragraph [ref=f1e471]: The authenticated native Studio backend is responding; no runtime liveness is inferred.
                - list [ref=f1e472]:
                  - listitem [ref=f1e473]:
                    - code [ref=f1e474]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e475]:
                  - generic "Inspect exact data" [ref=f1e476] [cursor=pointer]
            - row [ref=f1e477]:
              - rowheader "Provider / host compatibility" [ref=f1e478]
              - cell "available" [ref=f1e479]
              - cell [ref=f1e481]:
                - paragraph [ref=f1e482]: The installed owned reference provider declares compatibility with this native OS/architecture.
                - list [ref=f1e483]:
                  - listitem [ref=f1e484]:
                    - code [ref=f1e485]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e486]:
                  - generic "Inspect exact data" [ref=f1e487] [cursor=pointer]
            - row [ref=f1e488]:
              - rowheader "Model validity" [ref=f1e489]
              - cell "valid" [ref=f1e490]
              - cell [ref=f1e492]:
                - paragraph [ref=f1e493]: Public XDL validation and declared-intent compilation succeeded.
                - list [ref=f1e494]:
                  - listitem [ref=f1e495]:
                    - code [ref=f1e496]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=f1e497]:
              - rowheader "Artifact availability" [ref=f1e498]
              - cell "available" [ref=f1e499]
              - cell [ref=f1e501]:
                - paragraph [ref=f1e502]: Every selected artifact reference matches the installed owned model contract digest; no external download was performed.
                - list [ref=f1e503]:
                  - listitem [ref=f1e504]:
                    - code [ref=f1e505]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e506]:
                  - generic "Inspect exact data" [ref=f1e507] [cursor=pointer]
            - row [ref=f1e508]:
              - rowheader "Capability compatibility" [ref=f1e509]
              - cell "compatible" [ref=f1e510]
              - cell [ref=f1e512]:
                - paragraph [ref=f1e513]: The exact source/configuration matches the admitted owned reference contract.
                - list [ref=f1e514]:
                  - listitem [ref=f1e515]:
                    - code [ref=f1e516]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=f1e517]:
              - rowheader "Target readiness" [ref=f1e518]
              - cell "ready" [ref=f1e519]
              - cell [ref=f1e521]:
                - paragraph [ref=f1e522]: The owned executable can accept these inputs; it has not been started and no liveness/health is asserted.
                - list [ref=f1e523]:
                  - listitem [ref=f1e524]:
                    - code [ref=f1e525]: xdl://org.xverse.studio.process-control/system/reference-loop
            - row [ref=f1e526]:
              - rowheader "Resource availability" [ref=f1e527]
              - cell "available" [ref=f1e528]
              - cell [ref=f1e530]:
                - paragraph [ref=f1e531]: Advertised reference budgets have capacity at this read-only check.
                - list [ref=f1e532]:
                  - listitem [ref=f1e533]:
                    - code [ref=f1e534]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e535]:
                  - generic "Inspect exact data" [ref=f1e536] [cursor=pointer]
            - row [ref=f1e537]:
              - rowheader "Execution ownership" [ref=f1e538]
              - cell "available" [ref=f1e539]
              - cell [ref=f1e541]:
                - paragraph [ref=f1e542]: A new reference run will be owned by the native backend; browser disconnection does not own its lifetime.
                - list [ref=f1e543]:
                  - listitem [ref=f1e544]:
                    - code [ref=f1e545]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e546]:
                  - generic "Inspect exact data" [ref=f1e547] [cursor=pointer]
            - row [ref=f1e548]:
              - rowheader "Clock mappings" [ref=f1e549]
              - cell "compatible" [ref=f1e550]
              - cell [ref=f1e552]:
                - paragraph [ref=f1e553]: The owned simulation clock is declared; no cross-clock mapping or physical synchronization is claimed.
                - list [ref=f1e554]:
                  - listitem [ref=f1e555]:
                    - code [ref=f1e556]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e557]:
                  - generic "Inspect exact data" [ref=f1e558] [cursor=pointer]
            - row [ref=f1e559]:
              - rowheader "Execution authority" [ref=f1e560]
              - cell "available" [ref=f1e561]
              - cell [ref=f1e563]:
                - paragraph [ref=f1e564]: Backend-owned reference execution is admitted; no physical permit is acquired.
                - list [ref=f1e565]:
                  - listitem [ref=f1e566]:
                    - code [ref=f1e567]: xdl://org.xverse.studio.process-control/system/reference-loop
                - group [ref=f1e568]:
                  - generic "Inspect exact data" [ref=f1e569] [cursor=pointer]
      - generic [ref=f1e570]:
        - heading "Advertised execution limits" [level=3] [ref=f1e571]
        - paragraph [ref=f1e572]: These are the backend-reported bounds for studio.reference. Limits are rechecked by the backend before execution.
        - table "Advertised execution limits" [ref=f1e574]:
          - rowgroup [ref=f1e575]:
            - row [ref=f1e576]:
              - columnheader "Contract limit" [ref=f1e577]
              - columnheader "Exact advertised value" [ref=f1e578]
          - rowgroup [ref=f1e579]:
            - row [ref=f1e580]:
              - cell [ref=f1e581]:
                - code [ref=f1e582]: maxDurationSeconds
              - cell "30" [ref=f1e583]
            - row [ref=f1e584]:
              - cell [ref=f1e585]:
                - code [ref=f1e586]: maxSamples
              - cell "3000" [ref=f1e587]
            - row [ref=f1e588]:
              - cell [ref=f1e589]:
                - code [ref=f1e590]: maxConcurrentRuns
              - cell "4" [ref=f1e591]
            - row [ref=f1e592]:
              - cell [ref=f1e593]:
                - code [ref=f1e594]: maxElements
              - cell "200" [ref=f1e595]
            - row [ref=f1e596]:
              - cell [ref=f1e597]:
                - code [ref=f1e598]: maxConnections
              - cell "400" [ref=f1e599]
      - region "Readiness diagnostics" [ref=f1e600]:
        - heading "Diagnostic explanations" [level=3] [ref=f1e601]
        - paragraph [ref=f1e602]: No diagnostics reported for this request.
      - region "Readiness explanation" [ref=f1e603]:
        - heading "Readiness explanation" [level=3] [ref=f1e604]
        - paragraph [ref=f1e605]: Facts cite retained evidence. Studio does not infer root causes; hypotheses are unconfirmed and unknowns stay unknown.
        - paragraph [ref=f1e606]: No blocking findings were recorded for this frozen preflight. Readiness is not runtime health.
      - generic [ref=f1e607]:
        - generic [ref=f1e608]:
          - heading "Compiled plan" [level=3] [ref=f1e609]
          - button "Inspect compiled plan" [ref=f1e610] [cursor=pointer]
        - paragraph [ref=f1e611]: Frozen plan identities match
        - paragraph [ref=f1e612]: The identity fields match the backend's frozen preflight. Platform compiler output is read-only. Start rechecks mutable admission facts.
      - generic [ref=f1e613]:
        - button "Back to draft" [ref=f1e614] [cursor=pointer]
        - button "Start frozen snapshot" [active] [ref=f1e615] [cursor=pointer]
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
