# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: trace-claims.spec.ts >> reported external claims: frozen subjects, revision history, neutral PASS label and immutable exchange
- Location: tests/e2e/trace-claims.spec.ts:5:5

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

Expected: {"capabilityDigest": "sha256:bce965062c6d3655583597c1e3e79ad2c9d3ef28384ee3c7e354be8930c76d29", "compiler": [Object], "configuration": [Object], "createdAt": 1792932743.7360792, "documents": [Object], "plan": [Object], "planDigest": "sha256:c10e033f4525b0a3fc545e5e0c3b5a872a6b209b4727b494b8da09638c586330", "profileLocks": [Array], "projectDocuments": [Object], "projectId": "prj-499509cc-eda8-4433-9659-73b7503ece4b", "projectRevisionInputsDigest": "sha256:39ca25a02b9935c27cdbb9b2704faa3d722c6e511c9ff58e96dabace4c075f7a", "providerId": "studio.reference", "providerIdentity": [Object], "revision": 2, "selection": [Object], "semanticDigest": "sha256:810dab17895a904694f192f664e9622b021f1775fb0619c05fcd870011217604", "snapshotDigest": "sha256:3cea6daffd06c35179cff49a5a6a4b3dc9e9cc83206d070502caef8a857b22ad", "snapshotId": "snap-2952fc7e-d799-45dd-b664-9d19be6507c3"}
Received: undefined
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
          - code [ref=f2e110]: snap-2952fc7
          - generic [ref=f2e111]: stopped
      - generic [ref=f2e112]:
        - generic [ref=f2e113]:
          - generic [ref=f2e114]:
            - heading "Run results stopped" [level=2] [ref=f2e115]:
              - text: Run results
              - generic [ref=f2e116]: stopped
            - paragraph [ref=f2e117]:
              - code [ref=f2e118]: run-dd86d7e4-37da-4391-b596-d4d37b2d0511
              - generic [ref=f2e119]:
                - text: Snapshot
                - code [ref=f2e120]: snap-2952fc7e-d799
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
            - article "External reference urn:requirements:browser:legacy" [ref=f2e160]:
              - generic [ref=f2e161]:
                - strong [ref=f2e162]: trace_link
                - generic [ref=f2e163]: rev 1
              - paragraph
              - text: "1792932746.95766"
              - generic [ref=f2e164]:
                - generic [ref=f2e165]:
                  - generic [ref=f2e166]:
                    - term [ref=f2e167]: External URI
                    - definition [ref=f2e168]: urn:requirements:browser:legacy
                  - generic [ref=f2e169]:
                    - term [ref=f2e170]: Referenced revision
                    - definition [ref=f2e171]: unknown
                  - generic [ref=f2e172]:
                    - term [ref=f2e173]: Reported claim status
                    - definition [ref=f2e174]: Not supplied
                - paragraph [ref=f2e175]: Reported metadata only. Studio has not verified this external claim.
                - paragraph [ref=f2e176]: "Evidence: run-dd86d7e4-37da-4391-b596-d4d37b2d0511:reference-journal"
              - generic [ref=f2e177]:
                - button "Edit external reference" [ref=f2e178] [cursor=pointer]
                - button "Remove external reference" [ref=f2e179] [cursor=pointer]
              - group [ref=f2e180]:
                - generic "Inspect exact data" [ref=f2e181] [cursor=pointer]
            - article "External reference urn:requirements:browser:trace-1" [ref=f2e182]:
              - generic [ref=f2e183]:
                - strong [ref=f2e184]: trace_link
                - generic [ref=f2e185]: rev 3
              - paragraph [ref=f2e186]: Annotation removed; historical revisions retained.
              - text: "1792932746.3865876"
              - generic [ref=f2e187]:
                - generic [ref=f2e188]:
                  - generic [ref=f2e189]:
                    - term [ref=f2e190]: External URI
                    - definition [ref=f2e191]: urn:requirements:browser:trace-1
                  - generic [ref=f2e192]:
                    - term [ref=f2e193]: Referenced revision
                    - definition [ref=f2e194]: external-r7
                  - generic [ref=f2e195]:
                    - term [ref=f2e196]: Reported claim status
                    - definition [ref=f2e197]: Review still pending
                - paragraph [ref=f2e198]: Reported metadata only. Studio has not verified this external claim.
                - paragraph [ref=f2e199]: "Model / Scenario: xdl://org.xverse.studio.process-control/system/reference-loop#plant, xdl://org.xverse.studio.process-control/scenario/reference-response"
                - paragraph [ref=f2e200]: "Frozen definitions: state-within-bound (sha256:944ceedb67b5d774c363e339f383bafcbb90d4ef875b4634b5bfda9a9cff450e)"
                - paragraph [ref=f2e201]: "Evidence: run-dd86d7e4-37da-4391-b596-d4d37b2d0511:reference-journal"
              - group [ref=f2e202]:
                - generic "Revision history (2)" [ref=f2e203]
              - group [ref=f2e204]:
                - generic "Inspect exact data" [ref=f2e205] [cursor=pointer]
          - complementary [ref=f2e206]:
            - heading "Add a review note" [level=3] [ref=f2e207]
            - generic [ref=f2e208]:
              - generic [ref=f2e209]:
                - text: Comment
                - textbox "Comment" [ref=f2e210]
              - button "Save separate annotation" [disabled] [ref=f2e211]
            - paragraph [ref=f2e212]: An external requirement reference is traceability, not proof that the requirement passed.
            - generic [ref=f2e213]:
              - heading "External requirement / test reference" [level=3] [ref=f2e214]
              - button "Add external reference" [active] [ref=f2e215] [cursor=pointer]
      - generic [ref=f2e216]:
        - generic [ref=f2e217]: Local project · Saved on backend
        - generic [ref=f2e220]: Authoritative XDL · Layout stored separately
        - generic [ref=f2e221]: 1 provider(s) available
