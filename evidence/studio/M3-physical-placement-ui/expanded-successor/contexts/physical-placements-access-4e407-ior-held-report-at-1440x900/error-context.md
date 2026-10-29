# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: physical-placements-accessibility.spec.ts >> physical placements: new project ignores the prior held report at 1440x900
- Location: tests/e2e/physical-placements-accessibility.spec.ts:492:7

# Error details

```
Error: expect(locator).not.toHaveText(expected) failed

Locator:  getByRole('region', { name: 'Physical placement observation', exact: true }).locator('.key-values > div').filter({ has: getByText('Deployment document', { exact: true }) }).locator('dd')
Expected: not "doc-3"
Received: "doc-3"
Timeout:  10000ms

Call log:
  - Expect "not toHaveText" getByRole('region', { name: 'Physical placement observation', exact: true }).locator('.key-values > div').filter({ has: getByText('Deployment document', { exact: true }) }).locator('dd') with timeout 10000ms
  - waiting for getByRole('region', { name: 'Physical placement observation', exact: true }).locator('.key-values > div').filter({ has: getByText('Deployment document', { exact: true }) }).locator('dd')
    23 × locator resolved to <dd>doc-3</dd>
       - unexpected value "doc-3"

```

```yaml
- definition: doc-3
```

# Test source

