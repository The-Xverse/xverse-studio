# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: physical-placements-accessibility.spec.ts >> physical placements: labelled matched metadata cannot grant admission at 1024x768
- Location: tests/e2e/physical-placements-accessibility.spec.ts:275:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: false
Received: true
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
            - heading "Placement observation 1024" [level=1] [ref=f1e64]
            - generic [ref=f1e65]: Draft
            - generic "Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched." [ref=f1e66]: Process control terms
        - generic [ref=f1e69]:
          - 'button "Dependencies: none unresolved" [ref=f1e70] [cursor=pointer]': Dependencies
          - button "Undo" [disabled] [ref=f1e71]
          - button "Redo" [disabled] [ref=f1e72]
          - button "Export" [ref=f1e73] [cursor=pointer]
          - button "Validate" [ref=f1e76] [cursor=pointer]
          - button "Preflight & run" [ref=f1e79] [cursor=pointer]
      - tablist "System workflows" [ref=f1e82]:
        - tab "Model" [ref=f1e83] [cursor=pointer]
        - tab "Connections" [ref=f1e89] [cursor=pointer]
        - tab "Deployment" [selected] [ref=f1e94] [cursor=pointer]
        - tab "Experiments" [ref=f1e97] [cursor=pointer]
        - tab "Results" [ref=f1e100] [cursor=pointer]
        - button "XDL source" [ref=f1e104] [cursor=pointer]
      - generic [ref=f1e107]:
        - generic [ref=f1e108]:
          - text: Draft revision
          - code [ref=f1e110]: "2"
        - generic [ref=f1e111]: 3 elements · 2 connections
        - generic [ref=f1e112]:
          - text: Execution scope
          - generic [ref=f1e113]: Owned reference
      - generic [ref=f1e114]:
        - generic [ref=f1e115]:
          - generic [ref=f1e116]:
            - heading "Plant deployment variants" [level=2] [ref=f1e117]
            - paragraph [ref=f1e118]: Select an authored Deployment and its associated Scenario. Logical System identities remain stable.
          - generic [ref=f1e119]: Explicit compiler selection
        - generic [ref=f1e120]:
          - generic [ref=f1e121]:
            - generic [ref=f1e122]:
              - text: Deployment variant
              - combobox "Deployment variant" [ref=f1e123]:
                - option "Choose an authored deployment"
                - option "local-reference" [selected]
            - generic [ref=f1e124]:
              - text: Associated Scenario
              - combobox "Associated Scenario" [ref=f1e125]:
                - option "Choose a matching Scenario"
                - option "reference-response" [selected]
          - generic [ref=f1e126]:
            - generic [ref=f1e127]:
              - term [ref=f1e128]: Requested Deployment
              - definition [ref=f1e129]: xdl://org.xverse.studio.process-control/deployment/local-reference
            - generic [ref=f1e130]:
              - term [ref=f1e131]: Requested Scenario
              - definition [ref=f1e132]: xdl://org.xverse.studio.process-control/scenario/reference-response
            - generic [ref=f1e133]:
              - term [ref=f1e134]: Readiness
              - definition [ref=f1e135]: Fresh preflight required before every new run
          - paragraph [ref=f1e136]: Selection does not rewrite either resource. The backend rejects mismatched contributors and freezes exact selected inputs before execution.
        - generic [ref=f1e137]:
          - heading "Create a named variant" [level=3] [ref=f1e138]
          - paragraph [ref=f1e139]: Clone the selected Deployment together with its matching Scenario. Parameters, assessment references, and logical topology retain explicit authored provenance.
          - generic [ref=f1e141]:
            - generic [ref=f1e142]:
              - text: New variant name
              - textbox "New variant name" [ref=f1e143]:
                - /placeholder: Alternative reference deployment
            - button "Create deployment variant" [disabled] [ref=f1e144]
        - region "Physical placement observation" [ref=f1e147]:
          - generic [ref=f1e148]:
            - heading "Physical placement observation" [level=3] [ref=f1e149]
            - button "Inspect physical placements" [ref=f1e150] [cursor=pointer]
          - paragraph [ref=f1e151]: Read-only observation of the selected Deployment and committed revision. Logical identity and authored source stay unchanged. Asset observations do not grant permission or make physical execution available.
          - paragraph [ref=f1e152]:
            - text: "Authored Deployment for inspection:"
            - code [ref=f1e153]: xdl://org.xverse.studio.process-control/deployment/local-reference
          - generic [ref=f1e154]:
            - generic [ref=f1e155]:
              - term [ref=f1e156]: Project revision
              - definition [ref=f1e157]: "2"
            - generic [ref=f1e158]:
              - term [ref=f1e159]: Deployment document
              - definition [ref=f1e160]: doc-3
            - generic [ref=f1e161]:
              - term [ref=f1e162]: System
              - definition [ref=f1e163]: xdl://org.xverse.studio.process-control/system/reference-loop
            - generic [ref=f1e164]:
              - term [ref=f1e165]: Deployment
              - definition [ref=f1e166]: xdl://org.xverse.studio.process-control/deployment/local-reference
            - generic [ref=f1e167]:
              - term [ref=f1e168]: Runtime admission
              - definition [ref=f1e169]: unavailable
            - generic [ref=f1e170]:
              - term [ref=f1e171]: Active-operation readiness
              - definition [ref=f1e172]: Blocked
          - list [ref=f1e173]:
            - listitem [ref=f1e174]:
              - strong [ref=f1e175]: PROVIDER_INVENTORY_UNAVAILABLE
              - generic [ref=f1e176]: "Provider observation: fixture"
          - status [ref=f1e177]: Inventory observation is incomplete; missing asset facts remain unknown. Inventory observations are truncated.
          - article [ref=f1e179]:
            - generic [ref=f1e180]:
              - heading "plant-binding" [level=4] [ref=f1e181]
              - generic [ref=f1e182]: fixture
            - generic [ref=f1e183]:
              - generic [ref=f1e184]:
                - term [ref=f1e185]: Logical reference
                - definition [ref=f1e186]: xdl://org.xverse.studio.process-control/system/reference-loop#plant
              - generic [ref=f1e187]:
                - term [ref=f1e188]: Authored realization
                - definition [ref=f1e189]: physical
              - generic [ref=f1e190]:
                - term [ref=f1e191]: Target identity
                - definition [ref=f1e192]: reference-target
              - generic [ref=f1e193]:
                - term [ref=f1e194]: Asset reference
                - definition [ref=f1e195]: urn:fixture:inventory-presentation
              - generic [ref=f1e196]:
                - term [ref=f1e197]: Identity observation
                - definition [ref=f1e198]: resolved
              - generic [ref=f1e199]:
                - term [ref=f1e200]: Interface observation
                - definition [ref=f1e201]: compatible
              - generic [ref=f1e202]:
                - term [ref=f1e203]: Availability observation
                - definition [ref=f1e204]: observed
              - generic [ref=f1e205]:
                - term [ref=f1e206]: Metadata coverage
                - definition [ref=f1e207]: partial
              - generic [ref=f1e208]:
                - term [ref=f1e209]: Provider admission
                - definition [ref=f1e210]: unavailable
              - generic [ref=f1e211]:
                - term [ref=f1e212]: Permission scope
                - definition [ref=f1e213]: unknown
              - generic [ref=f1e214]:
                - term [ref=f1e215]: Active operation
                - definition [ref=f1e216]: blocked
              - generic [ref=f1e217]:
                - term [ref=f1e218]: Required interfaces
                - definition [ref=f1e219]: command, state
            - status [ref=f1e220]: Required interface observations are truncated; omitted declarations are not displayed.
            - generic [ref=f1e221]:
              - generic [ref=f1e222]:
                - term [ref=f1e223]: Provider
                - definition [ref=f1e224]: fixture
              - generic [ref=f1e225]:
                - term [ref=f1e226]: Provider version
                - definition [ref=f1e227]: fixture-provider-1.0
              - generic [ref=f1e228]:
                - term [ref=f1e229]: Physical declaration
                - definition [ref=f1e230]: Declared physical asset
              - generic [ref=f1e231]:
                - term [ref=f1e232]: Observed identity
                - definition [ref=f1e233]: "{\"serial\":\"SYNTHETIC-UI-001\",\"model\":\"🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪\"}"
              - generic [ref=f1e234]:
                - term [ref=f1e235]: Firmware
                - definition [ref=f1e236]: Observed · 🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪
              - generic [ref=f1e237]:
                - term [ref=f1e238]: Artifact revision
                - definition [ref=f1e239]: Unknown
              - generic [ref=f1e240]:
                - term [ref=f1e241]: Provider OS declaration
                - definition [ref=f1e242]: Linux
              - generic [ref=f1e243]:
                - term [ref=f1e244]: Declared capabilities
                - definition [ref=f1e245]: observe, stimulate
            - list [ref=f1e246]:
              - listitem [ref=f1e247]:
                - strong [ref=f1e248]: PHYSICAL_PROVIDER_NOT_ADMITTED
                - generic [ref=f1e249]: Placement observation diagnostic
            - group [ref=f1e250]:
              - generic "Inspect exact data" [active] [ref=f1e251] [cursor=pointer]
              - generic [ref=f1e252]: "{ \"bindingId\": \"plant-binding\", \"logicalRef\": \"xdl://org.xverse.studio.process-control/system/reference-loop#plant\", \"targetId\": \"reference-target\", \"realizationClass\": \"physical\", \"assetId\": \"urn:fixture:inventory-presentation\", \"asset\": { \"assetId\": \"urn:fixture:inventory-presentation\", \"providerId\": \"fixture\", \"providerVersion\": \"fixture-provider-1.0\", \"physical\": true, \"identity\": { \"serial\": \"SYNTHETIC-UI-001\", \"model\": \"🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪\" }, \"identityStatus\": \"observed\", \"firmware\": { \"status\": \"observed\", \"version\": \"🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪\" }, \"artifactRevision\": { \"status\": \"unknown\" }, \"metadata\": { \"status\": \"partial\", \"limitations\": [ \"Only allowlisted identity and revision observations are exposed.\" ] }, \"interfaces\": { \"command\": { \"id\": \"command\", \"direction\": \"input\", \"payloadSchema\": \"urn:fixture:command\" } }, \"interfacesStatus\": \"declared\", \"supportedOS\": [ \"Linux\" ], \"observationTruncated\": false, \"capabilities\": [ \"observe\", \"stimulate\" ], \"permissionScope\": \"unknown\", \"available\": true, \"evidenceScope\": \"fixture\", \"providerAdmission\": \"unavailable\", \"activeReady\": false, \"reservable\": false, \"diagnostics\": [ { \"code\": \"PHYSICAL_PROVIDER_NOT_ADMITTED\", \"message\": \"Asset observation diagnostic\" } ] }, \"requiredInterfaces\": { \"command\": { \"id\": \"command\", \"direction\": \"bidirectional\", \"payloadSchema\": \"urn:xverse:studio:normalized-scalar:v1\", \"unitSemantics\": \"1\", \"compatibility\": \"exact\" }, \"state\": { \"id\": \"state\", \"direction\": \"bidirectional\", \"payloadSchema\": \"urn:xverse:studio:normalized-scalar:v1\", \"unitSemantics\": \"1\", \"compatibility\": \"exact\" } }, \"requiredInterfacesTruncated\": true, \"evidenceScope\": \"fixture\", \"ready\": false, \"activeReady\": false, \"diagnostics\": [ \"PHYSICAL_PROVIDER_NOT_ADMITTED\" ], \"readiness\": { \"identity\": \"resolved\", \"interfaces\": \"compatible\", \"availability\": \"observed\", \"metadata\": \"partial\", \"providerAdmission\": \"unavailable\", \"permission\": \"unknown\", \"activeOperation\": \"blocked\" } }"
          - list [ref=f1e253]:
            - listitem [ref=f1e254]: Does not change deployment resolution or runtime admission.
            - listitem [ref=f1e255]: Physical controls and reservations remain unadmitted.
        - region [ref=f1e256]:
          - heading "Resolution and effective configuration" [level=3] [ref=f1e257]
          - generic [ref=f1e258]:
            - status [ref=f1e259]:
              - generic [ref=f1e260]: 2 blocking
              - text: Resolution 1.0 for
              - code [ref=f1e261]: local-reference
              - text: on host Linux with provider
              - code [ref=f1e262]: studio.reference
              - text: .
            - generic [ref=f1e263]:
              - paragraph [ref=f1e264]:
                - text: Provider
                - code [ref=f1e265]: studio.reference
                - generic [ref=f1e266]: fixture
                - text: declares realization simulated on targets model-unit.
              - list [ref=f1e267]:
                - listitem [ref=f1e268]: "Fidelity limit: Scalar first-order reference model only; no external simulator, physical device, native X-COM, or industrial fidelity claim."
                - listitem [ref=f1e269]: "Fidelity limit: Pause, rewind, step, live mutation and physical coupling are unsupported."
            - note [ref=f1e270]:
              - generic [ref=f1e271]: connections admitted
              - text: Under provider
              - code [ref=f1e272]: studio.reference
              - text: ": every declared flow is admitted for its declared semantics. See Connections for the checks."
            - region [ref=f1e273]:
              - heading "Bindings" [level=4] [ref=f1e274]
              - table [ref=f1e275]:
                - rowgroup [ref=f1e276]:
                  - row [ref=f1e277]:
                    - columnheader "Element" [ref=f1e278]
                    - columnheader "Realization → target" [ref=f1e279]
                    - columnheader "Status" [ref=f1e280]
                    - columnheader "Checks" [ref=f1e281]
                - rowgroup [ref=f1e282]:
                  - row [ref=f1e283]:
                    - rowheader "controller via controller-binding" [ref=f1e284]:
                      - text: controller
                      - generic [ref=f1e285]: via controller-binding
                    - cell "simulated → reference-target (model-unit)" [ref=f1e286]
                    - cell "compatible" [ref=f1e287]
                    - cell "pass realization Provider studio.reference declares support for simulated realization on model-unit targets." [ref=f1e289]:
                      - list [ref=f1e290]:
                        - listitem [ref=f1e291]:
                          - generic [ref=f1e292]: pass
                          - strong [ref=f1e293]: realization
                          - text: Provider studio.reference declares support for simulated realization on model-unit targets.
                  - row [ref=f1e294]:
                    - rowheader "plant via plant-binding" [ref=f1e295]:
                      - text: plant
                      - generic [ref=f1e296]: via plant-binding
                    - cell "physical → reference-target (model-unit)" [ref=f1e297]
                    - cell "unsupported" [ref=f1e298]
                    - cell "unsupported realization Provider studio.reference does not declare support for realization class physical. CAPABILITY_UNSUPPORTED" [ref=f1e300]:
                      - list [ref=f1e301]:
                        - listitem [ref=f1e302]:
                          - generic [ref=f1e303]: unsupported
                          - strong [ref=f1e304]: realization
                          - text: Provider studio.reference does not declare support for realization class physical.
                          - code [ref=f1e305]: CAPABILITY_UNSUPPORTED
            - region [ref=f1e306]:
              - heading "Effective values" [level=4] [ref=f1e307]
              - table [ref=f1e308]:
                - rowgroup [ref=f1e309]:
                  - row [ref=f1e310]:
                    - columnheader "Parameter" [ref=f1e311]
                    - columnheader "Effective" [ref=f1e312]
                    - columnheader "Status" [ref=f1e313]
                    - columnheader "Value sources (a default applies only when nothing is authored; authored layers have no defined precedence)" [ref=f1e314]
                - rowgroup [ref=f1e315]:
                  - row [ref=f1e316]:
                    - rowheader "scenario reference-response.target [1]" [ref=f1e317]:
                      - text: scenario reference-response.target
                      - generic [ref=f1e318]: "[1]"
                    - cell "1" [ref=f1e319]
                    - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default." [ref=f1e320]':
                      - generic [ref=f1e321]: default
                      - generic [ref=f1e322]: "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."
                    - cell "profile-default 1 scenario 1 xdl/scenario.xdl.yaml" [ref=f1e324]:
                      - list [ref=f1e325]:
                        - listitem [ref=f1e326]:
                          - strong [ref=f1e327]: profile-default
                          - text: "1"
                        - listitem [ref=f1e328]:
                          - strong [ref=f1e329]: scenario
                          - text: "1"
                          - generic [ref=f1e330]: xdl/scenario.xdl.yaml
                  - row [ref=f1e331]:
                    - rowheader "scenario reference-response.gain [1]" [ref=f1e332]:
                      - text: scenario reference-response.gain
                      - generic [ref=f1e333]: "[1]"
                    - cell "0.8" [ref=f1e334]
                    - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default." [ref=f1e335]':
                      - generic [ref=f1e336]: default
                      - generic [ref=f1e337]: "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."
                    - cell "profile-default 0.8 scenario 0.8 xdl/scenario.xdl.yaml" [ref=f1e339]:
                      - list [ref=f1e340]:
                        - listitem [ref=f1e341]:
                          - strong [ref=f1e342]: profile-default
                          - text: "0.8"
                        - listitem [ref=f1e343]:
                          - strong [ref=f1e344]: scenario
                          - text: "0.8"
                          - generic [ref=f1e345]: xdl/scenario.xdl.yaml
                  - row [ref=f1e346]:
                    - rowheader "scenario reference-response.initial [1]" [ref=f1e347]:
                      - text: scenario reference-response.initial
                      - generic [ref=f1e348]: "[1]"
                    - cell "0" [ref=f1e349]
                    - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default." [ref=f1e350]':
                      - generic [ref=f1e351]: default
                      - generic [ref=f1e352]: "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."
                    - cell "profile-default 0 scenario 0 xdl/scenario.xdl.yaml" [ref=f1e354]:
                      - list [ref=f1e355]:
                        - listitem [ref=f1e356]:
                          - strong [ref=f1e357]: profile-default
                          - text: "0"
                        - listitem [ref=f1e358]:
                          - strong [ref=f1e359]: scenario
                          - text: "0"
                          - generic [ref=f1e360]: xdl/scenario.xdl.yaml
                  - row [ref=f1e361]:
                    - rowheader "scenario reference-response.duration [s]" [ref=f1e362]:
                      - text: scenario reference-response.duration
                      - generic [ref=f1e363]: "[s]"
                    - cell "5" [ref=f1e364]
                    - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default." [ref=f1e365]':
                      - generic [ref=f1e366]: default
                      - generic [ref=f1e367]: "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."
                    - cell "profile-default 5 scenario 5 xdl/scenario.xdl.yaml" [ref=f1e369]:
                      - list [ref=f1e370]:
                        - listitem [ref=f1e371]:
                          - strong [ref=f1e372]: profile-default
                          - text: "5"
                        - listitem [ref=f1e373]:
                          - strong [ref=f1e374]: scenario
                          - text: "5"
                          - generic [ref=f1e375]: xdl/scenario.xdl.yaml
                  - row [ref=f1e376]:
                    - rowheader "scenario reference-response.timestep [s]" [ref=f1e377]:
                      - text: scenario reference-response.timestep
                      - generic [ref=f1e378]: "[s]"
                    - cell "0.1" [ref=f1e379]
                    - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default." [ref=f1e380]':
                      - generic [ref=f1e381]: default
                      - generic [ref=f1e382]: "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."
                    - cell "profile-default 0.1 scenario 0.1 xdl/scenario.xdl.yaml" [ref=f1e384]:
                      - list [ref=f1e385]:
                        - listitem [ref=f1e386]:
                          - strong [ref=f1e387]: profile-default
                          - text: "0.1"
                        - listitem [ref=f1e388]:
                          - strong [ref=f1e389]: scenario
                          - text: "0.1"
                          - generic [ref=f1e390]: xdl/scenario.xdl.yaml
                  - row [ref=f1e391]:
                    - rowheader "scenario reference-response.fault [1]" [ref=f1e392]:
                      - text: scenario reference-response.fault
                      - generic [ref=f1e393]: "[1]"
                    - cell "none" [ref=f1e394]
                    - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default." [ref=f1e395]':
                      - generic [ref=f1e396]: default
                      - generic [ref=f1e397]: "Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."
                    - cell "profile-default none scenario none xdl/scenario.xdl.yaml" [ref=f1e399]:
                      - list [ref=f1e400]:
                        - listitem [ref=f1e401]:
                          - strong [ref=f1e402]: profile-default
                          - text: none
                        - listitem [ref=f1e403]:
                          - strong [ref=f1e404]: scenario
                          - text: none
                          - generic [ref=f1e405]: xdl/scenario.xdl.yaml
            - region [ref=f1e406]:
              - heading "Portable intent and environment" [level=4] [ref=f1e407]
              - generic [ref=f1e408]:
                - generic [ref=f1e409]:
                  - heading "Portable intent" [level=5] [ref=f1e410]
                  - list [ref=f1e411]:
                    - listitem [ref=f1e412]: "controller: simulated on reference-target"
                    - listitem [ref=f1e413]: "plant: physical on reference-target"
                - generic [ref=f1e414]:
                  - heading "Environment references" [level=5] [ref=f1e415]
                  - list [ref=f1e416]:
                    - listitem [ref=f1e417]:
                      - generic [ref=f1e418]: unresolved
                      - text: "asset for reference-target:"
                      - code [ref=f1e419]: urn:fixture:unresolved-bench
                      - text: No environment binding admits this asset reference; Studio does not resolve it.
            - list [ref=f1e420]:
              - listitem [ref=f1e421]: Compatibility covers declared requirements only; a preserved logical identity never implies behavioural equivalence or fidelity.
              - listitem [ref=f1e422]: Values without an admitted precedence are rejected, never ordered by Studio.
        - region [ref=f1e423]:
          - heading "Time mappings" [level=3] [ref=f1e424]
          - paragraph [ref=f1e425]: No time mappings. Elements share the System's declared clocks.
          - generic [ref=f1e426]:
            - generic [ref=f1e427]:
              - text: Mapping identifier
              - textbox "Mapping identifier" [ref=f1e428]
            - generic [ref=f1e429]:
              - text: Source clock
              - combobox "Source clock" [ref=f1e430]:
                - option "Choose a declared time domain" [selected]
                - option "simulation-time"
            - generic [ref=f1e431]:
              - text: Target clock
              - combobox "Target clock" [ref=f1e432]:
                - option "Choose a declared time domain" [selected]
                - option "simulation-time"
            - generic [ref=f1e433]:
              - text: Mapping description
              - textbox "Mapping description" [ref=f1e434]
            - generic [ref=f1e435]:
              - text: Tolerance
              - spinbutton "Tolerance" [ref=f1e436]
            - generic [ref=f1e437]:
              - text: Tolerance unit
              - textbox "Tolerance unit" [ref=f1e438]: s
            - paragraph [ref=f1e439]: A mapping with an existing identifier replaces it. Studio records the declared relation; its accuracy is never evaluated.
            - button "Save time mapping" [ref=f1e440] [cursor=pointer]
        - generic [ref=f1e441]:
          - generic [ref=f1e442]:
            - generic [ref=f1e443]:
              - generic [ref=f1e444]: SELECTED VARIANT
              - heading "local-reference" [level=3] [ref=f1e445]
              - paragraph [ref=f1e446]: Studio-owned reference fixture.
              - generic [ref=f1e447]:
                - generic [ref=f1e448]:
                  - term [ref=f1e449]: System
                  - definition [ref=f1e450]: org.xverse.studio.process-control/reference-loop
                - generic [ref=f1e451]:
                  - term [ref=f1e452]: Targets
                  - definition [ref=f1e453]: "1"
                - generic [ref=f1e454]:
                  - term [ref=f1e455]: Artifacts
                  - definition [ref=f1e456]: "1"
                - generic [ref=f1e457]:
                  - term [ref=f1e458]: Bindings
                  - definition [ref=f1e459]: "2"
            - generic [ref=f1e460]:
              - heading "Provider readiness" [level=3] [ref=f1e461]
              - generic [ref=f1e462]:
                - generic [ref=f1e463]:
                  - strong [ref=f1e464]: Studio executable reference
                  - generic [ref=f1e465]: owned_reference
                - generic [ref=f1e466]: Available
              - generic [ref=f1e467]:
                - generic [ref=f1e468]:
                  - strong [ref=f1e469]: X-Verse Lite / CARLA
                  - generic [ref=f1e470]: unavailable
                - generic [ref=f1e471]: Unavailable
              - paragraph [ref=f1e472]: OS-specific provider support is separate from native Studio support. Run preflight to verify the selected bindings.
          - generic [ref=f1e473]:
            - heading "Logical element bindings" [level=3] [ref=f1e474]
            - table [ref=f1e476]:
              - rowgroup [ref=f1e477]:
                - row [ref=f1e478]:
                  - columnheader "Logical identity" [ref=f1e479]
                  - columnheader "Realization" [ref=f1e480]
                  - columnheader "Placement / target" [ref=f1e481]
                  - columnheader "Artifacts" [ref=f1e482]
              - rowgroup [ref=f1e483]:
                - row [ref=f1e484]:
                  - cell "controller controller-binding" [ref=f1e485]:
                    - strong [ref=f1e486]: controller
                    - generic [ref=f1e487]: controller-binding
                  - cell "simulated" [ref=f1e488]
                  - cell "reference-target" [ref=f1e490]
                  - cell "reference-model" [ref=f1e491]
                - row [ref=f1e492]:
                  - cell "plant plant-binding" [ref=f1e493]:
                    - strong [ref=f1e494]: plant
                    - generic [ref=f1e495]: plant-binding
                  - cell "physical" [ref=f1e496]
                  - cell "reference-target" [ref=f1e498]
                  - cell "reference-model" [ref=f1e499]
          - generic [ref=f1e501]:
            - heading "reference-model" [level=3] [ref=f1e502]
            - generic [ref=f1e503]:
              - generic [ref=f1e504]:
                - term [ref=f1e505]: Kind
                - definition [ref=f1e506]: model
              - generic [ref=f1e507]:
                - term [ref=f1e508]: Version
                - definition [ref=f1e509]: 1.0.0
              - generic [ref=f1e510]:
                - term [ref=f1e511]: Identity
                - definition [ref=f1e512]: sha256:5e166063f7d506c139b9c3a9f2545ba2983c82b6035af67e68051e90feef0095
              - generic [ref=f1e513]:
                - term [ref=f1e514]: Source
                - definition [ref=f1e515]: urn:xverse:studio:reference:first-order:v1
              - generic [ref=f1e516]:
                - term [ref=f1e517]: Maturity
                - definition [ref=f1e518]: prototype
          - generic [ref=f1e519]:
            - heading "Inspect and update a binding" [level=3] [ref=f1e520]
            - paragraph [ref=f1e521]: Role stays in the logical System. Realization and target placement are selected independently here. Provider compatibility is revalidated before execution.
            - generic [ref=f1e523]:
              - generic [ref=f1e524]:
                - text: Logical binding
                - combobox "Logical binding" [ref=f1e525]:
                  - option "controller" [selected]
                  - option "plant"
              - generic [ref=f1e526]:
                - text: Realization
                - combobox "Realization" [ref=f1e527]:
                  - option "Simulated" [selected]
                  - option "Virtual (not executable by studio.reference)"
                  - option "Physical (not executable by studio.reference)"
                  - option "Hybrid (not executable by studio.reference)"
              - generic [ref=f1e528]:
                - text: Target placement
                - combobox "Target placement" [ref=f1e529]:
                  - option "reference-target · model-unit" [selected]
              - button "Save draft binding" [ref=f1e530] [cursor=pointer]
            - paragraph [ref=f1e531]: Selecting a realization does not install a provider or authorize hardware. Unsupported combinations remain blocked at backend admission.
          - generic [ref=f1e532]:
            - heading "Effective configuration provenance" [level=3] [ref=f1e533]
            - paragraph [ref=f1e534]: Scenario values remain in authored XDL. No unspecified override precedence or implicit environment substitution is applied.
            - group [ref=f1e535]:
              - generic "Inspect exact data" [ref=f1e536] [cursor=pointer]
      - generic [ref=f1e537]:
        - generic [ref=f1e538]: Local project · Saved on backend
        - generic [ref=f1e541]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e542]: 1 provider(s) available
