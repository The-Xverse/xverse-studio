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
  throw new Error("Connection control is unreachable through native Tab order");
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
async function choose(page: Page, target: Locator, value: string) {
  // Native arrows skip disabled options; indices across all options would be wrong.
  const enabled = await target
    .locator("option")
    .evaluateAll((nodes) =>
      nodes
        .filter((node) => !(node as HTMLOptionElement).disabled)
        .map((node) => (node as HTMLOptionElement).value),
    );
  const index = enabled.indexOf(value);
  expect(index).toBeGreaterThanOrEqual(0);
  await tabTo(page, target);
  await page.keyboard.press("Home");
  for (let i = 0; i < index; i++) await page.keyboard.press("ArrowDown");
  await expect(target).toHaveValue(value);
}
function source(project: any, suffix: string): string {
  return (Object.values(project.documents) as any[]).find((d) =>
    d.path.endsWith("/" + suffix),
  ).content;
}

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test(`connection accessibility: native typed flow and rejected identifier recovery at ${viewport.width}x${viewport.height}`, async ({
    page,
  }, testInfo) => {
    test.setTimeout(90000);
    await page.setViewportSize(viewport);
    await connectStudio(page, testInfo);
    const { original, prepared } = await page.evaluate(async (width) => {
      const { csrfToken } = await fetch("/api/v1/session").then((r) =>
        r.json(),
      );
      const headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      };
      const created = await fetch("/api/v1/projects", {
        method: "POST",
        headers,
        body: JSON.stringify({ name: `Keyboard connection ${width}` }),
      });
      if (!created.ok) throw Error("Owned connection fixture creation failed");
      const original = await created.json();
      const response = await fetch(
        `/api/v1/projects/${original.projectId}/edits`,
        {
          method: "POST",
          headers: { ...headers, "If-Match": String(original.revision) },
          body: JSON.stringify({
            baseRevision: original.revision,
            edits: [{ kind: "disconnect_flow", flowId: "command-flow" }],
          }),
        },
      );
      if (!response.ok)
        throw Error("Owned connection fixture preparation failed");
      const prepared = await response.json();
      localStorage.setItem("studio.projectId", prepared.projectId);
      return { original, prepared };
    }, viewport.width);
    const projectId = prepared.projectId;
    const runIds = async () =>
      (await page.request.get("/api/v1/runs").then((r) => r.json())).items
        .filter((r: any) => r.projectId === projectId)
        .map((r: any) => r.runId)
        .sort();
    const beforeRuns = await runIds();
    await page.reload();
    await expect(
      page.getByRole("heading", { name: prepared.name, exact: true }),
    ).toBeVisible();
    const writes: { path: string; body: any }[] = [];
    page.on("request", (r) => {
      if (["POST", "PUT", "PATCH", "DELETE"].includes(r.method()))
        writes.push({
          path: new URL(r.url()).pathname,
          body: r.postDataJSON(),
        });
    });
    await activate(page, page.getByRole("tab", { name: /Connections/ }));
    const identifier = page.getByLabel("Flow identifier", { exact: true }),
      from = page.getByLabel("Source endpoint"),
      to = page.getByLabel("Destination endpoint");
    const connect = page.getByRole("button", {
      name: "Validate & connect",
      exact: true,
    });
    await type(page, identifier, "Bad_ID");
    await choose(page, from, "controller-out");
    await expect(to).toHaveAccessibleDescription(/compatible destination/);
    await expect(to.locator('option[value="observer-in"]')).toHaveJSProperty(
      "disabled",
      true,
    );
    await expect(to.locator('option[value="observer-in"]')).toContainText(
      "Interface state differs from command",
    );
    await choose(page, to, "plant-in");
    const nativeValidBefore = await identifier.evaluate(
      (n) => (n as HTMLInputElement).validity.valid,
    );
    expect.soft(nativeValidBefore).toBe(false);
    await expect.soft(identifier).toHaveAccessibleDescription(/lowercase/);
    await expect.soft(identifier).toHaveAttribute("aria-invalid", "true");
    let browserRefusal: any = null;
    if (nativeValidBefore) {
      // Pre-repair evidence: the browser accepted a format the backend rejects.
      const rejected = page.waitForResponse(
        (r) =>
          new URL(r.url()).pathname === `/api/v1/projects/${projectId}/edits` &&
          r.request().method() === "POST",
      );
      await activate(page, connect);
      const response = await rejected;
      expect(response.status()).toBe(422);
      browserRefusal = await response.json();
    } else {
      await activate(page, connect);
      await expect(identifier).toBeFocused();
      expect(writes).toEqual([]);
    }
    const afterBrowser = await page.request
      .get(`/api/v1/projects/${projectId}`)
      .then((r) => r.json());
    expect(afterBrowser.revision).toBe(prepared.revision);
    expect(afterBrowser.documents).toEqual(prepared.documents);
    // Explicit direct API negative: UI constraints never substitute for backend validation.
    const direct = await page.evaluate(
      async ({ projectId, revision }) => {
        const { csrfToken } = await fetch("/api/v1/session").then((r) =>
          r.json(),
        );
        const response = await fetch(`/api/v1/projects/${projectId}/edits`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
            "If-Match": String(revision),
          },
          body: JSON.stringify({
            baseRevision: revision,
            edits: [
              {
                kind: "connect_endpoints",
                flowId: "Bad_ID",
                sourceEndpointId: "controller-out",
                destinationEndpointIds: ["plant-in"],
                interfaceId: "command",
                timeDomainId: "simulation-time",
              },
            ],
          }),
        });
        return { status: response.status, body: await response.json() };
      },
      { projectId, revision: prepared.revision },
    );
    expect(direct.status).toBe(422);
    expect(direct.body.code).toBe("INVALID_EDIT");
    const afterDirect = await page.request
      .get(`/api/v1/projects/${projectId}`)
      .then((r) => r.json());
    expect(afterDirect.revision).toBe(prepared.revision);
    expect(afterDirect.documents).toEqual(prepared.documents);
    await type(page, identifier, "command-flow");
    await expect(identifier).toHaveAttribute("aria-invalid", "false");
    const writesBeforeSuccess = writes.length;
    const connected = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === `/api/v1/projects/${projectId}/edits` &&
        r.request().method() === "POST",
    );
    await activate(page, connect);
    expect((await connected).status()).toBe(200);
    await expect(page.locator(".alerts")).toContainText("Draft saved");
    expect(writes.slice(writesBeforeSuccess)).toEqual([
      {
        path: `/api/v1/projects/${projectId}/edits`,
        body: {
          baseRevision: prepared.revision,
          edits: [
            {
              kind: "connect_endpoints",
              flowId: "command-flow",
              sourceEndpointId: "controller-out",
              destinationEndpointIds: ["plant-in"],
              interfaceId: "command",
              timeDomainId: "simulation-time",
            },
          ],
        },
      },
    ]);
    const saved = await page.request
      .get(`/api/v1/projects/${projectId}`)
      .then((r) => r.json());
    expect(saved.revision).toBe(prepared.revision + 1);
    const system = parse(source(saved, "system.xdl.yaml")),
      before = parse(source(original, "system.xdl.yaml"));
    const flow = system.spec.flows.find((f: any) => f.id === "command-flow");
    expect(flow).toEqual(
      before.spec.flows.find((f: any) => f.id === "command-flow"),
    );
    expect(flow).toMatchObject({
      sourceEndpointId: "controller-out",
      destinationEndpointIds: ["plant-in"],
      interfaceId: "command",
      timeDomainId: "simulation-time",
      deliveryIntent: "ordered",
    });
    expect({ ...system.spec, flows: undefined }).toEqual({
      ...before.spec,
      flows: undefined,
    });
    expect(system.spec.flows.find((f: any) => f.id === "state-flow")).toEqual(
      before.spec.flows.find((f: any) => f.id === "state-flow"),
    );
    // Restoration may append the flow; compare all flow content independent of order.
    const byId = (a: any, b: any) => a.id.localeCompare(b.id);
    expect([...system.spec.flows].sort(byId)).toEqual(
      [...before.spec.flows].sort(byId),
    );
    for (const d of Object.values(saved.documents) as any[])
      if (!d.path.endsWith("/system.xdl.yaml"))
        expect(d.content).toBe(
          (Object.values(original.documents) as any[]).find(
            (old) => old.path === d.path,
          ).content,
        );
    const admission = page.getByRole("button", {
      name: /^Admission admitted; show checks for .*#command-flow$/,
    });
    await activate(page, admission);
    await expect(admission).toHaveAttribute("aria-expanded", "true");
    await expect(
      page
        .locator(".admission-checks")
        .filter({ hasText: "Exact interface compatibility" }),
    ).toBeVisible();
    const validation = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname ===
          `/api/v1/projects/${projectId}/validations` &&
        r.request().method() === "POST",
    );
    await activate(
      page,
      page.getByRole("button", { name: "Validate", exact: true }),
    );
    expect((await (await validation).json()).valid).toBe(true);
    expect(await runIds()).toEqual(beforeRuns);
    const pairs = await Promise.all([
      renderedContrast(
        page.locator("#target-guidance"),
        "Connection target guidance",
      ),
      renderedContrast(
        page.locator("#flow-id-guidance"),
        "Connection identifier guidance",
      ),
    ]);
    await testInfo.attach("connection-keyboard.json", {
      body: JSON.stringify({
        viewport,
        platform: process.platform,
        browser: await page.context().browser()?.version(),
        nativeValidBefore,
        browserRefusal,
        direct,
        initialRevision: prepared.revision,
        savedRevision: saved.revision,
        flow,
        completeFlowCollectionPreserved: true,
        identitiesPreserved: true,
        definitionsAndOtherDocumentsUnchanged: true,
        authoritativeValidation: true,
        projectRunSetUnchanged: true,
        measurements: pairs,
        writes,
        scope:
          "Native keyboard authored connection; explicit direct API rejection; no routing/traffic/native XCOM or provider execution claim",
      }),
      contentType: "application/json",
    });
    for (const pair of pairs) {
      expect(pair.supported).toBe(true);
      if (pair.supported) expect(pair.ratio).toBeGreaterThanOrEqual(4.5);
    }
  });
}
