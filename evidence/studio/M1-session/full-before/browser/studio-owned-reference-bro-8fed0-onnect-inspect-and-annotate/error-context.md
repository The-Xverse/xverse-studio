# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: studio.spec.ts >> owned reference browser workflow: author, preflight, execute, reconnect, inspect and annotate
- Location: tests/e2e/studio.spec.ts:7:5

# Error details

```
Error: expect(locator).toBeFocused() failed

Locator:  getByRole('button', { name: 'Preflight & run', exact: true })
Expected: focused
Received: inactive
Timeout:  10000ms

Call log:
  - Expect "toBeFocused" getByRole('button', { name: 'Preflight & run', exact: true }) with timeout 10000ms
  - waiting for getByRole('button', { name: 'Preflight & run', exact: true })
    24 × locator resolved to <button class="button primary" data-preflight-trigger="">…</button>
       - unexpected value "inactive"

```

```yaml
- button "Preflight & run"
```

# Test source

```ts
  155 |     .selectOption({ index: 1 });
  156 |   await page
  157 |     .getByRole("button", { name: "Evaluate assertion", exact: true })
  158 |     .click();
  159 |   await expect(page.getByText("indeterminate", { exact: true })).toBeVisible();
  160 |   await page
  161 |     .getByRole("button", { name: "Preflight & run", exact: true })
  162 |     .click();
  163 |   await expect(
  164 |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  165 |   ).toBeEnabled();
  166 |   await page
  167 |     .getByRole("button", { name: "Back to draft", exact: true })
  168 |     .click();
  169 |   await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  170 |   await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5,0.8]}');
  171 |   await page.getByLabel("Maximum runs", { exact: true }).fill("2");
  172 |   await page
  173 |     .getByRole("button", { name: "Create campaign", exact: true })
  174 |     .click();
  175 |   await expect(
  176 |     page.locator(".section-heading").getByText("complete", { exact: true }),
  177 |   ).toBeVisible({ timeout: 30000 });
  178 |   await page.screenshot({
  179 |     path: testInfo.outputPath("campaign.png"),
  180 |     fullPage: true,
  181 |   });
  182 |   await exerciseComposition(page, testInfo);
  183 |   await exerciseFrozenRerun(page, testInfo);
  184 |   for (const viewport of [
  185 |     { width: 1024, height: 768 },
  186 |     { width: 1440, height: 900 },
  187 |   ]) {
  188 |     await page.setViewportSize(viewport);
  189 |     await page.getByRole("tab", { name: "Model", exact: true }).click();
  190 |     const horizontalOverflow = await page.evaluate(
  191 |       () => document.documentElement.scrollWidth > window.innerWidth + 1,
  192 |     );
  193 |     expect(horizontalOverflow).toBe(false);
  194 |     await page.getByRole("button", { name: "Table view", exact: true }).focus();
  195 |     await page.keyboard.press("Enter");
  196 |     await expect(
  197 |       page.getByRole("button", { name: "plant", exact: true }),
  198 |     ).toBeVisible();
  199 |     await page.getByRole("button", { name: "Graph view", exact: true }).click();
  200 |     await page.screenshot({
  201 |       path: testInfo.outputPath(`workspace-${viewport.width}.png`),
  202 |       fullPage: true,
  203 |     });
  204 |   }
  205 |   await page.getByRole("button", { name: "Laboratory", exact: true }).click();
  206 |   await expect(
  207 |     page.getByRole("heading", { name: "No physical provider admitted" }),
  208 |   ).toBeVisible();
  209 |   expect(errors).toEqual([]);
  210 |   const keyboardActivate = async (
  211 |     target: ReturnType<typeof page.getByRole>,
  212 |   ) => {
  213 |     await expect(target).toBeVisible();
  214 |     for (let step = 0; step < 130; step++) {
  215 |       if (
  216 |         await target.evaluate((element) => document.activeElement === element)
  217 |       ) {
  218 |         await page.keyboard.press("Enter");
  219 |         return;
  220 |       }
  221 |       await page.keyboard.press("Tab");
  222 |     }
  223 |     throw new Error(
  224 |       "Keyboard target is not reachable through native Tab order.",
  225 |     );
  226 |   };
  227 |   await keyboardActivate(
  228 |     page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
  229 |   );
  230 |   await keyboardActivate(
  231 |     page
  232 |       .locator(".example-grid")
  233 |       .getByRole("button", { name: /Automotive reference/ }),
  234 |   );
  235 |   await expect(
  236 |     page.getByRole("heading", { name: "Automotive reference", exact: true }),
  237 |   ).toBeVisible();
  238 |   await keyboardActivate(
  239 |     page.getByRole("button", { name: "Validate", exact: true }),
  240 |   );
  241 |   await expect(
  242 |     page.getByText("Authoritative platform validation passed.", {
  243 |       exact: false,
  244 |     }),
  245 |   ).toBeVisible();
  246 |   await keyboardActivate(
  247 |     page.getByRole("button", { name: "Preflight & run", exact: true }),
  248 |   );
  249 |   await expect(
  250 |     page.getByRole("heading", { name: "Execution preflight" }),
  251 |   ).toBeVisible();
  252 |   await page.keyboard.press("Escape");
  253 |   await expect(
  254 |     page.getByRole("button", { name: "Preflight & run", exact: true }),
> 255 |   ).toBeFocused();
      |     ^ Error: expect(locator).toBeFocused() failed
  256 |   await page.keyboard.press("Enter");
  257 |   await keyboardActivate(
  258 |     page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  259 |   );
  260 |   await expect(
  261 |     page.getByRole("heading", { name: /Run results/ }),
  262 |   ).toBeVisible();
  263 |   await expect(page.getByText("running", { exact: true }).first()).toBeVisible({
  264 |     timeout: 10000,
  265 |   });
  266 |   await keyboardActivate(
  267 |     page.getByRole("button", { name: "Stop", exact: true }),
  268 |   );
  269 |   await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
  270 |     timeout: 15000,
  271 |   });
  272 |   await expect(page.getByRole("alert")).toHaveCount(0);
  273 |   expect(errors).toEqual([]);
  274 |   if (
  275 |     process.env.STUDIO_MEASURE_PERFORMANCE === "1" ||
  276 |     process.env.STUDIO_PERFORMANCE === "1"
  277 |   ) {
  278 |     const referenceProjectId = await page.evaluate(() =>
  279 |       localStorage.getItem("studio.projectId"),
  280 |     );
  281 |     await measureModel(page, testInfo);
  282 |     await measureHistory(page, testInfo, referenceProjectId || undefined);
  283 |   }
  284 |   expect(errors).toEqual([]);
  285 | });
  286 |
```