```

# Test source

```ts
  188 |     await expect(page.locator(".alerts [role=alert]")).toHaveCount(0);
  189 |     await activate(page,inspect(page));await expect(alert).toBeFocused();expect(responses).toEqual([412,412]);
  190 |     await reopen(page,project);await activate(page,inspect(page));
  191 |     await expect(field(panel(page),"Project revision")).toHaveText(String(project.revision));
  192 |     await expect(panel(page).getByRole("alert")).toHaveCount(0);expect(responses).toEqual([412,412,200]);
  193 |     await finish({actualRevisionConflictResponses:responses,oldUIRevision:old.project.revision,explicitReopenRecovered:true});
  194 |   });
  195 |
  196 |   test(`physical placements: actual unreadable source stays unavailable without acknowledgement at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  197 |     await page.setViewportSize(viewport);await connectStudio(page,info);
  198 |     const prepared=await setup(page,viewport.width), project=prepared.project;
  199 |     const root=realpathSync(process.env.STUDIO_BROWSER_DATA!), document=project.documents[prepared.documentId], file=path.resolve(root,"projects",project.projectId,"revisions",String(project.revision),document.path);
  200 |     expect(file.startsWith(root+path.sep)).toBe(true);expect(realpathSync(file)).toBe(file);expect(readFileSync(file,"utf8")).toBe(document.content);
  201 |     const finish=await observeWrites(page,project,info);
  202 |     try {
  203 |       writeFileSync(file,Buffer.from([0xff,0xfe,0x00,0x61]));
  204 |       const response=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith("/physical-bindings"));
  205 |       await activate(page,inspect(page));expect((await response).status()).toBe(409);
  206 |       const alert=panel(page).getByRole("alert");await expect(alert).toContainText("PROJECT_UNAVAILABLE");await expect(alert).toBeFocused();
  207 |       await expect(panel(page).locator(".placement-row")).toHaveCount(0);
  208 |       writeFileSync(file,document.content);
  209 |       await activate(page,inspect(page));await expect(heading(page)).toBeFocused();await expect(panel(page).locator(".placement-row")).toHaveCount(1);
  210 |       await finish({actualUnreadableHTTP409:true,exactOwnedFileRestored:true});
  211 |     } finally {writeFileSync(file,document.content);}
  212 |   });
  213 |
  214 |   for(const status of [200,503] as const) {
  215 |     test(`physical placements: Home ignores held HTTP${status} at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  216 |       await page.setViewportSize(viewport);await connectStudio(page,info);
  217 |       const prepared=await setup(page,viewport.width), finish=await observeWrites(page,prepared.project,info), pending=await hold(page,status);
  218 |       try {
  219 |         await activate(page,inspect(page));await expect.poll(pending.ready).toBe(true);await expect(inspect(page)).toBeDisabled();
  220 |         await activate(page,home(page));pending.depart();await expect(panel(page)).toHaveCount(0);
  221 |         pending.release();await pending.done;await page.waitForLoadState("networkidle");
  222 |         await expect(home(page)).toBeFocused();await expect(panel(page)).toHaveCount(0);await expect(page.locator(".alerts [role=alert]")).toHaveCount(0);expect(pending.reads()).toBe(1);
  223 |         await finish({heldStatus:status,actualReportHeld:status===200,labelledTransportFailure:status===503,departedHome:true});
  224 |       } finally {await pending.close();}
  225 |     });
  226 |   }
  227 |
  228 |   test(`physical placements: pending Enter and deliberate focus preserve one read at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  229 |     await page.setViewportSize(viewport);await connectStudio(page,info);
  230 |     const prepared=await setup(page,viewport.width), finish=await observeWrites(page,prepared.project,info), pending=await hold(page);
  231 |     try {
  232 |       await tabTo(page,inspect(page));const controlBounds=await bounds(inspect(page),viewport);await expect(inspect(page)).toHaveAccessibleDescription(/do not grant permission/);
  233 |       await page.keyboard.press("Enter");await expect.poll(pending.ready).toBe(true);await page.keyboard.press("Enter");await page.keyboard.press("Enter");expect(pending.reads()).toBe(1);
  234 |       await tabTo(page,home(page));pending.release();await pending.done;
  235 |       await expect(panel(page).locator(".placement-row")).toHaveCount(1);await expect(home(page)).toBeFocused();expect(pending.reads()).toBe(1);
  236 |       await finish({actualReportHeld:true,repeatedSubmissionReadCount:pending.reads(),deliberateFocusPreserved:true,controlBounds});
  237 |     } finally {await pending.close();}
  238 |   });
  239 |
  240 |   test(`physical placements: newer source draft keeps dialog focus after held observation at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  241 |     await page.setViewportSize(viewport);await connectStudio(page,info);
  242 |     const prepared=await setup(page,viewport.width), finish=await observeWrites(page,prepared.project,info), pending=await hold(page);
  243 |     try {
  244 |       await activate(page,inspect(page));await expect.poll(pending.ready).toBe(true);
  245 |       await activate(page,page.getByRole("button",{name:"XDL source",exact:true}));
  246 |       const dialog=page.getByRole("dialog",{name:"Authored XDL source",exact:true}), editor=dialog.getByRole("textbox",{name:"XDL source",exact:true});
  247 |       await tabTo(page,editor);await page.keyboard.press("ControlOrMeta+End");await page.keyboard.insertText("\n# newer owned unsaved draft\n");const draft=await editor.inputValue();
  248 |       pending.release();await pending.done;await expect(editor).toBeFocused();await expect(editor).toHaveValue(draft);await expect(dialog).toBeVisible();
  249 |       await page.keyboard.press("Escape");await expect(dialog).toHaveCount(0);
  250 |       await expect(panel(page).locator(".placement-row")).toHaveCount(1);
  251 |       await finish({actualReportHeld:true,newerUnsavedSourcePreserved:true,dialogFocusPreserved:true});
  252 |     } finally {await pending.close();}
  253 |   });
  254 |
  255 |   for(const mode of ["wrong revision","wrong project","wrong deployment","wrong system","authority flag","missing readiness","duplicate binding","incomplete inventory"] as const) {
  256 |     test(`physical placements: labelled ${mode} stays unknown at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  257 |       await page.setViewportSize(viewport);await connectStudio(page,info);
  258 |       const prepared=await setup(page,viewport.width),finish=await observeWrites(page,prepared.project,info),payload=structuredClone(prepared.report);
  259 |       if(mode==="wrong revision")payload.revision++;
  260 |       if(mode==="wrong project")payload.projectId="foreign-placement-context";
  261 |       if(mode==="wrong deployment")payload.deploymentRef="xdl://fixture/deployment/foreign";
  262 |       if(mode==="wrong system")payload.systemRef="xdl://fixture/system/foreign";
  263 |       if(mode==="authority flag")payload.activeReady=true;
  264 |       if(mode==="missing readiness")delete payload.bindings[0].readiness.permission;
  265 |       if(mode==="duplicate binding")payload.bindings.push(structuredClone(payload.bindings[0]));
  266 |       if(mode==="incomplete inventory")delete payload.inventoryComplete;
  267 |       await page.route(pattern,route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(payload)}));
  268 |       await activate(page,inspect(page));const alert=panel(page).getByRole("alert");await expect(alert).toContainText(/incomplete, malformed/);await expect(alert).toBeFocused();await expect(panel(page).locator(".placement-row")).toHaveCount(0);
  269 |       const contrast=mode==="authority flag" ? await paint(alert,"Placement malformed authority refusal"):undefined;
  270 |       await page.unroute(pattern);await activate(page,inspect(page));await expect(heading(page)).toBeFocused();await expect(panel(page).locator(".placement-row")).toHaveCount(1);
  271 |       await finish({labelledMalformedTransport:mode,actualRetrySucceeded:true,selectedContrast:contrast});
  272 |     });
  273 |   }
  274 |
  275 |   test(`physical placements: labelled matched metadata cannot grant admission at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  276 |     await page.setViewportSize(viewport);await connectStudio(page,info);
  277 |     const prepared=await setup(page,viewport.width),finish=await observeWrites(page,prepared.project,info),payload=structuredClone(prepared.report);
  278 |     const fixture=JSON.parse(readFileSync(path.resolve("tests/fixtures/providers/lab-inventory-observation.json"),"utf8")), asset=structuredClone(fixture.unicode.items[0]);
  279 |     payload.inventoryComplete=false;payload.inventoryTruncated=true;payload.diagnostics=[{code:"PROVIDER_INVENTORY_UNAVAILABLE",providerId:"fixture"}];
  280 |     asset.privateUnsupportedField="OMITTED-FIXTURE-SENTINEL";
  281 |     payload.bindings[0]={...payload.bindings[0],assetId:asset.assetId,asset,evidenceScope:asset.evidenceScope,requiredInterfacesTruncated:true,readiness:{...payload.bindings[0].readiness,identity:"resolved",interfaces:"compatible",availability:"observed",metadata:"partial"},diagnostics:["PHYSICAL_PROVIDER_NOT_ADMITTED"]};
  282 |     await page.route(pattern,route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(payload)}));
  283 |     await activate(page,inspect(page));const card=panel(page).locator(".placement-row");await expect(card).toBeVisible();
  284 |     await expect(field(card,"Firmware")).toHaveText(`Observed · ${asset.firmware.version}`);await expect(field(card,"Provider admission")).toHaveText("unavailable");await expect(field(card,"Permission scope")).toHaveText("unknown");await expect(field(card,"Active operation")).toHaveText("blocked");
  285 |     await expect(panel(page).getByRole("status").filter({hasText:"Inventory observation is incomplete"})).toContainText("truncated");await expect(card.getByRole("status")).toContainText("Required interface observations are truncated");
  286 |     await expect(panel(page).getByText("PROVIDER_INVENTORY_UNAVAILABLE",{exact:true})).toBeVisible();await expect(panel(page).getByRole("button",{name:/Reserve|Start|Connect|Probe/})).toHaveCount(0);
  287 |     await activate(page,card.locator("summary"));await expect(card.locator("pre")).not.toContainText("OMITTED-FIXTURE-SENTINEL");
