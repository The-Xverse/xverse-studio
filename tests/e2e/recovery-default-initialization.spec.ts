import { test, expect, type Page, type Locator } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, realpathSync } from "node:fs";
import path from "node:path";
import { connectStudio } from "./connect-studio";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (const [key, limit] of [["Shift+Tab", 40], ["Tab", 220]] as const)
    for (let i = 0; i < limit; i++) {
      if (await target.evaluate((node) => document.activeElement === node)) return;
      await page.keyboard.press(key);
    }
  await expect(target).toBeFocused();
}
async function activate(page: Page, target: Locator) {
  await tabTo(page, target);
  await page.keyboard.press("Enter");
}
function gate() {
  let release!: () => void;
  const promise = new Promise<void>((resolve) => { release = resolve; });
  return { promise, release };
}
const digest = (bytes: Buffer) => "sha256:" + createHash("sha256").update(bytes).digest("hex");
const get = async (page: Page, url: string) => (await page.request.get(url)).json();

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  for (const newer of ["none", "draft", "dialog"] as const) {
    test(`recovery default initialization: newer ${newer} at ${viewport.width}`, async ({ page }, info) => {
      test.setTimeout(90000);
      await page.setViewportSize(viewport);
      await connectStudio(page, info);
      const prior = await page.evaluate(async (name) => {
        const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
        const response = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ name }) });
        if (response.status !== 201) throw new Error("Owned initialization project creation refused");
        const project = await response.json();
        localStorage.setItem("studio.projectId", project.projectId);
        return project;
      }, `Default recovery origin ${viewport.width} ${newer}`);
      await page.reload();
      await expect(page.getByRole("heading", { name: prior.name, exact: true })).toBeVisible();
      const first = gate(), second = gate(), committed = gate(), deliver = gate(), events: Record<string, unknown>[] = [];
      let observations = 0, variantRef = "", recovered: any, owned: any;
      const assetRoot = realpathSync(process.env.STUDIO_BROWSER_DATA!), modified = Buffer.from([0xff, 0xfe, 0x00, 0x62]);
      function ownedFile(...parts: string[]) {
        const file = path.resolve(assetRoot, ...parts);
        expect(file.startsWith(assetRoot + path.sep)).toBe(true);
        return file;
      }
      await page.route(`**/api/v1/projects/${prior.projectId}/deployment-variants`, async (route) => {
        const response = await route.fetch(), body = await response.text(), value = JSON.parse(body);
        expect(response.status()).toBe(200); expect(value.items).toHaveLength(1);
        observations++; variantRef = value.items[0].ref;
        await (observations === 1 ? first.promise : second.promise);
        await route.fulfill({ response, body });
        events.push({ phase: "default-delivered", observation: observations, variantRef });
      });
      await page.route("**/api/v1/projects", async (route) => {
        if (route.request().method() !== "POST") { await route.continue(); return; }
        const response = await route.fetch(); expect(response.status()).toBe(201);
        const project = await response.json(), id = Object.keys(project.documents).find((id) => project.documents[id].path.endsWith("/system.xdl.yaml"))!;
        const document = project.documents[id], file = ownedFile("projects", project.projectId, "revisions", String(project.revision), document.path);
        expect(realpathSync(file)).toBe(file); expect(readFileSync(file, "utf8")).toBe(document.content);
        writeFileSync(file, modified); owned = { project, id, document, file };
        await route.fulfill({ response });
      });
      await page.route("**/api/v1/projects/*/recoveries", async (route) => {
        if (route.request().method() !== "POST") { await route.continue(); return; }
        expect(new URL(route.request().url()).pathname).toBe(`/api/v1/projects/${owned.project.projectId}/recoveries`);
        const response = await route.fetch(), body = await response.text(); expect(response.status()).toBe(200);
        recovered = JSON.parse(body); events.push({ phase: "recovery-committed", revision: recovered.project.revision }); committed.release();
        await deliver.promise; await route.fulfill({ response, body });
      });
      try {
        await activate(page, page.getByRole("tab", { name: "Deployment", exact: true }));
        await expect.poll(() => observations).toBe(1);
        await activate(page, page.getByRole("button", { name: "Catalog", exact: true }));
        await expect(page.getByRole("button", { name: "Back to workspace", exact: true })).toBeVisible();
        await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
        first.release();
        expect(await page.evaluate((id) => localStorage.getItem("studio.selection." + id), prior.projectId)).toBeNull();
        const entry = (await get(page, "/api/v1/catalog")).items.find((e: any) => e.kind === "blueprint" && e.providerIds?.includes("studio.reference"));
        expect(entry).toBeTruthy();
        await activate(page, page.getByRole("article").filter({ has: page.getByRole("heading", { name: entry.name, exact: true }) }).getByRole("button", { name: "Open as project", exact: true }));
        const recovery = page.getByRole("group", { name: "Source recovery", exact: true });
        await expect(recovery).toBeVisible();
        await activate(page, page.getByRole("button", { name: "Back to workspace", exact: true }));
        await expect.poll(() => observations).toBe(2);
        await expect(page.getByRole("heading", { name: prior.name, exact: true })).toBeVisible();
        expect(await page.evaluate((id) => localStorage.getItem("studio.selection." + id), prior.projectId)).toBeNull();
        await activate(page, recovery.getByRole("button", { name: `Restore committed revision ${owned.project.revision}`, exact: true }));
        await committed.promise;
        second.release();
        await expect(page.getByRole("combobox", { name: "Deployment variant", exact: true })).toHaveValue(variantRef);
        events.push({ phase: "prior-automatic-default-applied", priorId: prior.projectId });
        if (newer === "draft") {
          const input = page.getByRole("textbox", { name: "New variant name", exact: true });
          await tabTo(page, input); await page.keyboard.type("Newer authored variant");
          await expect(input).toHaveValue("Newer authored variant");
        } else if (newer === "dialog") {
          await activate(page, page.getByRole("button", { name: "XDL source", exact: true }));
          await expect(page.getByRole("dialog", { name: "Authored XDL source", exact: true })).toBeVisible();
        }
        const reply = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${owned.project.projectId}/recoveries` && r.request().method() === "POST");
        deliver.release(); expect((await reply).status()).toBe(200);
        await page.waitForLoadState("networkidle");
        if (newer === "none") {
          await expect(page.getByRole("heading", { name: owned.project.name, exact: true })).toBeVisible();
          await expect(page.getByRole("tab", { name: "Model", exact: true })).toHaveAttribute("aria-selected", "true");
          await expect(page.getByRole("button", { name: "XDL source", exact: true })).toBeFocused();
        } else {
          if (newer === "dialog") {
            await expect(page.getByRole("dialog", { name: "Authored XDL source", exact: true })).toBeVisible();
            await page.keyboard.press("Escape");
          } else await expect(page.getByRole("textbox", { name: "New variant name", exact: true })).toHaveValue("Newer authored variant");
          await expect(page.getByRole("heading", { name: prior.name, exact: true })).toBeVisible();
          await expect(page.getByRole("tab", { name: "Deployment", exact: true })).toHaveAttribute("aria-selected", "true");
        }
        const current = await get(page, `/api/v1/projects/${owned.project.projectId}`);
        expect(current.revision).toBe(owned.project.revision + 1);
        for (const id of Object.keys(owned.project.documents)) expect(current.documents[id].content).toBe(owned.project.documents[id].content);
        expect((await get(page, `/api/v1/projects/${prior.projectId}`)).documents).toEqual(prior.documents);
        const kept = recovered.recovery.preserved["document:" + owned.id];
        expect(kept.observedDigest).toBe(digest(modified));
        expect(readFileSync(ownedFile("projects", owned.project.projectId, "recoveries", recovered.recovery.recoveryId, kept.backupFile))).toEqual(modified);
        expect(readFileSync(owned.file)).toEqual(modified);
        expect((await get(page, "/api/v1/runs")).items.filter((r: any) => [prior.projectId, owned.project.projectId].includes(r.projectId))).toEqual([]);
        await info.attach("recovery-default-order", { body: JSON.stringify({ viewport, newer, events, backendRevision: current.revision, backupPreserved: true, priorDocumentsUnchanged: true, noRun: true, scope: "Real HTTP bodies deliberately ordered; owned unreadable-source fixture, no Start" }), contentType: "application/json" });
      } finally {
        first.release(); second.release(); committed.release(); deliver.release();
        await page.unrouteAll({ behavior: "wait" });
        if (owned) writeFileSync(owned.file, owned.document.content);
      }
    });
  }
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`recovery default initialization: closed newer Home dialog at ${viewport.width}`, async ({ page }, info) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const project = await page.evaluate(async (name) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) => r.json());
      const response = await fetch("/api/v1/projects", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ name }) });
      if (response.status !== 201) throw new Error("Owned Home recovery project creation refused");
      const value = await response.json(); localStorage.setItem("studio.projectId", value.projectId); return value;
    }, `Home recovery target ${viewport.width}`);
    const id = Object.keys(project.documents).find((id) => project.documents[id].path.endsWith("/system.xdl.yaml"))!, document = project.documents[id];
    const assetRoot = realpathSync(process.env.STUDIO_BROWSER_DATA!), modified = Buffer.from([0xff, 0xfe, 0x00, 0x62]);
    function ownedFile(...parts: string[]) {
      const file = path.resolve(assetRoot, ...parts); expect(file.startsWith(assetRoot + path.sep)).toBe(true); return file;
    }
    const file = ownedFile("projects", project.projectId, "revisions", String(project.revision), document.path);
    expect(realpathSync(file)).toBe(file); expect(readFileSync(file, "utf8")).toBe(document.content);
    writeFileSync(file, modified);
    const committed = gate(), deliver = gate(); let recovered: any, requests = 0;
    await page.route(`**/api/v1/projects/${project.projectId}/recoveries`, async (route) => {
      if (route.request().method() !== "POST") { await route.continue(); return; }
      requests++;
      const response = await route.fetch(), body = await response.text(); expect(response.status()).toBe(200);
      recovered = JSON.parse(body); committed.release(); await deliver.promise; await route.fulfill({ response, body });
    });
    try {
      await page.reload();
      const recovery = page.getByRole("group", { name: "Source recovery", exact: true });
      await expect(recovery).toBeVisible();
      await expect(page.getByRole("heading", { name: "Start with an example", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: project.name, exact: true })).toHaveCount(0);
      await activate(page, recovery.getByRole("button", { name: `Restore committed revision ${project.revision}`, exact: true }));
      await committed.promise;
      await activate(page, page.getByRole("button", { name: "New project", exact: true }));
      await expect(page.getByRole("dialog", { name: "Create a System workspace", exact: true })).toBeVisible();
      await page.keyboard.press("Escape"); await expect(page.getByRole("dialog")).toHaveCount(0);
      const reply = page.waitForResponse((r) => new URL(r.url()).pathname === `/api/v1/projects/${project.projectId}/recoveries` && r.request().method() === "POST");
      deliver.release(); expect((await reply).status()).toBe(200); await page.waitForLoadState("networkidle");
      await expect(page.getByRole("heading", { name: "Start with an example", exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: project.name, exact: true })).toHaveCount(0);
      await expect(page.getByRole("dialog")).toHaveCount(0);
      const current = await get(page, `/api/v1/projects/${project.projectId}`);
      expect(current.revision).toBe(project.revision + 1); expect(current.documents).toEqual(project.documents);
      const kept = recovered.recovery.preserved["document:" + id]; expect(kept.observedDigest).toBe(digest(modified));
      expect(readFileSync(ownedFile("projects", project.projectId, "recoveries", recovered.recovery.recoveryId, kept.backupFile))).toEqual(modified);
      expect(readFileSync(file)).toEqual(modified); expect(requests).toBe(1);
      expect((await get(page, "/api/v1/runs")).items.filter((r: any) => r.projectId === project.projectId)).toEqual([]);
      await info.attach("home-recovery-intent", { body: JSON.stringify({ viewport, backendRevision: current.revision, newerDialogOpenedAndClosed: true, homePreserved: true, backupPreserved: true, requests, noRun: true, scope: "Actual recovery response held after backend commit; native keyboard opens/closes newer Home dialog" }), contentType: "application/json" });
    } finally { committed.release(); deliver.release(); await page.unrouteAll({ behavior: "wait" }); writeFileSync(file, document.content); }
  });
}
