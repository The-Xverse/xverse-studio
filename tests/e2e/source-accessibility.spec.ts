import { test, expect, type Locator, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 200; i++) {
    if (await target.evaluate((n) => document.activeElement === n)) return;
    await page.keyboard.press("Tab");
  }
  throw Error("Source control is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
async function choose(page: Page, target: Locator, value: string) {
  const enabled = await target
    .locator("option")
    .evaluateAll((nodes) =>
      nodes
        .filter((n) => !(n as HTMLOptionElement).disabled)
        .map((n) => (n as HTMLOptionElement).value),
    );
  const index = enabled.indexOf(value);
  expect(index).toBeGreaterThanOrEqual(0);
  await tabTo(page, target);
  await page.keyboard.press("Home");
  for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  await expect(target).toHaveValue(value);
}
const dialog = (page: Page) =>
  page.getByRole("dialog", { name: "Authored XDL source", exact: true });
const text = (page: Page) =>
  dialog(page).getByRole("textbox", { name: /^(XDL source|Edited draft)$/ });
const save = (page: Page) =>
  dialog(page).getByRole("button", {
    name: "Save source revision",
    exact: true,
  });
async function read(page: Page, id: string) {
  return page.request.get(`/api/v1/projects/${id}`).then((r) => r.json());
}
async function runIds(page: Page, id: string) {
  return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
    .filter((r: any) => r.projectId === id)
    .map((r: any) => r.runId)
    .sort();
}
const docId = (project: any, suffix: string): string =>
  Object.keys(project.documents).find((id) =>
    project.documents[id].path.endsWith("/" + suffix),
  )!;
const cache = (page: Page, projectId: string, id: string) =>
  page.evaluate(
    ({ projectId, id }) =>
      sessionStorage.getItem(`studio.draft.${projectId}.${id}`),
    { projectId, id },
  );
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
    if (!r.ok) throw Error("Owned source fixture creation failed");
    const p = await r.json();
    localStorage.setItem("studio.projectId", p.projectId);
    return p;
  }, name);
  await page.reload();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  return project;
}
async function open(page: Page, id: string) {
  await activate(
    page,
    page.getByRole("button", { name: "XDL source", exact: true }),
  );
  await choose(page, dialog(page).getByLabel("Resource", { exact: true }), id);
  await expect(text(page)).toBeEnabled();
}
async function append(page: Page, comment: string) {
  await tabTo(page, text(page));
  await page.keyboard.press("ControlOrMeta+End");
  await page.keyboard.insertText(`\n# ${comment}\n`);
  return text(page).inputValue();
}
async function holdPut(page: Page, projectId: string, id: string) {
  const pattern = `**/api/v1/projects/${projectId}/documents/${id}`;
  const started = performance.now(),
    observations: Record<string, unknown>[] = [];
  const observe = (stage: string, details: Record<string, unknown> = {}) => {
    if (observations.length < 64)
      observations.push({
        stage,
        elapsedMs: Math.round(performance.now() - started),
        ...details,
      });
  };
  let release!: () => void,
    ready = false,
    seen = false,
    actual: any = null,
    requestError: unknown = null,
    finished: Promise<void> | undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(pattern, async (route) => {
    if (seen || route.request().method() !== "PUT") {
      await route.continue();
      return;
    }
    seen = true;
    observe("request", { method: route.request().method(), documentId: id });
    let finish!: () => void;
    finished = new Promise<void>((resolve) => {
      finish = resolve;
    });
    try {
      const response = await route.fetch({ timeout: 30000 });
      actual = { status: response.status(), body: await response.json() };
      ready = true;
      observe("authoritative response", {
        status: actual.status,
        revision: actual.body.revision,
        code: actual.body.code,
      });
      await held;
      await route.fulfill({ response });
      observe("released");
    } catch (error) {
      requestError = new Error(
        "The owned source PUT did not return a usable response within its configured transport bounds.",
      );
      observe("request failed", {
        errorType: error instanceof Error ? error.name : "unknown",
      });
      throw requestError;
    } finally {
      finish();
    }
  });
  return {
    async ready() {
      // This is setup for the focus countercheck, not a source-save performance target.
      await expect
        .poll(
          () => {
            observe("waiting", { requestSeen: seen, responseReady: ready });
            return ready || requestError !== null;
          },
          {
            timeout: 30000,
            intervals: [100, 250, 500, 1000],
            message:
              "Owned source PUT must return before the focus-preservation countercheck",
          },
        )
        .toBe(true);
      if (requestError) throw requestError;
      return actual;
    },
    async release() {
      release();
      await finished;
    },
    async close() {
      release();
      try {
        await finished;
      } finally {
        await page.unroute(pattern);
        await test.info().attach("held-source-request-observation.json", {
          body: JSON.stringify({
            projectId,
            documentId: id,
            requestSeen: seen,
            responseReady: ready,
            status: actual?.status,
            observations,
            scope:
              "Bounded real source PUT setup timings, with unchanged source/focus assertions; no authentication headers or private state",
          }),
          contentType: "application/json",
        });
      }
    },
  };
}