```ts
  429 |       `/projects/${prepared.project.projectId}/deployment-variants`,
  430 |       "POST",
  431 |       {
  432 |         baseRevision: prepared.project.revision,
  433 |         name: `Placement alternate ${viewport.width}`,
  434 |         sourceDeploymentId: prepared.documentId,
  435 |         sourceScenarioId: scenario[0],
  436 |       },
  437 |       prepared.project.revision,
  438 |     );
  439 |     await reopen(page, cloned.project);
  440 |     const variant = page.getByRole("combobox", {
  441 |       name: "Deployment variant",
  442 |       exact: true,
  443 |     });
  444 |     await expect(variant).toHaveValue(prepared.report.deploymentRef);
  445 |     const finish = await observeWrites(page, cloned.project, info),
  446 |       pending = await hold(page);
  447 |     try {
  448 |       await activate(page, inspect(page));
  449 |       await expect.poll(pending.ready).toBe(true);
  450 |       const options = await variant
  451 |         .locator("option")
  452 |         .evaluateAll((nodes) =>
  453 |           nodes.map((n) => (n as HTMLOptionElement).value),
  454 |         );
  455 |       const index = options.indexOf(cloned.variant.ref);
  456 |       expect(index).toBeGreaterThanOrEqual(0);
  457 |       await tabTo(page, variant);
  458 |       await page.keyboard.press("Home");
  459 |       for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  460 |       await expect(variant).toHaveValue(cloned.variant.ref);
  461 |       pending.depart();
  462 |       pending.release();
  463 |       await pending.done;
  464 |       await page.waitForLoadState("networkidle");
  465 |       await expect(variant).toBeFocused();
  466 |       await expect(panel(page).locator(".placement-row")).toHaveCount(0);
  467 |       await expect(panel(page).getByRole("alert")).toHaveCount(0);
  468 |       await expect(
  469 |         panel(page).getByText(
  470 |           `Authored Deployment for inspection: ${cloned.variant.ref}`,
  471 |           { exact: true },
  472 |         ),
  473 |       ).toBeVisible();
  474 |       await page.unroute(pattern);
  475 |       await activate(page, inspect(page));
  476 |       await expect(field(panel(page), "Deployment")).toHaveText(
  477 |         cloned.variant.ref,
  478 |       );
  479 |       await expect(field(panel(page), "Deployment document")).toHaveText(
  480 |         cloned.variant.documentId,
  481 |       );
  482 |       await finish({
  483 |         actualClonedVariant: true,
  484 |         heldOldReportIgnored: true,
  485 |         selectedNewDocument: cloned.variant.documentId,
  486 |       });
  487 |     } finally {
  488 |       await pending.close();
  489 |     }
  490 |   });
  491 |
  492 |   test(`physical placements: new project ignores the prior held report at ${viewport.width}x${viewport.height}`, async ({
  493 |     page,
  494 |   }, info) => {
  495 |     await page.setViewportSize(viewport);
  496 |     await connectStudio(page, info);
  497 |     const prepared = await setup(page, viewport.width),
  498 |       other = await request(page, "/projects", "POST", {
  499 |         name: `Placement destination ${viewport.width}`,
  500 |       });
  501 |     // Refresh only the Home listing during fixture setup, then restore the origin.
  502 |     await reopen(page, prepared.project);
  503 |     const finish = await observeWrites(page, prepared.project, info),
  504 |       pending = await hold(page);
  505 |     try {
  506 |       await activate(page, inspect(page));
  507 |       await expect.poll(pending.ready).toBe(true);
  508 |       await activate(page, home(page));
  509 |       pending.depart();
  510 |       await activate(
  511 |         page,
  512 |         page.locator(`[data-project-id="${other.projectId}"] .project-open`),
  513 |       );
  514 |       await expect(
  515 |         page.getByRole("heading", { name: other.name, exact: true }),
  516 |       ).toBeVisible();
  517 |       await activate(page, page.getByRole("tab", { name: /^Deployment/ }));
  518 |       await expect(inspect(page)).toBeEnabled();
  519 |       pending.release();
  520 |       await pending.done;
  521 |       await page.waitForLoadState("networkidle");
  522 |       await expect(panel(page).locator(".placement-row")).toHaveCount(0);
  523 |       await expect(panel(page).getByRole("alert")).toHaveCount(0);
  524 |       await expect(
  525 |         page.getByRole("tab", { name: /^Deployment/ }),
  526 |       ).toBeFocused();
  527 |       await page.unroute(pattern);
  528 |       await activate(page, inspect(page));
> 529 |       await expect(field(panel(page), "Deployment document")).not.toHaveText(
      |                                                                   ^ Error: expect(locator).not.toHaveText(expected) failed
  530 |         prepared.documentId,
  531 |       );
  532 |       await expect(
  533 |         panel(page).getByText(/No physical or hybrid bindings/),
  534 |       ).toBeVisible();
  535 |       expect(await request(page, `/projects/${other.projectId}`)).toEqual(
  536 |         other,
  537 |       );
  538 |       await finish({
  539 |         actualNewProjectId: other.projectId,
  540 |         heldOldReportIgnored: true,
  541 |         bothCanonicalProjectsUnchanged: true,
  542 |       });
  543 |     } finally {
  544 |       await pending.close();
  545 |     }
  546 |   });
  547 |
  548 |   test(`physical placements: saved newer revision ignores the prior held report at ${viewport.width}x${viewport.height}`, async ({
  549 |     page,
  550 |   }, info) => {
  551 |     await page.setViewportSize(viewport);
  552 |     await connectStudio(page, info);
  553 |     const prepared = await setup(page, viewport.width),
  554 |       pending = await hold(page);
  555 |     try {
  556 |       await activate(page, inspect(page));
  557 |       await expect.poll(pending.ready).toBe(true);
  558 |       await activate(
  559 |         page,
  560 |         page.getByRole("button", { name: "XDL source", exact: true }),
  561 |       );
  562 |       const dialog = page.getByRole("dialog", {
  563 |           name: "Authored XDL source",
  564 |           exact: true,
  565 |         }),
  566 |         editor = dialog.getByRole("textbox", {
  567 |           name: "XDL source",
  568 |           exact: true,
  569 |         });
  570 |       await tabTo(page, editor);
  571 |       await page.keyboard.press("ControlOrMeta+End");
  572 |       await page.keyboard.insertText(
  573 |         "\n# owned newer committed placement context\n",
  574 |       );
  575 |       const content = await editor.inputValue();
  576 |       const saving = page.waitForResponse(
  577 |         (r) =>
  578 |           r.request().method() === "PUT" &&
  579 |           new URL(r.url()).pathname.startsWith(
  580 |             `/api/v1/projects/${prepared.project.projectId}/documents/`,
  581 |           ),
  582 |       );
  583 |       await activate(
  584 |         page,
  585 |         dialog.getByRole("button", {
  586 |           name: "Save source revision",
  587 |           exact: true,
  588 |         }),
  589 |       );
  590 |       const response = await saving;
  591 |       expect(response.status()).toBe(200);
  592 |       expect(response.request().headers()["if-match"]).toBe(
  593 |         `"${prepared.project.revision}"`,
  594 |       );
  595 |       const project = await response.json();
  596 |       expect(project.revision).toBe(prepared.project.revision + 1);
  597 |       expect(
  598 |         Object.values<any>(project.documents).some(
  599 |           (d) => d.content === content,
  600 |         ),
  601 |       ).toBe(true);
  602 |       const changed = Object.keys(project.documents).filter(
  603 |         (id) =>
  604 |           project.documents[id].content !==
  605 |           prepared.project.documents[id].content,
  606 |       );
  607 |       expect(changed).toHaveLength(1);
  608 |       expect(project.supportingFiles).toEqual(prepared.project.supportingFiles);
  609 |       expect(project.manifest).toEqual(prepared.project.manifest);
  610 |       await page.keyboard.press("Escape");
  611 |       await expect(dialog).toHaveCount(0);
  612 |       await expect(inspect(page)).toBeEnabled();
  613 |       const finish = await observeWrites(page, project, info);
  614 |       pending.depart();
  615 |       pending.release();
  616 |       await pending.done;
  617 |       await page.waitForLoadState("networkidle");
  618 |       await expect(panel(page).locator(".placement-row")).toHaveCount(0);
  619 |       await expect(panel(page).getByRole("alert")).toHaveCount(0);
  620 |       await expect(
  621 |         page.getByRole("button", { name: "XDL source", exact: true }),
  622 |       ).toBeFocused();
  623 |       await page.unroute(pattern);
  624 |       await activate(page, inspect(page));
  625 |       await expect(field(panel(page), "Project revision")).toHaveText(
  626 |         String(project.revision),
  627 |       );
  628 |       await expect(heading(page)).toBeFocused();
  629 |       await finish({
```
