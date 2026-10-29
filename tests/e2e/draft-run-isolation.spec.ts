import { test, expect, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

const data = () => process.env.STUDIO_BROWSER_DATA!;
async function makeProject(page: Page, name: string, duration: number) {
  return page.evaluate(
    async ({ name, duration }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      };
      let r = await fetch("/api/v1/projects", {
        method: "POST",
        headers,
        body: JSON.stringify({ name }),
      });
      let project = await r.json();
      r = await fetch(`/api/v1/projects/${project.projectId}/edits`, {
        method: "POST",
        headers: { ...headers, "If-Match": String(project.revision) },
        body: JSON.stringify({
          baseRevision: project.revision,
          edits: [
            { kind: "set_parameter", parameterId: "duration", value: duration },
          ],
        }),
      });
      if (!r.ok) throw Error(await r.text());
      project = await r.json();
      localStorage.setItem("studio.projectId", project.projectId);
      return project;
    },
    { name, duration },
  );
}
async function readProject(page: Page, projectId: string) {
  return page.request
    .get(`/api/v1/projects/${projectId}`)
    .then((r) => r.json());
}
function parameter(project: any, id: string) {
  const scenario = Object.values(project.documents).find((d: any) =>
    d.content.includes("kind: Scenario"),
  ) as any;
  const match = scenario.content.match(
    new RegExp(`- id: ${id}\\n(?:\\s+.*\\n)*?\\s+value: ([^\\n]+)`),
  );
  return match?.[1];
}
async function applyDuration(page: Page, value: string) {
  await page.getByRole("tab", { name: /Model/ }).click();
  await page.getByRole("button", { name: "plant plant" }).click();
  await page.getByRole("button", { name: "Parameters", exact: true }).click();
  await page.getByLabel("Duration").fill(value);
  await page
    .getByLabel("Duration")
    .locator("xpath=ancestor::form")
    .getByRole("button", { name: "Apply", exact: true })
    .click();
  await expect(
    page.getByText("Draft saved. Existing run snapshots remain unchanged."),
  ).toBeVisible();
}

test("draft/run isolation: graph undo and redo are new revisions that never change the running snapshot", async ({
  page,
  context,
}, testInfo) => {
  test.setTimeout(90000);
  await connectStudio(page, testInfo);
  const project = await makeProject(page, "Undo redo isolation", 20);
  await page.reload();
  await page
    .getByRole("button", { name: "Preflight & run", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Start frozen snapshot", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: /Run results/ }),
  ).toContainText("running", { timeout: 15000 });
  const runId = (await page.evaluate(() =>
    localStorage.getItem("studio.lastRun"),
  ))!;
  const run = await page.request
    .get(`/api/v1/runs/${runId}`)
    .then((r) => r.json());
  const snapshotFile = path.join(
      data(),
      "snapshots",
      run.snapshotId,
      "snapshot.json",
    ),
    sha = () =>
      createHash("sha256").update(readFileSync(snapshotFile)).digest("hex"),
    snapshotBefore = sha();
  const starts: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST" && new URL(r.url()).pathname === "/api/v1/runs")
      starts.push(r.url());
  });
  await applyDuration(page, "12");
  await applyDuration(page, "8");
  const undo = page.getByRole("button", { name: "Undo", exact: true }),
    redo = page.getByRole("button", { name: "Redo", exact: true });
  await expect(redo).toBeDisabled();
  await undo.click();
  await expect(
    page.getByText(/Undid a graph edit as new revision/),
  ).toBeVisible();
  let current = await readProject(page, project.projectId);
  expect(parameter(current, "duration")).toBe("12");
  // Keyboard undo applies outside text fields.
  await page.locator(".project-header h1").click();
  await expect(undo).toBeEnabled();
  await page.keyboard.press("Control+z");
  await expect
    .poll(async () =>
      parameter(await readProject(page, project.projectId), "duration"),
    )
    .toBe("20");
  // A shortcut is ignored while another action is busy; wait as a user would.
  await expect(redo).toBeEnabled();
  await page.keyboard.press("Control+Shift+z");
  await expect
    .poll(async () =>
      parameter(await readProject(page, project.projectId), "duration"),
    )
    .toBe("12");
  current = await readProject(page, project.projectId);
  const history = await page.request
    .get(`/api/v1/projects/${project.projectId}/revisions`)
    .then((r) => r.json());
  expect(history.items[0].revision).toBe(current.revision);
  expect(history.items[0].origin.kind).toBe("restore");
  expect(history.items.length).toBe(current.revision);
  // The active run keeps its frozen inputs while the draft moves on.
  expect(sha()).toBe(snapshotBefore);
  const frozen = await page.request
    .get(`/api/v1/runs/${runId}/snapshot`)
    .then((r) => r.json());
  expect(frozen.snapshot.revision).toBe(project.revision);
  expect(starts).toEqual([]);
  // A change from another tab makes this tab's next step a conflict, never an overwrite.
  const other = await context.newPage();
  await other.goto("/");
  await other.evaluate(
    async ({ projectId, revision }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const r = await fetch(`/api/v1/projects/${projectId}/edits`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
          "If-Match": String(revision),
        },
        body: JSON.stringify({
          baseRevision: revision,
          edits: [{ kind: "set_parameter", parameterId: "gain", value: 0.5 }],
        }),
      });
      if (!r.ok) throw Error(await r.text());
    },
    { projectId: project.projectId, revision: current.revision },
  );
  await other.close();
  await undo.click();
  await expect(page.getByRole("alert")).toContainText("REVISION_CONFLICT");
  const after = await readProject(page, project.projectId);
  expect(after.revision).toBe(current.revision + 1);
  expect(parameter(after, "gain")).toBe("0.5");
  expect(sha()).toBe(snapshotBefore);
  await page.screenshot({
    path: testInfo.outputPath("undo-redo-isolation.png"),
  });
});

