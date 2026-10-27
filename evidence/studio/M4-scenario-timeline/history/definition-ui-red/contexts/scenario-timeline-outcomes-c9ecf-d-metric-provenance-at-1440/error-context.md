# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline-outcomes.spec.ts >> scenario timeline outcomes: actual pass, fail, indeterminate and metric provenance at 1440
- Location: tests/e2e/scenario-timeline-outcomes.spec.ts:18:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('region', { name: 'Frozen assessment definitions', exact: true })
Expected substring: "Inspection does not evaluate these definitions"
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('region', { name: 'Frozen assessment definitions', exact: true }) with timeout 10000ms
  - waiting for getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('region', { name: 'Frozen assessment definitions', exact: true })

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
  - heading "Timeline outcome coverage 1440" [level=1]
  - text: Draft Process control terms Blueprint default presentation (not bound). Domain terms relabel the shared workflows; they never change semantics, execution or fidelity.. Documentation references are shown, never fetched. rev 2
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
  - code: "2"
  - text: 3 elements · 2 connections Run snapshot
  - code: snap-81ab21f
  - text: stopped
  - button "Draft matches run inputs"
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
      - option "simulation-time · declared"
    - term: Run
    - definition: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54
    - term: Snapshot
    - definition: snap-81ab21f2-60ee-4d42-aaf3-570eeb78004c
    - term: Snapshot digest
    - definition: sha256:21de0140b1fc02c3b13588eadafbe6e42fa9ff9d3eb33b91320ec72bc3ef7bf8
    - term: Executed project revision
    - definition: "2"
    - term: Frozen Scenario
    - definition: xdl://org.xverse.studio.process-control/scenario/reference-response
    - term: Frozen Deployment
    - definition: xdl://org.xverse.studio.process-control/deployment/local-reference
    - term: Source clock
    - definition: simulation-time
    - term: Admitted axis unit
    - definition: microsecond
    - term: Intent display codec
    - definition: studio.reference.seconds-microseconds.v1
    - term: Evidence scope
    - definition: owned_reference
    - term: Journal integrity
    - definition: valid
    - term: Evidence collection
    - definition: complete
    - term: Timeline coverage
    - definition: Not attested
    - status: Showing rows 1–13 of 13. 7 unplaced rows across the projection.
    - paragraph: "Input completeness: intentions complete; recorded evidence complete; evaluation lookup complete. Clock list complete."
    - paragraph: "Recorded gaps: 0. Gap list complete. No line bridges missing observations; an empty page does not establish absence."
    - term: Missing source times
    - definition: "4"
    - term: Malformed source times
    - definition: "0"
    - term: Missing receipt times
    - definition: "0"
    - term: Unsupported receipt encodings
    - definition: "0"
    - figure "Selected-page markers · simulation-time · microsecond. Independent markers and half-open evaluation ranges; exact ticks are in the table.":
      - text: Selected-page markers · simulation-time · microsecond. Independent markers and half-open evaluation ranges; exact ticks are in the table.
      - img "Scenario intent, recorded events and evaluation windows; structured alternative in Timeline records table": intent recorded evaluation 0 200000
      - paragraph: 6 of 6 placed page rows drawn. Overlapping markers retain separate identities in the table. This page is a display projection, not canonical coverage.
    - region "Scrollable timeline records":
      - table "Timeline records":
        - rowgroup:
          - row "Layer / identity Original time / placement Observation or assessment Scope / provenance":
            - columnheader "Layer / identity"
            - columnheader "Original time / placement"
            - columnheader "Observation or assessment"
            - columnheader "Scope / provenance"
        - rowgroup:
          - 'row "intent · intent.step start-reference 0 simulation-time · microsecond Placed in selected clock Declared schedule: 0 s Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them. declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#start-reference"':
            - cell "intent · intent.step start-reference":
              - strong: intent · intent.step
              - code: start-reference
            - 'cell "0 simulation-time · microsecond Placed in selected clock Declared schedule: 0 s"'
            - cell "Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them."
            - cell "declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#start-reference":
              - text: declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#start-reference
              - group: Inspect exact data
          - 'row "recorded · observation.available run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:3 0 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"0\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.103966Z · unix_seconds_reference_v1 observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1 owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · observation.available run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:3":
              - strong: recorded · observation.available
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:3
            - 'cell "0 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"0\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.103966Z · unix_seconds_reference_v1"'
            - 'cell "observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0 1"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · fault.activation_requested run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:4 100000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"100000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.204288Z · unix_seconds_reference_v1 kind: stuck-sensor owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · fault.activation_requested run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:4":
              - strong: recorded · fault.activation_requested
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:4
            - 'cell "100000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"100000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.204288Z · unix_seconds_reference_v1"'
            - 'cell "kind: stuck-sensor"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · fault.activation_observed run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:5 100000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"100000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.204449Z · unix_seconds_reference_v1 kind: stuck-sensor · measuredValue: 0 owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · fault.activation_observed run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:5":
              - strong: recorded · fault.activation_observed
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:5
            - 'cell "100000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"100000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.204449Z · unix_seconds_reference_v1"'
            - 'cell "kind: stuck-sensor · measuredValue: 0"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · observation.available run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:6 100000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"100000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.204537Z · unix_seconds_reference_v1 observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0.08000000000000002 1 owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · observation.available run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:6":
              - strong: recorded · observation.available
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:6
            - 'cell "100000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"100000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.204537Z · unix_seconds_reference_v1"'
            - 'cell "observerRef: state-observer Measurements: control: 0.8 1 · measured: 0 1 · target: 1 1 · value: 0.08000000000000002 1"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · run.state_changed run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:7 200000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"200000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.304048Z · unix_seconds_reference_v1 state: stopped owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · run.state_changed run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:7":
              - strong: recorded · run.state_changed
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:7
            - 'cell "200000 simulation-time · microsecond Placed in selected clock Original metadata: {\"clockDomain\":\"simulation-time\",\"resolution\":\"microsecond\",\"tick\":\"200000\",\"uncertainty\":0} Receipt UTC: 2026-10-27T05:22:13.304048Z · unix_seconds_reference_v1"'
            - 'cell "state: stopped"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "intent · intent.observer state-observer No source tick simulation-time · Unit unknown Unplaced: DECLARED_TIME_UNAVAILABLE Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them. declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#state-observer"':
            - cell "intent · intent.observer state-observer":
              - strong: intent · intent.observer
              - code: state-observer
            - 'cell "No source tick simulation-time · Unit unknown Unplaced: DECLARED_TIME_UNAVAILABLE"'
            - cell "Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them."
            - cell "declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#state-observer":
              - text: declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#state-observer
              - group: Inspect exact data
          - 'row "intent · intent.metric final-state No source tick Clock unknown · Unit unknown Unplaced: DECLARED_TIME_UNAVAILABLE Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them. declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#final-state"':
            - cell "intent · intent.metric final-state":
              - strong: intent · intent.metric
              - code: final-state
            - 'cell "No source tick Clock unknown · Unit unknown Unplaced: DECLARED_TIME_UNAVAILABLE"'
            - cell "Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them."
            - cell "declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#final-state":
              - text: declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response#final-state
              - group: Inspect exact data
          - 'row "intent · intent.provider_configuration configuration.fault No source tick Clock unknown · Unit unknown Unplaced: CONFIGURATION_HAS_NO_AUTHORED_POSITION Frozen provider parameter: fault = stuck-sensor. No authored position is inferred. Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them. declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response"':
            - cell "intent · intent.provider_configuration configuration.fault":
              - strong: intent · intent.provider_configuration
              - code: configuration.fault
            - 'cell "No source tick Clock unknown · Unit unknown Unplaced: CONFIGURATION_HAS_NO_AUTHORED_POSITION"'
            - 'cell "Frozen provider parameter: fault = stuck-sensor. No authored position is inferred. Declared intent only. Opaque actions and fault activation/recovery remain in frozen source; this view does not execute them."'
            - cell "declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response":
              - text: declared_intent_only xdl://org.xverse.studio.process-control/scenario/reference-response
              - group: Inspect exact data
          - 'row "recorded · run.state_changed run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:1 No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.103841Z · unix_seconds_reference_v1 state: running owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · run.state_changed run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:1":
              - strong: recorded · run.state_changed
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:1
            - 'cell "No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.103841Z · unix_seconds_reference_v1"'
            - 'cell "state: running"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · log.appended run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:2 No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.103901Z · unix_seconds_reference_v1 Recorded event owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · log.appended run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:2":
              - strong: recorded · log.appended
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:2
            - 'cell "No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.103901Z · unix_seconds_reference_v1"'
            - cell "Recorded event"
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · cleanup.updated run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:8 No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.304251Z · unix_seconds_reference_v1 status: complete owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · cleanup.updated run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:8":
              - strong: recorded · cleanup.updated
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:8
            - 'cell "No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.304251Z · unix_seconds_reference_v1"'
            - 'cell "status: complete"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
          - 'row "recorded · evidence.updated run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:9 No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.304441Z · unix_seconds_reference_v1 status: complete owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
            - cell "recorded · evidence.updated run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:9":
              - strong: recorded · evidence.updated
              - code: run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:9
            - 'cell "No source tick Clock unknown · Unit unknown Unplaced: SOURCE_TIME_UNAVAILABLE Original metadata: {} Receipt UTC: 2026-10-27T05:22:13.304441Z · unix_seconds_reference_v1"'
            - 'cell "status: complete"'
            - 'cell "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"':
              - text: "owned_reference Source provider: studio.reference · 1.0.0 run-d8e985eb-79d9-47bd-8943-0ca42d5d0f54:reference-journal"
              - group: Inspect exact data
    - button "Previous timeline page" [disabled]
    - button "Next timeline page" [disabled]
    - list:
      - listitem: Same-axis placement is not causality or proof of an intended effect.
      - listitem: Unplaced declarations and unknown clocks remain unsupported; receipt time is independent.
      - listitem: Windowed evaluations retain their own exact evidence provenance and do not change lifecycle.
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  1  | import { test, expect, type Page } from "@playwright/test";
  2  | import { parse, stringify } from "yaml";
  3  | import { connectStudio } from "./connect-studio";
  4  |
  5  | async function readOrWrite(page: Page, path: string, method = "GET", body?: unknown, revision?: number) {
  6  |   return page.evaluate(async ({path, method, body, revision}) => {
  7  |     const {csrfToken} = await fetch("/api/v1/session").then(r => r.json());
  8  |     const response = await fetch("/api/v1" + path, {method, headers:{"Content-Type":"application/json","X-CSRF-Token":csrfToken,
  9  |       ...(revision === undefined ? {} : {"If-Match":String(revision)}), ...(method === "POST" ? {"Idempotency-Key":crypto.randomUUID()} : {})},
  10 |       ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  11 |     const value=await response.json();
  12 |     if (!response.ok) throw new Error(`Owned outcome setup ${response.status} ${value.code || path}`);
  13 |     return value;
  14 |   },{path,method,body,revision});
  15 | }
  16 |
  17 | for (const width of [1024,1440]) {
  18 |   test(`scenario timeline outcomes: actual pass, fail, indeterminate and metric provenance at ${width}`, async ({page}, info) => {
  19 |     await page.setViewportSize({width,height:width === 1024 ? 768 : 900});await connectStudio(page,info);
  20 |     let project=await readOrWrite(page,"/projects","POST",{name:`Timeline outcome coverage ${width}`});
  21 |     const [docId, doc]:any=Object.entries(project.documents).find(([,d]:any) => parse(d.content).kind === "Scenario")!;
  22 |     const source=parse(doc.content), parameters=source.extensions["io.xverse.experiment"].parameters;
  23 |     parameters.find((p:any) => p.id === "duration").value=0.2;
  24 |     parameters.find((p:any) => p.id === "fault").value="stuck-sensor";
  25 |     const pass=structuredClone(source.extensions["io.xverse.studio.experiments"].definitions[0]);
  26 |     pass.window.endTick="200000";
  27 |     const fail=structuredClone(pass);fail.evaluationId="timeline-fail";fail.name="Actual failed bound";fail.expression.right.value=-1;
  28 |     const incomplete=structuredClone(pass);incomplete.evaluationId="timeline-incomplete";incomplete.name="Missing window coverage";incomplete.window.endTick="400000";
  29 |     const metric={...structuredClone(pass),evaluationId:"timeline-outcome-peak",name:"Actual numeric metric",kind:"metric",resultUnit:"1",expression:structuredClone(pass.expression.left)};
  30 |     source.extensions["io.xverse.studio.experiments"].definitions=[pass,fail,incomplete,metric];
  31 |     project=await readOrWrite(page,`/projects/${project.projectId}/documents/${docId}`,"PUT",{content:stringify(source),format:"yaml"},project.revision);
  32 |     const pf=await readOrWrite(page,`/projects/${project.projectId}/preflights`,"POST",{revision:project.revision});
  33 |     expect(pf.status,JSON.stringify(pf)).toBe("ready");
  34 |     const started=await readOrWrite(page,"/runs","POST",{snapshotId:pf.snapshotId,preflightId:pf.preflightId});
  35 |     await expect.poll(async () => (await readOrWrite(page,`/runs/${started.runId}`)).state,{timeout:20000}).toBe("stopped");
  36 |     const run=await readOrWrite(page,`/runs/${started.runId}`), snapshot=(await readOrWrite(page,`/runs/${run.runId}/snapshot`)).snapshot;
  37 |     const definitions=(await readOrWrite(page,`/runs/${run.runId}/definitions`)).items, jobs:any[]=[];
  38 |     await page.evaluate(({project,run}) => {localStorage.setItem("studio.projectId",project.projectId);localStorage.setItem("studio.lastRun."+project.projectId,run.runId);localStorage.setItem("studio.lastRun",run.runId);},{project,run});
  39 |     await page.reload();await page.getByRole("tab",{name:"Experiments",exact:true}).focus();await page.keyboard.press("Enter");
  40 |     await page.getByRole("tab",{name:"Timeline",exact:true}).focus();await page.keyboard.press("Enter");
  41 |     const before=page.getByRole("region",{name:"Selected run timeline",exact:true});
  42 |     const initialWrites:string[]=[];const watch=(r:any) => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) initialWrites.push(r.method());};page.on("request",watch);
  43 |     await before.getByRole("button",{name:"Inspect selected run timeline",exact:true}).focus();await page.keyboard.press("Enter");
  44 |     await expect(before.getByRole("heading",{name:"Selected run timeline",exact:true})).toBeFocused();
  45 |     const declared=before.getByRole("region",{name:"Frozen assessment definitions",exact:true});
> 46 |     await expect(declared).toContainText("Inspection does not evaluate these definitions");
     |                            ^ Error: expect(locator).toContainText(expected) failed
  47 |     for (const d of definitions) {
  48 |       const row=declared.locator(`[data-definition-ref="${d.definitionRef}"]`);
  49 |       await expect(row).toContainText(d.definition.name);
  50 |       await row.getByText("Inspect exact data",{exact:true}).focus();await page.keyboard.press("Enter");
  51 |       expect(JSON.parse(await row.locator("pre").innerText())).toEqual(d);
  52 |     }
  53 |     await expect(before.locator('tr[data-timeline-id^="evaluation:"]')).toHaveCount(0);
  54 |     expect((await readOrWrite(page,`/runs/${run.runId}/evaluations`)).items).toEqual([]);
  55 |     expect(initialWrites).toEqual([]);page.off("request",watch);
  56 |     for (const d of definitions) {
  57 |       const accepted=await readOrWrite(page,`/runs/${run.runId}/evaluations`,"POST",{snapshotId:run.snapshotId,definitionRef:d.definitionRef,definitionDigest:d.definitionDigest,evidenceRefs:[run.runId+":reference-journal"]});
  58 |       await expect.poll(async () => (await readOrWrite(page,`/evaluations/${accepted.evaluationId}`)).status).toBe("complete");
  59 |       jobs.push(await readOrWrite(page,`/evaluations/${accepted.evaluationId}`));
  60 |     }
  61 |     const failed=jobs.find(j => j.definition.evaluationId === "timeline-fail"), unknown=jobs.find(j => j.definition.evaluationId === "timeline-incomplete"), numeric=jobs.find(j => j.definition.kind === "metric");
  62 |     expect(failed.verdict).toBe("fail");expect(failed.coverage).toBe("complete");expect(unknown.verdict).toBe("indeterminate");expect(unknown.coverage).toBe("incomplete");expect(unknown.reasons).toContain("COVERAGE_INCOMPLETE");expect(numeric.verdict).toBeNull();expect(Number.isFinite(numeric.value)).toBe(true);
  63 |     await page.evaluate(({project,run}) => {localStorage.setItem("studio.projectId",project.projectId);localStorage.setItem("studio.lastRun."+project.projectId,run.runId);localStorage.setItem("studio.lastRun",run.runId);},{project,run});
  64 |     await page.reload();await page.getByRole("tab",{name:"Experiments",exact:true}).focus();await page.keyboard.press("Enter");
  65 |     await page.getByRole("tab",{name:"Timeline",exact:true}).focus();await page.keyboard.press("Enter");
  66 |     const panel=page.getByRole("region",{name:"Selected run timeline",exact:true}), writes:string[]=[], errors:string[]=[];
  67 |     page.on("request",r => {if (!["GET","HEAD","OPTIONS"].includes(r.method())) writes.push(r.method()+" "+new URL(r.url()).pathname);});page.on("pageerror",e => errors.push(e.message));
  68 |     await panel.getByRole("button",{name:"Inspect selected run timeline",exact:true}).focus();await page.keyboard.press("Enter");
  69 |     await expect(panel.getByRole("heading",{name:"Selected run timeline",exact:true})).toBeFocused();
  70 |     for (const job of jobs) {
  71 |       const row=panel.locator(`[data-timeline-id="evaluation:${job.evaluationId}"]`);
  72 |       await expect(row.getByText("Execution: complete",{exact:true})).toBeVisible();
  73 |       await expect(row.getByText(job.verdict === null ? "No verdict" : `Assertion verdict: ${job.verdict}`,{exact:true})).toBeVisible();
  74 |       await expect(row).toContainText(`[${job.definition.window.startTick}, ${job.definition.window.endTick})`);
  75 |       await expect(row.getByText(`Reasons: ${job.reasons.join(", ") || "None reported"}`,{exact:true})).toBeVisible();
  76 |       await row.getByText("Inspect exact data",{exact:true}).focus();await page.keyboard.press("Enter");
  77 |       const shown=JSON.parse(await row.locator("pre").innerText());
  78 |       expect(shown.definitionDigest).toBe(job.definitionDigest);expect(shown.evidenceDigests).toEqual(job.evidenceDigests);expect(shown.inputEvidenceDigests).toEqual(job.inputEvidenceDigests);
  79 |       expect(shown.evaluatorIdentity).toEqual(job.evaluatorIdentity);expect(shown.window).toEqual(job.definition.window);expect(shown.matchesCurrentEvidence).toBe(true);
  80 |       await expect(row.getByText("Inspect exact data",{exact:true})).toBeFocused();
  81 |     }
  82 |     const unknownRow=panel.locator(`[data-timeline-id="evaluation:${unknown.evaluationId}"]`);
  83 |     await expect(unknownRow.getByText("Assertion verdict: pass",{exact:true})).toHaveCount(0);
  84 |     expect(await readOrWrite(page,`/projects/${project.projectId}`)).toEqual(project);
  85 |     expect((await readOrWrite(page,`/runs/${run.runId}/snapshot`)).snapshot).toEqual(snapshot);
  86 |     expect((await readOrWrite(page,`/runs/${run.runId}`)).journalDigest).toBe(run.journalDigest);
  87 |     for (const job of jobs) expect(await readOrWrite(page,`/evaluations/${job.evaluationId}`)).toEqual(job);
  88 |     expect(writes).toEqual([]);expect(errors).toEqual([]);expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth+1)).toBe(false);
  89 |     await info.attach("actual-outcome-provenance",{body:JSON.stringify({runId:run.runId,snapshotId:run.snapshotId,scope:run.evidenceScope,journalDigest:run.journalDigest,results:jobs.map(j => ({evaluationId:j.evaluationId,definitionRef:j.definitionRef,definitionDigest:j.definitionDigest,verdict:j.verdict,value:j.value,coverage:j.coverage,reasons:j.reasons,evaluatorIdentity:j.evaluatorIdentity,evidenceDigests:j.evidenceDigests}))},null,2),contentType:"application/json"});
  90 |     await page.screenshot({path:info.outputPath(`actual-outcomes-${width}.png`),fullPage:true});
  91 |   });
  92 | }
  93 |
```
