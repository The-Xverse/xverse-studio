# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: project-context.spec.ts >> project context: newest creation intent wins over earlier completion at 1024x768
- Location: tests/e2e/project-context.spec.ts:747:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: "prj-9d251219-eca8-4577-a22c-ecbb1482b710"
Received: "prj-d7722cf5-f13d-4a06-9355-ec1fbb5e11d8"
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
        - text: Project created. Review its scope and validate the XDL before running.
        - button "Dismiss notice" [ref=f1e55] [cursor=pointer]
      - generic [ref=f1e58]:
        - generic [ref=f1e59]:
          - generic [ref=f1e60]:
            - button "Workspace" [ref=f1e61] [cursor=pointer]
            - generic [ref=f1e64]: System
          - generic [ref=f1e65]:
            - heading "Process control reference" [level=1] [ref=f1e72]
            - generic [ref=f1e73]: Draft
        - generic [ref=f1e74]:
          - button "Dependencies" [ref=f1e75] [cursor=pointer]
          - button "Undo" [disabled] [ref=f1e76]
          - button "Redo" [disabled] [ref=f1e77]
          - button "Export" [ref=f1e78] [cursor=pointer]
          - button "Validate" [ref=f1e81] [cursor=pointer]
          - button "Preflight & run" [ref=f1e84] [cursor=pointer]
      - tablist "System workflows" [ref=f1e87]:
        - tab "Model" [selected] [ref=f1e88] [cursor=pointer]
        - tab "Connections" [ref=f1e94] [cursor=pointer]
        - tab "Deployment" [ref=f1e99] [cursor=pointer]
        - tab "Experiments" [ref=f1e102] [cursor=pointer]
        - tab "Results" [ref=f1e105] [cursor=pointer]
        - button "XDL source" [ref=f1e109] [cursor=pointer]
      - generic [ref=f1e112]:
        - generic [ref=f1e113]:
          - text: Draft revision
          - code [ref=f1e115]: "1"
        - generic [ref=f1e116]: 3 elements · 2 connections
        - generic [ref=f1e117]:
          - text: Execution scope
          - generic [ref=f1e118]: Owned reference
      - generic [ref=f1e119]:
        - complementary "Structured model navigation" [ref=f1e120]:
          - generic [ref=f1e121]:
            - heading "System explorer" [level=2] [ref=f1e122]
            - button "View XDL source" [ref=f1e123] [cursor=pointer]
          - textbox "Search elements" [ref=f1e130]:
            - /placeholder: Find an element…
          - generic [ref=f1e131]:
            - strong [ref=f1e137]: reference-loop
            - generic [ref=f1e138]: "3"
            - button "Group by node" [ref=f1e139] [cursor=pointer]
          - generic [ref=f1e140]:
            - button "controller controller" [ref=f1e141] [cursor=pointer]:
              - generic [ref=f1e147]: controller
              - generic [ref=f1e148]: controller
            - button "plant plant" [ref=f1e149] [cursor=pointer]:
              - generic [ref=f1e155]: plant
              - generic [ref=f1e156]: plant
            - button "observer-node observer" [ref=f1e157] [cursor=pointer]:
              - generic [ref=f1e160]: observer-node
              - generic [ref=f1e161]: observer
          - generic [ref=f1e162]:
            - generic [ref=f1e163]: RESOURCES
            - button "reference-controller Component" [ref=f1e164] [cursor=pointer]:
              - generic [ref=f1e167]: reference-controller
              - generic [ref=f1e168]: Component
            - button "reference-plant Component" [ref=f1e169] [cursor=pointer]:
              - generic [ref=f1e172]: reference-plant
              - generic [ref=f1e173]: Component
            - button "reference-loop System" [ref=f1e174] [cursor=pointer]:
              - generic [ref=f1e177]: reference-loop
              - generic [ref=f1e178]: System
            - button "local-reference Deployment" [ref=f1e179] [cursor=pointer]:
              - generic [ref=f1e182]: local-reference
              - generic [ref=f1e183]: Deployment
            - button "reference-response Scenario" [ref=f1e184] [cursor=pointer]:
              - generic [ref=f1e187]: reference-response
              - generic [ref=f1e188]: Scenario
            - button "experiment-lite Profile" [ref=f1e189] [cursor=pointer]:
              - generic [ref=f1e192]: experiment-lite
              - generic [ref=f1e193]: Profile
            - button "studio-experiments Profile" [ref=f1e194] [cursor=pointer]:
              - generic [ref=f1e197]: studio-experiments
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
          - generic [ref=f1e330]:
            - paragraph [ref=f1e331]: Select an element in the graph or explorer to inspect its stable identity, role, realization, and placement.
            - generic [ref=f1e332]:
              - generic [ref=f1e333]:
                - term [ref=f1e334]: Namespace
                - definition [ref=f1e335]: org.xverse.studio.process-control
              - generic [ref=f1e336]:
                - term [ref=f1e337]: XDL version
                - definition [ref=f1e338]: xverse.io/xdl/v1alpha1
              - generic [ref=f1e339]:
                - term [ref=f1e340]: Resources
                - definition [ref=f1e341]: "7"
              - generic [ref=f1e342]:
                - term [ref=f1e343]: Evidence scope
                - definition [ref=f1e344]: Owned reference only
            - heading "Reference parameters" [level=4] [ref=f1e345]
            - group [ref=f1e347]:
              - generic [ref=f1e348]:
                - generic [ref=f1e349]:
                  - text: Target
                  - generic [ref=f1e350]: "1"
                  - spinbutton "Target 1" [ref=f1e351]: "1"
                - paragraph [ref=f1e352]: Normalized reference setpoint, dimensionless.
                - generic [ref=f1e353]:
                  - generic [ref=f1e354]: Scenario XDL extension · default 1
                  - button "Apply" [disabled] [ref=f1e355]
              - generic [ref=f1e356]:
                - generic [ref=f1e357]:
                  - text: Response gain
                  - generic [ref=f1e358]: "1"
                  - spinbutton "Response gain 1" [ref=f1e359]: "0.8"
                - paragraph [ref=f1e360]: First-order response coefficient; gain × timestep must be at most one.
                - generic [ref=f1e361]:
                  - generic [ref=f1e362]: Scenario XDL extension · default 0.8
                  - button "Apply" [disabled] [ref=f1e363]
              - generic [ref=f1e364]:
                - generic [ref=f1e365]:
                  - text: Initial state
                  - generic [ref=f1e366]: "1"
                  - spinbutton "Initial state 1" [ref=f1e367]: "0"
                - paragraph [ref=f1e368]: Initial normalized scalar state.
                - generic [ref=f1e369]:
                  - generic [ref=f1e370]: Scenario XDL extension · default 0
                  - button "Apply" [disabled] [ref=f1e371]
              - generic [ref=f1e372]:
                - generic [ref=f1e373]:
                  - text: Duration
                  - generic [ref=f1e374]: s
                  - spinbutton "Duration s" [ref=f1e375]: "5"
                - paragraph [ref=f1e376]: Requested simulation horizon, in seconds; at most 3,000 samples.
                - generic [ref=f1e377]:
                  - generic [ref=f1e378]: Scenario XDL extension · default 5
                  - button "Apply" [disabled] [ref=f1e379]
              - generic [ref=f1e380]:
                - generic [ref=f1e381]:
                  - text: Time step
                  - generic [ref=f1e382]: s
                  - spinbutton "Time step s" [ref=f1e383]: "0.1"
                - paragraph [ref=f1e384]: Fixed simulation step in seconds. Duration must be an integer number of steps.
                - generic [ref=f1e385]:
                  - generic [ref=f1e386]: Scenario XDL extension · default 0.1
                  - button "Apply" [disabled] [ref=f1e387]
              - generic [ref=f1e388]:
                - generic [ref=f1e389]:
                  - text: Reference fault
                  - generic [ref=f1e390]: "1"
                  - combobox "Reference fault 1" [ref=f1e391]:
                    - option "none" [selected]
                    - option "stuck-sensor"
                - paragraph [ref=f1e392]: Owned model fault only; stuck-sensor freezes the reported observation.
                - generic [ref=f1e393]:
                  - generic [ref=f1e394]: Scenario XDL extension · default none
                  - button "Apply" [disabled] [ref=f1e395]
          - generic [ref=f1e396]: Backend validation determines semantic compatibility and execution readiness.
      - generic [ref=f1e401]:
        - generic [ref=f1e402]: Local project · Saved on backend
        - generic [ref=f1e405]: Authoritative XDL · Layout stored separately
        - generic [ref=f1e406]: 1 provider(s) available
