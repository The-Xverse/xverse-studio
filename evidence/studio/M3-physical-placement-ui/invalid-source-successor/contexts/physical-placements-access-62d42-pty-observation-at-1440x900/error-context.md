# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: physical-placements-accessibility.spec.ts >> physical placements: actual invalid source is not an empty observation at 1440x900
- Location: tests/e2e/physical-placements-accessibility.spec.ts:189:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Physical placement observation', exact: true }).getByRole('alert')
Expected substring: "source set is invalid"
Received string:    "Physical placement availability is unknown. The public diagnostics are incomplete or malformed. Inspect again to retry."
Timeout: 10000ms

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Physical placement observation', exact: true }).getByRole('alert') with timeout 10000ms
  - waiting for getByRole('region', { name: 'Physical placement observation', exact: true }).getByRole('alert')
    23 × locator resolved to <p role="alert" tabindex="-1" class="notice error">Physical placement availability is unknown. The p…</p>
       - unexpected value "Physical placement availability is unknown. The public diagnostics are incomplete or malformed. Inspect again to retry."

```

```yaml
- alert: Physical placement availability is unknown. The public diagnostics are incomplete or malformed. Inspect again to retry.
```

# Test source

```ts
  104 |     "state",
  105 |   ]);
  106 |   expect(report.bindings[0].diagnostics).toContain("ASSET_UNAVAILABLE");
  107 |   await page.evaluate(
  108 |     (id) => localStorage.setItem("studio.projectId", id),
  109 |     project.projectId,
  110 |   );
  111 |   await page.reload();
  112 |   await expect(
  113 |     page.getByRole("heading", { name: project.name, exact: true }),
  114 |   ).toBeVisible();
  115 |   await activate(page, page.getByRole("tab", { name: /^Deployment/ }));
  116 |   await expect(
  117 |     page.getByRole("combobox", { name: "Deployment variant", exact: true }),
  118 |   ).not.toHaveValue("");
  119 |   await page.waitForLoadState("networkidle");
  120 |   return {
  121 |     project: await request(page, `/projects/${project.projectId}`),
  122 |     documentId,
  123 |     url,
  124 |     report,
  125 |   };
  126 | }
  127 |
  128 | const panel = (page: Page) => page.getByRole("region", { name: "Physical placement observation", exact: true });
  129 | const inspect = (page: Page) => panel(page).getByRole("button", { name: "Inspect physical placements", exact: true });
  130 | const heading = (page: Page) => panel(page).getByRole("heading", { name: "Physical placement observation", exact: true });
  131 | const home = (page: Page) => page.getByRole("button", { name: "X-Verse Studio home", exact: true });
  132 | const pattern = "**/api/v1/projects/*/deployment-variants/*/physical-bindings?*";
  133 | const field = (scope: Locator, name: string) => scope.locator(".key-values > div").filter({ has: scope.page().getByText(name, { exact: true }) }).locator("dd");
  134 |
  135 | async function reopen(page: Page, project: any) {
  136 |   await page.reload();
  137 |   await expect(page.getByRole("heading", { name: project.name, exact: true })).toBeVisible();
  138 |   await activate(page, page.getByRole("tab", { name: /^Deployment/ }));
  139 |   await page.waitForLoadState("networkidle");
  140 | }
  141 |
  142 | async function observeWrites(page: Page, project: any, info: TestInfo) {
  143 |   const beforeRuns = await request(page, "/runs"), reads: string[] = [];
  144 |   let writes = 0;
  145 |   const listener = (r: import("@playwright/test").Request) => {
  146 |     if (!["GET", "HEAD"].includes(r.method())) writes++;
  147 |     if (new URL(r.url()).pathname.endsWith("/physical-bindings")) reads.push(new URL(r.url()).pathname + new URL(r.url()).search);
  148 |   };
  149 |   page.on("request", listener);
  150 |   return async (details: Record<string, unknown>) => {
  151 |     await page.unroute(pattern);
  152 |     await page.waitForLoadState("networkidle");
  153 |     expect(await request(page, `/projects/${project.projectId}`)).toEqual(project);
  154 |     expect(await request(page, "/runs")).toEqual(beforeRuns);
  155 |     expect(writes).toBe(0);
  156 |     page.off("request", listener);
  157 |     await info.attach("placement-journey.json", {
  158 |       body: JSON.stringify({ projectId: project.projectId, revision: project.revision, reads, mutativeRequestsAfterSetup: writes,
  159 |         canonicalProjectAndRunsUnchanged: true, ...details,
  160 |         scope: "Read-only native browser inspection; actual API results and labelled transport fixtures are distinguished. No physical provider installed, reservation, device operation or Start." }),
  161 |       contentType: "application/json",
  162 |     });
  163 |   };
  164 | }
  165 |
  166 | async function bounds(target: Locator, viewport: {width:number;height:number}) {
  167 |   await expect(target).toBeFocused();
  168 |   const geometry = await target.evaluate(n => {const box=n.getBoundingClientRect(), style=getComputedStyle(n);return {box:box.toJSON(),outline:style.outlineStyle,outlineWidth:parseFloat(style.outlineWidth)};});
  169 |   expect(geometry.box.left).toBeGreaterThanOrEqual(0);
  170 |   expect(geometry.box.top).toBeGreaterThanOrEqual(0);
  171 |   expect(geometry.box.right).toBeLessThanOrEqual(viewport.width);
  172 |   expect(geometry.box.bottom).toBeLessThanOrEqual(viewport.height);
  173 |   expect(geometry.outline).not.toBe("none");
  174 |   expect(geometry.outlineWidth).toBeGreaterThan(0);
  175 |   return geometry;
  176 | }
  177 |
  178 | async function paint(target: Locator, label: string) {
  179 |   const observed = await renderedContrast(target, label);
  180 |   expect(observed.supported).toBe(true);
  181 |   if (observed.supported) expect(observed.ratio).toBeGreaterThanOrEqual(4.5);
  182 |   return observed;
  183 | }
  184 |
  185 | for (const viewport of [
  186 |   { width: 1024, height: 768 },
  187 |   { width: 1440, height: 900 },
  188 | ]) {
  189 |   test(`physical placements: actual invalid source is not an empty observation at ${viewport.width}x${viewport.height}`, async ({page}, info) => {
  190 |     await page.setViewportSize(viewport);
  191 |     await connectStudio(page, info);
  192 |     const prepared = await setup(page, viewport.width);
  193 |     const [id, source] = Object.entries<any>(prepared.project.documents).find(([,d])=>parse(d.content).kind==="Scenario")!;
  194 |     const project = await request(page, `/projects/${prepared.project.projectId}/documents/${id}`, "PUT", {content: source.content + "\ninvalid: [\n", format:"yaml"}, prepared.project.revision);
  195 |     const report = await request(page, `${prepared.url}?revision=${project.revision}`);
  196 |     expect(report.sourceValid).toBe(false);
  197 |     expect(report.bindings).toEqual([]);
  198 |     expect(report.diagnostics.length).toBeGreaterThan(0);
  199 |     expect(report.inventoryComplete).toBeUndefined();
  200 |     await reopen(page, project);
  201 |     const finish = await observeWrites(page, project, info);
  202 |     await expect(inspect(page)).toBeEnabled();
  203 |     await activate(page, inspect(page));
> 204 |     await expect(panel(page).getByRole("alert")).toContainText("source set is invalid");
      |                                                  ^ Error: expect(locator).toContainText(expected) failed
  205 |     await expect(panel(page).getByRole("alert")).toBeFocused();
  206 |     await expect(panel(page).getByText(/No physical or hybrid bindings/)).toHaveCount(0);
  207 |     await finish({actualInvalidResolverReport:report});
  208 |   });
  209 |
  210 |   test(`physical placements: actual unresolved authored binding is read-only at ${viewport.width}x${viewport.height}`, async ({
  211 |     page,
  212 |   }, info) => {
  213 |     await page.setViewportSize(viewport);
  214 |     await connectStudio(page, info);
  215 |     const { project, documentId, url, report } = await setup(
  216 |         page,
  217 |         viewport.width,
  218 |       ),
  219 |       beforeRuns = await request(page, "/runs");
  220 |     let writes = 0;
  221 |     const reads: string[] = [];
  222 |     page.on("request", (r) => {
  223 |       if (!["GET", "HEAD"].includes(r.method())) writes++;
  224 |       if (new URL(r.url()).pathname === "/api/v1" + url)
  225 |         reads.push(new URL(r.url()).search);
  226 |     });
  227 |     const inspect = page.getByRole("button", {
  228 |       name: "Inspect physical placements",
  229 |       exact: true,
  230 |     });
  231 |     await expect.soft(inspect).toBeVisible();
  232 |     if (await inspect.count()) {
  233 |       await activate(page, inspect);
  234 |       const panel = page.getByRole("region", {
  235 |         name: "Physical placement observation",
  236 |         exact: true,
  237 |       });
  238 |       await expect(
  239 |         panel.getByText(report.systemRef, { exact: true }),
  240 |       ).toBeVisible();
  241 |       await expect(
  242 |         field(panel, "Deployment"),
  243 |       ).toHaveText(report.deploymentRef);
  244 |       await expect(
  245 |         panel.getByText(report.bindings[0].logicalRef, { exact: true }),
  246 |       ).toBeVisible();
  247 |       await expect(
  248 |         panel.getByText("urn:fixture:unresolved-bench", { exact: true }),
  249 |       ).toBeVisible();
  250 |       await expect(
  251 |         panel.getByText("ASSET_UNAVAILABLE", { exact: true }),
  252 |       ).toBeVisible();
  253 |       await expect(
  254 |         panel.getByRole("heading", {
  255 |           name: "Physical placement observation",
  256 |           exact: true,
  257 |         }),
  258 |       ).toBeFocused();
  259 |       expect(reads).toEqual([`?revision=${project.revision}`]);
  260 |     }
  261 |     const saved = await request(page, `/projects/${project.projectId}`);
  262 |     expect(saved).toEqual(project);
  263 |     expect(saved.documents[documentId]).toEqual(project.documents[documentId]);
  264 |     expect(await request(page, "/runs")).toEqual(beforeRuns);
  265 |     expect(writes).toBe(0);
  266 |     await info.attach("physical-placement-observation.json", {
  267 |       body: JSON.stringify({
  268 |         viewport,
  269 |         projectId: project.projectId,
  270 |         documentId,
  271 |         revision: project.revision,
  272 |         actualResolverReport: report,
  273 |         actualCanonicalUnchanged: true,
  274 |         mutativeRequestsAfterSetup: writes,
  275 |         observedUIReads: reads,
  276 |         scope:
  277 |           "Actual public source declaration and authoritative read-only resolver with empty/unadmitted inventory; no fixture provider installed, device operation, reservation or Start",
  278 |       }),
  279 |       contentType: "application/json",
  280 |     });
  281 |   });
  282 | }
  283 |
```
