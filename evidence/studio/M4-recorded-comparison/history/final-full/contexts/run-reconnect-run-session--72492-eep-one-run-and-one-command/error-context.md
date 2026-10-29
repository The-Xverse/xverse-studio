# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: run-reconnect.spec.ts >> run session: double Start, page close/reopen and a lost Stop acknowledgement keep one run and one command
- Location: tests/e2e/run-reconnect.spec.ts:827:5

# Error details

```
Error: expect(locator).toHaveAttribute(expected) failed

Locator:  locator('[data-control-operation]')
Expected: "completed"
Received: "sending"
Timeout:  10000ms

Call log:
  - Expect "toHaveAttribute" locator('[data-control-operation]') with timeout 10000ms
  - waiting for locator('[data-control-operation]')
    24 × locator resolved to <div class="control-operation" data-control-operation="sending">…</div>
       - unexpected value "sending"

```

```yaml
- heading "Stop request sending" [level=3]
- paragraph: Sent. Waiting for the backend to acknowledge this request.
```

# Test source

```ts
  810  |       tab.getByRole("heading", { name: /Run results/ }),
  811  |     ).toBeVisible();
  812  |     await expect(tab.locator(".run-identity code").first()).toHaveText(
  813  |       accepted[0].runId,
  814  |     );
  815  |   }
  816  |   await expect(page.locator("[data-pending-start]")).toHaveCount(0);
  817  |   // Three Start deliveries of one request identity; the backend owns exactly one run.
  818  |   expect(keys).toHaveLength(3);
  819  |   expect(new Set(keys).size).toBe(1);
  820  |   expect(await projectRuns(page, project.projectId)).toHaveLength(1);
  821  |   await second.close();
  822  |   await page.screenshot({
  823  |     path: testInfo.outputPath("lost-start-two-tab-retry.png"),
  824  |     fullPage: true,
  825  |   });
  826  | });
  827  | test("run session: double Start, page close/reopen and a lost Stop acknowledgement keep one run and one command", async ({
  828  |   page,
  829  |   context,
  830  | }, testInfo) => {
  831  |   test.setTimeout(90000);
  832  |   await connectStudio(page, testInfo);
  833  |   const project = await openTimedProject(page, "Owned control receipts", 20);
  834  |   const keys: string[] = [];
  835  |   recordStarts(page, keys);
  836  |   await page
  837  |     .getByRole("button", { name: "Preflight & run", exact: true })
  838  |     .click();
  839  |   await page
  840  |     .getByRole("button", { name: "Start frozen snapshot", exact: true })
  841  |     .dblclick();
  842  |   await expect(
  843  |     page.getByRole("heading", { name: /Run results/ }),
  844  |   ).toBeVisible();
  845  |   expect(new Set(keys).size).toBe(1);
  846  |   const [run] = await projectRuns(page, project.projectId);
  847  |   expect(await projectRuns(page, project.projectId)).toHaveLength(1);
  848  |   await expect(page.locator(".stream-indicator")).toHaveText("Connected");
  849  |   // Closing the only page does not stop the backend-owned run.
  850  |   await page.close();
  851  |   const reopened = await context.newPage(),
  852  |     reopenedWrites: string[] = [];
  853  |   reopened.on("request", (r) => {
  854  |     if (r.method() !== "GET")
  855  |       reopenedWrites.push(r.method() + " " + new URL(r.url()).pathname);
  856  |   });
  857  |   await reopened.goto("/");
  858  |   await reopened.getByRole("tab", { name: "Results", exact: false }).click();
  859  |   await expect(reopened.locator(".run-identity code").first()).toHaveText(
  860  |     run.runId,
  861  |   );
  862  |   await expect(
  863  |     reopened.getByRole("heading", { name: /Run results/ }),
  864  |   ).toContainText("running");
  865  |   expect(reopenedWrites).toEqual([]);
  866  |   const stop = reopened.getByRole("button", { name: "Stop", exact: true });
  867  |   await expect(stop).toBeEnabled();
  868  |   await expect(reopened.locator("#control-reason-stop")).toHaveText(
  869  |     "Request the declared orderly shutdown.",
  870  |   );
  871  |   const commandKeys: string[] = [];
  872  |   reopened.on("request", (request) => {
  873  |     if (
  874  |       request.method() === "POST" &&
  875  |       request.url().includes(`/runs/${run.runId}/commands`)
  876  |     )
  877  |       commandKeys.push(request.headers()["idempotency-key"]);
  878  |   });
  879  |   let dropped = 0;
  880  |   await reopened.route(
  881  |     `**/api/v1/runs/${run.runId}/commands`,
  882  |     async (route) => {
  883  |       if (dropped) return route.fallback();
  884  |       dropped++;
  885  |       await route.fetch();
  886  |       await route.abort("connectionreset");
  887  |     },
  888  |   );
  889  |   await stop.click();
  890  |   const operation = reopened.locator("[data-control-operation]");
  891  |   await expect(operation).toHaveAttribute(
  892  |     "data-control-operation",
  893  |     "unacknowledged",
  894  |   );
  895  |   // Only one control may be pending; both are unavailable with a stated reason.
  896  |   await expect(stop).toBeDisabled();
  897  |   // The delivered Stop may already have taken effect; either truthful reason applies.
  898  |   await expect(reopened.locator("#control-reason-cancel")).toHaveText(
  899  |     /^(A stop request must settle before another control\.|Not available while the run is (stopping|stopped)\.)$/,
  900  |   );
  901  |   await reopened.reload();
  902  |   await reopened.getByRole("tab", { name: "Results", exact: false }).click();
  903  |   await expect(operation).toHaveAttribute(
  904  |     "data-control-operation",
  905  |     "unacknowledged",
  906  |   );
  907  |   await reopened
  908  |     .getByRole("button", { name: "Retry same request", exact: true })
  909  |     .click();
> 910  |   await expect(operation).toHaveAttribute(
       |                           ^ Error: expect(locator).toHaveAttribute(expected) failed
  911  |     "data-control-operation",
  912  |     "completed",
  913  |     { timeout: 10000 },
  914  |   );
  915  |   await expect(operation).toContainText(
  916  |     "confirmed that this request took effect",
  917  |   );
  918  |   await expect(
  919  |     reopened.getByRole("heading", { name: /Run results/ }),
  920  |   ).toContainText("stopped");
  921  |   expect(commandKeys).toHaveLength(2);
  922  |   expect(new Set(commandKeys).size).toBe(1);
  923  |   await expect(stop).toBeDisabled();
  924  |   await expect(reopened.locator("#control-reason-stop")).toHaveText(
  925  |     "Not available while the run is stopped.",
  926  |   );
  927  |   const history = await reopened.request
  928  |     .get(`/api/v1/runs/${run.runId}/history?limit=200&type=command.delegated`)
  929  |     .then((r) => r.json());
  930  |   expect(history.integrity).toBe("valid");
  931  |   expect(history.counts.matchedRecords).toBe(1);
  932  |   const ended = await reopened.request
  933  |     .get(`/api/v1/runs/${run.runId}`)
  934  |     .then((r) => r.json());
  935  |   expect(ended.state).toBe("stopped");
  936  |   expect(await projectRuns(reopened, project.projectId)).toHaveLength(1);
  937  |   await reopened.screenshot({
  938  |     path: testInfo.outputPath("lost-stop-retry-completed.png"),
  939  |     fullPage: true,
  940  |   });
  941  | });
  942  | test("run controls: UI fixture renders failed and unknown command outcomes and unresolved ownership without sending controls", async ({
  943  |   page,
  944  | }, testInfo) => {
  945  |   test.setTimeout(60000);
  946  |   await connectStudio(page, testInfo);
  947  |   const project = await makeProject(page, "Control outcome UI fixture");
  948  |   const fixture = JSON.parse(
  949  |     execFileSync(
  950  |       path.resolve(".venv/bin/python"),
  951  |       [
  952  |         "tests/fixtures/evidence/create_stream_recovery_fixture.py",
  953  |         "--data-dir",
  954  |         process.env.STUDIO_BROWSER_DATA!,
  955  |         "--project-id",
  956  |         project.projectId,
  957  |         "--noise",
  958  |         "1000",
  959  |       ],
  960  |       { encoding: "utf8" },
  961  |     ),
  962  |   );
  963  |   const writes: string[] = [];
  964  |   page.on("request", (r) => {
  965  |     if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
  966  |       writes.push(r.method() + " " + r.url());
  967  |   });
  968  |   // Presentation-only fixture: the backend producer is proven by contract tests.
  969  |   let outcome: Record<string, string> = {
  970  |     status: "failed",
  971  |     code: "RUN_COMPLETED_BEFORE_COMMAND",
  972  |   };
  973  |   await page.route("**/api/v1/operations/op-ui-fixture", (route) =>
  974  |     route.fulfill({
  975  |       json: {
  976  |         operationId: "op-ui-fixture",
  977  |         runId: fixture.runId,
  978  |         kind: "stop",
  979  |         ...outcome,
  980  |       },
  981  |     }),
  982  |   );
  983  |   const seed = () =>
  984  |     page.evaluate((runId) => {
  985  |       localStorage.setItem(
  986  |         "studio.pendingCommand." + runId,
  987  |         JSON.stringify({
  988  |           key: "ui-fixture-key",
  989  |           runId,
  990  |           kind: "stop",
  991  |           expectedStateVersion: 1,
  992  |           sentAt: Date.now(),
  993  |           operationId: "op-ui-fixture",
  994  |           status: "delegated",
  995  |         }),
  996  |       );
  997  |     }, fixture.runId);
  998  |   await seed();
  999  |   await showRun(page, project.projectId, fixture.runId);
  1000 |   const operation = page.locator("[data-control-operation]");
  1001 |   await expect(operation).toHaveAttribute("data-control-operation", "failed");
  1002 |   await expect(operation).toContainText("Accepted, but it did not take effect");
  1003 |   await expect(operation).toContainText("RUN_COMPLETED_BEFORE_COMMAND");
  1004 |   outcome = { status: "unknown" };
  1005 |   await seed();
  1006 |   await showRun(page, project.projectId, fixture.runId);
  1007 |   await expect(operation).toHaveAttribute("data-control-operation", "unknown");
  1008 |   await expect(operation).toContainText("cannot prove whether");
  1009 |   const ownership = page.locator(".ownership-unresolved");
  1010 |   await expect(ownership).toContainText("Unresolved owned resources");
```
