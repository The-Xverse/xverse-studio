import { test, expect, type Page, type Locator } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, realpathSync } from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  // A removed error control can leave traversal after the persistent header.
  // Native reverse traversal reaches it without walking every recent-project row.
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
  await expect(target).toBeFocused();
  await page.keyboard.press("Enter");
}
const group = (page: Page) =>
  page.getByRole("group", { name: "Source recovery", exact: true });
const home = (page: Page) =>
  page.getByRole("button", { name: "X-Verse Studio home", exact: true });
const source = (page: Page) =>
  page.getByRole("button", { name: "XDL source", exact: true });
const digest = (value: string | Buffer) =>
  "sha256:" + createHash("sha256").update(value).digest("hex");
const read = (page: Page, pid: string) =>
  page.request.get(`/api/v1/projects/${pid}`).then((r) => r.json());
async function runs(page: Page, pid: string) {
  return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
    .filter((r: any) => r.projectId === pid)
    .map((r: any) => r.runId)
    .sort();
}
async function create(page: Page, name: string) {
  const project = await page.evaluate(async (name) => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const r = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ name }),
    });
    if (!r.ok) throw Error("Owned recovery project creation failed");
    const p = await r.json();
    localStorage.setItem("studio.projectId", p.projectId);
    return p;
  }, name);
  await page.reload();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  return project;
}
function ownedPath(...parts: string[]) {
  const data = process.env.STUDIO_BROWSER_DATA;
  expect(data).toBeTruthy();
  const root = realpathSync(data!);
  const file = path.resolve(root, ...parts);
  expect(file.startsWith(root + path.sep)).toBe(true);
  return file;
}
async function prepare(page: Page, name: string, broken = false) {
  const project = await create(page, name),
    pid = project.projectId,
    id = Object.keys(project.documents).find((id) =>
      project.documents[id].path.endsWith("/system.xdl.yaml"),
    )!,
    document = project.documents[id];
  const file = ownedPath(
    "projects",
    pid,
    "revisions",
    String(project.revision),
    document.path,
  );
  expect(realpathSync(file)).toBe(file);
  expect(readFileSync(file, "utf8")).toBe(document.content);
  const observed = broken
    ? Buffer.from([0xff, 0xfe, 0x00, 0x61])
    : Buffer.from(
        document.content + "\n# isolated owned external recovery fixture\n",
      );
  writeFileSync(file, observed);
  try {
    await page.reload();
    await expect(group(page)).toBeVisible();
  } catch (error) {
    writeFileSync(file, document.content);
    throw error;
  }
  return {
    project,
    pid,
    id,
    file,
    observed,
    restore() {
      writeFileSync(file, document.content);
    },
  };
}
const recoverButton = (page: Page, revision: number, action: string) =>
  group(page).getByRole("button", {
    name:
      action === "adopt_external"
        ? "Adopt external changes as a new revision"
        : `Restore committed revision ${revision}`,
    exact: true,
  });
