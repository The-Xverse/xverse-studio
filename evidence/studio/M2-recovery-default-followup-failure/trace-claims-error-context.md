# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: trace-claims.spec.ts >> reported external claims: frozen subjects, revision history, neutral PASS label and immutable exchange
- Location: tests/e2e/trace-claims.spec.ts:5:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('article', { name: 'External reference urn:requirements:browser:trace-1', exact: true })
Timeout: 10000ms
- Expected substring  -  1
+ Received string     + 30

- Review still pending
+ trace_linkrev 11793180829.325683External URIurn:requirements:browser:trace-1Referenced revisionexternal-r7Reported claim status  PASS reported externally  Reported metadata only. Studio has not verified this external claim.Model / Scenario: xdl://org.xverse.studio.process-control/system/reference-loop#plant, xdl://org.xverse.studio.process-control/scenario/reference-responseFrozen definitions: state-within-bound (sha256:944ceedb67b5d774c363e339f383bafcbb90d4ef875b4634b5bfda9a9cff450e)Evidence: run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6:reference-journalEdit external referenceRemove external referenceInspect exact data{
+   "annotationId": "ann-52088a24-b99f-48be-bfdd-5cce82e36d89",
+   "author": "local-operator",
+   "createdAt": 1793180829.325683,
+   "definitionRefs": [
+     {
+       "definitionDigest": "sha256:944ceedb67b5d774c363e339f383bafcbb90d4ef875b4634b5bfda9a9cff450e",
+       "definitionRef": "state-within-bound"
+     }
+   ],
+   "deleted": false,
+   "elementRefs": [
+     "xdl://org.xverse.studio.process-control/system/reference-loop#plant",
+     "xdl://org.xverse.studio.process-control/scenario/reference-response"
+   ],
+   "evidenceRefs": [
+     "run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6:reference-journal"
+   ],
+   "history": [],
+   "kind": "trace_link",
+   "revision": 1,
+   "runId": "run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6",
+   "target": {
+     "claimStatus": "  PASS reported externally  ",
+     "revision": "external-r7",
+     "uri": "urn:requirements:browser:trace-1"
+   },
+   "text": "",
+   "updatedAt": 1793180829.3256834
+ }

Call log:
  - Expect "toContainText" getByRole('article', { name: 'External reference urn:requirements:browser:trace-1', exact: true }) with timeout 10000ms
  - waiting for getByRole('article', { name: 'External reference urn:requirements:browser:trace-1', exact: true })
    24 × locator resolved to <article class="annotation" aria-label="External reference urn:requirements:browser:trace-1">…</article>
       - unexpected value "trace_linkrev 11793180829.325683External URIurn:requirements:browser:trace-1Referenced revisionexternal-r7Reported claim status  PASS reported externally  Reported metadata only. Studio has not verified this external claim.Model / Scenario: xdl://org.xverse.studio.process-control/system/reference-loop#plant, xdl://org.xverse.studio.process-control/scenario/reference-responseFrozen definitions: state-within-bound (sha256:944ceedb67b5d774c363e339f383bafcbb90d4ef875b4634b5bfda9a9cff450e)Evidence: run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6:reference-journalEdit external referenceRemove external referenceInspect exact data{
  "annotationId": "ann-52088a24-b99f-48be-bfdd-5cce82e36d89",
  "author": "local-operator",
  "createdAt": 1793180829.325683,
  "definitionRefs": [
    {
      "definitionDigest": "sha256:944ceedb67b5d774c363e339f383bafcbb90d4ef875b4634b5bfda9a9cff450e",
      "definitionRef": "state-within-bound"
    }
  ],
  "deleted": false,
  "elementRefs": [
    "xdl://org.xverse.studio.process-control/system/reference-loop#plant",
    "xdl://org.xverse.studio.process-control/scenario/reference-response"
  ],
  "evidenceRefs": [
    "run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6:reference-journal"
  ],
  "history": [],
  "kind": "trace_link",
  "revision": 1,
  "runId": "run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6",
  "target": {
    "claimStatus": "  PASS reported externally  ",
    "revision": "external-r7",
    "uri": "urn:requirements:browser:trace-1"
  },
  "text": "",
  "updatedAt": 1793180829.3256834
}"

