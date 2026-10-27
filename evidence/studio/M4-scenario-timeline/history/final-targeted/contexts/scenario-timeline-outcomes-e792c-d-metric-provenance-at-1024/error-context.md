# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scenario-timeline-outcomes.spec.ts >> scenario timeline outcomes: actual pass, fail, indeterminate and metric provenance at 1024
- Location: tests/e2e/scenario-timeline-outcomes.spec.ts:41:7

# Error details

```
Error: expect(locator).toBeFocused() failed

Locator:  getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('heading', { name: 'Selected run timeline', exact: true })
Expected: focused
Received: inactive
Timeout:  10000ms

Call log:
  - Expect "toBeFocused" getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('heading', { name: 'Selected run timeline', exact: true }) with timeout 10000ms
  - waiting for getByRole('region', { name: 'Selected run timeline', exact: true }).getByRole('heading', { name: 'Selected run timeline', exact: true })
    24 × locator resolved to <h3 tabindex="-1">Selected run timeline</h3>
       - unexpected value "inactive"

```

```yaml
- heading "Selected run timeline" [level=3]
```

# Test source

```ts
  152 |     });
  153 |     await expect(declared).toContainText(
  154 |       "Inspection does not evaluate these definitions",
  155 |     );
  156 |     await declared
  157 |       .getByText(`Inspect frozen definitions (${definitions.length})`, {
  158 |         exact: true,
  159 |       })
  160 |       .focus();
  161 |     await page.keyboard.press("Enter");
  162 |     for (const d of definitions) {
  163 |       const row = declared.locator(
  164 |         `[data-definition-ref="${d.definitionRef}"]`,
  165 |       );
  166 |       await expect(row).toContainText(d.definition.name);
  167 |       await row.getByText("Inspect exact data", { exact: true }).focus();
  168 |       await page.keyboard.press("Enter");
  169 |       expect(JSON.parse(await row.locator("pre").innerText())).toEqual(d);
  170 |     }
  171 |     await expect(
  172 |       before.locator('tr[data-timeline-id^="evaluation:"]'),
  173 |     ).toHaveCount(0);
  174 |     expect(
  175 |       (await readOrWrite(page, `/runs/${run.runId}/evaluations`)).items,
  176 |     ).toEqual([]);
  177 |     expect(initialWrites).toEqual([]);
  178 |     page.off("request", watch);
  179 |     for (const d of definitions) {
  180 |       const accepted = await readOrWrite(
  181 |         page,
  182 |         `/runs/${run.runId}/evaluations`,
  183 |         "POST",
  184 |         {
  185 |           snapshotId: run.snapshotId,
  186 |           definitionRef: d.definitionRef,
  187 |           definitionDigest: d.definitionDigest,
  188 |           evidenceRefs: [run.runId + ":reference-journal"],
  189 |         },
  190 |       );
  191 |       await expect
  192 |         .poll(
  193 |           async () =>
  194 |             (await readOrWrite(page, `/evaluations/${accepted.evaluationId}`))
  195 |               .status,
  196 |         )
  197 |         .toBe("complete");
  198 |       jobs.push(
  199 |         await readOrWrite(page, `/evaluations/${accepted.evaluationId}`),
  200 |       );
  201 |     }
  202 |     const failed = jobs.find(
  203 |         (j) => j.definition.evaluationId === "timeline-fail",
  204 |       ),
  205 |       unknown = jobs.find(
  206 |         (j) => j.definition.evaluationId === "timeline-incomplete",
  207 |       ),
  208 |       numeric = jobs.find((j) => j.definition.kind === "metric");
  209 |     expect(failed.verdict).toBe("fail");
  210 |     expect(failed.coverage).toBe("complete");
  211 |     expect(unknown.verdict).toBe("indeterminate");
  212 |     expect(unknown.coverage).toBe("incomplete");
  213 |     expect(unknown.reasons).toContain("COVERAGE_INCOMPLETE");
  214 |     expect(numeric.verdict).toBeNull();
  215 |     expect(Number.isFinite(numeric.value)).toBe(true);
  216 |     await page.evaluate(
  217 |       ({ project, run }) => {
  218 |         localStorage.setItem("studio.projectId", project.projectId);
  219 |         localStorage.setItem("studio.lastRun." + project.projectId, run.runId);
  220 |         localStorage.setItem("studio.lastRun", run.runId);
  221 |       },
  222 |       { project, run },
  223 |     );
  224 |     await page.reload();
  225 |     await page.getByRole("tab", { name: "Experiments", exact: true }).focus();
  226 |     await page.keyboard.press("Enter");
  227 |     await page.getByRole("tab", { name: "Timeline", exact: true }).focus();
  228 |     await page.keyboard.press("Enter");
  229 |     const panel = page.getByRole("region", {
  230 |         name: "Selected run timeline",
  231 |         exact: true,
  232 |       }),
  233 |       writes: string[] = [],
  234 |       errors: string[] = [];
  235 |     page.on("request", (r) => {
  236 |       if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
  237 |         writes.push(r.method() + " " + new URL(r.url()).pathname);
  238 |     });
  239 |     page.on("pageerror", (e) => errors.push(e.message));
  240 |     await panel
  241 |       .getByRole("button", {
  242 |         name: "Inspect selected run timeline",
  243 |         exact: true,
  244 |       })
  245 |       .focus();
  246 |     await page.keyboard.press("Enter");
  247 |     await expect(
  248 |       panel.getByRole("heading", {
  249 |         name: "Selected run timeline",
  250 |         exact: true,
  251 |       }),
> 252 |     ).toBeFocused();
      |       ^ Error: expect(locator).toBeFocused() failed
  253 |     for (const job of jobs) {
  254 |       const row = panel.locator(
  255 |         `[data-timeline-id="evaluation:${job.evaluationId}"]`,
  256 |       );
  257 |       await expect(
  258 |         row.getByText("Execution: complete", { exact: true }),
  259 |       ).toBeVisible();
  260 |       await expect(
  261 |         row.getByText(
  262 |           job.verdict === null
  263 |             ? "No verdict"
  264 |             : `Assertion verdict: ${job.verdict}`,
  265 |           { exact: true },
  266 |         ),
  267 |       ).toBeVisible();
  268 |       await expect(row).toContainText(
  269 |         `[${job.definition.window.startTick}, ${job.definition.window.endTick})`,
  270 |       );
  271 |       await expect(
  272 |         row.getByText(`Reasons: ${job.reasons.join(", ") || "None reported"}`, {
  273 |           exact: true,
  274 |         }),
  275 |       ).toBeVisible();
  276 |       await row.getByText("Inspect exact data", { exact: true }).focus();
  277 |       await page.keyboard.press("Enter");
  278 |       const shown = JSON.parse(await row.locator("pre").innerText());
  279 |       expect(shown.definitionDigest).toBe(job.definitionDigest);
  280 |       expect(shown.evidenceDigests).toEqual(job.evidenceDigests);
  281 |       expect(shown.inputEvidenceDigests).toEqual(job.inputEvidenceDigests);
  282 |       expect(shown.evaluatorIdentity).toEqual(job.evaluatorIdentity);
  283 |       expect(shown.window).toEqual(job.definition.window);
  284 |       expect(shown.matchesCurrentEvidence).toBe(true);
  285 |       await expect(
  286 |         row.getByText("Inspect exact data", { exact: true }),
  287 |       ).toBeFocused();
  288 |     }
  289 |     const unknownRow = panel.locator(
  290 |       `[data-timeline-id="evaluation:${unknown.evaluationId}"]`,
  291 |     );
  292 |     await expect(
  293 |       unknownRow.getByText("Assertion verdict: pass", { exact: true }),
  294 |     ).toHaveCount(0);
  295 |     expect(await readOrWrite(page, `/projects/${project.projectId}`)).toEqual(
  296 |       project,
  297 |     );
  298 |     expect(
  299 |       (await readOrWrite(page, `/runs/${run.runId}/snapshot`)).snapshot,
  300 |     ).toEqual(snapshot);
  301 |     expect((await readOrWrite(page, `/runs/${run.runId}`)).journalDigest).toBe(
  302 |       run.journalDigest,
  303 |     );
  304 |     for (const job of jobs)
  305 |       expect(
  306 |         await readOrWrite(page, `/evaluations/${job.evaluationId}`),
  307 |       ).toEqual(job);
  308 |     expect(writes).toEqual([]);
  309 |     expect(errors).toEqual([]);
  310 |     expect(
  311 |       await page.evaluate(
  312 |         () => document.documentElement.scrollWidth > innerWidth + 1,
  313 |       ),
  314 |     ).toBe(false);
  315 |     await info.attach("actual-outcome-provenance", {
  316 |       body: JSON.stringify(
  317 |         {
  318 |           runId: run.runId,
  319 |           snapshotId: run.snapshotId,
  320 |           scope: run.evidenceScope,
  321 |           journalDigest: run.journalDigest,
  322 |           results: jobs.map((j) => ({
  323 |             evaluationId: j.evaluationId,
  324 |             definitionRef: j.definitionRef,
  325 |             definitionDigest: j.definitionDigest,
  326 |             verdict: j.verdict,
  327 |             value: j.value,
  328 |             coverage: j.coverage,
  329 |             reasons: j.reasons,
  330 |             evaluatorIdentity: j.evaluatorIdentity,
  331 |             evidenceDigests: j.evidenceDigests,
  332 |           })),
  333 |         },
  334 |         null,
  335 |         2,
  336 |       ),
  337 |       contentType: "application/json",
  338 |     });
  339 |     await page.screenshot({
  340 |       path: info.outputPath(`actual-outcomes-${width}.png`),
  341 |       fullPage: true,
  342 |     });
  343 |   });
  344 | }
  345 |
```
