import { test, expect } from "@playwright/test";
import { connectStudio } from "./connect-studio";
import { measureModel } from "../performance/browser-model";
import { measureHistory } from "../performance/browser-history";
import { exerciseComposition } from "./composition-flow";
import { exerciseFrozenRerun } from "./frozen-rerun-flow";
test("owned reference browser workflow: author, preflight, execute, reconnect, inspect and annotate", async ({
  page,
}, testInfo) => {
  test.setTimeout(240000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await connectStudio(page, testInfo);
  await page.screenshot({
    path: testInfo.outputPath("home.png"),
    fullPage: true,
  });
  await page
    .locator(".example-grid")
    .getByRole("button", { name: /Process control reference/ })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Process control reference",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "plant plant" })).toBeVisible();
  await page.getByRole("button", { name: "plant plant" }).click();
  await expect(page.locator(".inspector .key-values")).toContainText(
    "reference-response",
  );
  await expect(
    page.getByRole("heading", { name: "Element inspector" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Parameters", exact: true }).click();
  await page.getByLabel("Duration").fill("1");
  await page
    .getByLabel("Duration")
    .locator("xpath=ancestor::form")
    .getByRole("button", { name: "Apply", exact: true })
    .click();
  await expect(
    page.getByText("Draft saved. Existing run snapshots remain unchanged."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect(
    page.getByText("Authoritative platform validation passed.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("model.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Table view", exact: true }).click();
  await expect(
    page.getByRole("table").getByRole("button", { name: "plant", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Graph view", exact: true }).click();
  await page.getByRole("tab", { name: "Connections", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Endpoint contracts" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Deployment", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Inspect and update a binding" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Scheduled actions" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "XDL source", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Resource", exact: true })
    .selectOption({ index: 0 });
  const before = await page
    .getByLabel("XDL source", { exact: true })
    .inputValue();
  await page
    .getByLabel("XDL source", { exact: true })
    .fill(before + "\n# Browser round-trip verification\n");
  await page
    .getByRole("button", { name: "Compare changes", exact: true })
    .click();
  await expect(page.getByText("Edited draft", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Save source revision", exact: true })
    .click();
  await expect(page.getByText("Saved revision", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close dialog", exact: true }).click();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Execution preflight" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toBeVisible();
  await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
    timeout: 20000,
  });
  const runIds = await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  );
  expect(runIds).toBeTruthy();
  await page.reload();
  await expect(
    page.getByRole("heading", {
      name: "Process control reference",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Results", exact: false }).click();
  await expect(page.getByText(runIds!, { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(
    page.getByRole("img", { name: /Recorded observation chart/ }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("results.png"),
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  await expect(
    page.getByRole("heading", { name: "Events and permitted logs" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Annotations", exact: true }).click();
  await page
    .getByLabel("Comment", { exact: true })
    .fill("Browser verification note; separate from immutable evidence.");
  await page
    .getByRole("button", { name: "Save separate annotation", exact: true })
    .click();
  await expect(
    page.getByText(
      "Browser verification note; separate from immutable evidence.",
      { exact: true },
    ),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await page.getByRole("tab", { name: "Assertions", exact: true }).click();
  await expect(
    page.getByLabel("Snapshot definition reference").locator("option"),
  ).toHaveCount(2);
  await page
    .getByLabel("Snapshot definition reference")
    .selectOption({ index: 1 });
  await page
    .getByRole("button", { name: "Evaluate assertion", exact: true })
    .click();
  await expect(page.getByText("indeterminate", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  ).toBeEnabled();
  await page
    .getByRole("button", { name: "Back to draft", exact: true })
    .click();
  await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5,0.8]}');
  await page.getByLabel("Maximum runs", { exact: true }).fill("2");
  await page
    .getByRole("button", { name: "Create campaign", exact: true })
    .click();
  await expect(
    page.locator(".section-heading").getByText("complete", { exact: true }),
  ).toBeVisible({ timeout: 30000 });
  await page.screenshot({
    path: testInfo.outputPath("campaign.png"),
    fullPage: true,
  });
  await exerciseComposition(page, testInfo);
  await exerciseFrozenRerun(page, testInfo);
  for (const viewport of [
    { width: 1024, height: 768 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    await page.getByRole("tab", { name: "Model", exact: true }).click();
    const horizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth + 1,
    );
    expect(horizontalOverflow).toBe(false);
    await page.getByRole("button", { name: "Table view", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("button", { name: "plant", exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Graph view", exact: true }).click();
    await page.screenshot({
      path: testInfo.outputPath(`workspace-${viewport.width}.png`),
      fullPage: true,
    });
  }
  await page.getByRole("button", { name: "Laboratory", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No physical provider admitted" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
  const keyboardActivate = async (
    target: ReturnType<typeof page.getByRole>,
  ) => {
    await expect(target).toBeVisible();
    for (let step = 0; step < 130; step++) {
      if (
        await target.evaluate((element) => document.activeElement === element)
      ) {
        await page.keyboard.press("Enter");
        return;
      }
      await page.keyboard.press("Tab");
    }
    throw new Error(
      "Keyboard target is not reachable through native Tab order.",
    );
  };
  await keyboardActivate(
    page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
  );
  await keyboardActivate(
    page
      .locator(".example-grid")
      .getByRole("button", { name: /Automotive reference/ }),
  );
  await expect(
    page.getByRole("heading", { name: "Automotive reference", exact: true }),
  ).toBeVisible();
  await keyboardActivate(
    page.getByRole("button", { name: "Validate", exact: true }),
  );
  await expect(
    page.getByText("Authoritative platform validation passed.", {
      exact: false,
    }),
  ).toBeVisible();
  await keyboardActivate(
    page.getByRole("button", { name: "Preflight & run", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: "Execution preflight" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Preflight & run", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await keyboardActivate(
    page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
  );
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toBeVisible();
  await expect(page.getByText("running", { exact: true }).first()).toBeVisible({
    timeout: 10000,
  });
  await keyboardActivate(
    page.getByRole("button", { name: "Stop", exact: true }),
  );
  await expect(page.getByText("stopped", { exact: true }).first()).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByRole("alert")).toHaveCount(0);
  expect(errors).toEqual([]);
  if (
    process.env.STUDIO_MEASURE_PERFORMANCE === "1" ||
    process.env.STUDIO_PERFORMANCE === "1"
  ) {
    const referenceProjectId = await page.evaluate(() =>
      localStorage.getItem("studio.projectId"),
    );
    await measureModel(page, testInfo);
    await measureHistory(page, testInfo, referenceProjectId || undefined);
  }
  expect(errors).toEqual([]);
});