```

```yaml
- article "External reference urn:requirements:browser:trace-1":
  - strong: trace_link
  - text: rev 1
  - paragraph
  - text: "1793180829.325683"
  - term: External URI
  - definition: urn:requirements:browser:trace-1
  - term: Referenced revision
  - definition: external-r7
  - term: Reported claim status
  - definition: PASS reported externally
  - paragraph: Reported metadata only. Studio has not verified this external claim.
  - paragraph: "Model / Scenario: xdl://org.xverse.studio.process-control/system/reference-loop#plant, xdl://org.xverse.studio.process-control/scenario/reference-response"
  - paragraph: "Frozen definitions: state-within-bound (sha256:944ceedb67b5d774c363e339f383bafcbb90d4ef875b4634b5bfda9a9cff450e)"
  - paragraph: "Evidence: run-b983b1e1-51d2-48a4-8fcd-8f018c90c7e6:reference-journal"
  - button "Edit external reference"
  - button "Remove external reference"
  - group: Inspect exact data
```

# Test source

```ts
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
  103 |     .fill("  PASS reported externally  ");
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
> 153 |   await expect(row).toContainText("Review still pending");
      |                     ^ Error: expect(locator).toContainText(expected) failed
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
  175 |   await page.route(`**/api/v1/runs/${runId}/snapshot`, (route) =>
  176 |     route.fulfill({
  177 |       status: 503,
  178 |       contentType: "application/json",
  179 |       body: JSON.stringify({
  180 |         code: "SNAPSHOT_UNAVAILABLE",
  181 |         message: "Subject reader unavailable for this UI transport fixture.",
  182 |       }),
  183 |     }),
  184 |   );
  185 |   await inspectTraceForm(page);
  186 |   await expect(
  187 |     page
  188 |       .getByRole("alert")
  189 |       .filter({ hasText: "Journal-only references remain available" }),
  190 |   ).toBeVisible();
  191 |   await page
  192 |     .getByLabel("Requirement or test URI", { exact: true })
  193 |     .fill("urn:requirements:browser:legacy");
  194 |   await page.getByLabel("Referenced revision", { exact: true }).fill("unknown");
  195 |   await page
  196 |     .getByRole("button", { name: "Save external reference", exact: true })
  197 |     .click();
  198 |   await expect(
  199 |     page.getByRole("article", {
  200 |       name: "External reference urn:requirements:browser:legacy",
  201 |       exact: true,
  202 |     }),
  203 |   ).toContainText("Not supplied");
  204 |   await page.unroute(`**/api/v1/runs/${runId}/snapshot`);
  205 |   const latest = (await traceApi(page, `/runs/${runId}/annotations`)).body
  206 |     .items;
  207 |   expect(
  208 |     latest.find((r: any) => r.target?.uri.endsWith(":legacy")).target,
  209 |   ).not.toHaveProperty("claimStatus");
  210 |   expect(
  211 |     latest.find((r: any) => r.annotationId === linked.annotationId).deleted,
  212 |   ).toBe(true);
  213 |   expect(
  214 |     (await traceApi(page, `/runs/${runId}/snapshot`)).body.snapshot,
  215 |   ).toEqual(beforeSnapshot);
  216 |   expect((await traceApi(page, `/runs/${runId}/evidence`)).body).toEqual(
  217 |     beforeEvidence,
  218 |   );
  219 |   expect((await traceApi(page, "/runs/" + runId)).body.verdict).toBe("fail");
  220 |   await page.screenshot({
  221 |     path: testInfo.outputPath("reported-claim-separate-from-fail.png"),
  222 |     fullPage: true,
  223 |   });
  224 |   await page.getByRole("tab", { name: "Evidence", exact: true }).click();
  225 |   const downloadPromise = page.waitForEvent("download");
  226 |   await page
  227 |     .getByRole("button", { name: "Export evidence bundle", exact: true })
  228 |     .click();
  229 |   const download = await downloadPromise;
  230 |   const bundle = testInfo.outputPath("reported-claim-evidence.zip");
  231 |   await download.saveAs(bundle);
  232 |   await page
  233 |     .getByRole("button", { name: "X-Verse Studio home", exact: true })
  234 |     .click();
  235 |   const imported = page.waitForResponse(
  236 |     (r) =>
  237 |       r.url().endsWith("/evidence/imports") && r.request().method() === "POST",
  238 |   );
  239 |   await page
  240 |     .getByLabel("Import evidence archive", { exact: true })
  241 |     .setInputFiles(bundle);
  242 |   const response = await imported;
  243 |   expect(response.status()).toBe(201);
  244 |   const importedBundle = await response.json();
  245 |   expect(importedBundle.annotations).toEqual(latest);
  246 |   expect(importedBundle.inspection.executionAllowed).toBe(false);
  247 |   expect(errors).toEqual([]);
  248 | });
  249 |
```
