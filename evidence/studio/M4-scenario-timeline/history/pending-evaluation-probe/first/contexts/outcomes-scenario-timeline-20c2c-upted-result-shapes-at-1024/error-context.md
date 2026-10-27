# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: outcomes.spec.ts >> scenario timeline pending: labelled valid pending and interrupted result shapes at 1024
- Location: .studio-local/scenario-timeline/pending-evaluation-probe/outcomes.spec.ts:129:6

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('region', { name: 'Selected run timeline', exact: true }).locator('tr[data-timeline-id]').filter({ hasText: 'evaluation · assertion' }).getByText('Execution: running', { exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('region', { name: 'Selected run timeline', exact: true }).locator('tr[data-timeline-id]').filter({ hasText: 'evaluation · assertion' }).getByText('Execution: running', { exact: true }) with timeout 10000ms
  - waiting for getByRole('region', { name: 'Selected run timeline', exact: true }).locator('tr[data-timeline-id]').filter({ hasText: 'evaluation · assertion' }).getByText('Execution: running', { exact: true })

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
  - heading "Owned timeline 1024" [level=1]
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
    - tab "Deployment"
    - tab "Experiments" [selected]
    - tab "Results 1"
    - button "XDL source"
  - text: Draft revision
  - code: "3"
  - text: 3 elements · 2 connections Run snapshot
  - code: snap-ab14d71
  - text: stopped
  - button "Draft differs from run inputs (1 document, 0 elements, 0 parameters)"
  - heading "Experiments" [level=2]
  - paragraph: Author bounded intent, inspect actual events, and assess immutable evidence.
  - button "Edit scenario XDL"
  - tablist "Experiment sections":
    - tab "Scenario"
    - tab "Timeline" [selected]
    - tab "Assertions"
    - tab "Campaigns"
  - region "Selected run timeline":
    - heading "Selected run timeline" [level=3]
    - paragraph: Frozen intentions, recorded events and immutable evaluation windows.
    - button "Inspect selected run timeline"
    - paragraph: Read-only inspection. Same-axis placement does not prove causality or an intended effect. Source time and receipt time remain separate.
    - text: Timeline clock
    - combobox "Timeline clock":
      - option "Frozen System default" [selected]
    - alert: Timeline availability is unknown. The timeline is malformed, unsupported or belongs to another input selection. Inspect again to retry. Inspect again to read the first page.
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  44  |   const duration = dense ? 2.1 : 0.2;
  45  |   params.find((p: any) => p.id === "duration").value = duration;
  46  |   if (dense) params.find((p: any) => p.id === "timestep").value = 0.01;
  47  |   params.find((p: any) => p.id === "fault").value = "stuck-sensor";
  48  |   const definitions =
  49  |     scenario.extensions["io.xverse.studio.experiments"].definitions;
  50  |   definitions.forEach(
  51  |     (d: any) => (d.window.endTick = String(Math.round(duration * 1000000))),
  52  |   );
  53  |   definitions.push({
  54  |     ...structuredClone(definitions[0]),
  55  |     evaluationId: "timeline-peak",
  56  |     name: "Timeline peak",
  57  |     kind: "metric",
  58  |     resultUnit: "1",
  59  |     expression: structuredClone(definitions[0].expression.left),
  60  |   });
  61  |   project = await request(
  62  |     page,
  63  |     `/projects/${project.projectId}/documents/${docId}`,
  64  |     "PUT",
  65  |     { content: stringify(scenario), format: "yaml" },
  66  |     project.revision,
  67  |   );
  68  |   const pf = await request(
  69  |     page,
  70  |     `/projects/${project.projectId}/preflights`,
  71  |     "POST",
  72  |     { revision: project.revision },
  73  |   );
  74  |   expect(pf.status, JSON.stringify(pf)).toBe("ready");
  75  |   const created = await request(page, "/runs", "POST", {
  76  |     snapshotId: pf.snapshotId,
  77  |     preflightId: pf.preflightId,
  78  |   });
  79  |   await expect
  80  |     .poll(async () => (await request(page, `/runs/${created.runId}`)).state)
  81  |     .toBe("stopped");
  82  |   const run = await request(page, `/runs/${created.runId}`);
  83  |   const snapshot = (await request(page, `/runs/${run.runId}/snapshot`))
  84  |     .snapshot;
  85  |   for (const d of (await request(page, `/runs/${run.runId}/definitions`))
  86  |     .items) {
  87  |     await request(page, `/runs/${run.runId}/evaluations`, "POST", {
  88  |       snapshotId: run.snapshotId,
  89  |       definitionRef: d.definitionRef,
  90  |       definitionDigest: d.definitionDigest,
  91  |       evidenceRefs: [run.runId + ":reference-journal"],
  92  |     });
  93  |   }
  94  |   const timeline = await request(page, `/runs/${run.runId}/timeline?limit=200`);
  95  |   expect(
  96  |     timeline.items.some((r: any) => r.kind === "fault.activation_observed"),
  97  |   ).toBe(true);
  98  |   scenario.spec.steps[0].id = "later-start";
  99  |   project = await request(
  100 |     page,
  101 |     `/projects/${project.projectId}/documents/${docId}`,
  102 |     "PUT",
  103 |     { content: stringify(scenario), format: "yaml" },
  104 |     project.revision,
  105 |   );
  106 |   const runIds = (await request(page, "/runs")).items.map((r: any) => r.runId);
  107 |   await page.evaluate(
  108 |     ({ project, run, snapshot }) => {
  109 |       localStorage.setItem("studio.projectId", project.projectId);
  110 |       localStorage.setItem("studio.lastRun." + project.projectId, run.runId);
  111 |       localStorage.setItem("studio.lastRun", run.runId);
  112 |       localStorage.setItem(
  113 |         "studio.selection." + project.projectId,
  114 |         JSON.stringify({
  115 |           deploymentRef: snapshot.selection.deploymentRef,
  116 |           scenarioRef: snapshot.selection.scenarioRef,
  117 |         }),
  118 |       );
  119 |     },
  120 |     { project, run, snapshot },
  121 |   );
  122 |   await page.reload();
  123 |   await page.getByRole("tab", { name: "Experiments", exact: true }).focus();
  124 |   await page.keyboard.press("Enter");
  125 |   return { project, run, snapshot, timeline, runIds };
  126 | }
  127 |
  128 | for (const width of [1024,1440]) {
  129 |  test(`scenario timeline pending: labelled valid pending and interrupted result shapes at ${width}`,async ({page},info) => {
  130 |   await page.setViewportSize({width,height:width === 1024 ? 768 : 900});await connectStudio(page,info);const made=await prepare(page,width);
  131 |   await page.getByRole("tab",{name:"Timeline",exact:true}).focus();await page.keyboard.press("Enter");
  132 |   const panel=page.getByRole("region",{name:"Selected run timeline",exact:true}), inspect=panel.getByRole("button",{name:"Inspect selected run timeline",exact:true});
  133 |   let status="running";
  134 |   await page.route(`**/api/v1/runs/${made.run.runId}/timeline*`,async route => {
  135 |    const value=structuredClone(made.timeline);value.evidenceScope="fixture";
  136 |    const row=value.items.find((r:any) => r.layer === "evaluation" && r.kind === "assertion");
  137 |    Object.assign(row,{executionStatus:status,coverage:null,partial:null,verdict:null,value:null,unit:null,evaluatorIdentity:{},reasons:status === "error" ? ["EVALUATION_INTERRUPTED"] : [],matchesCurrentEvidence:false,evidenceScope:"fixture"});
  138 |    await route.fulfill({json:value});
  139 |   });
  140 |   const writes:string[]=[];page.on("request",r => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) writes.push(r.method());});
  141 |   for (const selected of ["running","error"]) {
  142 |    status=selected;await expect(inspect).toBeEnabled();await inspect.focus();await page.keyboard.press("Enter");
  143 |    const row=panel.locator('tr[data-timeline-id]').filter({hasText:"evaluation · assertion"});
> 144 |    await expect(row.getByText("Execution: "+status,{exact:true})).toBeVisible();
      |                                                                   ^ Error: expect(locator).toBeVisible() failed
  145 |    await expect(row.getByText("No verdict",{exact:true})).toBeVisible();
  146 |    await expect(row).toContainText("Coverage: Unknown; partial: Unknown");
  147 |    await expect(row.getByText("Assertion verdict: pass",{exact:true})).toHaveCount(0);
  148 |    if (status === "error") await expect(row).toContainText("EVALUATION_INTERRUPTED");
  149 |    await expect(panel.locator('tr[data-timeline-id^="recorded:"]')).not.toHaveCount(0);
  150 |   }
  151 |   expect(writes).toEqual([]);expect((await request(page,`/runs/${made.run.runId}`)).journalDigest).toBe(made.run.journalDigest);
  152 |   await info.attach("shape-scope",{body:"Labelled transport shapes for valid pending/interrupted API records, not an actual live evaluation interruption or physical-provider claim.",contentType:"text/plain"});
  153 |  });
  154 | }
  155 |
```