```

# Test source

```ts
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
  204 |   const latest = (await traceApi(page, `/runs/${runId}/annotations`)).body
  205 |     .items;
  206 |   expect(
  207 |     latest.find((r: any) => r.target?.uri.endsWith(":legacy")).target,
  208 |   ).not.toHaveProperty("claimStatus");
  209 |   expect(
  210 |     latest.find((r: any) => r.annotationId === linked.annotationId).deleted,
  211 |   ).toBe(true);
  212 |   expect(
  213 |     (await traceApi(page, `/runs/${runId}/snapshot`)).body.snapshot,
> 214 |   ).toEqual(beforeSnapshot);
      |     ^ Error: expect(received).toEqual(expected) // deep equality
  215 |   expect((await traceApi(page, `/runs/${runId}/evidence`)).body).toEqual(
  216 |     beforeEvidence,
  217 |   );
  218 |   expect((await traceApi(page, "/runs/" + runId)).body.verdict).toBe("fail");
  219 |   await page.screenshot({
  220 |     path: testInfo.outputPath("reported-claim-separate-from-fail.png"),
  221 |     fullPage: true,
  222 |   });
  223 |   await page.getByRole("tab", { name: "Evidence", exact: true }).click();
  224 |   const downloadPromise = page.waitForEvent("download");
  225 |   await page
  226 |     .getByRole("button", { name: "Export evidence bundle", exact: true })
  227 |     .click();
  228 |   const download = await downloadPromise;
  229 |   const bundle = testInfo.outputPath("reported-claim-evidence.zip");
  230 |   await download.saveAs(bundle);
  231 |   await page
  232 |     .getByRole("button", { name: "X-Verse Studio home", exact: true })
  233 |     .click();
  234 |   const imported = page.waitForResponse(
  235 |     (r) =>
  236 |       r.url().endsWith("/evidence/imports") && r.request().method() === "POST",
  237 |   );
  238 |   await page
  239 |     .getByLabel("Import evidence archive", { exact: true })
  240 |     .setInputFiles(bundle);
  241 |   const response = await imported;
  242 |   expect(response.status()).toBe(201);
  243 |   const importedBundle = await response.json();
  244 |   expect(importedBundle.annotations).toEqual(latest);
  245 |   expect(importedBundle.inspection.executionAllowed).toBe(false);
  246 |   expect(errors).toEqual([]);
  247 | });
  248 |
```
