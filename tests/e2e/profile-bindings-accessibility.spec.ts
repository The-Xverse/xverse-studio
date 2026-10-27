import { test, expect, type Page, type Locator } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, realpathSync } from "node:fs";
import path from "node:path";
import { parse } from "yaml";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (const [key, limit] of [
    ["Shift+Tab", 40],
    ["Tab", 220],
  ] as const) {
    for (let i = 0; i < limit; i++) {
      if (await target.evaluate((n) => document.activeElement === n)) return;
      await page.keyboard.press(key);
    }
  }
  await expect(target).toBeFocused();
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
async function request(
  page: Page,
  route: string,
  body?: unknown,
  revision?: number,
) {
  return page.evaluate(
    async ({ route, body, revision }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const response = await fetch("/api/v1" + route, {
        method: body === undefined ? "GET" : "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
          ...(revision === undefined ? {} : { "If-Match": `"${revision}"` }),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const value = await response.json();
      if (!response.ok)
        throw Error(
          `Owned profile fixture request failed: ${response.status} ${value.code}`,
        );
      return value;
    },
    { route, body, revision },
  );
}
async function create(page: Page, name: string) {
  const project = await request(page, "/projects", { name });
  await page.evaluate(
    (pid) => localStorage.setItem("studio.projectId", pid),
    project.projectId,
  );
  await page.reload();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  return project;
}
const panel = (page: Page) => page.locator(".profile-binding-panel");
const bind = (page: Page) =>
  panel(page).getByRole("button", {
    name: "Bind selected profile locks",
    exact: true,
  });
async function environment(page: Page) {
  await activate(
    page,
    page.getByRole("button", { name: "Environment", exact: true }),
  );
  await expect(
    panel(page).getByRole("heading", {
      name: "Admitted profile locks",
      exact: true,
    }),
  ).toBeVisible();
}
async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(
    () =>
      new Promise<void>((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
      ),
  );
  await page.waitForLoadState("networkidle");
}
async function runs(page: Page, pid: string) {
  return (await request(page, "/runs")).items
    .filter((r: any) => r.projectId === pid)
    .map((r: any) => r.runId)
    .sort();
}
const digest = (value: string) =>
  "sha256:" + createHash("sha256").update(value).digest("hex");
const identity = (entry: any) => ({
  profileId: entry.profileId,
  version: entry.version,
  schemaDigest: entry.schemaDigest,
  presentationDigest: entry.presentationDigest,
});
async function choose(page: Page, name: string) {
  const control = panel(page).getByRole("checkbox", {
    name: `Select profile ${name}`,
    exact: true,
  });
  await tabTo(page, control);
  await page.keyboard.press("Space");
  return control;
}
async function holdBinding(page: Page, pid: string, status = 200) {
  let release!: () => void,
    ready = false,
    result: any,
    finished: Promise<void> | undefined;
  const gate = new Promise<void>((r) => (release = r)),
    pattern = `**/api/v1/projects/${pid}/profile-bindings`,
    writes: any[] = [];
  await page.route(pattern, async (route) => {
    let finish!: () => void;
    finished = new Promise<void>((r) => (finish = r));
    try {
      writes.push({
        body: route.request().postDataJSON(),
        ifMatch: route.request().headers()["if-match"],
      });
      const response = await route.fetch();
      expect(response.status()).toBe(status);
      result = await response.json();
      ready = true;
      await gate;
      await route.fulfill({ response });
    } finally {
      finish();
    }
  });
  return {
    writes,
    async ready() {
      await expect.poll(() => ready).toBe(true);
      return result;
    },
    async release() {
      release();
      await finished;
    },
    async close() {
      release();
      await finished;
      await page.unroute(pattern);
    },
  };
}
async function paint(target: Locator, label: string) {
  const value = await renderedContrast(target, label);
  expect.soft(value.supported).toBe(true);
  if (value.supported) expect.soft(value.ratio).toBeGreaterThanOrEqual(4.5);
  return value;
}
async function visibleFocus(
  target: Locator,
  viewport: { width: number; height: number },
) {
  await expect(target).toBeFocused();
  const value = await target.evaluate((n) => {
    const box = n.getBoundingClientRect(),
      style = getComputedStyle(n);
    return {
      box: box.toJSON(),
      outline: style.outlineStyle,
      outlineWidth: parseFloat(style.outlineWidth),
    };
  });
  expect(value.box.left).toBeGreaterThanOrEqual(0);
  expect(value.box.top).toBeGreaterThanOrEqual(0);
  expect(value.box.right).toBeLessThanOrEqual(viewport.width);
  expect(value.box.bottom).toBeLessThanOrEqual(viewport.height);
  expect(value.outline).not.toBe("none");
  expect(value.outlineWidth).toBeGreaterThan(0);
  return value;
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  for (const mode of [
    "current pending",
    "newer selection",
    "deliberate focus",
    "newer head and readiness",
  ] as const) {
    test(`profile bindings: ${mode} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const project = await create(page, `Profile ${mode} ${viewport.width}`),
        beforeRuns = await runs(page, project.projectId);
      await environment(page);
      const checkbox = await choose(page, "Automotive terminology");
      await expect(checkbox).toBeChecked();
      await expect(checkbox).toHaveAccessibleDescription(
        /keeps existing locks/,
      );
      const checkboxFocus = await visibleFocus(checkbox, viewport);
      const guidance = await paint(
          panel(page).locator(":scope > p.field-hint"),
          "Additive immutable profile binding guidance",
        ),
        pending = await holdBinding(page, project.projectId);
      try {
        await tabTo(page, bind(page));
        await expect(bind(page)).toHaveAccessibleDescription(
          /keeps existing locks/,
        );
        const bindFocus = await visibleFocus(bind(page), viewport);
        await page.keyboard.press("Enter");
        const committed = await pending.ready();
        await expect(bind(page)).toBeDisabled();
        let newerChoice: Locator | undefined,
          newest: any,
          history: string | null = null,
          readyId: string | undefined,
          readySnapshot: string | undefined;
        if (mode === "current pending") {
          await page.keyboard.press("Enter");
          await page.keyboard.press("Enter");
          expect(pending.writes).toHaveLength(1);
        } else if (mode === "newer selection") {
          newerChoice = await choose(page, "Process-control terminology");
          await expect(newerChoice).toBeChecked();
        } else if (mode === "deliberate focus") {
          await tabTo(
            page,
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          );
        } else {
          await activate(
            page,
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          );
          await activate(
            page,
            page.locator(
              `.project-list-row[data-project-id="${project.projectId}"] .project-open`,
            ),
          );
          await activate(
            page,
            page.getByRole("button", { name: "Parameters", exact: true }),
          );
          const duration = page.getByRole("spinbutton", {
            name: "Duration s",
            exact: true,
          });
          await tabTo(page, duration);
          await page.keyboard.press("ControlOrMeta+A");
          await page.keyboard.insertText("6");
          const changed = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname ===
                `/api/v1/projects/${project.projectId}/edits` &&
              r.request().method() === "POST",
          );
          await activate(
            page,
            duration
              .locator("xpath=ancestor::form")
              .getByRole("button", { name: "Apply", exact: true }),
          );
          expect((await changed).status()).toBe(200);
          newest = await request(page, `/projects/${project.projectId}`);
          expect(newest.revision).toBe(project.revision + 2);
          history = await page.evaluate(
            (pid) => sessionStorage.getItem("studio.graphHistory." + pid),
            project.projectId,
          );
          expect(JSON.parse(history!).undo).toHaveLength(1);
          const ready = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname ===
                `/api/v1/projects/${project.projectId}/preflights` &&
              r.request().method() === "POST",
          );
          await activate(
            page,
            page.getByRole("button", { name: "Preflight & run", exact: true }),
          );
          const report = await (await ready).json();
          expect(report.status).toBe("ready");
          readyId = report.preflightId;
          readySnapshot = report.snapshotId;
          await activate(
            page,
            page.getByText("Frozen request identities", { exact: true }),
          );
          await expect(
            page.getByRole("dialog").getByText(readyId!, { exact: true }),
          ).toBeVisible();
          await tabTo(
            page,
            page.getByRole("button", {
              name: "Start frozen snapshot",
              exact: true,
            }),
          );
        }
        await pending.release();
        await settle(page);
        expect(pending.writes).toHaveLength(1);
        const saved = await request(page, `/projects/${project.projectId}`);
        if (mode === "current pending") {
          await expect(panel(page)).toHaveCount(0);
          await expect(page.locator(".project-header h1")).toHaveText(
            project.name,
          );
          await expect(
            page.getByText(
              "Profile locks saved with exact schema and presentation identities.",
              { exact: true },
            ),
          ).toBeVisible();
          const source = page.getByRole("button", {
            name: "XDL source",
            exact: true,
          });
          await expect(source).toBeFocused();
          const box = await source.boundingBox();
          expect(box!.y).toBeGreaterThanOrEqual(0);
          expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height);
          expect(saved.revision).toBe(committed.revision);
        } else if (mode === "newer selection" || mode === "deliberate focus") {
          await expect(panel(page)).toBeVisible();
          await expect(checkbox).toBeChecked();
          await expect(
            panel(page).getByText(
              `Selected project: ${project.name} · revision ${committed.revision}`,
              { exact: true },
            ),
          ).toBeVisible();
          await expect(panel(page).getByRole("status")).toContainText(
            "Saved the submitted profile locks",
          );
          if (newerChoice) {
            await expect(newerChoice).toBeChecked();
            await expect(newerChoice).toBeFocused();
            expect(
              saved.manifest.profiles.some(
                (p: any) =>
                  p.namespace === "io.xverse.studio.domain.process-control",
              ),
            ).toBe(false);
          } else
            await expect(
              page.getByRole("button", {
                name: "X-Verse Studio home",
                exact: true,
              }),
            ).toBeFocused();
        } else {
          expect(saved.documents).toEqual(newest.documents);
          expect(saved.revision).toBe(newest.revision);
          expect(
            await page.evaluate(
              (pid) => sessionStorage.getItem("studio.graphHistory." + pid),
              project.projectId,
            ),
          ).toBe(history);
          const dialog = page.getByRole("dialog", {
            name: "Execution preflight",
            exact: true,
          });
          await expect(
            dialog.getByText(readyId!, { exact: true }),
          ).toBeVisible();
          await expect(
            dialog
              .locator(".preflight-identities")
              .getByText(readySnapshot!, { exact: true }),
          ).toBeVisible();
          await expect(
            dialog.getByRole("button", {
              name: "Start frozen snapshot",
              exact: true,
            }),
          ).toBeEnabled();
          await expect(
            dialog.getByRole("button", {
              name: "Start frozen snapshot",
              exact: true,
            }),
          ).toBeFocused();
        }
        expect(await runs(page, project.projectId)).toEqual(beforeRuns);
        await info.attach("profile-completion.json", {
          body: JSON.stringify({
            viewport,
            mode,
            projectId: project.projectId,
            committedRevision: committed.revision,
            currentRevision: saved.revision,
            actualPendingPosts: pending.writes.length,
            readyId,
            readySnapshot,
            measurements: [guidance],
            checkboxFocus,
            bindFocus,
            noStart: true,
            scope:
              "Actual immutable profile transaction; preserve current navigation, checkbox/focus intent, newer canonical history and real ready preflight",
          }),
          contentType: "application/json",
        });
      } finally {
        await pending.close();
      }
    });
  }
  for (const departed of [false, true]) {
    test(`profile bindings: actual stale refusal ${departed ? "after departure" : "current"} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const project = await create(
          page,
          `Stale profile ${departed} ${viewport.width}`,
        ),
        entries = (await request(page, "/profiles")).items,
        other = entries.find(
          (p: any) => p.namespace === "io.xverse.studio.domain.process-control",
        ),
        beforeRuns = await runs(page, project.projectId);
      await environment(page);
      const checkbox = await choose(page, "Automotive terminology");
      const advanced = await request(
        page,
        `/projects/${project.projectId}/profile-bindings`,
        { baseRevision: project.revision, profiles: [identity(other)] },
        project.revision,
      );
      const pending = await holdBinding(page, project.projectId, 412);
      try {
        await activate(page, bind(page));
        const rejected = await pending.ready();
        expect(rejected.code).toBe("REVISION_CONFLICT");
        if (departed)
          await activate(
            page,
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          );
        await pending.release();
        await settle(page);
        if (departed) {
          await expect(
            page.getByRole("heading", { name: "Recent projects", exact: true }),
          ).toBeVisible();
          await expect(page.locator(".alerts .notice.error")).toHaveCount(0);
        } else {
          await expect(checkbox).toBeChecked();
          await expect(bind(page)).toBeEnabled();
          const error = page.getByRole("alert", {
            name: "Operation error",
            exact: true,
          });
          await expect(error).toContainText("REVISION_CONFLICT");
          await expect(error).toBeFocused();
          await activate(
            page,
            error.getByRole("button", {
              name: "Load current revision",
              exact: true,
            }),
          );
          await expect(page.locator(".workspace-context")).toContainText(
            `Draft revision ${advanced.revision}`,
          );
        }
        const saved = await request(page, `/projects/${project.projectId}`);
        expect(saved.revision).toBe(advanced.revision);
        expect(saved.documents).toEqual(advanced.documents);
        expect(saved.manifest.profiles).toEqual(advanced.manifest.profiles);
        expect(pending.writes).toHaveLength(1);
        expect(await runs(page, project.projectId)).toEqual(beforeRuns);
        await info.attach("profile-stale.json", {
          body: JSON.stringify({
            viewport,
            departed,
            projectId: project.projectId,
            actualStatus: 412,
            code: rejected.code,
            revisionUnchangedAfterRefusal: true,
            selectionRetainedUntilExplicitReload: !departed,
            noStart: true,
          }),
          contentType: "application/json",
        });
      } finally {
        await pending.close();
      }
    });
  }
  for (const mode of ["missing digest", "duplicate", "empty"] as const) {
    test(`profile bindings: discovery ${mode} observation at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const project = await create(
          page,
          `Profile registry ${mode} ${viewport.width}`,
        ),
        actual = await request(page, "/profiles"),
        pattern = "**/api/v1/profiles";
      let reads = 0,
        writes = 0;
      page.on("request", (r) => {
        if (
          r.method() === "POST" &&
          new URL(r.url()).pathname.endsWith("/profile-bindings")
        )
          writes++;
      });
      await page.route(pattern, async (route) => {
        reads++;
        if (reads > 1) {
          const response = await route.fetch();
          expect(response.status()).toBe(200);
          await route.fulfill({ response });
          return;
        }
        const value = structuredClone(actual);
        value.items =
          mode === "empty"
            ? []
            : mode === "duplicate"
              ? [value.items[0], value.items[0]]
              : [{ ...value.items[0], schemaDigest: undefined }];
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(value),
        });
      });
      try {
        await environment(page);
        await expect(bind(page)).toBeDisabled();
        const measurements = [];
        if (mode === "empty") {
          const notice = panel(page).getByRole("status");
          await expect(notice).toHaveText(
            "No admitted profiles were returned by this discovery request.",
          );
          await expect(panel(page).getByRole("alert")).toHaveCount(0);
          await expect(
            panel(page).getByRole("button", {
              name: "Retry profile discovery",
              exact: true,
            }),
          ).toHaveCount(0);
          measurements.push(
            await paint(notice, "Observed empty profile response"),
          );
        } else {
          const error = panel(page).getByRole("alert");
          await expect(error).toContainText("Availability is unknown");
          measurements.push(
            await paint(error, "Unknown malformed profile discovery"),
          );
          await activate(
            page,
            panel(page).getByRole("button", {
              name: "Retry profile discovery",
              exact: true,
            }),
          );
          const first = panel(page).getByRole("checkbox", {
            name: `Select profile ${actual.items[0].presentation.name}`,
            exact: true,
          });
          await expect(first).toBeVisible();
          await expect(first).toBeFocused();
          expect(reads).toBe(2);
        }
        const unchanged = await request(page, `/projects/${project.projectId}`);
        expect(unchanged.documents).toEqual(project.documents);
        expect(unchanged.revision).toBe(project.revision);
        expect(unchanged.manifest.profiles).toEqual(project.manifest.profiles);
        expect(writes).toBe(0);
        await info.attach("profile-observation.json", {
          body: JSON.stringify({
            viewport,
            mode,
            measurements,
            labelledTransportFixture: true,
            actualRegistryCount: actual.items.length,
            bindingWrites: writes,
            scope:
              "Controlled discovery response only; empty observation is not evidence that the actual registry has no profiles; no provider or execution authority",
          }),
          contentType: "application/json",
        });
      } finally {
        await page.unroute(pattern);
      }
    });
  }
  test(`profile bindings: foreign recovery preserves newer profile draft at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, info) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const project = await create(
        page,
        `Profile recovery context ${viewport.width}`,
      ),
      beforeRuns = await runs(page, project.projectId),
      entries = (await request(page, "/catalog")).items,
      entry = entries.find(
        (e: any) =>
          e.kind === "blueprint" && e.providerIds?.includes("studio.reference"),
      );
    expect(entry).toBeTruthy();
    await activate(
      page,
      page.getByRole("button", { name: "Catalog", exact: true }),
    );
    let fixture: { project: any; file: string; original: string } | undefined,
      committed: any,
      release!: () => void,
      ready = false,
      finished: Promise<void> | undefined;
    const gate = new Promise<void>((r) => (release = r)),
      createPattern = "**/api/v1/projects",
      recoveryPattern = "**/api/v1/projects/*/recoveries";
    await page.route(createPattern, async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const response = await route.fetch();
      expect(response.status()).toBe(201);
      const other = await response.json(),
        id = Object.keys(other.documents).find(
          (id) => parse(other.documents[id].content).kind === "System",
        )!,
        document = other.documents[id];
      expect(process.env.STUDIO_BROWSER_DATA).toBeTruthy();
      const root = realpathSync(process.env.STUDIO_BROWSER_DATA!),
        file = path.resolve(
          root,
          "projects",
          other.projectId,
          "revisions",
          String(other.revision),
          document.path,
        );
      expect(file.startsWith(root + path.sep)).toBe(true);
      expect(realpathSync(file)).toBe(file);
      expect(readFileSync(file, "utf8")).toBe(document.content);
      fixture = { project: other, file, original: document.content };
      writeFileSync(file, Buffer.from([0xff, 0xfe, 0x00, 0x64]));
      await route.fulfill({ response });
    });
    await page.route(recoveryPattern, async (route) => {
      if (
        route.request().method() !== "POST" ||
        !fixture ||
        new URL(route.request().url()).pathname !==
          `/api/v1/projects/${fixture.project.projectId}/recoveries`
      ) {
        await route.continue();
        return;
      }
      let finish!: () => void;
      finished = new Promise<void>((r) => (finish = r));
      try {
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        committed = await response.json();
        ready = true;
        await gate;
        await route.fulfill({ response });
      } finally {
        finish();
      }
    });
    try {
      await activate(
        page,
        page
          .getByRole("article")
          .filter({
            has: page.getByRole("heading", { name: entry.name, exact: true }),
          })
          .getByRole("button", { name: "Open as project", exact: true }),
      );
      const recovery = page.getByRole("group", {
        name: "Source recovery",
        exact: true,
      });
      await expect(recovery).toBeVisible();
      expect(fixture).toBeDefined();
      await environment(page);
      const checkbox = panel(page).getByRole("checkbox", {
        name: "Select profile Automotive terminology",
        exact: true,
      });
      await expect(checkbox).toBeVisible();
      await activate(
        page,
        recovery.getByRole("button", {
          name: `Restore committed revision ${fixture!.project.revision}`,
          exact: true,
        }),
      );
      await expect.poll(() => ready).toBe(true);
      await tabTo(page, checkbox);
      await page.keyboard.press("Space");
      await expect(checkbox).toBeChecked();
      release();
      await finished;
      await settle(page);
      const current = async () => ({
        panelCount: await panel(page).count(),
        checked: (await checkbox.count()) ? await checkbox.isChecked() : null,
        focused: (await checkbox.count())
          ? await checkbox.evaluate((n) => document.activeElement === n)
          : false,
        selectionLabel: await panel(page)
          .getByText(
            `Selected project: ${project.name} · revision ${project.revision}`,
            { exact: true },
          )
          .count(),
        storedProject: await page.evaluate(() =>
          localStorage.getItem("studio.projectId"),
        ),
      });
      await expect.soft.poll(current).toEqual({
        panelCount: 1,
        checked: true,
        focused: true,
        selectionLabel: 1,
        storedProject: project.projectId,
      });
      const saved = await request(page, `/projects/${project.projectId}`),
        recovered = await request(
          page,
          `/projects/${fixture!.project.projectId}`,
        );
      expect(saved.revision).toBe(project.revision);
      expect(saved.documents).toEqual(project.documents);
      expect(saved.manifest.profiles).toEqual(project.manifest.profiles);
      expect(committed.project.projectId).toBe(fixture!.project.projectId);
      expect(recovered.revision).toBe(fixture!.project.revision + 1);
      for (const [id, document] of Object.entries<any>(
        fixture!.project.documents,
      ))
        expect(recovered.documents[id].content).toBe(document.content);
      expect(await runs(page, project.projectId)).toEqual(beforeRuns);
      expect(await runs(page, recovered.projectId)).toEqual([]);
      await info.attach("profile-foreign-recovery.json", {
        body: JSON.stringify({
          viewport,
          activeProjectId: project.projectId,
          recoveredProjectId: recovered.projectId,
          measuredContext: await current(),
          backendRecoveryCommitted: true,
          profileDraftUnsubmitted: true,
          activeCanonicalUnchanged: true,
          noStart: true,
          scope:
            "Only newly owned test source made unreadable; real foreign recovery held after commit while active Environment profile checkbox changes",
        }),
        contentType: "application/json",
      });
    } finally {
      release();
      await finished;
      await page.unroute(createPattern);
      await page.unroute(recoveryPattern);
      if (fixture) writeFileSync(fixture.file, fixture.original);
    }
  });
  test(`profile bindings: discovery failure stays unknown and retries actual registry at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, info) => {
    test.setTimeout(60000);
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const project = await create(page, `Profile discovery ${viewport.width}`),
      beforeRuns = await runs(page, project.projectId);
    let reads = 0,
      writes = 0;
    page.on("request", (r) => {
      if (
        r.method() === "POST" &&
        new URL(r.url()).pathname.endsWith("/profile-bindings")
      )
        writes++;
    });
    const pattern = "**/api/v1/profiles";
    await page.route(pattern, async (route) => {
      reads++;
      if (reads === 1)
        await route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            code: "PROFILE_DISCOVERY_UNAVAILABLE",
            message: "Controlled registry transport failure",
            retryable: true,
          }),
        });
      else {
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        await route.fulfill({ response });
      }
    });
    try {
      await environment(page);
      await expect.poll(() => reads).toBe(1);
      await expect(panel(page).getByRole("alert")).toContainText(
        /unknown|unavailable|could not/i,
      );
      await expect(panel(page).getByRole("checkbox")).toHaveCount(0);
      await expect(bind(page)).toBeDisabled();
      await activate(
        page,
        panel(page).getByRole("button", {
          name: "Retry profile discovery",
          exact: true,
        }),
      );
      await expect(
        panel(page).getByRole("checkbox", {
          name: "Select profile Automotive terminology",
          exact: true,
        }),
      ).toBeVisible();
      expect(reads).toBe(2);
      await expect(panel(page).getByRole("alert")).toHaveCount(0);
      expect(writes).toBe(0);
      expect(
        (await request(page, `/projects/${project.projectId}`)).documents,
      ).toEqual(project.documents);
      expect(await runs(page, project.projectId)).toEqual(beforeRuns);
      await info.attach("profile-discovery.json", {
        body: JSON.stringify({
          viewport,
          controlledInitialStatus: 503,
          retryStatus: 200,
          actualRegistryRetried: true,
          observationsStayUnknownOnFailure: true,
          bindingWrites: writes,
          noStart: true,
          scope:
            "Labelled discovery transport failure then actual admitted registry; no provider installation or execution authority",
        }),
        contentType: "application/json",
      });
    } finally {
      await page.unroute(pattern);
    }
  });

  test(`profile bindings: committed reply cannot announce success on departed Home at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, info) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const project = await create(
        page,
        `Profile binding departure ${viewport.width}`,
      ),
      beforeRuns = await runs(page, project.projectId),
      beforeProviders = await request(page, "/providers"),
      beforePlan = await request(
        page,
        `/projects/${project.projectId}/compilations`,
        { revision: project.revision },
      ),
      entries = (await request(page, "/profiles")).items,
      selected = entries.find(
        (p: any) => p.namespace === "io.xverse.studio.domain.automotive",
      );
    expect(selected.presentation.name).toBe("Automotive terminology");
    expect(selected.executionAllowed).toBe(false);
    await environment(page);
    const checkbox = panel(page).getByRole("checkbox", {
      name: "Select profile Automotive terminology",
      exact: true,
    });
    await tabTo(page, checkbox);
    await page.keyboard.press("Space");
    await expect(checkbox).toBeChecked();
    let release!: () => void,
      finish!: () => void,
      ready = false,
      committed: any;
    const gate = new Promise<void>((r) => (release = r)),
      finished = new Promise<void>((r) => (finish = r)),
      pattern = `**/api/v1/projects/${project.projectId}/profile-bindings`;
    const writes: { ifMatch?: string; body: any }[] = [];
    await page.route(pattern, async (route) => {
      try {
        expect(route.request().method()).toBe("POST");
        writes.push({
          ifMatch: route.request().headers()["if-match"],
          body: route.request().postDataJSON(),
        });
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        committed = await response.json();
        ready = true;
        await gate;
        await route.fulfill({ response });
      } finally {
        finish();
      }
    });
    try {
      await activate(page, bind(page));
      await expect.poll(() => ready).toBe(true);
      expect(committed.projectId).toBe(project.projectId);
      expect(committed.revision).toBe(project.revision + 1);
      await activate(
        page,
        page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
      );
      await expect(
        page.getByRole("heading", { name: "Recent projects", exact: true }),
      ).toBeVisible();
      release();
      await finished;
      await settle(page);
      await expect.soft(page.locator(".project-header")).toHaveCount(0);
      await expect
        .soft(page.locator(".alerts .notice:not(.busy)"))
        .toHaveCount(0);
      const saved = await request(page, `/projects/${project.projectId}`);
      expect(writes).toEqual([
        {
          ifMatch: `"${project.revision}"`,
          body: {
            baseRevision: project.revision,
            profiles: [
              {
                profileId: selected.profileId,
                version: selected.version,
                schemaDigest: selected.schemaDigest,
                presentationDigest: selected.presentationDigest,
              },
            ],
          },
        },
      ]);
      expect(saved.revision).toBe(project.revision + 1);
      for (const [id, document] of Object.entries<any>(project.documents))
        expect(saved.documents[id]).toEqual(document);
      for (const [name, content] of Object.entries(project.supportingFiles))
        expect(saved.supportingFiles[name]).toBe(content);
      const added = Object.keys(saved.documents).filter(
        (id) => !(id in project.documents),
      );
      expect(added).toHaveLength(1);
      const resource = parse(saved.documents[added[0]].content);
      expect(resource.kind).toBe("Profile");
      expect(resource.spec.extensionNamespace).toBe(selected.namespace);
      expect(resource.metadata.version).toBe(selected.version);
      const lock = saved.manifest.profiles.find(
        (p: any) => p.namespace === selected.namespace,
      );
      expect(lock).toMatchObject({
        namespace: selected.namespace,
        version: selected.version,
        schemaDigest: selected.schemaDigest,
        presentationDigest: selected.presentationDigest,
      });
      expect(digest(saved.supportingFiles[lock.schemaPath])).toBe(
        lock.schemaDigest,
      );
      expect(digest(saved.supportingFiles[lock.presentationPath])).toBe(
        lock.presentationDigest,
      );
      for (const previous of project.manifest.profiles)
        expect(saved.manifest.profiles).toContainEqual(previous);
      expect(saved.manifest.profiles).toHaveLength(
        project.manifest.profiles.length + 1,
      );
      expect(
        (
          await request(page, `/projects/${project.projectId}/validations`, {
            revision: saved.revision,
          })
        ).valid,
      ).toBe(true);
      expect(
        (
          await request(page, `/projects/${project.projectId}/compilations`, {
            revision: saved.revision,
          })
        ).planDigest,
      ).toBe(beforePlan.planDigest);
      expect(await request(page, "/providers")).toEqual(beforeProviders);
      expect(await runs(page, project.projectId)).toEqual(beforeRuns);
      await info.attach("profile-binding-departure.json", {
        body: JSON.stringify({
          viewport,
          projectId: project.projectId,
          profileId: selected.profileId,
          committedRevision: saved.revision,
          originalDocumentsPreserved: true,
          additiveLocksPreserved: true,
          exactSidecarDigests: true,
          authoritativeValidation: true,
          executablePlanUnchanged: true,
          providerDiscoveryUnchanged: true,
          noStart: true,
          scope:
            "Actual additive presentation-only lock transaction held after commit; departed workspace must not display stale success",
        }),
        contentType: "application/json",
      });
    } finally {
      release();
      await finished;
      await page.unroute(pattern);
    }
  });
}
