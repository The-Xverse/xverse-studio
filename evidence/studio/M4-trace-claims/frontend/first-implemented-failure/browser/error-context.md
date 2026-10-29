# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: trace-claims.spec.ts >> reported external claims: frozen subjects, revision history, neutral PASS label and immutable exchange
- Location: tests/e2e/trace-claims.spec.ts:5:5

# Error details

```
TimeoutError: locator.fill: Timeout 15000ms exceeded.
Call log:
  - waiting for getByLabel('Reported claim status', { exact: true })

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
    - complementary "Main navigation" [ref=f2e22]:
      - button "Workspace" [ref=f2e23] [cursor=pointer]
      - button "Catalog" [ref=f2e30] [cursor=pointer]
      - button "Laboratory" [ref=f2e37] [cursor=pointer]:
        - generic [ref=f2e41]: Lab
      - button "Compatibility and environment" [ref=f2e42] [cursor=pointer]:
        - generic [ref=f2e48]: Settings
      - generic [ref=f2e49]: v0.1
    - main [ref=f2e50]:
      - generic [ref=f2e51]:
        - generic [ref=f2e52]:
          - generic [ref=f2e53]:
            - button "Workspace" [ref=f2e54] [cursor=pointer]
            - generic [ref=f2e57]: System
          - generic [ref=f2e58]:
            - heading "Reported claim browser reference" [level=1] [ref=f2e65]
            - generic [ref=f2e66]: Draft
            - generic [ref=f2e67]: rev 2
        - generic [ref=f2e68]:
          - button "Export" [ref=f2e69] [cursor=pointer]
          - button "Validate" [ref=f2e72] [cursor=pointer]
          - button "Preflight & run" [ref=f2e75] [cursor=pointer]
      - tablist "System workflows" [ref=f2e78]:
        - tab "Model" [ref=f2e79] [cursor=pointer]
        - tab "Connections" [ref=f2e85] [cursor=pointer]
        - tab "Deployment" [ref=f2e90] [cursor=pointer]
        - tab "Experiments" [ref=f2e93] [cursor=pointer]
        - tab "Results 1" [selected] [ref=f2e96] [cursor=pointer]:
          - text: Results
          - generic [ref=f2e99]: "1"
        - button "XDL source" [ref=f2e101] [cursor=pointer]
      - generic [ref=f2e104]:
        - generic [ref=f2e105]:
          - text: Draft revision
          - code [ref=f2e107]: "2"
        - generic [ref=f2e108]: 3 elements · 2 connections
        - generic [ref=f2e109]:
          - text: Run snapshot
          - code [ref=f2e110]: snap-ce49f35
          - generic [ref=f2e111]: stopped
      - generic [ref=f2e112]:
        - generic [ref=f2e113]:
          - generic [ref=f2e114]:
            - heading "Run results stopped" [level=2] [ref=f2e115]:
              - text: Run results
              - generic [ref=f2e116]: stopped
            - paragraph [ref=f2e117]:
              - code [ref=f2e118]: run-71a3921d-a15d-4c76-bf4b-1ec7b83ff26b
              - generic [ref=f2e119]:
                - text: Snapshot
                - code [ref=f2e120]: snap-ce49f354-cb17
          - generic [ref=f2e121]:
            - button "Frozen inputs" [ref=f2e122] [cursor=pointer]
            - button "Rerun frozen inputs" [ref=f2e125] [cursor=pointer]
            - button "Refresh" [ref=f2e128] [cursor=pointer]
        - generic [ref=f2e131]:
          - generic [ref=f2e132]:
            - text: Execution
            - strong [ref=f2e133]: stopped
            - text: Lifecycle outcome
          - generic [ref=f2e135]:
            - text: Assertion verdict
            - strong [ref=f2e136]: fail
            - text: Separate assessment result
          - generic [ref=f2e138]:
            - text: Cleanup
            - strong [ref=f2e139]: complete
            - text: Owned-resource release
          - generic [ref=f2e141]:
            - text: Evidence
            - strong [ref=f2e142]: complete
            - text: Integrity and completeness
        - generic [ref=f2e144]:
          - generic [ref=f2e145]: owned_reference
          - generic [ref=f2e146]: owned_reference · Source clocks retained · Browser presentation is bounded
          - generic [ref=f2e147]: Retained history available
        - tablist "Result sections" [ref=f2e149]:
          - tab "Observations" [ref=f2e150] [cursor=pointer]
          - tab "Events & logs 0" [ref=f2e151] [cursor=pointer]:
            - text: Events & logs
            - generic [ref=f2e152]: "0"
          - tab "Evidence" [ref=f2e153] [cursor=pointer]
          - tab "Compare" [ref=f2e154] [cursor=pointer]
          - tab "Annotations" [selected] [ref=f2e155] [cursor=pointer]
        - generic [ref=f2e156]:
          - generic [ref=f2e157]:
            - heading "Separate annotations" [level=3] [ref=f2e158]
            - paragraph [ref=f2e159]: User commentary and trace links do not modify the historical evidence.
            - paragraph [ref=f2e160]: No annotations on this run.
          - complementary [ref=f2e161]:
            - heading "Add a review note" [level=3] [ref=f2e162]
            - generic [ref=f2e163]:
              - generic [ref=f2e164]:
                - text: Comment
                - textbox "Comment" [ref=f2e165]
              - button "Save separate annotation" [disabled] [ref=f2e166]
            - paragraph [ref=f2e167]: An external requirement reference is traceability, not proof that the requirement passed.
            - generic [ref=f2e168]:
              - heading "External requirement / test reference" [level=3] [ref=f2e169]
              - generic [ref=f2e170]:
                - paragraph [ref=f2e171]: These associations use this run's immutable inputs. They do not change source, definitions, evaluation verdicts or evidence.
                - generic [ref=f2e172]:
                  - text: Requirement or test URI
                  - textbox "Requirement or test URI" [ref=f2e173]:
                    - /placeholder: urn:requirements:example:17
                    - text: urn:requirements:browser:trace-1
                - generic [ref=f2e174]:
                  - text: Referenced revision
                  - textbox "Referenced revision" [ref=f2e175]:
                    - /placeholder: Pinned revision, or unknown
                    - text: external-r7
                - generic [ref=f2e176]:
                  - checkbox "Include reported claim status" [checked] [active] [ref=f2e177]
                  - text: Include reported claim status
                - generic [ref=f2e178]:
                  - text: Reported claim status
                  - textbox "Reported claim status Preserved as reported text. Studio does not verify it or infer a pass." [ref=f2e179]
                  - text: Preserved as reported text. Studio does not verify it or infer a pass.
                - generic [ref=f2e180]:
                  - text: Reference note (optional)
                  - textbox "Reference note (optional)" [ref=f2e181]
                - paragraph [ref=f2e182]: "Frozen snapshot: snap-ce49f354-cb17-4ee8-b33d-176acb7f94aa"
                - group "Frozen model and Scenario references" [ref=f2e183]:
                  - generic [ref=f2e185]:
                    - checkbox "Component · reference-controller" [ref=f2e186]
                    - text: Component · reference-controller
                  - generic [ref=f2e187]:
                    - checkbox "Deployment · local-reference" [ref=f2e188]
                    - text: Deployment · local-reference
                  - generic [ref=f2e189]:
                    - checkbox "Profile · studio-experiments" [ref=f2e190]
                    - text: Profile · studio-experiments
                  - generic [ref=f2e191]:
                    - checkbox "Component · reference-plant" [ref=f2e192]
                    - text: Component · reference-plant
                  - generic [ref=f2e193]:
                    - checkbox "Profile · experiment-lite" [ref=f2e194]
                    - text: Profile · experiment-lite
                  - generic [ref=f2e195]:
                    - checkbox "Scenario · reference-response" [ref=f2e196]
                    - text: Scenario · reference-response
                  - generic [ref=f2e197]:
                    - checkbox "System · reference-loop" [ref=f2e198]
                    - text: System · reference-loop
                  - generic [ref=f2e199]:
                    - checkbox "node · controller-node" [ref=f2e200]
                    - text: node · controller-node
                  - generic [ref=f2e201]:
                    - checkbox "node · plant-node" [ref=f2e202]
                    - text: node · plant-node
                  - generic [ref=f2e203]:
                    - checkbox "node · observer-node" [ref=f2e204]
                    - text: node · observer-node
                  - generic [ref=f2e205]:
                    - checkbox "componentInstance · controller" [ref=f2e206]
                    - text: componentInstance · controller
                  - generic [ref=f2e207]:
                    - checkbox "componentInstance · plant" [ref=f2e208]
                    - text: componentInstance · plant
                  - generic [ref=f2e209]:
                    - checkbox "flow · command-flow" [ref=f2e210]
                    - text: flow · command-flow
                  - generic [ref=f2e211]:
                    - checkbox "flow · state-flow" [ref=f2e212]
                    - text: flow · state-flow
                - group "Frozen assertions and metrics" [ref=f2e213]:
                  - generic [ref=f2e215]:
                    - checkbox "assertion · Reference state within bound" [ref=f2e216]
                    - text: assertion · Reference state within bound
                - generic [ref=f2e217]:
                  - checkbox "Owned run journal" [checked] [ref=f2e218]
                  - text: Owned run journal
                - generic [ref=f2e219]:
                  - button "Save external reference" [disabled] [ref=f2e220]
                  - button "Cancel reference edit" [ref=f2e221] [cursor=pointer]
      - generic [ref=f2e222]:
        - generic [ref=f2e223]: Local project · Saved on backend
        - generic [ref=f2e226]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e227]: 1 provider(s) available
```

