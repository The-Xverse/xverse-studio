# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: physical-placements-accessibility.spec.ts >> physical placements: actual unresolved authored binding is read-only at 1024x768
- Location: tests/e2e/physical-placements-accessibility.spec.ts:129:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('button', { name: 'Inspect physical placements', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "soft toBeVisible" getByRole('button', { name: 'Inspect physical placements', exact: true }) with timeout 10000ms
  - waiting for getByRole('button', { name: 'Inspect physical placements', exact: true })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace
  - button "Environment"
  - text: LO
- navigation "Main navigation":
  - button "Workspace"
  - button "Catalog"
  - button "Laboratory": Lab
  - button "Compatibility and environment": Settings
  - text: v0.1
- main:
  - button "Workspace"
  - text: System
  - heading "Placement observation 1024" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched.
  - 'button "Dependencies: none unresolved"': Dependencies
  - button "Undo" [disabled]
  - button "Redo" [disabled]
  - button "Export"
  - button "Validate"
  - button "Preflight & run"
  - tablist "System workflows":
    - tab "Model"
    - tab "Connections"
    - tab "Deployment" [selected]
    - tab "Experiments"
    - tab "Results"
    - button "XDL source"
  - text: Draft revision
  - code: "2"
  - text: 3 elements · 2 connections Execution scope Owned reference
  - heading "Plant deployment variants" [level=2]
  - paragraph: Select an authored Deployment and its associated Scenario. Logical System identities remain stable.
  - text: Explicit compiler selection Deployment variant
  - combobox "Deployment variant":
    - option "Choose an authored deployment"
    - option "local-reference" [selected]
  - text: Associated Scenario
  - combobox "Associated Scenario":
    - option "Choose a matching Scenario"
    - option "reference-response" [selected]
  - term: Requested Deployment
  - definition: xdl://org.xverse.studio.process-control/deployment/local-reference
  - term: Requested Scenario
  - definition: xdl://org.xverse.studio.process-control/scenario/reference-response
  - term: Readiness
  - definition: Fresh preflight required before every new run
  - paragraph: Selection does not rewrite either resource. The backend rejects mismatched contributors and freezes exact selected inputs before execution.
  - heading "Create a named variant" [level=3]
  - paragraph: Clone the selected Deployment together with its matching Scenario. Parameters, assessment references, and logical topology retain explicit authored provenance.
  - text: New variant name
  - textbox "New variant name":
    - /placeholder: Alternative reference deployment
  - button "Create deployment variant" [disabled]
  - region "Resolution and effective configuration":
    - heading "Resolution and effective configuration" [level=3]
    - status:
      - text: 2 blocking Resolution 1.0 for
      - code: local-reference
      - text: on host Linux with provider
      - code: studio.reference
      - text: .
    - paragraph:
      - text: Provider
      - code: studio.reference
      - text: fixture declares realization simulated on targets model-unit.
    - list:
      - listitem: "Fidelity limit: Scalar first-order reference model only; no external simulator, physical device, native X-COM, or industrial fidelity claim."
      - listitem: "Fidelity limit: Pause, rewind, step, live mutation and physical coupling are unsupported."
    - note:
      - text: connections admitted Under provider
      - code: studio.reference
      - text: ": every declared flow is admitted for its declared semantics. See Connections for the checks."
    - region "Bindings":
      - heading "Bindings" [level=4]
      - table:
        - rowgroup:
          - row "Element Realization → target Status Checks":
            - columnheader "Element"
            - columnheader "Realization → target"
            - columnheader "Status"
            - columnheader "Checks"
        - rowgroup:
          - row "controller via controller-binding simulated → reference-target (model-unit) compatible pass realization Provider studio.reference declares support for simulated realization on model-unit targets.":
            - rowheader "controller via controller-binding"
            - cell "simulated → reference-target (model-unit)"
            - cell "compatible"
            - cell "pass realization Provider studio.reference declares support for simulated realization on model-unit targets.":
              - list:
                - listitem:
                  - text: pass
                  - strong: realization
                  - text: Provider studio.reference declares support for simulated realization on model-unit targets.
          - row "plant via plant-binding physical → reference-target (model-unit) unsupported unsupported realization Provider studio.reference does not declare support for realization class physical. CAPABILITY_UNSUPPORTED":
            - rowheader "plant via plant-binding"
            - cell "physical → reference-target (model-unit)"
            - cell "unsupported"
            - cell "unsupported realization Provider studio.reference does not declare support for realization class physical. CAPABILITY_UNSUPPORTED":
              - list:
                - listitem:
                  - text: unsupported
                  - strong: realization
                  - text: Provider studio.reference does not declare support for realization class physical.
                  - code: CAPABILITY_UNSUPPORTED
    - region "Effective values":
      - heading "Effective values" [level=4]
      - table:
        - rowgroup:
          - row "Parameter Effective Status Value sources (a default applies only when nothing is authored; authored layers have no defined precedence)":
            - columnheader "Parameter"
            - columnheader "Effective"
            - columnheader "Status"
            - columnheader "Value sources (a default applies only when nothing is authored; authored layers have no defined precedence)"
        - rowgroup:
          - 'row "scenario reference-response.target [1] 1 default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default. profile-default 1 scenario 1 xdl/scenario.xdl.yaml"':
            - rowheader "scenario reference-response.target [1]"
            - cell "1"
            - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."'
            - cell "profile-default 1 scenario 1 xdl/scenario.xdl.yaml":
              - list:
                - listitem:
                  - strong: profile-default
                  - text: "1"
                - listitem:
                  - strong: scenario
                  - text: 1 xdl/scenario.xdl.yaml
          - 'row "scenario reference-response.gain [1] 0.8 default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default. profile-default 0.8 scenario 0.8 xdl/scenario.xdl.yaml"':
            - rowheader "scenario reference-response.gain [1]"
            - cell "0.8"
            - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."'
            - cell "profile-default 0.8 scenario 0.8 xdl/scenario.xdl.yaml":
              - list:
                - listitem:
                  - strong: profile-default
                  - text: "0.8"
                - listitem:
                  - strong: scenario
                  - text: 0.8 xdl/scenario.xdl.yaml
          - 'row "scenario reference-response.initial [1] 0 default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default. profile-default 0 scenario 0 xdl/scenario.xdl.yaml"':
            - rowheader "scenario reference-response.initial [1]"
            - cell "0"
            - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."'
            - cell "profile-default 0 scenario 0 xdl/scenario.xdl.yaml":
              - list:
                - listitem:
                  - strong: profile-default
                  - text: "0"
                - listitem:
                  - strong: scenario
                  - text: 0 xdl/scenario.xdl.yaml
          - 'row "scenario reference-response.duration [s] 5 default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default. profile-default 5 scenario 5 xdl/scenario.xdl.yaml"':
            - rowheader "scenario reference-response.duration [s]"
            - cell "5"
            - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."'
            - cell "profile-default 5 scenario 5 xdl/scenario.xdl.yaml":
              - list:
                - listitem:
                  - strong: profile-default
                  - text: "5"
                - listitem:
                  - strong: scenario
                  - text: 5 xdl/scenario.xdl.yaml
          - 'row "scenario reference-response.timestep [s] 0.1 default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default. profile-default 0.1 scenario 0.1 xdl/scenario.xdl.yaml"':
            - rowheader "scenario reference-response.timestep [s]"
            - cell "0.1"
            - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."'
            - cell "profile-default 0.1 scenario 0.1 xdl/scenario.xdl.yaml":
              - list:
                - listitem:
                  - strong: profile-default
                  - text: "0.1"
                - listitem:
                  - strong: scenario
                  - text: 0.1 xdl/scenario.xdl.yaml
          - 'row "scenario reference-response.fault [1] none default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default. profile-default none scenario none xdl/scenario.xdl.yaml"':
            - rowheader "scenario reference-response.fault [1]"
            - cell "none"
            - 'cell "default Declared by the owned reference profile: a Scenario value replaces the admitted parameter default."'
            - cell "profile-default none scenario none xdl/scenario.xdl.yaml":
              - list:
                - listitem:
                  - strong: profile-default
                  - text: none
                - listitem:
                  - strong: scenario
                  - text: none xdl/scenario.xdl.yaml
    - region "Portable intent and environment":
      - heading "Portable intent and environment" [level=4]
      - heading "Portable intent" [level=5]
      - list:
        - listitem: "controller: simulated on reference-target"
        - listitem: "plant: physical on reference-target"
      - heading "Environment references" [level=5]
      - list:
        - listitem:
          - text: "unresolved asset for reference-target:"
          - code: urn:fixture:unresolved-bench
          - text: No environment binding admits this asset reference; Studio does not resolve it.
    - list:
      - listitem: Compatibility covers declared requirements only; a preserved logical identity never implies behavioural equivalence or fidelity.
      - listitem: Values without an admitted precedence are rejected, never ordered by Studio.
  - region "Time mappings":
    - heading "Time mappings" [level=3]
    - paragraph: No time mappings. Elements share the System's declared clocks.
    - text: Mapping identifier
    - textbox "Mapping identifier"
    - text: Source clock
    - combobox "Source clock":
      - option "Choose a declared time domain" [selected]
      - option "simulation-time"
    - text: Target clock
    - combobox "Target clock":
      - option "Choose a declared time domain" [selected]
      - option "simulation-time"
    - text: Mapping description
    - textbox "Mapping description"
    - text: Tolerance
    - spinbutton "Tolerance"
    - text: Tolerance unit
    - textbox "Tolerance unit": s
    - paragraph: A mapping with an existing identifier replaces it. Studio records the declared relation; its accuracy is never evaluated.
    - button "Save time mapping"
  - text: SELECTED VARIANT
  - heading "local-reference" [level=3]
  - paragraph: Studio-owned reference fixture.
  - term: System
  - definition: org.xverse.studio.process-control/reference-loop
  - term: Targets
  - definition: "1"
  - term: Artifacts
  - definition: "1"
  - term: Bindings
  - definition: "2"
  - heading "Provider readiness" [level=3]
  - strong: Studio executable reference
  - text: owned_reference Available
  - strong: X-Verse Lite / CARLA
  - text: unavailable Unavailable
  - paragraph: OS-specific provider support is separate from native Studio support. Run preflight to verify the selected bindings.
  - heading "Logical element bindings" [level=3]
  - table:
    - rowgroup:
      - row "Logical identity Realization Placement / target Artifacts":
        - columnheader "Logical identity"
        - columnheader "Realization"
        - columnheader "Placement / target"
        - columnheader "Artifacts"
    - rowgroup:
      - row "controller controller-binding simulated reference-target reference-model":
        - cell "controller controller-binding":
          - strong: controller
          - text: controller-binding
        - cell "simulated"
        - cell "reference-target"
        - cell "reference-model"
      - row "plant plant-binding physical reference-target reference-model":
        - cell "plant plant-binding":
          - strong: plant
          - text: plant-binding
        - cell "physical"
        - cell "reference-target"
        - cell "reference-model"
  - heading "reference-model" [level=3]
  - term: Kind
  - definition: model
  - term: Version
  - definition: 1.0.0
  - term: Identity
  - definition: sha256:5e166063f7d506c139b9c3a9f2545ba2983c82b6035af67e68051e90feef0095
  - term: Source
  - definition: urn:xverse:studio:reference:first-order:v1
  - term: Maturity
  - definition: prototype
  - heading "Inspect and update a binding" [level=3]
  - paragraph: Role stays in the logical System. Realization and target placement are selected independently here. Provider compatibility is revalidated before execution.
  - text: Logical binding
  - combobox "Logical binding":
    - option "controller" [selected]
    - option "plant"
  - text: Realization
  - combobox "Realization":
    - option "Simulated" [selected]
    - option "Virtual (not executable by studio.reference)"
    - option "Physical (not executable by studio.reference)"
    - option "Hybrid (not executable by studio.reference)"
  - text: Target placement
  - combobox "Target placement":
    - option "reference-target · model-unit" [selected]
  - button "Save draft binding"
  - paragraph: Selecting a realization does not install a provider or authorize hardware. Unsupported combinations remain blocked at backend admission.
  - heading "Effective configuration provenance" [level=3]
  - paragraph: Scenario values remain in authored XDL. No unspecified override precedence or implicit environment substitution is applied.
  - group: Inspect exact data
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  50  |     { route, method, body, revision },
  51  |   );
  52  | }
  53  | async function setup(page: Page, width: number) {
  54  |   const initial = await request(page, "/projects", "POST", {
  55  |     name: `Placement observation ${width}`,
  56  |   });
  57  |   const [documentId, document] = Object.entries<any>(initial.documents).find(
  58  |     ([, d]) => parse(d.content).kind === "Deployment",
  59  |   )!;
  60  |   const deployment = parse(document.content);
  61  |   deployment.spec.targets[0].externalAssetRef = "urn:fixture:unresolved-bench";
  62  |   deployment.spec.bindings[1].realizationClass = "physical";
  63  |   const project = await request(
  64  |     page,
  65  |     `/projects/${initial.projectId}/documents/${documentId}`,
  66  |     "PUT",
  67  |     { content: stringify(deployment), format: "yaml" },
  68  |     initial.revision,
  69  |   );
  70  |   const url = `/projects/${project.projectId}/deployment-variants/${documentId}/physical-bindings`,
  71  |     report = await request(page, `${url}?revision=${project.revision}`);
  72  |   expect(report).toMatchObject({
  73  |     bindingObservationVersion: "1.0",
  74  |     projectId: project.projectId,
  75  |     documentId,
  76  |     revision: project.revision,
  77  |     sourceValid: true,
  78  |     scope: "read_only_placement_observation",
  79  |     activeReady: false,
  80  |     runtimeAdmission: "unavailable",
  81  |     inventoryComplete: true,
  82  |   });
  83  |   expect(report.bindings).toHaveLength(1);
  84  |   expect(report.bindings[0]).toMatchObject({
  85  |     bindingId: "plant-binding",
  86  |     realizationClass: "physical",
  87  |     assetId: "urn:fixture:unresolved-bench",
  88  |     asset: null,
  89  |     ready: false,
  90  |     activeReady: false,
  91  |     readiness: {
  92  |       identity: "unknown",
  93  |       interfaces: "unknown",
  94  |       providerAdmission: "unavailable",
  95  |       permission: "unknown",
  96  |       activeOperation: "blocked",
  97  |     },
  98  |   });
  99  |   expect(Object.keys(report.bindings[0].requiredInterfaces).sort()).toEqual([
  100 |     "command",
  101 |     "state",
  102 |   ]);
  103 |   expect(report.bindings[0].diagnostics).toContain("ASSET_UNAVAILABLE");
  104 |   await page.evaluate(
  105 |     (id) => localStorage.setItem("studio.projectId", id),
  106 |     project.projectId,
  107 |   );
  108 |   await page.reload();
  109 |   await expect(
  110 |     page.getByRole("heading", { name: project.name, exact: true }),
  111 |   ).toBeVisible();
  112 |   await activate(page, page.getByRole("tab", { name: /^Deployment/ }));
  113 |   await expect(
  114 |     page.getByRole("combobox", { name: "Deployment variant", exact: true }),
  115 |   ).not.toHaveValue("");
  116 |   await page.waitForLoadState("networkidle");
  117 |   return {
  118 |     project: await request(page, `/projects/${project.projectId}`),
  119 |     documentId,
  120 |     url,
  121 |     report,
  122 |   };
  123 | }
  124 |
  125 | for (const viewport of [
  126 |   { width: 1024, height: 768 },
  127 |   { width: 1440, height: 900 },
  128 | ]) {
  129 |   test(`physical placements: actual unresolved authored binding is read-only at ${viewport.width}x${viewport.height}`, async ({
  130 |     page,
  131 |   }, info) => {
  132 |     await page.setViewportSize(viewport);
  133 |     await connectStudio(page, info);
  134 |     const { project, documentId, url, report } = await setup(
  135 |         page,
  136 |         viewport.width,
  137 |       ),
  138 |       beforeRuns = await request(page, "/runs");
  139 |     let writes = 0;
  140 |     const reads: string[] = [];
  141 |     page.on("request", (r) => {
  142 |       if (!["GET", "HEAD"].includes(r.method())) writes++;
  143 |       if (new URL(r.url()).pathname === "/api/v1" + url)
  144 |         reads.push(new URL(r.url()).search);
  145 |     });
  146 |     const inspect = page.getByRole("button", {
  147 |       name: "Inspect physical placements",
  148 |       exact: true,
  149 |     });
> 150 |     await expect.soft(inspect).toBeVisible();
      |                                ^ Error: expect(locator).toBeVisible() failed
  151 |     if (await inspect.count()) {
  152 |       await activate(page, inspect);
  153 |       const panel = page.getByRole("region", {
  154 |         name: "Physical placement observation",
  155 |         exact: true,
  156 |       });
  157 |       await expect(
  158 |         panel.getByText(report.systemRef, { exact: true }),
  159 |       ).toBeVisible();
  160 |       await expect(
  161 |         panel.getByText(report.deploymentRef, { exact: true }),
  162 |       ).toBeVisible();
  163 |       await expect(
  164 |         panel.getByText(report.bindings[0].logicalRef, { exact: true }),
  165 |       ).toBeVisible();
  166 |       await expect(
  167 |         panel.getByText("urn:fixture:unresolved-bench", { exact: true }),
  168 |       ).toBeVisible();
  169 |       await expect(
  170 |         panel.getByText("ASSET_UNAVAILABLE", { exact: true }),
  171 |       ).toBeVisible();
  172 |       await expect(
  173 |         panel.getByRole("heading", {
  174 |           name: "Physical placement observation",
  175 |           exact: true,
  176 |         }),
  177 |       ).toBeFocused();
  178 |       expect(reads).toEqual([`?revision=${project.revision}`]);
  179 |     }
  180 |     const saved = await request(page, `/projects/${project.projectId}`);
  181 |     expect(saved).toEqual(project);
  182 |     expect(saved.documents[documentId]).toEqual(project.documents[documentId]);
  183 |     expect(await request(page, "/runs")).toEqual(beforeRuns);
  184 |     expect(writes).toBe(0);
  185 |     await info.attach("physical-placement-observation.json", {
  186 |       body: JSON.stringify({
  187 |         viewport,
  188 |         projectId: project.projectId,
  189 |         documentId,
  190 |         revision: project.revision,
  191 |         actualResolverReport: report,
  192 |         actualCanonicalUnchanged: true,
  193 |         mutativeRequestsAfterSetup: writes,
  194 |         observedUIReads: reads,
  195 |         scope:
  196 |           "Actual public source declaration and authoritative read-only resolver with empty/unadmitted inventory; no fixture provider installed, device operation, reservation or Start",
  197 |       }),
  198 |       contentType: "application/json",
  199 |     });
  200 |   });
  201 | }
  202 |
```
