import { test, expect, type Page } from "@playwright/test";
import { parse, stringify } from "yaml";
import { connectStudio } from "./connect-studio";

async function request(
  page: Page,
  path: string,
  method = "GET",
  body?: any,
  revision?: number,
) {
  return page.evaluate(
    async ({ path, method, body, revision }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const r = await fetch("/api/v1" + path, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
          ...(revision ? { "If-Match": String(revision) } : {}),
          ...(method === "POST"
            ? { "Idempotency-Key": crypto.randomUUID() }
            : {}),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      const v = await r.json();
      if (!r.ok) throw new Error(`Owned campaign setup ${r.status} ${v.code}`);
      return v;
    },
    { path, method, body, revision },
  );
}
async function prepare(page: Page, width: number) {
  let project = await request(page, "/projects", "POST", {
    name: `Owned campaign history ${width}`,
  });
  const [docId, doc]: any = Object.entries(project.documents).find(
    ([, d]: any) => parse(d.content).kind === "Scenario",
  )!;
  const source = parse(doc.content);
  source.extensions["io.xverse.experiment"].parameters.find(
    (p: any) => p.id === "duration",
  ).value = 0.2;
  project = await request(
    page,
    `/projects/${project.projectId}/documents/${docId}`,
    "PUT",
    { content: stringify(source), format: "yaml" },
    project.revision,
  );
  const pf = await request(
    page,
    `/projects/${project.projectId}/preflights`,
    "POST",
    { revision: project.revision },
  );
  expect(pf.status).toBe("ready");
  await page.evaluate(
    ({ project, pf }) => {
      localStorage.setItem("studio.projectId", project.projectId);
      localStorage.setItem(
        "studio.selection." + project.projectId,
        JSON.stringify(pf.selection),
      );
    },
    { project, pf },
  );
  await page.reload();
  await page.getByRole("tab", { name: "Experiments", exact: true }).click();
  await page.getByRole("tab", { name: "Campaigns", exact: true }).click();
  return { project, pf };
}
for (const width of [1024, 1440]) {
  for (const departure of ["newer draft", "Home"]) {
    test(`campaign completion: accepted creation preserves ${departure} at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      const { project } = await prepare(page, width);
      await page
        .getByRole("button", { name: "Preflight & run", exact: true })
        .click();
      await expect(
        page.getByRole("button", {
          name: "Start frozen snapshot",
          exact: true,
        }),
      ).toBeEnabled();
      await page
        .getByRole("button", { name: "Back to draft", exact: true })
        .click();
      await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5]}');
      await page.getByLabel("Maximum runs", { exact: true }).fill("1");
      await page
        .getByLabel("Maximum total simulated seconds", { exact: true })
        .fill("1");
      await page
        .getByRole("button", { name: "Preview campaign", exact: true })
        .click();
      await expect(
        page.getByRole("heading", {
          name: "Authoritative campaign preview",
          exact: true,
        }),
      ).toBeVisible();
      let release!: () => void, ready!: () => void;
      const gate = new Promise<void>((r) => (release = r)),
        accepted = new Promise<void>((r) => (ready = r));
      let receipt: any = null,
        count = 0,
        delivered = false;
      await page.route("**/api/v1/campaigns", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        count++;
        const response = await route.fetch();
        expect(response.status()).toBe(202);
        receipt = await response.json();
        ready();
        await gate;
        try {
          await route.fulfill({ response });
        } catch {
          /* A departed browser request can be aborted after real acceptance. */
        }
        delivered = true;
      });
      try {
        await page
          .getByRole("button", { name: "Create campaign", exact: true })
          .focus();
        await page.keyboard.press("Enter");
        await page.keyboard.press("Enter");
        await expect
          .poll(() => receipt?.campaignId, { timeout: 30000 })
          .toBeTruthy();
        await accepted;
        if (departure === "newer draft") {
          await page
            .getByLabel("Parameter matrix (JSON)")
            .fill('{"gain":[0.9]}');
          await page.getByLabel("Parameter matrix (JSON)").focus();
        } else {
          await page
            .getByRole("button", { name: "X-Verse Studio home", exact: true })
            .click();
          await page
            .getByRole("button", { name: "X-Verse Studio home", exact: true })
            .focus();
        }
        release();
        await expect.poll(() => delivered).toBe(true);
        if (departure === "newer draft") {
          await expect(page.getByLabel("Parameter matrix (JSON)")).toHaveValue(
            '{"gain":[0.9]}',
          );
          await expect(
            page.getByLabel("Parameter matrix (JSON)"),
          ).toBeFocused();
          await expect(
            page.getByRole("region", {
              name: "Selected campaign",
              exact: true,
            }),
          ).not.toContainText(receipt.campaignId);
        } else {
          await expect(
            page.getByRole("tab", { name: "Campaigns", exact: true }),
          ).not.toBeVisible();
          await expect(
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          ).toBeFocused();
        }
        expect(count).toBe(1);
        const recorded = await request(
          page,
          `/campaigns/${receipt.campaignId}`,
        );
        expect(recorded.matrix).toEqual({ gain: [0.5] });
        await expect.poll(async () => (await request(page, `/campaigns/${receipt.campaignId}`)).status, { timeout: 30000 }).toBe("complete");
        expect(await request(page, `/projects/${project.projectId}`)).toEqual(
          project,
        );
        await info.attach("actual-delayed-campaign-acceptance", {
          contentType: "application/json",
          body: JSON.stringify({
            departure,
            projectId: project.projectId,
            campaignId: receipt.campaignId,
            originalMatrix: recorded.matrix,
            requests: count,
            scope:
              "Held real 202 response after durable acceptance; no synthetic campaign record",
          }),
        });
      } finally {
        release();
      }
    });
  }
  test(`campaign response guards: labelled history pages and unavailable provenance at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const { pf, project } = await prepare(page, width);
    const made = await request(page, "/campaigns", "POST", {
      snapshotId: pf.snapshotId,
      matrix: { gain: [0.5] },
      budget: { maxRuns: 1, maxTotalSeconds: 1 },
      concurrency: 1,
    });
    await expect
      .poll(
        async () =>
          (await request(page, `/campaigns/${made.campaignId}`)).status,
        { timeout: 30000 },
      )
      .toBe("complete");
    const actual = await request(page, `/campaigns/${made.campaignId}`);
    const readIds = (await request(page, "/runs")).items.map(
      (r: any) => r.runId,
    );
    const history = page.getByRole("region", {
      name: "Retained campaign history",
      exact: true,
    });
    await page.route("**/api/v1/campaigns?*", (route) => {
      const cursor = new URL(route.request().url()).searchParams.get("cursor");
      const items = cursor
        ? [{ ...actual, campaignId: "fixture-last-campaign" }]
        : Array.from({ length: 20 }, (_, i) => ({
            ...actual,
            campaignId: i === 0 ? made.campaignId : `fixture-campaign-${i}`,
          }));
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items, nextCursor: cursor ? null : "20" }),
      });
    });
    await history
      .getByRole("button", { name: "Refresh campaign history", exact: true })
      .click();
    await expect(
      history.getByRole("button", { name: /^Inspect campaign / }),
    ).toHaveCount(20);
    await history
      .getByRole("button", { name: "Next campaign page", exact: true })
      .click();
    await expect(
      history.getByRole("button", {
        name: "Inspect campaign fixture-last-campaign",
        exact: true,
      }),
    ).toBeVisible();
    await history
      .getByRole("button", { name: "Previous campaign page", exact: true })
      .click();
    for (const mode of [
      "wrong identity",
      "unknown version",
      "unavailable provenance",
    ]) {
      await page.route(`**/api/v1/campaigns/${made.campaignId}`, (route) => {
        const value = structuredClone(actual);
        if (mode === "wrong identity") value.campaignId = "foreign-campaign";
        else if (mode === "unknown version") value.campaignVersion = "2.0";
        else
          value.baseInput = {
            status: "unavailable",
            reason: "SNAPSHOT_INTEGRITY",
            projectId: "fixture-spoofed-project",
            revision: 999,
          };
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(value),
        });
      });
      await history
        .getByRole("button", {
          name: `Inspect campaign ${made.campaignId}`,
          exact: true,
        })
        .click();
      const panel = page.getByRole("region", {
        name: "Selected campaign",
        exact: true,
      });
      if (mode === "unavailable provenance") {
        await expect(panel).toContainText(
          "Frozen input provenance is unavailable",
        );
        await expect(panel).not.toContainText("fixture-spoofed-project");
        await expect(panel).not.toContainText(project.projectId);
        await expect(panel).toContainText(actual.children[0].runId);
      } else {
        await expect(page.getByRole("alert")).toContainText(
          "malformed, unsupported",
        );
        await expect(panel).not.toContainText(actual.children[0].runId);
      }
      await page.unroute(`**/api/v1/campaigns/${made.campaignId}`);
    }
    await page.unroute("**/api/v1/campaigns?*");
    expect(
      (await request(page, "/runs")).items.map((r: any) => r.runId),
    ).toEqual(readIds);
    await info.attach("labelled-campaign-transport-fixtures", {
      contentType: "application/json",
      body: JSON.stringify({
        scope:
          "Synthetic transport history paging/foreign identity/version/unavailable-provenance fixtures derived from one actual completed campaign; no provider or execution admission",
        rows: 21,
        noExtraRuns: true,
      }),
    });
  });
  test(`campaign control: actual admission failure policy and pending cancellation at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const { pf } = await prepare(page, width);
    const failed = await request(page, "/campaigns", "POST", {
      snapshotId: pf.snapshotId,
      matrix: { gain: [999, 0.5, 0.8] },
      budget: { maxRuns: 3, maxTotalSeconds: 1 },
      concurrency: 1,
      stopPolicy: "stop_on_failure",
    });
    await expect
      .poll(
        async () =>
          (await request(page, `/campaigns/${failed.campaignId}`)).status,
        { timeout: 30000 },
      )
      .toBe("complete");
    const refused = await request(page, `/campaigns/${failed.campaignId}`);
    expect(refused.children.map((c: any) => c.state)).toEqual([
      "rejected",
      "cancelled",
      "cancelled",
    ]);
    const refresh = page.getByRole("button", {
      name: "Refresh campaign history",
      exact: true,
    });
    await refresh.click();
    await page
      .getByRole("button", {
        name: `Inspect campaign ${failed.campaignId}`,
        exact: true,
      })
      .click();
    const panel = page.getByRole("region", {
      name: "Selected campaign",
      exact: true,
    });
    await expect(panel).toContainText(refused.children[0].reason);
    await expect(
      panel.getByRole("button", { name: "Stop scheduling", exact: true }),
    ).toBeDisabled();
    const pending = await request(page, "/campaigns", "POST", {
      snapshotId: pf.snapshotId,
      matrix: { gain: Array.from({ length: 16 }, (_, i) => (i + 1) / 10) },
      budget: { maxRuns: 16, maxTotalSeconds: 5 },
      concurrency: 1,
      stopPolicy: "continue",
    });
    await refresh.click();
    await page
      .getByRole("button", {
        name: `Inspect campaign ${pending.campaignId}`,
        exact: true,
      })
      .click();
    const cancel = panel.getByRole("button", {
      name: "Stop scheduling",
      exact: true,
    });
    await expect(cancel).toBeEnabled();
    let cancelRequests = 0;
    page.on("request", (r) => {
      if (
        r.method() === "POST" &&
        new URL(r.url()).pathname ===
          `/api/v1/campaigns/${pending.campaignId}/cancel`
      )
        cancelRequests++;
    });
    await cancel.focus();
    await page.keyboard.press("Enter");
    await page.keyboard.press("Enter");
    await expect(
      page.getByText(/Scheduling cancellation acknowledged\./),
    ).toBeVisible();
    await expect
      .poll(
        async () =>
          (await request(page, `/campaigns/${pending.campaignId}`)).status,
        { timeout: 30000 },
      )
      .toBe("cancelled");
    const cancelled = await request(page, `/campaigns/${pending.campaignId}`);
    expect(cancelled.children.some((c: any) => c.state === "cancelled")).toBe(
      true,
    );
    expect(
      cancelled.children.some((c: any) =>
        ["pending", "running", "dispatching"].includes(c.state),
      ),
    ).toBe(false);
    expect(cancelRequests).toBe(1);
    await info.attach("actual-failure-policy-and-cancel", {
      contentType: "application/json",
      body: JSON.stringify({
        refused,
        cancelled,
        oneCancellationRequest: true,
      }),
    });
  });
  test(`campaign input bounds: deep imported matrix keeps authoring available at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    await prepare(page, width);
    await page
      .getByRole("button", { name: "Preflight & run", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
    ).toBeEnabled();
    await page
      .getByRole("button", { name: "Back to draft", exact: true })
      .click();
    const errors: string[] = [],
      writes: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("request", (r) => {
      if (
        r.method() === "POST" &&
        /\/campaigns(?:\/preview)?$/.test(new URL(r.url()).pathname)
      )
        writes.push(r.url());
    });
    const field = page.getByLabel("Parameter matrix (JSON)");
    const deep =
      '{"gain":[' + "[".repeat(12000) + "0" + "]".repeat(12000) + "]}";
    expect(deep.length).toBeLessThan(32768);
    await field.fill(deep);
    await expect(field).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Create campaign", exact: true }),
    ).toBeDisabled();
    await expect(
      page.getByRole("button", { name: "Preview campaign", exact: true }),
    ).toBeDisabled();
    expect(errors).toEqual([]);
    expect(writes).toEqual([]);
    await field.fill('{"gain":[0.5,0.8]}');
    await expect(field).toHaveValue('{"gain":[0.5,0.8]}');
  });
  test(`campaign workflow: authoritative budgets, scheduling and immutable child inputs at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const { project } = await prepare(page, width);
    await page
      .getByRole("button", { name: "Preflight & run", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Start frozen snapshot", exact: true }),
    ).toBeEnabled();
    await page
      .getByRole("button", { name: "Back to draft", exact: true })
      .click();
    await page.getByLabel("Parameter matrix (JSON)").fill('{"gain":[0.5,0.8]}');
    await page.getByLabel("Maximum runs", { exact: true }).fill("2");
    await page
      .getByLabel("Maximum total simulated seconds", { exact: true })
      .fill("0.3");
    await page
      .getByLabel("Stop policy", { exact: true })
      .selectOption("stop_on_failure");
    const before = (await request(page, "/campaigns")).items.map(
      (c: any) => c.campaignId,
    );
    const beforeRuns = (await request(page, "/runs")).items.map((r: any) => r.runId);
    const preview = page.getByRole("button", {
      name: "Preview campaign",
      exact: true,
    });
    await preview.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("alert")).toContainText("CAMPAIGN_BUDGET");
    expect(
      (await request(page, "/campaigns")).items.map((c: any) => c.campaignId),
    ).toEqual(before);
    expect((await request(page, "/runs")).items.map((r: any) => r.runId)).toEqual(beforeRuns);
    await page
      .getByLabel("Maximum total simulated seconds", { exact: true })
      .fill("1");
    await preview.focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("heading", {
        name: "Authoritative campaign preview",
        exact: true,
      }),
    ).toBeFocused();
    expect(
      (await request(page, "/campaigns")).items.map((c: any) => c.campaignId),
    ).toEqual(before);
    const created: any[] = [];
    page.on("request", (r) => {
      if (
        r.method() === "POST" &&
        new URL(r.url()).pathname === "/api/v1/campaigns"
      )
        created.push(r.postDataJSON());
    });
    const create = page.getByRole("button", {
      name: "Create campaign",
      exact: true,
    });
    await create.focus();
    await page.keyboard.press("Enter");
    await page.keyboard.press("Enter");
    const panel = page.getByRole("region", {
      name: "Selected campaign",
      exact: true,
    });
    await expect(
      panel.locator(".section-heading").getByText("complete", { exact: true }),
    ).toBeVisible({ timeout: 30000 });
    expect(created).toHaveLength(1);
    expect(created[0].budget).toEqual({ maxRuns: 2, maxTotalSeconds: 1 });
    expect(created[0].stopPolicy).toBe("stop_on_failure");
    const records = (await request(page, "/campaigns")).items.filter(
      (c: any) => !before.includes(c.campaignId),
    );
    expect(records).toHaveLength(1);
    const campaign = records[0];
    expect(campaign.baseInput.projectId).toBe(project.projectId);
    expect(campaign.children.map((c: any) => c.state)).toEqual([
      "stopped",
      "stopped",
    ]);
    const child = campaign.children[0];
    await panel
      .getByRole("button", {
        name: `Inspect child inputs ${child.runId}`,
        exact: true,
      })
      .focus();
    await page.keyboard.press("Enter");
    await expect(
      panel.getByRole("heading", {
        name: "Verified child inputs",
        exact: true,
      }),
    ).toBeVisible();
    const run = await request(page, `/runs/${child.runId}`);
    const snapshot = (await request(page, `/runs/${child.runId}/snapshot`))
      .snapshot;
    expect(snapshot.snapshotId).toBe(run.snapshotId);
    expect(snapshot.parentSnapshotId).toBe(campaign.baseSnapshotId);
    expect(snapshot.configuration.gain).toBe(child.parameters.gain);
    await expect(panel).toContainText(snapshot.snapshotDigest);
    expect(await request(page, `/campaigns/${campaign.campaignId}`)).toEqual(
      campaign,
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    await info.attach("actual-campaign-preview-and-children", {
      contentType: "application/json",
      body: JSON.stringify({
        campaign,
        childSnapshotId: snapshot.snapshotId,
        childDigest: snapshot.snapshotDigest,
        inspectionCreatesNoChildren: true,
      }),
    });
  });
  test(`campaign workflow: retained native children reopen without scheduling at ${width}`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
    await connectStudio(page, info);
    const { project, pf } = await prepare(page, width);
    const made = await request(page, "/campaigns", "POST", {
      snapshotId: pf.snapshotId,
      matrix: { gain: [0.5, 0.8] },
      budget: { maxRuns: 2, maxTotalSeconds: 1 },
      concurrency: 1,
      stopPolicy: "continue",
    });
    await expect
      .poll(
        async () =>
          (await request(page, `/campaigns/${made.campaignId}`)).status,
        { timeout: 30000 },
      )
      .toBe("complete");
    const before = await request(page, `/campaigns/${made.campaignId}`);
    const runsBefore = (await request(page, "/runs")).items.map(
      (r: any) => r.runId,
    );
    const writes: string[] = [];
    page.on("request", (r) => {
      if (!["GET", "HEAD", "OPTIONS"].includes(r.method()))
        writes.push(r.method() + " " + new URL(r.url()).pathname);
    });
    const refresh = page.getByRole("button", {
      name: "Refresh campaign history",
      exact: true,
    });
    await expect(refresh).toBeVisible();
    await refresh.focus();
    await page.keyboard.press("Enter");
    const open = page.getByRole("button", {
      name: `Inspect campaign ${made.campaignId}`,
      exact: true,
    });
    await expect(open).toBeVisible();
    await open.focus();
    await page.keyboard.press("Enter");
    const panel = page.getByRole("region", {
      name: "Selected campaign",
      exact: true,
    });
    await expect(panel).toContainText(pf.snapshotId);
    await expect(panel).toContainText(project.projectId);
    for (const c of before.children) {
      await expect(panel).toContainText(c.childKey);
      await expect(panel).toContainText(c.runId);
    }
    await expect(panel).toContainText("complete");
    expect(await request(page, `/campaigns/${made.campaignId}`)).toEqual(
      before,
    );
    expect(
      (await request(page, "/runs")).items.map((r: any) => r.runId),
    ).toEqual(runsBefore);
    expect(writes).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    await info.attach("retained-campaign", {
      contentType: "application/json",
      body: JSON.stringify({
        projectId: project.projectId,
        campaignId: made.campaignId,
        snapshotId: pf.snapshotId,
        children: before.children,
        noInspectionWrites: true,
      }),
    });
  });
}
