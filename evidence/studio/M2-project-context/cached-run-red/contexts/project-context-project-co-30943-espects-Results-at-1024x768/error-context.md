# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: project-context.spec.ts >> project context: cached run metadata respects Results at 1024x768
- Location: tests/e2e/project-context.spec.ts:439:9

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Recorded fixture scope', { exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('Recorded fixture scope', { exact: true }) with timeout 10000ms
  - waiting for getByText('Recorded fixture scope', { exact: true })

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
  - heading "Cached run context Results 1024" [level=1]
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
    - tab "Experiments"
    - tab "Results" [selected]
    - button "XDL source"
  - text: Draft revision
  - code: "1"
  - text: 3 elements · 2 connections Execution scope Owned reference
  - heading "Your evidence starts with a run" [level=3]
  - text: Validate the draft and run preflight to create an immutable input snapshot.
  - button "Preflight & run"
  - text: Local project · Saved on backend Authoritative XDL · Layout stored separately 1 provider(s) available
```

# Test source

```ts
  373 |         await gate;
  374 |         await route.fulfill({ response });
  375 |       } finally {
  376 |         finish();
  377 |       }
  378 |     } else await route.fulfill({ response });
  379 |   });
  380 |   if (holdLoad)
  381 |     await page.route(loadPattern, async (route) => {
  382 |       if (
  383 |         route.request().method() !== "GET" ||
  384 |         !fixture ||
  385 |         new URL(route.request().url()).pathname !==
  386 |           `/api/v1/projects/${fixture.pid}`
  387 |       ) {
  388 |         await route.continue();
  389 |         return;
  390 |       }
  391 |       let finish!: () => void;
  392 |       finished = new Promise((r) => (finish = r));
  393 |       try {
  394 |         const response = await route.fetch();
  395 |         loadStatus = response.status();
  396 |         ready = true;
  397 |         await gate;
  398 |         await route.fulfill({ response });
  399 |       } finally {
  400 |         finish();
  401 |       }
  402 |     });
  403 |   await activate(
  404 |     page,
  405 |     page
  406 |       .getByRole("article")
  407 |       .filter({
  408 |         has: page.getByRole("heading", { name: entry.name, exact: true }),
  409 |       })
  410 |       .getByRole("button", { name: "Open as project", exact: true }),
  411 |   );
  412 |   return {
  413 |     async fixture() {
  414 |       await expect.poll(() => !!fixture).toBe(true);
  415 |       return fixture!;
  416 |     },
  417 |     async ready() {
  418 |       await expect.poll(() => ready).toBe(true);
  419 |       return loadStatus;
  420 |     },
  421 |     async release() {
  422 |       release();
  423 |       await finished;
  424 |     },
  425 |     async close() {
  426 |       release();
  427 |       await finished;
  428 |       await page.unroute(createPattern);
  429 |       if (holdLoad) await page.unroute(loadPattern);
  430 |       fixture?.restore();
  431 |     },
  432 |   };
  433 | }
  434 | for (const viewport of [
  435 |   { width: 1024, height: 768 },
  436 |   { width: 1440, height: 900 },
  437 | ]) {
  438 |   for (const destination of ["Results", "Home"] as const) {
  439 |     test(`project context: cached run metadata respects ${destination} at ${viewport.width}x${viewport.height}`, async ({ page }, info) => {
  440 |       await page.setViewportSize(viewport);
  441 |       await connectStudio(page, info);
  442 |       const current = await create(page, `Cached run context ${destination} ${viewport.width}`),
  443 |         python = process.env.STUDIO_PYTHON || path.join(process.cwd(), ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python"),
  444 |         fixture = JSON.parse(execFileSync(python, ["-I", path.join(process.cwd(), "tests/fixtures/performance/create_recorded_history.py"), "--data-dir", process.env.STUDIO_BROWSER_DATA!, "--project-id", current.projectId], { encoding: "utf8", timeout: 60000, maxBuffer: 1024 * 1024 })),
  445 |         beforeRuns = await runs(page, current.projectId);
  446 |       expect(fixture.recordCount).toBe(50000);
  447 |       expect(fixture.integrity).toBe("valid");
  448 |       await page.evaluate(f => {
  449 |         localStorage.setItem("studio.lastRun", f.runId);
  450 |         localStorage.setItem("studio.lastRun." + f.projectId, f.runId);
  451 |       }, fixture);
  452 |       let release!: () => void, finish!: () => void, ready = false, intercepted = false;
  453 |       const gate = new Promise<void>(r => release = r), finished = new Promise<void>(r => finish = r), pattern = `**/api/v1/runs/${fixture.runId}`;
  454 |       await page.route(pattern, async route => {
  455 |         if (intercepted) { await route.continue(); return; }
  456 |         intercepted = true;
  457 |         try {
  458 |           const response = await route.fetch();
  459 |           expect(response.status()).toBe(200);
  460 |           expect((await response.json()).projectId).toBe(current.projectId);
  461 |           ready = true;
  462 |           await gate;
  463 |           await route.fulfill({ response });
  464 |         } finally { finish(); }
  465 |       });
  466 |       try {
  467 |         await page.reload();
  468 |         await expect.poll(() => ready).toBe(true);
  469 |         if (destination === "Results") await activate(page, page.getByRole("tab", { name: "Results", exact: true }));
  470 |         else await activate(page, home(page));
  471 |         release(); await finished; await settle(page);
  472 |         if (destination === "Results") {
> 473 |           await expect(page.getByText("Recorded fixture scope", { exact: true })).toBeVisible();
      |                                                                                   ^ Error: expect(locator).toBeVisible() failed
  474 |           await expect(page.locator(".results-view .run-identity code").first()).toHaveText(fixture.runId);
  475 |           await expect(page.getByRole("button", { name: "Stop", exact: true })).toHaveCount(0);
  476 |         } else {
  477 |           await expect(page.locator(".project-header")).toHaveCount(0);
  478 |           await expect(page.getByText("Recorded fixture scope", { exact: true })).toHaveCount(0);
  479 |         }
  480 |         expect((await read(page, current.projectId)).documents).toEqual(current.documents);
  481 |         expect(await runs(page, current.projectId)).toEqual(beforeRuns);
  482 |         await info.attach("project-context-cached-run.json", { body: JSON.stringify({ viewport, destination, projectId: current.projectId, runId: fixture.runId, integrity: fixture.integrity, sourceRecords: fixture.recordCount, heldActualMetadataRead: true, noStart: true, scope: "Trusted inert registered journal fixture; metadata may restore within its active project after Results navigation but cannot recapture Home; no process/provider/device authority" }), contentType: "application/json" });
  483 |       } finally { release(); await finished; await page.unroute(pattern); }
  484 |     });
  485 |   }
  486 |   for (const mode of [
  487 |     "source draft",
  488 |     "source save",
  489 |     "parameter draft",
  490 |   ] as const) {
  491 |     test(`project context: foreign recovery preserves newer ${mode} at ${viewport.width}x${viewport.height}`, async ({
  492 |       page,
  493 |     }, info) => {
  494 |       test.setTimeout(90000);
  495 |       await page.setViewportSize(viewport);
  496 |       await connectStudio(page, info);
  497 |       const current = await create(
  498 |           page,
  499 |           `Active context ${mode} ${viewport.width}`,
  500 |         ),
  501 |         beforeRuns = await runs(page, current.projectId),
  502 |         target = await catalogTarget(page, true, false);
  503 |       let pending: Awaited<ReturnType<typeof hold>> | undefined;
  504 |       try {
  505 |         const other = await target.fixture();
  506 |         await expect(group(page)).toBeVisible();
  507 |         await expect(group(page)).toHaveAccessibleDescription(
  508 |           new RegExp(other.pid),
  509 |         );
  510 |         await expect(group(page).locator(":scope > p").first()).toContainText(
  511 |           other.project.name,
  512 |         );
  513 |         const contrast = await renderedContrast(
  514 |           group(page).locator(":scope > p").first(),
  515 |           "Named foreign recovery target",
  516 |         );
  517 |         expect(contrast.supported).toBe(true);
  518 |         if (contrast.supported)
  519 |           expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
  520 |         await activate(
  521 |           page,
  522 |           page.getByRole("button", { name: "Back to workspace", exact: true }),
  523 |         );
  524 |         await expect(
  525 |           page.getByRole("heading", { name: current.name, exact: true }),
  526 |         ).toBeVisible();
  527 |         pending = await hold(page, other.pid);
  528 |         await activate(
  529 |           page,
  530 |           recoverButton(page, other.project.revision, "restore_revision"),
  531 |         );
  532 |         const committed = await pending.ready();
  533 |         expect(committed.status).toBe(200);
  534 |         let authored: Awaited<ReturnType<typeof sourceDraft>> | undefined;
  535 |         if (mode === "parameter draft") {
  536 |           await activate(
  537 |             page,
  538 |             page.getByRole("button", { name: "Parameters", exact: true }),
  539 |           );
  540 |           const duration = page.getByRole("spinbutton", {
  541 |             name: "Duration s",
  542 |             exact: true,
  543 |           });
  544 |           await tabTo(page, duration);
  545 |           await page.keyboard.press("ControlOrMeta+A");
  546 |           await page.keyboard.insertText("7");
  547 |           await expect(duration).toHaveValue("7");
  548 |         } else {
  549 |           authored = await sourceDraft(
  550 |             page,
  551 |             current,
  552 |             `newer-A-${mode}-${viewport.width}`,
  553 |           );
  554 |           await expect
  555 |             .poll(() =>
  556 |               page.evaluate(
  557 |                 ({ pid, id }) =>
  558 |                   sessionStorage.getItem(`studio.draft.${pid}.${id}`),
  559 |                 { pid: current.projectId, id: authored!.id },
  560 |               ),
  561 |             )
  562 |             .toBe(authored.content);
  563 |           if (mode === "source save") {
  564 |             const reply = page.waitForResponse(
  565 |               (r) =>
  566 |                 new URL(r.url()).pathname ===
  567 |                   `/api/v1/projects/${current.projectId}/documents/${authored!.id}` &&
  568 |                 r.request().method() === "PUT",
  569 |             );
  570 |             await page.keyboard.press("ControlOrMeta+s");
  571 |             expect((await reply).status()).toBe(200);
  572 |             await expect.soft(authored.save).toBeDisabled();
  573 |           }
```