# Test source

```ts
  3   | import { connectStudio } from "./connect-studio";
  4   | import { inspectTraceForm, traceApi } from "./trace-claims-flow";
  5   | test("reported external claims: frozen subjects, revision history, neutral PASS label and immutable exchange", async ({
  6   |   page,
  7   | }, testInfo) => {
  8   |   test.setTimeout(120000);
  9   |   await connectStudio(page, testInfo);
  10  |   const errors: string[] = [];
  11  |   page.on("pageerror", (error) => errors.push(error.message));
  12  |   await page.getByRole("button", { name: "New project", exact: true }).click();
  13  |   await page
  14  |     .getByLabel("Project name", { exact: true })
  15  |     .fill("Reported claim browser reference");
  16  |   await page
  17  |     .getByRole("button", { name: "Create project", exact: true })
  18  |     .click();
  19  |   await expect(page.locator(".project-header h1")).toHaveText(
  20  |     "Reported claim browser reference",
  21  |   );
  22  |   const projectId = await page.evaluate(() =>
  23  |     localStorage.getItem("studio.projectId"),
  24  |   );
  25  |   const project = (await traceApi(page, "/projects/" + projectId)).body;
  26  |   const [documentId, document] = Object.entries(project.documents).find(
  27  |     ([, value]: any) => parse(value.content).kind === "Scenario",
  28  |   )! as [string, any];
  29  |   const scenario = parse(document.content);
  30  |   scenario.extensions["io.xverse.experiment"].parameters.find(
  31  |     (p: any) => p.id === "duration",
  32  |   ).value = 0.2;
  33  |   scenario.extensions[
  34  |     "io.xverse.studio.experiments"
  35  |   ].definitions[0].window.endTick = "200000";
  36  |   scenario.extensions[
  37  |     "io.xverse.studio.experiments"
  38  |   ].definitions[0].expression.right.value = -1;
  39  |   expect(
  40  |     (
  41  |       await traceApi(
  42  |         page,
  43  |         `/projects/${projectId}/documents/${documentId}`,
  44  |         "PUT",
  45  |         { content: stringify(scenario), format: "yaml" },
  46  |         project.revision,
  47  |       )
  48  |     ).status,
  49  |   ).toBe(200);
  50  |   await page.reload();
  51  |   await expect(page.locator(".project-header h1")).toHaveText(
  52  |     "Reported claim browser reference",
  53  |   );
  54  |   await page
  55  |     .getByRole("button", { name: "Preflight & run", exact: true })
  56  |     .click();
  57  |   await expect(
  58  |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  59  |   ).toBeEnabled();
  60  |   await page
  61  |     .getByRole("button", { name: "Start frozen snapshot", exact: true })
  62  |     .click();
  63  |   await expect(
  64  |     page.getByRole("heading", { name: /Run results/ }),
  65  |   ).toBeVisible();
  66  |   await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
  67  |     timeout: 20000,
  68  |   });
  69  |   const runId = (await page.evaluate(() =>
  70  |     localStorage.getItem("studio.lastRun"),
  71  |   ))!;
  72  |   const run = (await traceApi(page, "/runs/" + runId)).body;
  73  |   const definition = (await traceApi(page, `/runs/${runId}/definitions`)).body
  74  |     .items[0];
  75  |   const evaluated = await traceApi(page, `/runs/${runId}/evaluations`, "POST", {
  76  |     snapshotId: run.snapshotId,
  77  |     definitionRef: definition.definitionRef,
  78  |     definitionDigest: definition.definitionDigest,
  79  |     evidenceRefs: [runId + ":reference-journal"],
  80  |   });
  81  |   expect(evaluated.status).toBe(202);
  82  |   const beforeSnapshot = (await traceApi(page, `/runs/${runId}/snapshot`)).body
  83  |     .snapshot;
  84  |   const beforeEvidence = (await traceApi(page, `/runs/${runId}/evidence`)).body;
  85  |   expect((await traceApi(page, "/runs/" + runId)).body.verdict).toBe("fail");
  86  |   await page.reload();
  87  |   await page.getByRole("tab", { name: "Results", exact: false }).click();
  88  |   await expect(
  89  |     page.locator(".status-card").filter({ hasText: "Assertion verdict" }),
  90  |   ).toContainText("fail");
  91  |   await inspectTraceForm(page);
  92  |   await page
  93  |     .getByLabel("Requirement or test URI", { exact: true })
  94  |     .fill("urn:requirements:browser:trace-1");
  95  |   await page
  96  |     .getByLabel("Referenced revision", { exact: true })
  97  |     .fill("external-r7");
  98  |   await page
  99  |     .getByLabel("Include reported claim status", { exact: true })
  100 |     .check();
  101 |   await page
  102 |     .getByLabel("Reported claim status", { exact: true })
> 103 |     .fill("  PASS reported externally  ");
      |      ^ TimeoutError: locator.fill: Timeout 15000ms exceeded.
  104 |   const subjects = page.getByRole("group", {
  105 |     name: "Frozen model and Scenario references",
  106 |     exact: true,
  107 |   });
  108 |   await subjects
  109 |     .getByLabel("componentInstance · plant", { exact: true })
  110 |     .check();
  111 |   await subjects
  112 |     .getByLabel("Scenario · reference-response", { exact: true })
  113 |     .check();
  114 |   await page
  115 |     .getByRole("group", { name: "Frozen assertions and metrics", exact: true })
  116 |     .getByRole("checkbox")
  117 |     .first()
  118 |     .check();
  119 |   await page.getByLabel("Owned run journal", { exact: true }).check();
  120 |   await page
  121 |     .getByRole("button", { name: "Save external reference", exact: true })
  122 |     .focus();
  123 |   await page.keyboard.press("Enter");
  124 |   const row = page.getByRole("article", {
  125 |     name: "External reference urn:requirements:browser:trace-1",
  126 |     exact: true,
  127 |   });
  128 |   await expect(row.locator(".trace-reported-status")).toHaveText(
  129 |     "  PASS reported externally  ",
  130 |   );
  131 |   expect(await row.locator(".trace-reported-status").textContent()).toBe(
  132 |     "  PASS reported externally  ",
  133 |   );
  134 |   await expect(
  135 |     row.getByText("Reported claim status", { exact: true }),
  136 |   ).toBeVisible();
  137 |   await expect(row.locator(".badge")).toHaveCount(0);
  138 |   await expect(
  139 |     page.locator(".status-card").filter({ hasText: "Assertion verdict" }),
  140 |   ).toContainText("fail");
  141 |   await row
  142 |     .getByRole("button", { name: "Edit external reference", exact: true })
  143 |     .click();
  144 |   await expect(
  145 |     page.getByLabel("Reported claim status", { exact: true }),
  146 |   ).toHaveValue("  PASS reported externally  ");
  147 |   await page
  148 |     .getByLabel("Reported claim status", { exact: true })
  149 |     .fill("Review still pending");
  150 |   await page
  151 |     .getByRole("button", { name: "Save reference revision", exact: true })
  152 |     .click();
  153 |   await expect(row).toContainText("Review still pending");
  154 |   const rows = (await traceApi(page, `/runs/${runId}/annotations`)).body.items;
  155 |   const linked = rows.find(
  156 |     (r: any) => r.target?.uri === "urn:requirements:browser:trace-1",
  157 |   );
  158 |   expect(linked.revision).toBe(2);
  159 |   expect(linked.target.claimStatus).toBe("Review still pending");
  160 |   expect(linked.history[0].target.claimStatus).toBe(
  161 |     "  PASS reported externally  ",
  162 |   );
  163 |   expect(linked.definitionRefs).toEqual([
  164 |     {
  165 |       definitionRef: definition.definitionRef,
  166 |       definitionDigest: definition.definitionDigest,
  167 |     },
  168 |   ]);
  169 |   await row
  170 |     .getByRole("button", { name: "Remove external reference", exact: true })
  171 |     .click();
  172 |   await expect(row).toContainText(
  173 |     "Annotation removed; historical revisions retained.",
  174 |   );
  175 |   await inspectTraceForm(page);
  176 |   await page
  177 |     .getByLabel("Requirement or test URI", { exact: true })
  178 |     .fill("urn:requirements:browser:legacy");
  179 |   await page.getByLabel("Referenced revision", { exact: true }).fill("unknown");
  180 |   await page
  181 |     .getByRole("button", { name: "Save external reference", exact: true })
  182 |     .click();
  183 |   await expect(
  184 |     page.getByRole("article", {
  185 |       name: "External reference urn:requirements:browser:legacy",
  186 |       exact: true,
  187 |     }),
  188 |   ).toContainText("Not supplied");
  189 |   const latest = (await traceApi(page, `/runs/${runId}/annotations`)).body
  190 |     .items;
  191 |   expect(
  192 |     latest.find((r: any) => r.target?.uri.endsWith(":legacy")).target,
  193 |   ).not.toHaveProperty("claimStatus");
  194 |   expect(
  195 |     latest.find((r: any) => r.annotationId === linked.annotationId).deleted,
  196 |   ).toBe(true);
  197 |   expect(
  198 |     (await traceApi(page, `/runs/${runId}/snapshot`)).body.snapshot,
  199 |   ).toEqual(beforeSnapshot);
  200 |   expect((await traceApi(page, `/runs/${runId}/evidence`)).body).toEqual(
  201 |     beforeEvidence,
  202 |   );
  203 |   expect((await traceApi(page, "/runs/" + runId)).body.verdict).toBe("fail");
```
