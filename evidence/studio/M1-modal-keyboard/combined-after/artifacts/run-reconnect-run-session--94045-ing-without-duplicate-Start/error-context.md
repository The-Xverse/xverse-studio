# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: run-reconnect.spec.ts >> run session: native owned execution survives real replay-window expiry while running without duplicate Start
- Location: tests/e2e/run-reconnect.spec.ts:246:5

# Error details

```
Error: expect(received).toBeGreaterThan(expected)

Expected: > 0
Received:   0

Call Log:
- Timeout 4000ms exceeded while waiting on the predicate
```

# Test source

```ts
  292 |         { snapshotId: pf.snapshotId, preflightId: pf.preflightId },
  293 |         undefined,
  294 |         key,
  295 |       ),
  296 |       key,
  297 |       snapshotId: pf.snapshotId,
  298 |     };
  299 |   }, project);
  300 |   const runId = made.start.runId,
  301 |     writes: string[] = [],
  302 |     streams: string[] = [];
  303 |   page.on("request", (r) => {
  304 |     if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
  305 |       writes.push(r.method() + " " + r.url());
  306 |     if (r.url().includes(`/runs/${runId}/events`)) streams.push(r.url());
  307 |   });
  308 |   const expiredResponses: any[] = [];
  309 |   page.on("response", (response) => {
  310 |     if (
  311 |       response.url().includes(`/runs/${runId}/events`) &&
  312 |       response.status() === 410
  313 |     ) {
  314 |       const entry: any = { url: response.url(), status: response.status() };
  315 |       expiredResponses.push(entry);
  316 |       void response
  317 |         .json()
  318 |         .then((body) => {
  319 |           entry.code = body.code;
  320 |         })
  321 |         .catch(() => {
  322 |           entry.bodyUnavailable = true;
  323 |         });
  324 |     }
  325 |   });
  326 |   const journalPath = path.join(
  327 |       process.env.STUDIO_BROWSER_DATA!,
  328 |       "runs",
  329 |       runId,
  330 |       "evidence.jsonl",
  331 |     ),
  332 |     snapshotPath = path.join(
  333 |       process.env.STUDIO_BROWSER_DATA!,
  334 |       "snapshots",
  335 |       made.snapshotId,
  336 |       "snapshot.json",
  337 |     );
  338 |   const sha = (bytes: Buffer) =>
  339 |     createHash("sha256").update(bytes).digest("hex");
  340 |   const snapshotHash = sha(readFileSync(snapshotPath));
  341 |   const prefixRecoveries: any[] = [];
  342 |   await page.route(`**/api/v1/runs/${runId}/resync`, async (route) => {
  343 |     const response = await route.fetch();
  344 |     const recovery = await response.json();
  345 |     prefixRecoveries.push({
  346 |       integrity: recovery.history?.integrity,
  347 |       state: recovery.run?.state,
  348 |       resumeCursor: recovery.resumeCursor,
  349 |       afterExpiry: expiredResponses.length,
  350 |     });
  351 |     await route.fulfill({ response });
  352 |   });
  353 |   await showRun(page, project.projectId, runId);
  354 |   await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  355 |   await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  356 |   await page
  357 |     .getByRole("button", { name: "Live buffer · at most 200", exact: true })
  358 |     .click();
  359 |   await expect
  360 |     .poll(() => page.locator(".event-row").count())
  361 |     .toBeGreaterThan(2);
  362 |   const before = await page.request
  363 |     .get(`/api/v1/runs/${runId}/history?limit=200`)
  364 |     .then((r) => r.json());
  365 |   const initialJournal = readFileSync(journalPath),
  366 |     prefixBytes = initialJournal.subarray(
  367 |       0,
  368 |       initialJournal.lastIndexOf(10) + 1,
  369 |     ),
  370 |     prefixHash = sha(prefixBytes);
  371 |   await delivery(page, true);
  372 |   await expect
  373 |     .poll(() =>
  374 |       prefixRecoveries.some(
  375 |         (r) => r.integrity === "verified_prefix" && r.state === "running",
  376 |       ),
  377 |     )
  378 |     .toBe(true);
  379 |   await expect(
  380 |     page.getByText(/Reader integrity: verified_prefix/),
  381 |   ).toBeVisible();
  382 |   await new Promise((resolve) => setTimeout(resolve, 12000));
  383 |   await delivery(page, false);
  384 |   const during = await page.request
  385 |     .get(`/api/v1/runs/${runId}/history?limit=200`)
  386 |     .then((r) => r.json());
  387 |   expect(
  388 |     during.counts.totalRecords - before.counts.totalRecords,
  389 |   ).toBeGreaterThan(1000);
  390 |   await expect
  391 |     .poll(() => expiredResponses.length, { timeout: 4000 })
> 392 |     .toBeGreaterThan(0);
      |      ^ Error: expect(received).toBeGreaterThan(expected)
  393 |   await expect
  394 |     .poll(
  395 |       () =>
  396 |         prefixRecoveries.some(
  397 |           (r) =>
  398 |             r.afterExpiry > 0 &&
  399 |             r.integrity === "verified_prefix" &&
  400 |             r.state === "running",
  401 |         ),
  402 |       { timeout: 4000 },
  403 |     )
  404 |     .toBe(true);
  405 |   await expect(
  406 |     page.getByText(/Reader integrity: verified_prefix/),
  407 |   ).toBeVisible();
  408 |   await expect.poll(() => streams.length).toBeGreaterThan(1);
  409 |   await expect
  410 |     .poll(async () =>
  411 |       page.request
  412 |         .get(`/api/v1/runs/${runId}`)
  413 |         .then((r) => r.json())
  414 |         .then((r) => r.state),
  415 |     )
  416 |     .toBe("stopped");
  417 |   await page.reload();
  418 |   await page.getByRole("tab", { name: "Results", exact: false }).click();
  419 |   await expect(
  420 |     page.getByRole("heading", { name: /Run results/ }),
  421 |   ).toContainText("stopped");
  422 |   await expect(page.locator(".stream-indicator")).toHaveText(
  423 |     "Retained history available",
  424 |   );
  425 |   const list = await page.request.get("/api/v1/runs").then((r) => r.json());
  426 |   expect(
  427 |     list.items.filter((r: any) => r.projectId === project.projectId),
  428 |   ).toHaveLength(1);
  429 |   const finalJournal = readFileSync(journalPath);
  430 |   expect(sha(finalJournal.subarray(0, prefixBytes.length))).toBe(prefixHash);
  431 |   expect(sha(readFileSync(snapshotPath))).toBe(snapshotHash);
  432 |   const finalRun = await page.request
  433 |     .get(`/api/v1/runs/${runId}`)
  434 |     .then((r) => r.json());
  435 |   expect(finalRun.journalDigest).toBe("sha256:" + sha(finalJournal));
  436 |   expect(finalRun.providerId).toBe("studio.reference");
  437 |   expect(finalRun.evidenceScope).toBe("owned_reference");
  438 |   await testInfo.attach("actual-window-expiry", {
  439 |     body: JSON.stringify({
  440 |       expiredResponses,
  441 |       sourceRecordsBefore: before.counts.totalRecords,
  442 |       sourceRecordsDuringPause: during.counts.totalRecords,
  443 |       pauseMilliseconds: 12000,
  444 |       requestedDurationSeconds: 16,
  445 |       timestepSeconds: 0.01,
  446 |       prefixByteLength: prefixBytes.length,
  447 |       prefixSha256: prefixHash,
  448 |       snapshotSha256: snapshotHash,
  449 |       finalJournalSha256: sha(finalJournal),
  450 |       readOnly: true,
  451 |     }),
  452 |     contentType: "application/json",
  453 |   });
  454 |   await testInfo.attach("active-prefix-recovery", {
  455 |     body: JSON.stringify(prefixRecoveries),
  456 |     contentType: "application/json",
  457 |   });
  458 |   expect(writes).toEqual([]);
  459 |   expect(
  460 |     streams.every(
  461 |       (url) => new URL(url).searchParams.get("streamVersion") === "1.1",
  462 |     ),
  463 |   ).toBe(true);
  464 |   expect(
  465 |     streams
  466 |       .slice(1)
  467 |       .some((url) =>
  468 |         new URL(url).searchParams.get("after")?.startsWith("st1."),
  469 |       ),
  470 |   ).toBe(true);
  471 |   await page.screenshot({
  472 |     path: testInfo.outputPath("owned-run-after-disconnect-refresh.png"),
  473 |     fullPage: true,
  474 |   });
  475 | });
  476 |
  477 | test("run session: UI metadata fixture updates evidence at the same lifecycle version without altering evidence", async ({
  478 |   page,
  479 | }, testInfo) => {
  480 |   test.setTimeout(60000);
  481 |   await connectStudio(page, testInfo);
  482 |   const project = await makeProject(
  483 |     page,
  484 |     "Same-version evidence UI metadata fixture",
  485 |   );
  486 |   const fixture = JSON.parse(
  487 |     execFileSync(
  488 |       path.resolve(".venv/bin/python"),
  489 |       [
  490 |         "tests/fixtures/evidence/create_stream_recovery_fixture.py",
  491 |         "--data-dir",
  492 |         process.env.STUDIO_BROWSER_DATA!,
```