async function backup(
  page: Page,
  fixture: Awaited<ReturnType<typeof prepare>>,
  result: any,
) {
  const { pid, id, observed, project, file } = fixture,
    rid = result.recovery.recoveryId,
    key = "document:" + id;
  const listed = (
    await page.request
      .get(`/api/v1/projects/${pid}/recoveries`)
      .then((r) => r.json())
  ).items;
  expect(listed).toHaveLength(1);
  expect(listed[0].recoveryId).toBe(rid);
  const entry = result.recovery.preserved[key];
  expect(entry.observedDigest).toBe(digest(observed));
  expect(entry.committedDigest).toBe(digest(project.documents[id].content));
  const preserved = await page.request
    .get(
      `/api/v1/projects/${pid}/recoveries/${rid}/preserved?key=${encodeURIComponent(key)}`,
    )
    .then((r) => r.json());
  expect(preserved.observedDigest).toBe(digest(observed));
  if (preserved.encoding === "utf-8")
    expect(preserved.content).toBe(observed.toString("utf8"));
  else {
    expect(preserved.encoding).toBe("binary");
    expect(preserved.content).toBe(null);
  }
  const kept = ownedPath("projects", pid, "recoveries", rid, entry.backupFile);
  expect(readFileSync(kept)).toEqual(observed);
  expect(readFileSync(file)).toEqual(observed);
  return {
    recoveryId: rid,
    committedDigest: entry.committedDigest,
    observedDigest: entry.observedDigest,
    preservedEncoding: preserved.encoding,
    exactBackupBytes: true,
    oldRevisionDirectoryUnchanged: true,
  };
}
async function hold(page: Page, pid: string) {
  const pattern = `**/api/v1/projects/${pid}/recoveries`;
  let seen = false,
    ready = false,
    result: any,
    release!: () => void,
    finished: Promise<void> | undefined;
  const gate = new Promise<void>((r) => (release = r));
  let writes: any[] = [];
  await page.route(pattern, async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    writes.push({
      body: route.request().postDataJSON(),
      ifMatch: route.request().headers()["if-match"],
    });
    if (seen) {
      await route.continue();
      return;
    }
    seen = true;
    let finish!: () => void;
    finished = new Promise((r) => (finish = r));
    try {
      const response = await route.fetch();
      result = { status: response.status(), body: await response.json() };
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
async function openCurrent(page: Page, pid: string, name: string) {
  await activate(page, home(page));
  await expect(
    page.getByRole("heading", { name: "Recent projects", exact: true }),
  ).toBeVisible();
  await activate(
    page,
    page.locator(`.project-list-row[data-project-id="${pid}"] .project-open`),
  );
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
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
const authoredDialog = (page: Page) =>
  page.getByRole("dialog", { name: "Authored XDL source", exact: true });
async function sourceDraft(page: Page, project: any, comment: string) {
  await activate(page, source(page));
  const resource = authoredDialog(page).getByLabel("Resource", { exact: true }),
    id = Object.keys(project.documents).find((id) =>
      project.documents[id].path.endsWith("/system.xdl.yaml"),
    )!;
  const values = await resource
    .locator("option")
    .evaluateAll((options) =>
      options
        .filter((n) => !(n as HTMLOptionElement).disabled)
        .map((n) => (n as HTMLOptionElement).value),
    );
  await tabTo(page, resource);
  await page.keyboard.press("Home");
  for (let i = 0; i < values.indexOf(id); i++)
    await page.keyboard.press("ArrowDown");
  await expect(resource).toHaveValue(id);
  const editor = authoredDialog(page).getByRole("textbox", {
    name: "XDL source",
    exact: true,
  });
  await tabTo(page, editor);
  await page.keyboard.press("ControlOrMeta+End");
  await page.keyboard.insertText(`\n# ${comment}\n`);
  const content = await editor.inputValue();
  return {
    id,
    content,
    editor,
    save: authoredDialog(page).getByRole("button", {
      name: "Save source revision",
      exact: true,
    }),
  };
}
async function renderedContext(page: Page, pid: string, id?: string) {
  return {
    projectName: await page.locator(".project-header h1").textContent(),
    storedProject: await page.evaluate(() =>
      localStorage.getItem("studio.projectId"),
    ),
    sourceModal: await authoredDialog(page).count(),
    documentId: (await page
      .locator('.source-editor select[aria-label="Resource"]')
      .count())
      ? await page
          .locator('.source-editor select[aria-label="Resource"]')
          .inputValue()
      : null,
    sourceDigest: (await page.locator(".source-textarea").count())
      ? digest(await page.locator(".source-textarea").inputValue())
      : null,
    draftDigest: id
      ? await page
          .evaluate(
            ({ pid, id }) =>
              sessionStorage.getItem(`studio.draft.${pid}.${id}`),
            { pid, id },
          )
          .then((v) => (v === null ? null : digest(v)))
      : null,
    operationErrors: await page
      .locator('.alerts .notice.error[role="alert"]')
      .count(),
  };
}
async function catalogTarget(
  page: Page,
  broken: boolean,
  holdLoad: boolean,
  holdCreate = false,
) {
  const entry = (
    await page.request.get("/api/v1/catalog").then((r) => r.json())
  ).items.find(
    (e: any) =>
      e.kind === "blueprint" && e.providerIds?.includes("studio.reference"),
  );
  expect(entry).toBeTruthy();
  await activate(
    page,
    page.getByRole("button", { name: "Catalog", exact: true }),
  );
  let fixture: Awaited<ReturnType<typeof prepare>> | undefined,
    release!: () => void,
    ready = false,
    loadStatus: number | undefined,
    finished: Promise<void> | undefined;
  const gate = new Promise<void>((r) => (release = r));
  const createPattern = "**/api/v1/projects",
    loadPattern = "**/api/v1/projects/*";
  await page.route(createPattern, async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    const project = await response.json(),
      pid = project.projectId,
      id = Object.keys(project.documents).find((id) =>
        project.documents[id].path.endsWith("/system.xdl.yaml"),
      )!,
      doc = project.documents[id];
    const file = ownedPath(
      "projects",
      pid,
      "revisions",
      String(project.revision),
      doc.path,
    );
    expect(realpathSync(file)).toBe(file);
    expect(readFileSync(file, "utf8")).toBe(doc.content);
    const observed = broken
      ? Buffer.from([0xff, 0xfe, 0x00, 0x64])
      : Buffer.from(doc.content);
    if (broken) writeFileSync(file, observed);
    fixture = {
      project,
      pid,
      id,
      file,
      observed,
      restore() {
        writeFileSync(file, doc.content);
      },
    };
    if (holdCreate) {
      let finish!: () => void;
      finished = new Promise((r) => (finish = r));
      try {
        loadStatus = response.status();
        ready = true;
        await gate;
        await route.fulfill({ response });
      } finally {
        finish();
      }
    } else await route.fulfill({ response });
  });
  if (holdLoad)
    await page.route(loadPattern, async (route) => {
      if (
        route.request().method() !== "GET" ||
        !fixture ||
        new URL(route.request().url()).pathname !==
          `/api/v1/projects/${fixture.pid}`
      ) {
        await route.continue();
        return;
      }
      let finish!: () => void;
      finished = new Promise((r) => (finish = r));
      try {
        const response = await route.fetch();
        loadStatus = response.status();
        ready = true;
        await gate;
        await route.fulfill({ response });
      } finally {
        finish();
      }
    });
  await activate(
    page,
    page
      .getByRole("article")
      .filter({
        has: page.getByRole("heading", { name: entry.name, exact: true }),
      })
      .getByRole("button", { name: "Open as project", exact: true }),
  );
  return {
    async fixture() {
      await expect.poll(() => !!fixture).toBe(true);
      return fixture!;
    },
    async ready() {
      await expect.poll(() => ready).toBe(true);
      return loadStatus;
    },
    async release() {
      release();
      await finished;
    },
    async close() {
      release();
      await finished;
      await page.unroute(createPattern);
      if (holdLoad) await page.unroute(loadPattern);
      fixture?.restore();
    },
  };
}
for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  for (const destination of ["Results", "Source", "Home"] as const) {
    test(`project context: cached run metadata respects ${destination} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const current = await create(
          page,
          `Cached run context ${destination} ${viewport.width}`,
        ),
        python =
          process.env.STUDIO_PYTHON ||
          path.join(
            process.cwd(),
            ".venv",
            process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
          ),
        fixture = JSON.parse(
          execFileSync(
            python,
            [
              "-I",
              path.join(
                process.cwd(),
                "tests/fixtures/evidence/create_recorded_evidence.py",
              ),
              "--data-dir",
              process.env.STUDIO_BROWSER_DATA!,
              "--project-id",
              current.projectId,
            ],
            { encoding: "utf8", timeout: 60000, maxBuffer: 1024 * 1024 },
          ),
        ),
        beforeRuns = await runs(page, current.projectId);
      expect(fixture.recordCount).toBeGreaterThan(200);
      expect(fixture.recordCount).toBeLessThanOrEqual(512);
      const evidence = await page.request
        .get(`/api/v1/runs/${fixture.runId}/evidence`)
        .then((r) => r.json());
      expect(evidence.integrity).toBe("valid");
      expect(evidence.items[0].recordCount).toBe(fixture.recordCount);
      await page.evaluate((f) => {
        localStorage.setItem("studio.lastRun", f.runId);
        localStorage.setItem("studio.lastRun." + f.projectId, f.runId);
      }, fixture);
      let release!: () => void,
        finish!: () => void,
        ready = false,
        intercepted = false;
      const gate = new Promise<void>((r) => (release = r)),
        finished = new Promise<void>((r) => (finish = r)),
        pattern = `**/api/v1/runs/${fixture.runId}`;
      await page.route(pattern, async (route) => {
        if (intercepted) {
          await route.continue();
          return;
        }
        intercepted = true;
        try {
          const response = await route.fetch();
          expect(response.status()).toBe(200);
          expect((await response.json()).projectId).toBe(current.projectId);
          ready = true;
          await gate;
          await route.fulfill({ response });
        } finally {
          finish();
        }
      });
      try {
        await page.reload();
        await expect.poll(() => ready).toBe(true);
        if (destination === "Results")
          await activate(
            page,
            page.getByRole("tab", { name: /^Results(?: \d+)?$/ }),
          );
        else if (destination === "Source") await activate(page, source(page));
        else await activate(page, home(page));
        release();
        await finished;
        await settle(page);
        if (destination !== "Home") {
          if (destination === "Source") {
            await expect(
              page.getByRole("dialog", { name: /XDL source/ }),
            ).toBeVisible();
            await page.keyboard.press("Escape");
            await activate(
              page,
              page.getByRole("tab", { name: /^Results(?: \d+)?$/ }),
            );
          }
          await expect(
            page.getByText("Recorded fixture scope", { exact: true }),
          ).toBeVisible();
          await expect(
            page.locator(".results-view .run-identity code").first(),
          ).toHaveText(fixture.runId);
          await expect(
            page.getByRole("button", { name: "Stop", exact: true }),
          ).toHaveCount(0);
        } else {
          await expect(page.locator(".project-header")).toHaveCount(0);
          await expect(
            page.getByText("Recorded fixture scope", { exact: true }),
          ).toHaveCount(0);
        }
        expect((await read(page, current.projectId)).documents).toEqual(
          current.documents,
        );
        expect(await runs(page, current.projectId)).toEqual(beforeRuns);
        await info.attach("project-context-cached-run.json", {
          body: JSON.stringify({
            viewport,
            destination,
            projectId: current.projectId,
            runId: fixture.runId,
            integrity: evidence.integrity,
            sourceRecords: fixture.recordCount,
            heldActualMetadataRead: true,
            noStart: true,
            scope:
              "Trusted inert registered journal fixture; metadata may restore within its active project after Results navigation but cannot recapture Home; no process/provider/device authority",
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
  for (const mode of [
    "source draft",
    "source save",
    "parameter draft",
  ] as const) {
    test(`project context: foreign recovery preserves newer ${mode} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const current = await create(
          page,
          `Active context ${mode} ${viewport.width}`,
        ),
        beforeRuns = await runs(page, current.projectId),
        target = await catalogTarget(page, true, false);
      let pending: Awaited<ReturnType<typeof hold>> | undefined;
      try {
        const other = await target.fixture();
        await expect(group(page)).toBeVisible();
        await expect(group(page)).toHaveAccessibleDescription(
          new RegExp(other.pid),
        );
        await expect(group(page).locator(":scope > p").first()).toContainText(
          other.project.name,
        );
        const contrast = await renderedContrast(
          group(page).locator(":scope > p").first(),
          "Named foreign recovery target",
        );
        expect(contrast.supported).toBe(true);
        if (contrast.supported)
          expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
        await activate(
          page,
          page.getByRole("button", { name: "Back to workspace", exact: true }),
        );
        await expect(
          page.getByRole("heading", { name: current.name, exact: true }),
        ).toBeVisible();
        pending = await hold(page, other.pid);
        await activate(
          page,
          recoverButton(page, other.project.revision, "restore_revision"),
        );
        const committed = await pending.ready();
        expect(committed.status).toBe(200);
        let authored: Awaited<ReturnType<typeof sourceDraft>> | undefined;
        if (mode === "parameter draft") {
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
          await page.keyboard.insertText("7");
          await expect(duration).toHaveValue("7");
        } else {
          authored = await sourceDraft(
            page,
            current,
            `newer-A-${mode}-${viewport.width}`,
          );
          await expect
            .poll(() =>
              page.evaluate(
                ({ pid, id }) =>
                  sessionStorage.getItem(`studio.draft.${pid}.${id}`),
                { pid: current.projectId, id: authored!.id },
              ),
            )
            .toBe(authored.content);
          if (mode === "source save") {
            const reply = page.waitForResponse(
              (r) =>
                new URL(r.url()).pathname ===
                  `/api/v1/projects/${current.projectId}/documents/${authored!.id}` &&
                r.request().method() === "PUT",
            );
            await page.keyboard.press("ControlOrMeta+s");
            expect((await reply).status()).toBe(200);
            await expect.soft(authored.save).toBeDisabled();
          }
        }
        await pending.release();
        await settle(page);
        if (authored) {
          await expect.soft
            .poll(() => renderedContext(page, current.projectId, authored!.id))
            .toEqual({
              projectName: current.name,
              storedProject: current.projectId,
              sourceModal: 1,
              documentId: authored.id,
              sourceDigest: digest(authored.content),
              draftDigest:
                mode === "source save" ? null : digest(authored.content),
              operationErrors: 0,
            });
          await expect.soft(authored.editor).toBeFocused();
        } else {
          await expect
            .soft(page.locator(".project-header h1"))
            .toHaveText(current.name);
          await expect
            .soft(
              page.getByRole("spinbutton", { name: "Duration s", exact: true }),
            )
            .toHaveValue("7");
          expect(
            await page.evaluate(() => localStorage.getItem("studio.projectId")),
          ).toBe(current.projectId);
        }
        const saved = await read(page, current.projectId);
        expect(saved.revision).toBe(
          current.revision + (mode === "source save" ? 1 : 0),
        );
        for (const id of Object.keys(current.documents))
          expect(saved.documents[id].content).toBe(
            authored && mode === "source save" && id === authored.id
              ? authored.content
              : current.documents[id].content,
          );
        expect((await read(page, other.pid)).revision).toBe(
          other.project.revision + 1,
        );
        const preserved = await backup(page, other, committed.body);
        expect(await runs(page, current.projectId)).toEqual(beforeRuns);
        expect(await runs(page, other.pid)).toEqual([]);
        await info.attach("project-context-recovery.json", {
          body: JSON.stringify({
            viewport,
            mode,
            activeProjectId: current.projectId,
            recoveredProjectId: other.pid,
            distinctProjects: true,
            activeRevision: saved.revision,
            independentRecoveryCommitted: true,
            preserved,
            contrast,
            ownProjectRunSetsUnchanged: true,
            scope:
              "Real foreign owned recovery held after commit; preserve newer authoring intent in still-rendered active project; no Start",
          }),
          contentType: "application/json",
        });
      } finally {
        await pending?.close();
        await target.close();
      }
    });
  }
  for (const broken of [false, true]) {
    test(`project context: obsolete ${broken ? "failed" : "successful"} load preserves newer source save at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const current = await create(
          page,
          `Current load context ${broken} ${viewport.width}`,
        ),
        beforeRuns = await runs(page, current.projectId),
        target = await catalogTarget(page, broken, true);
      try {
        const other = await target.fixture();
        expect(await target.ready()).toBe(broken ? 409 : 200);
        await activate(
          page,
          page.getByRole("button", { name: "Back to workspace", exact: true }),
        );
        await expect(
          page.getByRole("heading", { name: current.name, exact: true }),
        ).toBeVisible();
        const authored = await sourceDraft(
          page,
          current,
          `newer-source-before-load-${broken}-${viewport.width}`,
        );
        const reply = page.waitForResponse(
          (r) =>
            new URL(r.url()).pathname ===
              `/api/v1/projects/${current.projectId}/documents/${authored.id}` &&
            r.request().method() === "PUT",
        );
        await page.keyboard.press("ControlOrMeta+s");
        expect((await reply).status()).toBe(200);
        await expect.soft(authored.save).toBeDisabled();
        await target.release();
        await settle(page);
        await expect.soft
          .poll(() => renderedContext(page, current.projectId, authored.id))
          .toEqual({
            projectName: current.name,
            storedProject: current.projectId,
            sourceModal: 1,
            documentId: authored.id,
            sourceDigest: digest(authored.content),
            draftDigest: null,
            operationErrors: 0,
          });
        const saved = await read(page, current.projectId);
        expect(saved.revision).toBe(current.revision + 1);
        expect(saved.documents[authored.id].content).toBe(authored.content);
        expect(readFileSync(other.file)).toEqual(other.observed);
        expect(
          (
            await page.request
              .get(`/api/v1/projects/${other.pid}/recoveries`)
              .then((r) => r.json())
          ).items,
        ).toEqual([]);
        expect(await runs(page, current.projectId)).toEqual(beforeRuns);
        expect(await runs(page, other.pid)).toEqual([]);
        await info.attach("project-context-load.json", {
          body: JSON.stringify({
            viewport,
            broken,
            loadStatus: broken ? 409 : 200,
            activeProjectId: current.projectId,
            loadTargetId: other.pid,
            sourceCommitAcknowledged: true,
            newerModalPreserved: true,
            ownProjectRunSetsUnchanged: true,
            scope:
              "Held actual load response and actual source PUT; obsolete creation continuation/error must not change newer authoring context; no Start",
          }),
          contentType: "application/json",
        });
      } finally {
        await target.close();
      }
    });
  }
  test(`project context: obsolete creation reply preserves newer source save at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const current = await create(
        page,
        `Current creation context ${viewport.width}`,
      ),
      beforeRuns = await runs(page, current.projectId),
      target = await catalogTarget(page, false, false, true);
    try {
      const other = await target.fixture();
      expect(await target.ready()).toBe(201);
      await activate(
        page,
        page.getByRole("button", { name: "Back to workspace", exact: true }),
      );
      const authored = await sourceDraft(
        page,
        current,
        `newer-source-before-create-${viewport.width}`,
      );
      const reply = page.waitForResponse(
        (r) =>
          new URL(r.url()).pathname ===
            `/api/v1/projects/${current.projectId}/documents/${authored.id}` &&
          r.request().method() === "PUT",
      );
      await page.keyboard.press("ControlOrMeta+s");
      expect((await reply).status()).toBe(200);
      await expect(authored.save).toBeDisabled();
      await target.release();
      await settle(page);
      expect(
        await renderedContext(page, current.projectId, authored.id),
      ).toEqual({
        projectName: current.name,
        storedProject: current.projectId,
        sourceModal: 1,
        documentId: authored.id,
        sourceDigest: digest(authored.content),
        draftDigest: null,
        operationErrors: 0,
      });
      await expect(authored.editor).toBeFocused();
      const saved = await read(page, current.projectId);
      expect(saved.revision).toBe(current.revision + 1);
      expect(saved.documents[authored.id].content).toBe(authored.content);
      expect((await read(page, other.pid)).documents).toEqual(
        other.project.documents,
      );
      expect(await runs(page, current.projectId)).toEqual(beforeRuns);
      expect(await runs(page, other.pid)).toEqual([]);
      await info.attach("project-context-creation.json", {
        body: JSON.stringify({
          viewport,
          activeProjectId: current.projectId,
          createdProjectId: other.pid,
          createdProjectRetained: true,
          newerSourceSaveAcknowledged: true,
          newerModalAndFocusPreserved: true,
          noStart: true,
        }),
        contentType: "application/json",
      });
    } finally {
      await target.close();
    }
  });
  test(`project context: newest creation intent wins over earlier completion at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const current = await create(
        page,
        `Overlapping creation context ${viewport.width}`,
      ),
      beforeRuns = await runs(page, current.projectId);
    await activate(
      page,
      page.getByRole("button", { name: "Catalog", exact: true }),
    );
    const entry = (
      await page.request.get("/api/v1/catalog").then((r) => r.json())
    ).items.find(
      (e: any) =>
        e.kind === "blueprint" && e.providerIds?.includes("studio.reference"),
    );
    const control = page
      .getByRole("article")
      .filter({
        has: page.getByRole("heading", { name: entry.name, exact: true }),
      })
      .getByRole("button", { name: "Open as project", exact: true });
    const pending: {
      project: any;
      release: () => void;
      finished: Promise<void>;
    }[] = [];
    const pattern = "**/api/v1/projects";
    await page.route(pattern, async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const response = await route.fetch();
      expect(response.status()).toBe(201);
      const project = await response.json();
      let release!: () => void, finish!: () => void;
      const gate = new Promise<void>((r) => (release = r)),
        finished = new Promise<void>((r) => (finish = r));
      pending.push({ project, release, finished });
      try {
        await gate;
        await route.fulfill({ response });
      } finally {
        finish();
      }
    });
    try {
      await activate(page, control);
      await expect.poll(() => pending.length).toBe(1);
      await activate(page, control);
      await expect.poll(() => pending.length).toBe(2);
      const metadata = page.waitForResponse(
        (r) =>
          new URL(r.url()).pathname === "/api/v1/projects" &&
          r.request().method() === "GET",
      );
      pending[0].release();
      await pending[0].finished;
      expect((await metadata).status()).toBe(200);
      // Let the earlier creation's metadata continuation run while the newer POST is held.
      await page.evaluate(
        () =>
          new Promise<void>((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
          ),
      );
      pending[1].release();
      await pending[1].finished;
      await settle(page);
      const accepted = pending[1].project;
      await expect(page.locator(".project-header h1")).toHaveText(
        accepted.name,
      );
      expect(
        await page.evaluate(() => localStorage.getItem("studio.projectId")),
      ).toBe(accepted.projectId);
      expect(accepted.projectId).not.toBe(pending[0].project.projectId);
      for (const held of pending) {
        expect((await read(page, held.project.projectId)).documents).toEqual(
          held.project.documents,
        );
        expect(await runs(page, held.project.projectId)).toEqual([]);
      }
      expect((await read(page, current.projectId)).documents).toEqual(
        current.documents,
      );
      expect(await runs(page, current.projectId)).toEqual(beforeRuns);
      await info.attach("project-context-newest-creation.json", {
        body: JSON.stringify({
          viewport,
          originalProjectId: current.projectId,
          creationOrder: pending.map((p) => p.project.projectId),
          acceptedProjectId: accepted.projectId,
          completionOrder:
            "Earlier response released while newer response remains held",
          bothProjectsPreserved: true,
          noStart: true,
        }),
        contentType: "application/json",
      });
    } finally {
      for (const held of pending) held.release();
      await Promise.all(pending.map((p) => p.finished));
      await page.unroute(pattern);
    }
  });
  for (const failed of [false, true]) {
    test(`project context: obsolete startup ${failed ? "failure" : "success"} preserves Home at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, info) => {
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const current = await create(
          page,
          `Startup context ${failed} ${viewport.width}`,
        ),
        beforeRuns = await runs(page, current.projectId);
      let release!: () => void,
        finish!: () => void,
        ready = false;
      const gate = new Promise<void>((r) => (release = r)),
        finished = new Promise<void>((r) => (finish = r)),
        pattern = "**/api/v1/providers";
      await page.route(pattern, async (route) => {
        try {
          const response = await route.fetch();
          expect(response.status()).toBe(200);
          ready = true;
          await gate;
          if (failed)
            await route.fulfill({
              status: 503,
              contentType: "application/json",
              body: JSON.stringify({
                code: "PROVIDER_DISCOVERY_UNAVAILABLE",
                message: "Controlled startup metadata failure",
                retryable: true,
              }),
            });
          else await route.fulfill({ response });
        } finally {
          finish();
        }
      });
      try {
        await page.reload();
        await expect.poll(() => ready).toBe(true);
        await activate(page, home(page));
        release();
        await finished;
        await settle(page);
        await expect(page.locator(".project-header")).toHaveCount(0);
        await expect(
          page.locator('.alerts .notice.error[role="alert"]'),
        ).toHaveCount(0);
        expect(
          await page.evaluate(() => localStorage.getItem("studio.projectId")),
        ).toBe(current.projectId);
        expect((await read(page, current.projectId)).documents).toEqual(
          current.documents,
        );
        expect(await runs(page, current.projectId)).toEqual(beforeRuns);
        await info.attach("project-context-startup.json", {
          body: JSON.stringify({
            viewport,
            failed,
            originalProviderReadStatus: 200,
            releasedStatus: failed ? 503 : 200,
            newerHomePreserved: true,
            projectUnchanged: true,
            scope: failed
              ? "Controlled HTTP failure of startup metadata after explicit Home"
              : "Held actual successful startup metadata after explicit Home",
            noStart: true,
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
}