```

# Test source

```ts
  727 |         other.project.documents,
  728 |       );
  729 |       expect(await runs(page, current.projectId)).toEqual(beforeRuns);
  730 |       expect(await runs(page, other.pid)).toEqual([]);
  731 |       await info.attach("project-context-creation.json", {
  732 |         body: JSON.stringify({
  733 |           viewport,
  734 |           activeProjectId: current.projectId,
  735 |           createdProjectId: other.pid,
  736 |           createdProjectRetained: true,
  737 |           newerSourceSaveAcknowledged: true,
  738 |           newerModalAndFocusPreserved: true,
  739 |           noStart: true,
  740 |         }),
  741 |         contentType: "application/json",
  742 |       });
  743 |     } finally {
  744 |       await target.close();
  745 |     }
  746 |   });
  747 |   test(`project context: newest creation intent wins over earlier completion at ${viewport.width}x${viewport.height}`, async ({
  748 |     page,
  749 |   }, info) => {
  750 |     await page.setViewportSize(viewport);
  751 |     await connectStudio(page, info);
  752 |     const current = await create(
  753 |         page,
  754 |         `Overlapping creation context ${viewport.width}`,
  755 |       ),
  756 |       beforeRuns = await runs(page, current.projectId);
  757 |     await activate(
  758 |       page,
  759 |       page.getByRole("button", { name: "Catalog", exact: true }),
  760 |     );
  761 |     const entry = (
  762 |       await page.request.get("/api/v1/catalog").then((r) => r.json())
  763 |     ).items.find(
  764 |       (e: any) =>
  765 |         e.kind === "blueprint" && e.providerIds?.includes("studio.reference"),
  766 |     );
  767 |     const control = page
  768 |       .getByRole("article")
  769 |       .filter({
  770 |         has: page.getByRole("heading", { name: entry.name, exact: true }),
  771 |       })
  772 |       .getByRole("button", { name: "Open as project", exact: true });
  773 |     const pending: {
  774 |       project: any;
  775 |       release: () => void;
  776 |       finished: Promise<void>;
  777 |     }[] = [];
  778 |     const pattern = "**/api/v1/projects";
  779 |     await page.route(pattern, async (route) => {
  780 |       if (route.request().method() !== "POST") {
  781 |         await route.continue();
  782 |         return;
  783 |       }
  784 |       const response = await route.fetch();
  785 |       expect(response.status()).toBe(201);
  786 |       const project = await response.json();
  787 |       let release!: () => void, finish!: () => void;
  788 |       const gate = new Promise<void>((r) => (release = r)),
  789 |         finished = new Promise<void>((r) => (finish = r));
  790 |       pending.push({ project, release, finished });
  791 |       try {
  792 |         await gate;
  793 |         await route.fulfill({ response });
  794 |       } finally {
  795 |         finish();
  796 |       }
  797 |     });
  798 |     try {
  799 |       await activate(page, control);
  800 |       await expect.poll(() => pending.length).toBe(1);
  801 |       await activate(page, control);
  802 |       await expect.poll(() => pending.length).toBe(2);
  803 |       const metadata = page.waitForResponse(
  804 |         (r) =>
  805 |           new URL(r.url()).pathname === "/api/v1/projects" &&
  806 |           r.request().method() === "GET",
  807 |       );
  808 |       pending[0].release();
  809 |       await pending[0].finished;
  810 |       expect((await metadata).status()).toBe(200);
  811 |       // Let the earlier creation's metadata continuation run while the newer POST is held.
  812 |       await page.evaluate(
  813 |         () =>
  814 |           new Promise<void>((resolve) =>
  815 |             requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
  816 |           ),
  817 |       );
  818 |       pending[1].release();
  819 |       await pending[1].finished;
  820 |       await settle(page);
  821 |       const accepted = pending[1].project;
  822 |       await expect(page.locator(".project-header h1")).toHaveText(
  823 |         accepted.name,
  824 |       );
  825 |       expect(
  826 |         await page.evaluate(() => localStorage.getItem("studio.projectId")),
> 827 |       ).toBe(accepted.projectId);
      |         ^ Error: expect(received).toBe(expected) // Object.is equality
  828 |       expect(accepted.projectId).not.toBe(pending[0].project.projectId);
  829 |       for (const held of pending) {
  830 |         expect((await read(page, held.project.projectId)).documents).toEqual(
  831 |           held.project.documents,
  832 |         );
  833 |         expect(await runs(page, held.project.projectId)).toEqual([]);
  834 |       }
  835 |       expect((await read(page, current.projectId)).documents).toEqual(
  836 |         current.documents,
  837 |       );
  838 |       expect(await runs(page, current.projectId)).toEqual(beforeRuns);
  839 |       await info.attach("project-context-newest-creation.json", {
  840 |         body: JSON.stringify({
  841 |           viewport,
  842 |           originalProjectId: current.projectId,
  843 |           creationOrder: pending.map((p) => p.project.projectId),
  844 |           acceptedProjectId: accepted.projectId,
  845 |           completionOrder:
  846 |             "Earlier response released while newer response remains held",
  847 |           bothProjectsPreserved: true,
  848 |           noStart: true,
  849 |         }),
  850 |         contentType: "application/json",
  851 |       });
  852 |     } finally {
  853 |       for (const held of pending) held.release();
  854 |       await Promise.all(pending.map((p) => p.finished));
  855 |       await page.unroute(pattern);
  856 |     }
  857 |   });
  858 |   for (const failed of [false, true]) {
  859 |     test(`project context: obsolete startup ${failed ? "failure" : "success"} preserves Home at ${viewport.width}x${viewport.height}`, async ({
  860 |       page,
  861 |     }, info) => {
  862 |       await page.setViewportSize(viewport);
  863 |       await connectStudio(page, info);
  864 |       const current = await create(
  865 |           page,
  866 |           `Startup context ${failed} ${viewport.width}`,
  867 |         ),
  868 |         beforeRuns = await runs(page, current.projectId);
  869 |       let release!: () => void,
  870 |         finish!: () => void,
  871 |         ready = false;
  872 |       const gate = new Promise<void>((r) => (release = r)),
  873 |         finished = new Promise<void>((r) => (finish = r)),
  874 |         pattern = "**/api/v1/providers";
  875 |       await page.route(pattern, async (route) => {
  876 |         try {
  877 |           const response = await route.fetch();
  878 |           expect(response.status()).toBe(200);
  879 |           ready = true;
  880 |           await gate;
  881 |           if (failed)
  882 |             await route.fulfill({
  883 |               status: 503,
  884 |               contentType: "application/json",
  885 |               body: JSON.stringify({
  886 |                 code: "PROVIDER_DISCOVERY_UNAVAILABLE",
  887 |                 message: "Controlled startup metadata failure",
  888 |                 retryable: true,
  889 |               }),
  890 |             });
  891 |           else await route.fulfill({ response });
  892 |         } finally {
  893 |           finish();
  894 |         }
  895 |       });
  896 |       try {
  897 |         await page.reload();
  898 |         await expect.poll(() => ready).toBe(true);
  899 |         await activate(page, home(page));
  900 |         release();
  901 |         await finished;
  902 |         await settle(page);
  903 |         await expect(page.locator(".project-header")).toHaveCount(0);
  904 |         await expect(
  905 |           page.locator('.alerts .notice.error[role="alert"]'),
  906 |         ).toHaveCount(0);
  907 |         expect(
  908 |           await page.evaluate(() => localStorage.getItem("studio.projectId")),
  909 |         ).toBe(current.projectId);
  910 |         expect((await read(page, current.projectId)).documents).toEqual(
  911 |           current.documents,
  912 |         );
  913 |         expect(await runs(page, current.projectId)).toEqual(beforeRuns);
  914 |         await info.attach("project-context-startup.json", {
  915 |           body: JSON.stringify({
  916 |             viewport,
  917 |             failed,
  918 |             originalProviderReadStatus: 200,
  919 |             releasedStatus: failed ? 503 : 200,
  920 |             newerHomePreserved: true,
  921 |             projectUnchanged: true,
  922 |             scope: failed
  923 |               ? "Controlled HTTP failure of startup metadata after explicit Home"
  924 |               : "Held actual successful startup metadata after explicit Home",
  925 |             noStart: true,
  926 |           }),
  927 |           contentType: "application/json",
```
