# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: source-recovery-accessibility.spec.ts >> recovery accessibility: unreadable target replaces previous project context at 1440x900
- Location: tests/e2e/source-recovery-accessibility.spec.ts:770:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: 'Process control reference', exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('heading', { name: 'Process control reference', exact: true }) with timeout 10000ms
  - waiting for getByRole('heading', { name: 'Process control reference', exact: true })

```

```yaml
- link "Skip to workspace":
  - /url: "#main-content"
- banner:
  - button "X-Verse Studio home": X X-VERSE STUDIO
  - text: Local workspace REFERENCE PREVIEW
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
  - heading "Prior recovery workspace 1440" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched. rev 1
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
  - code: "1"
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
  - region "Physical placement observation":
    - heading "Physical placement observation" [level=3]
    - button "Inspect physical placements"
    - paragraph: Read-only observation of the selected Deployment and committed revision. Logical identity and authored source stay unchanged. Asset observations do not grant permission or make physical execution available.
    - paragraph:
      - text: "Authored Deployment for inspection:"
      - code: xdl://org.xverse.studio.process-control/deployment/local-reference
    - paragraph: Inspect the selected Deployment to read its physical and hybrid binding observations.
  - region "Resolution and effective configuration":
    - heading "Resolution and effective configuration" [level=3]
    - status:
      - text: no blocking findings Resolution 1.0 for
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
          - row "plant via plant-binding simulated → reference-target (model-unit) compatible pass realization Provider studio.reference declares support for simulated realization on model-unit targets.":
            - rowheader "plant via plant-binding"
            - cell "simulated → reference-target (model-unit)"
            - cell "compatible"
            - cell "pass realization Provider studio.reference declares support for simulated realization on model-unit targets.":
              - list:
                - listitem:
                  - text: pass
                  - strong: realization
                  - text: Provider studio.reference declares support for simulated realization on model-unit targets.
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
        - listitem: "plant: simulated on reference-target"
      - heading "Environment references" [level=5]
      - paragraph: No asset or secret references; nothing environment-specific to resolve.
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
      - row "plant plant-binding simulated reference-target reference-model":
        - cell "plant plant-binding":
          - strong: plant
          - text: plant-binding
        - cell "simulated"
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
  772 |   }, info) => {
  773 |     test.setTimeout(90000);
  774 |     await page.setViewportSize(viewport);
  775 |     await connectStudio(page, info);
  776 |     const previous = await create(
  777 |         page,
  778 |         `Prior recovery workspace ${viewport.width}`,
  779 |       ),
  780 |       previousRuns = await runs(page, previous.projectId);
  781 |     await activate(
  782 |       page,
  783 |       page.getByRole("tab", { name: "Deployment", exact: true }),
  784 |     );
  785 |     const entry = (
  786 |       await page.request.get("/api/v1/catalog").then((r) => r.json())
  787 |     ).items.find(
  788 |       (e: any) =>
  789 |         e.kind === "blueprint" && e.providerIds?.includes("studio.reference"),
  790 |     );
  791 |     expect(entry).toBeTruthy();
  792 |     await activate(
  793 |       page,
  794 |       page.getByRole("button", { name: "Catalog", exact: true }),
  795 |     );
  796 |     let fixture: Awaited<ReturnType<typeof prepare>> | undefined;
  797 |     const pattern = "**/api/v1/projects";
  798 |     await page.route(pattern, async (route) => {
  799 |       if (route.request().method() !== "POST") {
  800 |         await route.continue();
  801 |         return;
  802 |       }
  803 |       const response = await route.fetch();
  804 |       expect(response.status()).toBe(201);
  805 |       const project = await response.json(),
  806 |         pid = project.projectId,
  807 |         id = Object.keys(project.documents).find((id) =>
  808 |           project.documents[id].path.endsWith("/system.xdl.yaml"),
  809 |         )!,
  810 |         document = project.documents[id];
  811 |       const file = ownedPath(
  812 |         "projects",
  813 |         pid,
  814 |         "revisions",
  815 |         String(project.revision),
  816 |         document.path,
  817 |       );
  818 |       expect(realpathSync(file)).toBe(file);
  819 |       expect(readFileSync(file, "utf8")).toBe(document.content);
  820 |       const observed = Buffer.from([0xff, 0xfe, 0x00, 0x62]);
  821 |       writeFileSync(file, observed);
  822 |       fixture = {
  823 |         project,
  824 |         pid,
  825 |         id,
  826 |         file,
  827 |         observed,
  828 |         restore() {
  829 |           writeFileSync(file, document.content);
  830 |         },
  831 |       };
  832 |       await route.fulfill({ response });
  833 |     });
  834 |     try {
  835 |       await activate(
  836 |         page,
  837 |         page
  838 |           .getByRole("article")
  839 |           .filter({
  840 |             has: page.getByRole("heading", { name: entry.name, exact: true }),
  841 |           })
  842 |           .getByRole("button", { name: "Open as project", exact: true }),
  843 |       );
  844 |       await expect(group(page)).toBeVisible();
  845 |       expect(fixture).toBeDefined();
  846 |       const owned = fixture!;
  847 |       // Returning from Catalog does not load another project; the failed target is still selected.
  848 |       await activate(
  849 |         page,
  850 |         page.getByRole("button", { name: "Back to workspace", exact: true }),
  851 |       );
  852 |       await expect(
  853 |         page.getByRole("heading", { name: previous.name, exact: true }),
  854 |       ).toBeVisible();
  855 |       await expect(
  856 |         page.getByRole("tab", { name: "Deployment", exact: true }),
  857 |       ).toHaveAttribute("aria-selected", "true");
  858 |       const reply = page.waitForResponse(
  859 |         (r) =>
  860 |           new URL(r.url()).pathname ===
  861 |             `/api/v1/projects/${owned.pid}/recoveries` &&
  862 |           r.request().method() === "POST",
  863 |       );
  864 |       await activate(
  865 |         page,
  866 |         recoverButton(page, owned.project.revision, "restore_revision"),
  867 |       );
  868 |       const result = await (await reply).json();
  869 |       await page.waitForLoadState("networkidle");
  870 |       await expect(
  871 |         page.getByRole("heading", { name: owned.project.name, exact: true }),
> 872 |       ).toBeVisible();
      |         ^ Error: expect(locator).toBeVisible() failed
  873 |       await expect
  874 |         .soft(page.getByRole("tab", { name: "Model", exact: true }))
  875 |         .toHaveAttribute("aria-selected", "true");
  876 |       await expect.soft(source(page)).toBeFocused();
  877 |       const current = await read(page, owned.pid);
  878 |       expect(current.revision).toBe(owned.project.revision + 1);
  879 |       for (const id of Object.keys(owned.project.documents))
  880 |         expect(current.documents[id].content).toBe(
  881 |           owned.project.documents[id].content,
  882 |         );
  883 |       expect((await read(page, previous.projectId)).documents).toEqual(
  884 |         previous.documents,
  885 |       );
  886 |       expect(await runs(page, previous.projectId)).toEqual(previousRuns);
  887 |       expect(await runs(page, owned.pid)).toEqual([]);
  888 |       await backup(page, owned, result);
  889 |       await info.attach("recovery-previous-project.json", {
  890 |         body: JSON.stringify({
  891 |           viewport,
  892 |           previousProjectId: previous.projectId,
  893 |           recoveredProjectId: owned.pid,
  894 |           distinctIdentities: previous.projectId !== owned.pid,
  895 |           previousCanonicalDocumentsUnchanged: true,
  896 |           recoveredInitialView: "Model",
  897 |           actualCreationThenUnreadableLoad: true,
  898 |           scope:
  899 |             "Owned fixture breaks only the newly created project's source before its first UI read; previous workspace remains rendered; no Start",
  900 |         }),
  901 |         contentType: "application/json",
  902 |       });
  903 |     } finally {
  904 |       await page.unroute(pattern);
  905 |       fixture?.restore();
  906 |     }
  907 |   });
  908 | }
  909 |
```