> 288 |     expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)).toBe(false);
      |                                                                                        ^ Error: expect(received).toBe(expected) // Object.is equality
  289 |     const selectedContrast=await Promise.all([paint(panel(page).locator("p.field-hint").first(),"Placement guidance"),paint(card.locator(".badge"),"Placement evidence scope"),paint(field(card,"Provider admission"),"Placement unavailable admission"),paint(field(card,"Active operation"),"Placement blocked operation")]);
  290 |     await finish({labelledMatchedPublicTransport:true,backendProjectionFixture:fixture.fixtureScope,admissionUnchanged:true,unicodeCodePoints:Array.from(asset.firmware.version).length,selectedContrast});
  291 |   });
  292 |
  293 |   test(`physical placements: labelled maximum report is accessible in bounded pages at ${viewport.width}x${viewport.height}`,async({page},info)=>{
  294 |     await page.setViewportSize(viewport);await connectStudio(page,info);
  295 |     const prepared=await setup(page,viewport.width),finish=await observeWrites(page,prepared.project,info),payload=structuredClone(prepared.report);
  296 |     payload.bindings=Array.from({length:1000},(_,i)=>({...structuredClone(prepared.report.bindings[0]),bindingId:`fixture-binding-${String(i).padStart(4,"0")}`}));
  297 |     let reads=0;await page.route(pattern,route=>{reads++;return route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(payload)});});
  298 |     await activate(page,inspect(page));await expect(panel(page).locator(".placement-row")).toHaveCount(50);await expect(heading(page)).toBeFocused();
  299 |     const ids:string[]=[];
  300 |     for(let i=0;i<20;i++){
  301 |       await expect(panel(page).getByText(`Placement page ${i+1} of 20 · 1000 reported bindings`,{exact:true})).toBeVisible();
  302 |       ids.push(...await panel(page).locator(".placement-row h4").allTextContents());
  303 |       if(i<19){await activate(page,panel(page).getByRole("button",{name:"Next placement page",exact:true}));await expect(heading(page)).toBeFocused();}
  304 |     }
  305 |     expect(ids).toEqual(payload.bindings.map((r:any)=>r.bindingId));expect(new Set(ids).size).toBe(1000);expect(reads).toBe(1);
  306 |     await expect(panel(page).getByRole("button",{name:"Next placement page",exact:true})).toBeDisabled();
  307 |     await activate(page,panel(page).getByRole("button",{name:"Previous placement page",exact:true}));await expect(heading(page)).toBeFocused();await expect(panel(page).getByText("fixture-binding-0900",{exact:true})).toBeVisible();
  308 |     await finish({labelledMaximumReportTransport:true,totalAccessibleRows:ids.length,maximumRenderedRows:50,localPaginationReads:reads});
  309 |   });
  310 | }
  311 |
  312 | async function observeWrites(page: Page, project: any, info: TestInfo) {
  313 |   const beforeRuns = await request(page, "/runs"), reads: string[] = [];
  314 |   let writes = 0;
  315 |   const listener = (r: import("@playwright/test").Request) => {
  316 |     if (!["GET", "HEAD"].includes(r.method())) writes++;
  317 |     if (new URL(r.url()).pathname.endsWith("/physical-bindings")) reads.push(new URL(r.url()).pathname + new URL(r.url()).search);
  318 |   };
  319 |   page.on("request", listener);
  320 |   return async (details: Record<string, unknown>) => {
  321 |     await page.unroute(pattern);
  322 |     await page.waitForLoadState("networkidle");
  323 |     expect(await request(page, `/projects/${project.projectId}`)).toEqual(project);
  324 |     expect(await request(page, "/runs")).toEqual(beforeRuns);
  325 |     expect(writes).toBe(0);
  326 |     page.off("request", listener);
  327 |     await info.attach("placement-journey.json", {
  328 |       body: JSON.stringify({ projectId: project.projectId, revision: project.revision, reads, mutativeRequestsAfterSetup: writes,
  329 |         canonicalProjectAndRunsUnchanged: true, ...details,
  330 |         scope: "Read-only native browser inspection; actual API results and labelled transport fixtures are distinguished. No physical provider installed, reservation, device operation or Start." }),
  331 |       contentType: "application/json",
  332 |     });
  333 |   };
  334 | }
  335 |
  336 | async function bounds(target: Locator, viewport: {width:number;height:number}) {
  337 |   await expect(target).toBeFocused();
  338 |   const geometry = await target.evaluate(n => {const box=n.getBoundingClientRect(), style=getComputedStyle(n);return {box:box.toJSON(),outline:style.outlineStyle,outlineWidth:parseFloat(style.outlineWidth)};});
  339 |   expect(geometry.box.left).toBeGreaterThanOrEqual(0);
  340 |   expect(geometry.box.top).toBeGreaterThanOrEqual(0);
  341 |   expect(geometry.box.right).toBeLessThanOrEqual(viewport.width);
  342 |   expect(geometry.box.bottom).toBeLessThanOrEqual(viewport.height);
  343 |   expect(geometry.outline).not.toBe("none");
  344 |   expect(geometry.outlineWidth).toBeGreaterThan(0);
  345 |   return geometry;
  346 | }
  347 |
  348 | async function paint(target: Locator, label: string) {
  349 |   const observed = await renderedContrast(target, label);
  350 |   expect(observed.supported).toBe(true);
  351 |   if (observed.supported) expect(observed.ratio).toBeGreaterThanOrEqual(4.5);
  352 |   return observed;
  353 | }
  354 |
  355 | for (const viewport of [
  356 |   { width: 1024, height: 768 },
  357 |   { width: 1440, height: 900 },
  358 | ]) {
  359 |   test(`physical placements: actual invalid source is not an empty observation at ${viewport.width}x${viewport.height}`, async ({page}, info) => {
  360 |     await page.setViewportSize(viewport);
  361 |     await connectStudio(page, info);
  362 |     const prepared = await setup(page, viewport.width);
  363 |     const [id, source] = Object.entries<any>(prepared.project.documents).find(([,d])=>parse(d.content).kind==="Scenario")!;
  364 |     const project = await request(page, `/projects/${prepared.project.projectId}/documents/${id}`, "PUT", {content: source.content + "\ninvalid: [\n", format:"yaml"}, prepared.project.revision);
  365 |     const report = await request(page, `${prepared.url}?revision=${project.revision}`);
  366 |     expect(report.sourceValid).toBe(false);
  367 |     expect(report.bindings).toEqual([]);
  368 |     expect(report.diagnostics.length).toBeGreaterThan(0);
  369 |     expect(report.inventoryComplete).toBeUndefined();
  370 |     await reopen(page, project);
  371 |     const finish = await observeWrites(page, project, info);
  372 |     await expect(inspect(page)).toBeEnabled();
  373 |     await activate(page, inspect(page));
  374 |     await expect(panel(page).getByRole("alert")).toContainText("source set is invalid");
  375 |     await expect(panel(page).getByRole("alert")).toBeFocused();
  376 |     await expect(panel(page).getByText(/No physical or hybrid bindings/)).toHaveCount(0);
  377 |     await finish({actualInvalidResolverReport:report});
  378 |   });
  379 |
  380 |   test(`physical placements: actual unresolved authored binding is read-only at ${viewport.width}x${viewport.height}`, async ({
  381 |     page,
  382 |   }, info) => {
  383 |     await page.setViewportSize(viewport);
  384 |     await connectStudio(page, info);
  385 |     const { project, documentId, url, report } = await setup(
  386 |         page,
  387 |         viewport.width,
  388 |       ),
```