test("draft/run isolation: externally modified sources are preserved before an explicit recovery", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await makeProject(page, "External source recovery", 5);
  const [documentId, document] = Object.entries(project.documents).find(
    ([, d]: any) => d.path.endsWith("/plant.xdl.yaml"),
  ) as [string, any];
  const file = path.join(
    data(),
    "projects",
    project.projectId,
    "revisions",
    String(project.revision),
    document.path,
  );
  const external = document.content.replace(
    "Studio-owned reference fixture.",
    "Edited outside Studio.",
  );
  writeFileSync(file, external);
  await page.reload();
  const notice = page
    .getByRole("alert")
    .filter({ hasText: "Source files changed outside Studio" });
  await expect(notice).toBeVisible();
  await notice
    .getByRole("button", {
      name: "Adopt external changes as a new revision",
      exact: true,
    })
    .click();
  await expect(page.getByText(/Recovered as revision \d+/)).toBeVisible();
  await expect(notice).toHaveCount(0);
  const recovered = await readProject(page, project.projectId);
  expect(recovered.sourceIntegrity).toBe("intact");
  expect(recovered.revision).toBe(project.revision + 1);
  expect(recovered.documents[documentId].content).toBe(external);
  const backups = await page.request
    .get(`/api/v1/projects/${project.projectId}/recoveries`)
    .then((r) => r.json());
  expect(backups.items).toHaveLength(1);
  const preserved = await page.request
    .get(
      `/api/v1/projects/${project.projectId}/recoveries/${backups.items[0].recoveryId}/preserved?key=${encodeURIComponent("document:" + documentId)}`,
    )
    .then((r) => r.json());
  expect(preserved.content).toBe(external);
  expect(preserved.committedDigest).toBe(document.digest);
});

test("draft/run isolation: undo never crosses a change it did not record", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await makeProject(page, "Interleaved source save", 20);
  await page.reload();
  await applyDuration(page, "12");
  const undo = page.getByRole("button", { name: "Undo", exact: true });
  await expect(undo).toBeEnabled();
  // A source save outside graph history (here through the API, as another editor would).
  const current = await readProject(page, project.projectId);
  const [documentId, document] = Object.entries(current.documents).find(
    ([, d]: any) => d.path.endsWith("/plant.xdl.yaml"),
  ) as [string, any];
  const saved = await page.evaluate(
    async ({ projectId, documentId, content, revision }) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const r = await fetch(
        `/api/v1/projects/${projectId}/documents/${documentId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
            "If-Match": String(revision),
          },
          body: JSON.stringify({ content, format: "yaml" }),
        },
      );
      if (!r.ok) throw Error(await r.text());
      return r.json();
    },
    {
      projectId: project.projectId,
      documentId,
      content: document.content + "# source save outside graph history\n",
      revision: current.revision,
    },
  );
  await page.reload();
  // The loaded revision was not produced by this tab's graph history.
  await expect(undo).toBeDisabled();
  await applyDuration(page, "8");
  await expect(undo).toBeEnabled();
  await undo.click();
  await expect(page.getByText(/Undid a graph edit/)).toBeVisible();
  await expect(undo).toBeDisabled();
  const after = await readProject(page, project.projectId);
  expect(parameter(after, "duration")).toBe("12");
  expect(after.documents[documentId].content).toBe(
    saved.documents[documentId].content,
  );
});

test("draft/run isolation: an unreadable committed source is restored from recorded history", async ({
  page,
}, testInfo) => {
  test.setTimeout(60000);
  await connectStudio(page, testInfo);
  const project = await makeProject(page, "Unreadable source recovery", 5);
  const document = Object.values(project.documents).find((d: any) =>
    d.path.endsWith("/system.xdl.yaml"),
  ) as any;
  const file = path.join(
    data(),
    "projects",
    project.projectId,
    "revisions",
    String(project.revision),
    document.path,
  );
  writeFileSync(file, Buffer.from([0xff, 0xfe, 0x00]));
  await page.reload();
  const alert = page
    .getByRole("alert")
    .filter({ hasText: "PROJECT_UNAVAILABLE" });
  await expect(alert).toBeVisible();
  await expect(
    alert.getByRole("button", {
      name: "Adopt external changes as a new revision",
    }),
  ).toHaveCount(0);
  await alert
    .getByRole("button", {
      name: `Restore committed revision ${project.revision}`,
    })
    .click();
  await expect(page.getByText(/Recovered as revision \d+/)).toBeVisible();
  await expect(page.locator(".project-header h1")).toHaveText(
    "Unreadable source recovery",
  );
  const recovered = await readProject(page, project.projectId);
  expect(recovered.revision).toBe(project.revision + 1);
  expect(
    (Object.values(recovered.documents) as any[]).find((d) =>
      d.path.endsWith("/system.xdl.yaml"),
    ).content,
  ).toBe(document.content);
});
