# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: run-reconnect.spec.ts >> run session: UI metadata fixture updates evidence at the same lifecycle version without altering evidence
- Location: tests/e2e/run-reconnect.spec.ts:477:5

# Error details

```
TimeoutError: page.screenshot: Timeout 15000ms exceeded.
Call log:
  - taking page screenshot
  - waiting for fonts to load...
  - fonts loaded

```

```
Error: apiResponse.json: Response has been disposed
```

# Test source

```ts
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
  493 |         "--project-id",
  494 |         project.projectId,
  495 |         "--noise",
  496 |         "1000",
  497 |       ],
  498 |       { encoding: "utf8" },
  499 |     ),
  500 |   );
  501 |   const journalPath = path.join(
  502 |       process.env.STUDIO_BROWSER_DATA!,
  503 |       "runs",
  504 |       fixture.runId,
  505 |       "evidence.jsonl",
  506 |     ),
  507 |     snapshotPath = path.join(
  508 |       process.env.STUDIO_BROWSER_DATA!,
  509 |       "snapshots",
  510 |       fixture.snapshotId,
  511 |       "snapshot.json",
  512 |     ),
  513 |     sha = (p: string) =>
  514 |       createHash("sha256").update(readFileSync(p)).digest("hex");
  515 |   const journalHash = sha(journalPath),
  516 |     snapshotHash = sha(snapshotPath);
  517 |   let facet = "partial";
  518 |   const versions: number[] = [],
  519 |     writes: string[] = [];
  520 |   await page.route(`**/api/v1/runs/${fixture.runId}`, async (route) => {
  521 |     const response = await route.fetch(),
> 522 |       metadata = await response.json();
      |                                 ^ Error: apiResponse.json: Response has been disposed
  523 |     versions.push(metadata.stateVersion);
  524 |     await route.fulfill({ response, json: { ...metadata, evidence: facet } });
  525 |   });
  526 |   page.on("request", (r) => {
  527 |     if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
  528 |       writes.push(r.method() + " " + r.url());
  529 |   });
  530 |   await showRun(page, project.projectId, fixture.runId);
  531 |   await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  532 |   const evidence = page
  533 |       .locator(".status-card")
  534 |       .filter({ has: page.getByText("Evidence", { exact: true }) }),
  535 |     execution = page
  536 |       .locator(".status-card")
  537 |       .filter({ has: page.getByText("Execution", { exact: true }) });
  538 |   await expect(evidence).toContainText(/partial/i);
  539 |   await expect(execution).toContainText(/unknown/i);
  540 |   facet = "invalid";
  541 |   await expect(evidence).toContainText(/invalid/i, { timeout: 8000 });
  542 |   await expect(execution).toContainText(/unknown/i);
  543 |   facet = "unavailable";
  544 |   await expect(evidence).toContainText(/unavailable/i, { timeout: 8000 });
  545 |   await expect(execution).toContainText(/unknown/i);
  546 |   expect(new Set(versions).size).toBe(1);
  547 |   expect(sha(journalPath)).toBe(journalHash);
  548 |   expect(sha(snapshotPath)).toBe(snapshotHash);
  549 |   const actual = await page.request
  550 |     .get(`/api/v1/runs/${fixture.runId}`)
  551 |     .then((r) => r.json());
  552 |   expect(actual.evidence).toBe("partial");
  553 |   expect(actual.stateVersion).toBe(versions[0]);
  554 |   expect(writes).toEqual([]);
  555 |   await testInfo.attach("same-version-ui-negative-scope", {
  556 |     body: JSON.stringify({
  557 |       scope:
  558 |         "controlled HTTP metadata UI negative only; source journal and snapshot unchanged",
  559 |       evidenceScope: fixture.evidenceScope,
  560 |       requestedStates: ["partial", "invalid", "unavailable"],
  561 |       stateVersions: versions,
  562 |       journalSha256: journalHash,
  563 |       snapshotSha256: snapshotHash,
  564 |       backendEvidence: actual.evidence,
  565 |       mutations: writes,
  566 |     }),
  567 |     contentType: "application/json",
  568 |   });
  569 |   await page.screenshot({
  570 |     path: testInfo.outputPath(
  571 |       "same-version-evidence-unavailable-ui-fixture.png",
  572 |     ),
  573 |     fullPage: true,
  574 |   });
  575 | });
  576 |
```