async function geometry(target: Locator) {
  return target.evaluate((n) => {
    const box = n.getBoundingClientRect(),
      style = getComputedStyle(n);
    return {
      focused: document.activeElement === n,
      activeTag: document.activeElement?.tagName,
      box: box.toJSON(),
      viewport: { width: innerWidth, height: innerHeight },
      outline: style.outlineStyle,
      outlineWidth: parseFloat(style.outlineWidth),
    };
  });
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  for (const trigger of ["shortcut", "button"] as const) {
    test(`source accessibility: native undo redo and ${trigger} save at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      const project = await create(
          page,
          `Keyboard source ${trigger} ${viewport.width}`,
        ),
        pid = project.projectId,
        id = docId(project, "system.xdl.yaml"),
        runs = await runIds(page, pid);
      await open(page, id);
      const original = project.documents[id].content;
      const edited = await append(page, `source-${trigger}-${viewport.width}`);
      expect(edited).toBe(
        original + `\n# source-${trigger}-${viewport.width}\n`,
      );
      await page.keyboard.press("ControlOrMeta+z");
      await expect(text(page)).toHaveValue(original);
      await page.keyboard.press("ControlOrMeta+Shift+Z");
      await expect.soft(text(page)).toHaveValue(edited);
      const shortcutRedoWorked = (await text(page).inputValue()) === edited;
      if (!shortcutRedoWorked) {
        await activate(
          page,
          dialog(page).getByRole("button", { name: "Redo", exact: true }),
        );
        await expect(text(page)).toHaveValue(edited);
      }
      await expect
        .soft(text(page))
        .toHaveAccessibleDescription(/Exact authored content is retained/);
      const writes: { path: string; body: any }[] = [];
      page.on("request", (r) => {
        if (r.method() === "PUT")
          writes.push({
            path: new URL(r.url()).pathname,
            body: r.postDataJSON(),
          });
      });
      const response = page.waitForResponse(
        (r) =>
          new URL(r.url()).pathname ===
            `/api/v1/projects/${pid}/documents/${id}` &&
          r.request().method() === "PUT",
      );
      if (trigger === "shortcut") {
        await tabTo(page, text(page));
        await page.keyboard.press("ControlOrMeta+s");
      } else await activate(page, save(page));
      expect((await response).status()).toBe(200);
      await page.waitForLoadState("networkidle");
      await expect(text(page)).toBeEnabled();
      await expect(save(page)).toBeDisabled();
      await expect.soft(text(page)).toBeFocused();
      const focus = await geometry(text(page));
      expect.soft(focus.outline).not.toBe("none");
      expect.soft(focus.outlineWidth).toBeGreaterThan(0);
      expect.soft(focus.box.top).toBeGreaterThanOrEqual(0);
      expect.soft(focus.box.bottom).toBeLessThanOrEqual(viewport.height);
      await expect.poll(() => cache(page, pid, id)).toBe(null);
      const saved = await read(page, pid);
      expect(saved.revision).toBe(project.revision + 1);
      expect(saved.documents[id].content).toBe(edited);
      expect(Object.keys(saved.documents).sort()).toEqual(
        Object.keys(project.documents).sort(),
      );
      for (const key of Object.keys(project.documents))
        if (key !== id)
          expect(saved.documents[key].content).toBe(
            project.documents[key].content,
          );
      expect(writes).toEqual([
        {
          path: `/api/v1/projects/${pid}/documents/${id}`,
          body: { content: edited, format: "yaml" },
        },
      ]);
      const pair = await renderedContrast(
        dialog(page).locator(".field-hint"),
        "Source authoring guidance",
      );
      await page.keyboard.press("Escape");
      await open(page, id);
      await expect(text(page)).toHaveValue(edited);
      await expect(save(page)).toBeDisabled();
      await page.keyboard.press("Escape");
      const validation = page.waitForResponse(
        (r) =>
          new URL(r.url()).pathname === `/api/v1/projects/${pid}/validations` &&
          r.request().method() === "POST",
      );
      await activate(
        page,
        page.getByRole("button", { name: "Validate", exact: true }),
      );
      expect((await (await validation).json()).valid).toBe(true);
      expect(await runIds(page, pid)).toEqual(runs);
      await testInfo.attach("source-keyboard.json", {
        body: JSON.stringify({
          viewport,
          trigger,
          shortcutRedoWorked,
          focus,
          revisions: [project.revision, saved.revision],
          exactSubmittedSource: true,
          savedSourceDigest:
            "sha256:" + createHash("sha256").update(edited).digest("hex"),
          documentIdentitiesAndOtherBytesPreserved: true,
          recoveryCacheCleared: true,
          authoritativeValidation: true,
          ownProjectRunSetUnchanged: true,
          measurements: [pair],
          writes,
          scope:
            "Native source text edit and save only; no Start/live mutation",
        }),
        contentType: "application/json",
      });
      expect(pair.supported).toBe(true);
      if (pair.supported) expect(pair.ratio).toBeGreaterThanOrEqual(4.5);
    });
  }
  for (const mode of [
    "Home",
    "newer revision",
    "same document draft",
    "other document",
    "deliberate focus",
    "newer readiness",
  ] as const) {
    test(`source accessibility: late save preserves ${mode} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      const project = await create(
          page,
          `Late source ${mode} ${viewport.width}`,
        ),
        pid = project.projectId,
        id = docId(project, "system.xdl.yaml"),
        otherId = docId(project, "controller.xdl.yaml"),
        runs = await runIds(page, pid);
      await open(page, id);
      const submitted = await append(page, `held-source-${viewport.width}`),
        pending = await holdPut(page, pid, id);
      let newerText: string | null = null,
        history: string | null = null,
        readyId: string | null = null;
      try {
        await page.keyboard.press("ControlOrMeta+s");
        const actual = await pending.ready();
        expect(actual.status).toBe(200);
        if (mode !== "deliberate focus") await page.keyboard.press("Escape");
        if (mode === "Home" || mode === "newer revision") {
          await activate(
            page,
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          );
          await expect(
            page.getByRole("heading", { name: "Recent projects", exact: true }),
          ).toBeVisible();
        }
        if (mode === "newer revision") {
          await activate(
            page,
            page.locator(
              `.project-list-row[data-project-id="${pid}"] .project-open`,
            ),
          );
          await activate(
            page,
            page.getByRole("button", { name: "Parameters", exact: true }),
          );
          const duration = page.getByLabel("Duration");
          await tabTo(page, duration);
          await page.keyboard.press("ControlOrMeta+A");
          await page.keyboard.insertText("6");
          await activate(
            page,
            duration
              .locator("xpath=ancestor::form")
              .getByRole("button", { name: "Apply", exact: true }),
          );
          await expect(page.locator(".alerts")).toContainText("Draft saved");
          history = await page.evaluate(
            (pid) => sessionStorage.getItem("studio.graphHistory." + pid),
            pid,
          );
        }
        if (
          ["same document draft", "other document", "newer revision"].includes(
            mode,
          )
        ) {
          await open(page, mode === "other document" ? otherId : id);
          newerText = await append(page, `newer-${mode}-${viewport.width}`);
          await expect
            .poll(() =>
              cache(page, pid, mode === "other document" ? otherId : id),
            )
            .toBe(newerText);
        }
        if (mode === "deliberate focus")
          await tabTo(
            page,
            dialog(page).getByRole("button", {
              name: "Compare changes",
              exact: true,
            }),
          );
        if (mode === "newer readiness") {
          const validation = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname ===
                `/api/v1/projects/${pid}/validations` &&
              r.request().method() === "POST",
          );
          await activate(
            page,
            page.getByRole("button", { name: "Validate", exact: true }),
          );
          expect((await validation).status()).toBe(412);
          await expect(page.locator(".notice.busy")).toHaveCount(0);
          const readiness = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname ===
                `/api/v1/projects/${pid}/preflights` &&
              r.request().method() === "POST",
          );
          await activate(
            page,
            page.getByRole("button", { name: "Preflight & run", exact: true }),
          );
          const report = await (await readiness).json();
          expect(report.status).toBe("ready");
          readyId = report.preflightId;
          await activate(
            page,
            page.getByText("Frozen request identities", { exact: true }),
          );
          await expect(
            page.getByRole("dialog").getByText(readyId!, { exact: true }),
          ).toBeVisible();
        }
        await pending.release();
        await page.waitForLoadState("networkidle");
        if (mode === "Home")
          await expect
            .soft(
              page.getByRole("heading", {
                name: "Recent projects",
                exact: true,
              }),
            )
            .toBeVisible();
        if (newerText !== null) {
          await expect(text(page)).toHaveValue(newerText);
          await expect(text(page)).toBeFocused();
          await expect
            .poll(() =>
              cache(page, pid, mode === "other document" ? otherId : id),
            )
            .toBe(newerText);
        }
        if (mode === "newer revision") {
          await expect(page.locator(".workspace-context")).toContainText(
            `Draft revision ${project.revision + 2}`,
          );
          expect(
            await page.evaluate(
              (pid) => sessionStorage.getItem("studio.graphHistory." + pid),
              pid,
            ),
          ).toBe(history);
        }
        if (mode === "deliberate focus")
          await expect(
            dialog(page).getByRole("button", {
              name: "Compare changes",
              exact: true,
            }),
          ).toBeFocused();
        if (mode === "newer readiness")
          await expect
            .soft(page.getByRole("dialog").getByText(readyId!, { exact: true }))
            .toBeVisible();
        const saved = await read(page, pid);
        expect(saved.revision).toBe(
          project.revision + (mode === "newer revision" ? 2 : 1),
        );
        expect(saved.documents[id].content).toBe(submitted);
        expect(saved.documents[otherId].content).toBe(
          project.documents[otherId].content,
        );
        expect(await runIds(page, pid)).toEqual(runs);
        await testInfo.attach("source-completion.json", {
          body: JSON.stringify({
            mode,
            viewport,
            committedRevision: actual.body.revision,
            savedRevision: saved.revision,
            newerDraftPreserved: newerText !== null,
            newerHistory: history,
            readyId,
            activeTag: await page.evaluate(
              () => document.activeElement?.tagName,
            ),
            ownProjectRunSetUnchanged: true,
            scope:
              "Held real PUT response; preserve navigation/drafts/newer history/readiness and deliberate focus",
          }),
          contentType: "application/json",
        });
      } finally {
        await pending.close();
      }
    });
  }
  for (const departed of [false, true]) {
    test(`source accessibility: real conflict ${departed ? "after departure" : "and explicit recovery"} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      const project = await create(
          page,
          `Source conflict ${departed} ${viewport.width}`,
        ),
        pid = project.projectId,
        id = docId(project, "system.xdl.yaml"),
        runs = await runIds(page, pid);
      await open(page, id);
      const local = await append(page, `local-conflict-${viewport.width}`),
        external =
          project.documents[id].content +
          `\n# other-session-${viewport.width}\n`;
      const advanced = await page.evaluate(
        async ({ pid, id, revision, content }) => {
          const { csrfToken } = await fetch("/api/v1/session").then((r) =>
            r.json(),
          );
          const r = await fetch(`/api/v1/projects/${pid}/documents/${id}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrfToken,
              "If-Match": String(revision),
            },
            body: JSON.stringify({ content, format: "yaml" }),
          });
          if (!r.ok) throw Error("Owned other-session source fixture failed");
          return r.json();
        },
        { pid, id, revision: project.revision, content: external },
      );
      const pending = await holdPut(page, pid, id);
      let contrast: any = null;
      try {
        await page.keyboard.press("ControlOrMeta+s");
        expect((await pending.ready()).status).toBe(412);
        if (departed) {
          await page.keyboard.press("Escape");
          await activate(
            page,
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          );
        }
        await pending.release();
        await page.waitForLoadState("networkidle");
        expect((await read(page, pid)).documents).toEqual(advanced.documents);
        await expect.poll(() => cache(page, pid, id)).toBe(local);
        if (departed) {
          await expect(
            page.getByRole("heading", { name: "Recent projects", exact: true }),
          ).toBeVisible();
          await expect
            .soft(page.locator(".alerts").getByRole("alert"))
            .toHaveCount(0);
        } else {
          await expect(text(page)).toHaveValue(local);
          await expect(save(page)).toBeEnabled();
          await expect
            .soft(dialog(page).getByRole("alert"))
            .toContainText("REVISION_CONFLICT");
          await page.keyboard.press("Escape");
          await activate(
            page,
            page.getByRole("button", {
              name: "Load current revision",
              exact: true,
            }),
          );
          await expect(page.locator(".alerts")).toContainText(
            "Current revision loaded",
          );
          await open(page, id);
          await expect(text(page)).toHaveValue(local);
          await activate(
            page,
            dialog(page).getByRole("button", {
              name: "Compare changes",
              exact: true,
            }),
          );
          await expect(dialog(page).locator(".source-baseline")).toHaveText(
            external,
          );
          contrast = await renderedContrast(
            dialog(page).locator(".source-baseline"),
            "Saved source in conflict comparison",
          );
          await tabTo(page, text(page));
          const savedResponse = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname.endsWith(`/documents/${id}`) &&
              r.request().method() === "PUT",
          );
          await page.keyboard.press("ControlOrMeta+s");
          expect((await savedResponse).status()).toBe(200);
          await page.waitForLoadState("networkidle");
          const saved = await read(page, pid);
          expect(saved.revision).toBe(advanced.revision + 1);
          expect(saved.documents[id].content).toBe(local);
          await expect.poll(() => cache(page, pid, id)).toBe(null);
          const revisions = (
            await page.request
              .get(`/api/v1/projects/${pid}/revisions`)
              .then((r) => r.json())
          ).items;
          expect(
            revisions.find((r: any) => r.revision === advanced.revision)
              .documents[id].digest,
          ).toBe(
            "sha256:" + createHash("sha256").update(external).digest("hex"),
          );
        }
        expect(await runIds(page, pid)).toEqual(runs);
        await testInfo.attach("source-conflict.json", {
          body: JSON.stringify({
            viewport,
            departed,
            refusedStatus: 412,
            localDraftPreserved: true,
            beforeRevision: project.revision,
            advancedRevision: advanced.revision,
            finalRevision: (await read(page, pid)).revision,
            explicitRecovery: !departed,
            ownProjectRunSetUnchanged: true,
            measurements: contrast ? [contrast] : [],
            scope:
              "Actual stale source refusal; explicit current-revision comparison/retry; historical digest retained; no external-file adoption or Start",
          }),
          contentType: "application/json",
        });
        if (contrast) {
          expect(contrast.supported).toBe(true);
          if (contrast.supported)
            expect(contrast.ratio).toBeGreaterThanOrEqual(4.5);
        }
      } finally {
        await pending.close();
      }
    });
  }
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test(`source accessibility: UTF-8 recovery bound and real size refusal at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, testInfo) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await create(page, `Source byte bound ${viewport.width}`),
      pid = project.projectId,
      id = docId(project, "system.xdl.yaml"),
      runs = await runIds(page, pid);
    await open(page, id);
    const prefix = project.documents[id].content + "\n# ",
      remaining = 524288 - new TextEncoder().encode(prefix).length - 1;
    const bounded =
      prefix +
      "界".repeat(Math.floor(remaining / 3)) +
      "a".repeat(remaining % 3) +
      "\n";
    const digest = (value: string | null) =>
        createHash("sha256")
          .update(value ?? "")
          .digest("hex"),
      boundedDigest = digest(bounded);
    expect(new TextEncoder().encode(bounded).length).toBe(524288);
    await tabTo(page, text(page));
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.insertText(bounded);
    await expect
      .poll(async () => digest(await cache(page, pid, id)))
      .toBe(boundedDigest);
    await page.keyboard.press("ControlOrMeta+End");
    await page.keyboard.insertText("🔧");
    await expect.soft(dialog(page).getByRole("alert")).toContainText("512 KiB");
    await expect.soft
      .poll(async () => digest(await cache(page, pid, id)))
      .toBe(boundedDigest);
    const refused = bounded + "\n# " + "界".repeat(175000) + "\n";
    expect(new TextEncoder().encode(refused).length).toBeGreaterThan(1048576);
    expect(refused.length).toBeLessThan(524288);
    await tabTo(page, text(page));
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.insertText(refused);
    const response = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname.endsWith(`/documents/${id}`) &&
        r.request().method() === "PUT",
    );
    await page.keyboard.press("ControlOrMeta+s");
    expect((await response).status()).toBe(413);
    await page.waitForLoadState("networkidle");
    const failure = dialog(page)
      .locator('.error-banner[role="alert"]')
      .filter({ hasText: "LIMIT_EXCEEDED" });
    await expect(failure).toContainText("1 MiB");
    await expect.soft(failure).not.toContainText("load the current revision");
    expect(digest(await text(page).inputValue())).toBe(digest(refused));
    await expect(save(page)).toBeEnabled();
    expect((await read(page, pid)).documents).toEqual(project.documents);
    expect((await read(page, pid)).revision).toBe(project.revision);
    await page.keyboard.press("Escape");
    await open(page, id);
    expect(digest(await text(page).inputValue())).toBe(boundedDigest);
    await expect.soft(dialog(page)).toContainText("last cached text");
    expect(await runIds(page, pid)).toEqual(runs);
    await testInfo.attach("source-recovery-bound.json", {
      body: JSON.stringify({
        viewport,
        cachedBytes: 524288,
        overBoundaryBytes: 524292,
        retainedCacheDigest: "sha256:" + boundedDigest,
        refusalBytes: new TextEncoder().encode(refused).length,
        actualRefusedStatus: 413,
        unchangedCanonicalRevision: project.revision,
        canonicalDocumentsUnchanged: true,
        ownProjectRunSetUnchanged: true,
        scope:
          "Native Unicode source edit; exact UTF-8 browser recovery boundary and actual backend size refusal; no Start",
      }),
      contentType: "application/json",
    });
  });
  for (const failAt of ["open", "switch"] as const) {
    test(`source accessibility: recovery read failure on ${failAt} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      const project = await create(
          page,
          `Source storage ${failAt} ${viewport.width}`,
        ),
        pid = project.projectId,
        id = docId(project, "system.xdl.yaml"),
        otherId = docId(project, "controller.xdl.yaml"),
        runs = await runIds(page, pid);
      await open(page, id);
      const cached = await append(
        page,
        `preserve-unread-cache-${failAt}-${viewport.width}`,
      );
      await expect.poll(() => cache(page, pid, id)).toBe(cached);
      if (failAt === "open") await page.keyboard.press("Escape");
      await page.evaluate(() => {
        const original = Storage.prototype.getItem;
        (window as any).__sourceRecoveryRead = original;
        Storage.prototype.getItem = function (key) {
          if (key.startsWith("studio.draft."))
            throw new DOMException(
              "Controlled recovery read refusal",
              "SecurityError",
            );
          return original.call(this, key);
        };
      });
      try {
        if (failAt === "open") await open(page, id);
        else
          await choose(
            page,
            dialog(page).getByLabel("Resource", { exact: true }),
            otherId,
          );
        const shownId = failAt === "open" ? id : otherId;
        await expect(text(page)).toBeEnabled();
        await expect(text(page)).toHaveValue(
          project.documents[shownId].content,
        );
        await expect(dialog(page).getByRole("alert")).toContainText(
          "could not be read",
        );
        await append(page, "editable-with-unread-recovery");
        await expect(dialog(page).getByRole("alert")).toContainText(
          "could not be read",
        );
        await page.keyboard.press("Escape");
        expect(
          await page.evaluate(
            ({ pid, id }) =>
              (window as any).__sourceRecoveryRead.call(
                sessionStorage,
                `studio.draft.${pid}.${id}`,
              ),
            { pid, id },
          ),
        ).toBe(cached);
      } finally {
        await page.evaluate(() => {
          Storage.prototype.getItem = (window as any).__sourceRecoveryRead;
          delete (window as any).__sourceRecoveryRead;
        });
      }
      await open(page, otherId);
      await choose(
        page,
        dialog(page).getByLabel("Resource", { exact: true }),
        id,
      );
      await expect(text(page)).toHaveValue(cached);
      await expect(dialog(page)).toContainText(
        "Recovered an uncommitted draft",
      );
      const current = await read(page, pid);
      expect(current.revision).toBe(project.revision);
      expect(current.documents).toEqual(project.documents);
      expect(await runIds(page, pid)).toEqual(runs);
      await testInfo.attach("source-recovery-read.json", {
        body: JSON.stringify({
          viewport,
          failAt,
          fixture:
            "Browser Storage.prototype.getItem refusal scoped only to studio.draft.*",
          canonicalFallbackEditable: true,
          unreadCachedDraftPreserved: true,
          recoveryAfterReadRestored: true,
          canonicalRevisionUnchanged: true,
          ownProjectRunSetUnchanged: true,
          scope:
            "Controlled browser-storage failure; actual owned canonical Project unchanged; no platform/filesystem failure claim",
        }),
        contentType: "application/json",
      });
    });
  }
}
