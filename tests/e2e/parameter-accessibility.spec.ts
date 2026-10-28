import { test, expect, type Locator, type Page } from "@playwright/test";
import { parse } from "yaml";
import { connectStudio } from "./connect-studio";
import { renderedContrast } from "./contrast";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 180; i++) {
    if (await target.evaluate((node) => document.activeElement === node))
      return;
    await page.keyboard.press("Tab");
  }
  throw Error("Parameter control is unreachable through native Tab order");
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
async function type(page: Page, target: Locator, value: string) {
  await tabTo(page, target);
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.insertText(value);
}
const duration = (page: Page) => page.getByLabel("Duration");
const apply = (input: Locator) =>
  input
    .locator("xpath=ancestor::form")
    .getByRole("button", { name: "Apply", exact: true });
async function create(
  page: Page,
  name: string,
  beforeReload?: (id: string) => Promise<void>,
) {
  const project = await page.evaluate(async (name) => {
    const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
    const response = await fetch("/api/v1/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) throw Error("Owned parameter fixture creation failed");
    const project = await response.json();
    localStorage.setItem("studio.projectId", project.projectId);
    return project;
  }, name);
  await beforeReload?.(project.projectId);
  await page.reload();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  await activate(
    page,
    page.getByRole("button", { name: "Parameters", exact: true }),
  );
  return project;
}
async function read(page: Page, id: string) {
  return page.request.get(`/api/v1/projects/${id}`).then((r) => r.json());
}
async function runIds(page: Page, id: string) {
  return (await page.request.get("/api/v1/runs").then((r) => r.json())).items
    .filter((r: any) => r.projectId === id)
    .map((r: any) => r.runId)
    .sort();
}
function scenario(project: any) {
  const document: any = Object.values(project.documents).find((d: any) =>
    d.path.endsWith("/scenario.xdl.yaml"),
  );
  return parse(document.content);
}
function value(project: any, parameterId: string) {
  return scenario(project).extensions["io.xverse.experiment"].parameters.find(
    (p: any) => p.id === parameterId,
  ).value;
}
async function holdResponse(
  page: Page,
  id: string,
  suffix = "edits",
  method = "POST",
) {
  let release!: () => void,
    ready = false,
    seen = false,
    actual: any = null,
    finished: Promise<void> | undefined;
  const pattern = `**/api/v1/projects/${id}/${suffix}`,
    held = new Promise<void>((resolve) => {
      release = resolve;
    });
  await page.route(pattern, async (route) => {
    if (seen || route.request().method() !== method) {
      await route.continue();
      return;
    }
    seen = true;
    let finish!: () => void;
    finished = new Promise<void>((resolve) => {
      finish = resolve;
    });
    try {
      const response = await route.fetch();
      actual = { status: response.status(), body: await response.json() };
      ready = true;
      await held;
      await route.fulfill({ response });
    } finally {
      finish();
    }
  });
  return {
    async ready() {
      await expect.poll(() => ready).toBe(true);
      return actual;
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
async function geometry(input: Locator) {
  return input.evaluate((node) => {
    const box = node.getBoundingClientRect(),
      style = getComputedStyle(node);
    return {
      focused: document.activeElement === node,
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
  test(`parameter accessibility: native range recovery and save at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, testInfo) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await create(page, `Keyboard parameter ${viewport.width}`),
      id = project.projectId,
      beforeRuns = await runIds(page, id);
    const writes: { path: string; body: any }[] = [];
    page.on("request", (r) => {
      if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
        writes.push({
          path: new URL(r.url()).pathname,
          body: r.postDataJSON(),
        });
    });
    const input = duration(page);
    await expect(input).toHaveAttribute("max", "30");
    await type(page, input, "31");
    await activate(page, apply(input));
    await expect(input).toBeFocused();
    expect(
      await input.evaluate(
        (n) => (n as HTMLInputElement).validity.rangeOverflow,
      ),
    ).toBe(true);
    expect(writes).toEqual([]);
    const afterRefusal = await read(page, id);
    expect(afterRefusal.revision).toBe(project.revision);
    expect(afterRefusal.documents).toEqual(project.documents);
    await expect
      .soft(input)
      .toHaveAccessibleDescription(/Requested simulation horizon/);
    await type(page, input, "6");
    const savedResponse = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === `/api/v1/projects/${id}/edits` &&
        r.request().method() === "POST",
    );
    await activate(page, apply(input));
    const response = await savedResponse;
    expect(response.status()).toBe(200);
    const saved = await response.json();
    await expect(page.locator(".alerts")).toContainText("Draft saved");
    await expect(apply(input)).toBeDisabled();
    const focus = await geometry(input);
    await expect.soft(input).toBeFocused();
    expect.soft(focus.outline).not.toBe("none");
    expect.soft(focus.outlineWidth).toBeGreaterThan(0);
    expect.soft(focus.box.top).toBeGreaterThanOrEqual(0);
    expect.soft(focus.box.bottom).toBeLessThanOrEqual(viewport.height);
    expect(saved.revision).toBe(project.revision + 1);
    expect(value(saved, "duration")).toBe(6);
    expect(writes).toEqual([
      {
        path: `/api/v1/projects/${id}/edits`,
        body: {
          baseRevision: project.revision,
          edits: [{ kind: "set_parameter", parameterId: "duration", value: 6 }],
        },
      },
    ]);
    for (const [key, document] of Object.entries(project.documents) as [
      string,
      any,
    ][])
      if (!document.path.endsWith("/scenario.xdl.yaml"))
        expect(saved.documents[key].content).toBe(document.content);
    const expected = scenario(project);
    expected.extensions["io.xverse.experiment"].parameters.find(
      (p: any) => p.id === "duration",
    ).value = 6;
    expect(scenario(saved)).toEqual(expected);
    const validation = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === `/api/v1/projects/${id}/validations` &&
        r.request().method() === "POST",
    );
    await activate(
      page,
      page.getByRole("button", { name: "Validate", exact: true }),
    );
    expect((await (await validation).json()).valid).toBe(true);
    expect(await runIds(page, id)).toEqual(beforeRuns);
    const pair = await renderedContrast(
      input.locator("xpath=ancestor::form").locator(".field-hint"),
      "Duration purpose and constraint guidance",
    );
    await testInfo.attach("parameter-keyboard.json", {
      body: JSON.stringify({
        viewport,
        platform: process.platform,
        browser: await page.context().browser()?.version(),
        focus,
        revisions: [project.revision, saved.revision],
        nativeRangeRejected: true,
        canonicalDuration: value(saved, "duration"),
        otherDocumentsByteIdentical: true,
        otherScenarioContentPreserved: true,
        authoritativeValidation: true,
        ownProjectRunSetUnchanged: true,
        measurements: [pair],
        writes,
        scope: "Native authored parameter edit only; no live mutation or Start",
      }),
      contentType: "application/json",
    });
    expect(pair.supported).toBe(true);
    if (pair.supported) expect(pair.ratio).toBeGreaterThanOrEqual(4.5);
  });
  for (const mode of [
    "Home",
    "other project",
    "newer head",
    "newer same-field draft",
    "reverted same-field draft",
    "other field draft",
    "deliberate focus",
    "newer readiness",
  ] as const) {
    test(`parameter accessibility: late save preserves ${mode} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      const project = await create(
          page,
          `Late parameter ${mode} ${viewport.width}`,
        ),
        id = project.projectId,
        runs = await runIds(page, id);
      const other =
        mode === "other project"
          ? await page.evaluate(async (name) => {
              const { csrfToken } = await fetch("/api/v1/session").then((r) =>
                r.json(),
              );
              const r = await fetch("/api/v1/projects", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-CSRF-Token": csrfToken,
                },
                body: JSON.stringify({ name }),
              });
              if (!r.ok) throw Error("Second owned parameter fixture failed");
              return r.json();
            }, `Other parameter project ${viewport.width}`)
          : null;
      const otherRuns = other ? await runIds(page, other.projectId) : null;
      if (other) {
        // Finish API fixture setup before the keyboard journey. Reload the first
        // project so its initial Home list includes both prepared projects.
        await page.reload();
        await expect(
          page.getByRole("heading", { name: project.name, exact: true }),
        ).toBeVisible();
        await activate(
          page,
          page.getByRole("button", { name: "Parameters", exact: true }),
        );
      }
      await type(page, duration(page), "6");
      const pending = await holdResponse(page, id);
      let newerHistory: string | null = null,
        readyId: string | null = null;
      try {
        await activate(page, apply(duration(page)));
        const actual = await pending.ready();
        expect(actual.status).toBe(200);
        const home = page.getByRole("button", {
          name: "X-Verse Studio home",
          exact: true,
        });
        if (
          mode === "Home" ||
          mode === "newer head" ||
          mode === "other project"
        ) {
          await activate(page, home);
          await expect(
            page.getByRole("heading", { name: "Recent projects", exact: true }),
          ).toBeVisible();
        }
        if (mode === "other project") {
          await activate(
            page,
            page.locator(
              `.project-list-row[data-project-id="${other.projectId}"] .project-open`,
            ),
          );
          await activate(
            page,
            page.getByRole("button", { name: "Parameters", exact: true }),
          );
          await type(page, duration(page), "8");
        }
        if (mode === "newer head") {
          await activate(
            page,
            page.locator(
              `.project-list-row[data-project-id="${id}"] .project-open`,
            ),
          );
          if (!(await duration(page).isVisible()))
            await activate(
              page,
              page.getByRole("button", { name: "Parameters", exact: true }),
            );
          await type(page, duration(page), "7");
          await activate(page, apply(duration(page)));
          await expect(page.locator(".alerts")).toContainText("Draft saved");
          expect(value(await read(page, id), "duration")).toBe(7);
          newerHistory = await page.evaluate(
            (id) => sessionStorage.getItem("studio.graphHistory." + id),
            id,
          );
        }
        if (mode === "newer same-field draft")
          await type(page, duration(page), "7");
        if (mode === "reverted same-field draft")
          await type(page, duration(page), "5");
        if (mode === "other field draft")
          await type(page, page.getByLabel("Target", { exact: false }), "2.5");
        if (mode === "deliberate focus") await tabTo(page, home);
        if (mode === "newer readiness") {
          const staleValidation = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname ===
                `/api/v1/projects/${id}/validations` &&
              r.request().method() === "POST",
          );
          await activate(
            page,
            page.getByRole("button", { name: "Validate", exact: true }),
          );
          expect((await staleValidation).status()).toBe(412);
          await expect(page.locator(".notice.busy")).toHaveCount(0);
          const readiness = page.waitForResponse(
            (r) =>
              new URL(r.url()).pathname ===
                `/api/v1/projects/${id}/preflights` &&
              r.request().method() === "POST",
          );
          await activate(
            page,
            page.getByRole("button", { name: "Preflight & run", exact: true }),
          );
          const report = await (await readiness).json();
          expect(report.status).toBe("ready");
          readyId = report.preflightId;
          await expect(
            page.getByRole("dialog", {
              name: "Execution preflight",
              exact: true,
            }),
          ).toBeVisible();
          await activate(
            page,
            page.getByText("Frozen request identities", { exact: true }),
          );
          await expect(
            page.getByRole("dialog").getByText(readyId!, { exact: true }),
          ).toBeVisible();
        }
        await pending.release();
        // These no-run fixtures have finite requests. An earlier action can clear
        // the shared busy label, so drain response-triggered refreshes before
        // asserting completion rather than treating an empty label as proof.
        await page.waitForLoadState("networkidle");
        await expect(page.locator(".notice.busy")).toHaveCount(0);
        if (mode === "Home")
          await expect
            .soft(
              page.getByRole("heading", {
                name: "Recent projects",
                exact: true,
              }),
            )
            .toBeVisible();
        if (mode === "other project") {
          await expect(
            page.getByRole("heading", { name: other.name, exact: true }),
          ).toBeVisible();
          await expect(duration(page)).toHaveValue("8");
          await expect(duration(page)).toBeFocused();
          await expect(apply(duration(page))).toBeEnabled();
          const untouched = await read(page, other.projectId);
          expect(untouched.revision).toBe(other.revision);
          expect(untouched.documents).toEqual(other.documents);
          expect(await runIds(page, other.projectId)).toEqual(otherRuns);
        }
        if (mode === "Home" || mode === "deliberate focus")
          await expect.soft(home).toBeFocused();
        if (mode === "newer head") {
          await expect.soft(duration(page)).toHaveValue("7");
          await expect
            .soft(page.locator(".workspace-context"))
            .toContainText(`Draft revision ${project.revision + 2}`);
          expect
            .soft(
              await page.evaluate(
                (id) => sessionStorage.getItem("studio.graphHistory." + id),
                id,
              ),
            )
            .toBe(newerHistory);
        }
        if (mode === "newer same-field draft") {
          await expect.soft(duration(page)).toHaveValue("7");
          await expect.soft(apply(duration(page))).toBeEnabled();
          await expect(
            duration(page).locator("xpath=ancestor::form").getByRole("status"),
          ).toContainText("Current saved value: 6");
        }
        if (mode === "reverted same-field draft") {
          await expect.soft(duration(page)).toHaveValue("5");
          await expect.soft(apply(duration(page))).toBeEnabled();
          await expect(
            duration(page).locator("xpath=ancestor::form").getByRole("status"),
          ).toContainText("Current saved value: 6");
        }
        if (mode === "other field draft") {
          await expect
            .soft(page.getByLabel("Target", { exact: false }))
            .toHaveValue("2.5");
          await expect
            .soft(apply(page.getByLabel("Target", { exact: false })))
            .toBeEnabled();
        }
        if (mode === "newer readiness") {
          await expect
            .soft(
              page.getByRole("dialog", {
                name: "Execution preflight",
                exact: true,
              }),
            )
            .toBeVisible();
          await expect(
            page.getByRole("dialog").getByText(readyId!, { exact: true }),
          ).toBeVisible();
        }
        const saved = await read(page, id);
        expect(saved.revision).toBe(
          project.revision + (mode === "newer head" ? 2 : 1),
        );
        expect(value(saved, "duration")).toBe(mode === "newer head" ? 7 : 6);
        expect(await runIds(page, id)).toEqual(runs);
        await testInfo.attach("late-parameter.json", {
          body: JSON.stringify({
            mode,
            viewport,
            actualStatus: actual.status,
            beforeRevision: project.revision,
            savedRevision: saved.revision,
            canonicalDuration: value(saved, "duration"),
            newerHistory,
            historyAfter: await page.evaluate(
              (id) => sessionStorage.getItem("studio.graphHistory." + id),
              id,
            ),
            readyId,
            activeTag: await page.evaluate(
              () => document.activeElement?.tagName,
            ),
            ownProjectRunSetUnchanged: true,
            scope:
              "Held real committed edit response; preserved navigation, history, newer drafts/readiness/focus; no Start",
          }),
          contentType: "application/json",
        });
      } finally {
        await pending.close();
      }
    });
  }
  for (const departed of [false, true]) {
    test(`parameter accessibility: real stale failure ${departed ? "after departure" : "in current form"} at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(60000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      const project = await create(
          page,
          `Parameter stale ${departed} ${viewport.width}`,
        ),
        id = project.projectId;
      const runs = await runIds(page, id);
      const advanced = await page.evaluate(
        async ({ id, revision }) => {
          const { csrfToken } = await fetch("/api/v1/session").then((r) =>
            r.json(),
          );
          const r = await fetch(`/api/v1/projects/${id}/edits`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrfToken,
              "If-Match": String(revision),
            },
            body: JSON.stringify({
              baseRevision: revision,
              edits: [
                { kind: "set_parameter", parameterId: "target", value: 2.5 },
              ],
            }),
          });
          if (!r.ok) throw Error("Owned external revision fixture failed");
          return r.json();
        },
        { id, revision: project.revision },
      );
      await type(page, duration(page), "6");
      const pending = await holdResponse(page, id);
      try {
        await activate(page, apply(duration(page)));
        const actual = await pending.ready();
        expect(actual.status).toBe(412);
        if (departed)
          await activate(
            page,
            page.getByRole("button", {
              name: "X-Verse Studio home",
              exact: true,
            }),
          );
        await pending.release();
        await page.waitForLoadState("networkidle");
        if (departed) {
          await expect(
            page.getByRole("heading", { name: "Recent projects", exact: true }),
          ).toBeVisible();
          await expect
            .soft(page.locator(".alerts").getByRole("alert"))
            .toHaveCount(0);
        } else {
          await expect(
            page.locator(".alerts").getByRole("alert"),
          ).toContainText("REVISION_CONFLICT");
          await expect(duration(page)).toHaveValue("6");
          await expect(apply(duration(page))).toBeEnabled();
          await expect(apply(duration(page))).toBeFocused();
          await expect(duration(page)).not.toBeFocused();
        }
        const saved = await read(page, id);
        expect(saved.revision).toBe(advanced.revision);
        expect(saved.documents).toEqual(advanced.documents);
        expect(value(saved, "duration")).toBe(5);
        expect(await runIds(page, id)).toEqual(runs);
        await testInfo.attach("parameter-failure.json", {
          body: JSON.stringify({
            viewport,
            departed,
            status: actual.status,
            code: actual.body.code,
            projectRevisionUnchangedAfterRefusal: true,
            canonicalDuration: value(saved, "duration"),
            ownProjectRunSetUnchanged: true,
            scope:
              "Real stale revision refusal; failure is not a save acknowledgement and cannot pollute a departed context",
          }),
          contentType: "application/json",
        });
      } finally {
        await pending.close();
      }
    });
  }
  for (const moved of [false, true]) {
    test(`parameter accessibility: delayed presentation preserves ${moved ? "moved" : "field"} focus at ${viewport.width}x${viewport.height}`, async ({
      page,
    }, testInfo) => {
      test.setTimeout(60000);
      await page.setViewportSize(viewport);
      await connectStudio(page, testInfo);
      let pending: Awaited<ReturnType<typeof holdResponse>> | undefined;
      const project = await create(
        page,
        `Parameter presentation ${moved} ${viewport.width}`,
        async (id) => {
          pending = await holdResponse(page, id, "presentation", "GET");
        },
      );
      const runs = await runIds(page, project.projectId);
      try {
        const actual = await pending!.ready();
        expect(actual.status).toBe(200);
        expect(actual.body.formGroups.length).toBeGreaterThan(0);
        const expectedGroup = actual.body.formGroups.find((group: any) =>
          group.parameters.includes("duration"),
        );
        expect(expectedGroup).toBeTruthy();
        await type(page, duration(page), "8");
        await expect(duration(page)).toBeFocused();
        const oldControl = await duration(page).elementHandle();
        const home = page.getByRole("button", {
          name: "X-Verse Studio home",
          exact: true,
        });
        if (moved) await tabTo(page, home);
        await pending!.release();
        await page.waitForLoadState("networkidle");
        if (moved) {
          await expect(
            duration(page)
              .locator("xpath=ancestor::fieldset")
              .locator("legend"),
          ).toHaveText(expectedGroup.label);
        } else {
          expect(await oldControl!.evaluate((node) => node.isConnected)).toBe(
            true,
          );
        }
        const measured = await geometry(duration(page));
        await testInfo.attach("parameter-presentation.json", {
          body: JSON.stringify({
            viewport,
            moved,
            formGroups: actual.body.formGroups,
            originalControlStillConnected: await oldControl!.evaluate(
              (node) => node.isConnected,
            ),
            measured,
            canonicalDuration: value(
              await read(page, project.projectId),
              "duration",
            ),
            scope:
              "Held real inert presentation metadata; regrouping must preserve input and current focus intent",
          }),
          contentType: "application/json",
        });
        await expect(duration(page)).toHaveValue("8");
        await expect(apply(duration(page))).toBeEnabled();
        if (moved) await expect(home).toBeFocused();
        else await expect(duration(page)).toBeFocused();
        expect((await read(page, project.projectId)).documents).toEqual(
          project.documents,
        );
        expect(await runIds(page, project.projectId)).toEqual(runs);
        if (!moved) {
          // Native selection remains intact until focus leaves the parameter form.
          await tabTo(page, home);
          await expect(
            duration(page)
              .locator("xpath=ancestor::fieldset")
              .locator("legend"),
          ).toHaveText(expectedGroup.label);
          await expect(home).toBeFocused();
          await expect(duration(page)).toHaveValue("8");
        }
      } finally {
        await pending?.close();
      }
    });
  }
  test(`parameter accessibility: numeric normalization at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, testInfo) => {
    test.setTimeout(60000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const project = await create(
        page,
        `Parameter normalization ${viewport.width}`,
      ),
      id = project.projectId,
      runs = await runIds(page, id);
    await type(page, duration(page), "5.0");
    await expect(apply(duration(page))).toBeEnabled();
    const response = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === `/api/v1/projects/${id}/edits` &&
        r.request().method() === "POST",
    );
    await activate(page, apply(duration(page)));
    expect((await response).status()).toBe(200);
    await expect(page.locator(".alerts")).toContainText("Draft saved");
    await expect.soft(duration(page)).toHaveValue("5");
    await expect.soft(apply(duration(page))).toBeDisabled();
    await expect.soft(duration(page)).toBeFocused();
    const saved = await read(page, id);
    expect(saved.revision).toBe(project.revision + 1);
    expect(value(saved, "duration")).toBe(5);
    expect(await runIds(page, id)).toEqual(runs);
    await testInfo.attach("parameter-normalization.json", {
      body: JSON.stringify({
        viewport,
        submittedText: "5.0",
        authoredValue: value(saved, "duration"),
        displayedText: await duration(page).inputValue(),
        savedRevision: saved.revision,
        ownProjectRunSetUnchanged: true,
        scope:
          "Actual typed-value acknowledgement may normalize its own generation; failed saves cannot",
      }),
      contentType: "application/json",
    });
  });
}
