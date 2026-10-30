import { test, expect } from "@playwright/test";
import { connectStudio } from "../e2e/connect-studio";

for (const viewport of [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]) {
  test(`Autoverse untrusted display and session boundary at ${viewport.width}`, async ({ page, context }, info) => {
    await page.setViewportSize(viewport);
    await connectStudio(page, info);
    const name = 'Autoverse Ω <img data-studio-untrusted src=x onerror="window.__studioSecurityFlag=true">';
    const proof = await page.evaluate(async (name) => {
      const session = await fetch("/api/v1/session").then(r => r.json());
      const headers = { "Content-Type": "application/json", "X-CSRF-Token": session.csrfToken };
      const created = await fetch("/api/v1/projects", { method: "POST", headers,
        body: JSON.stringify({ name, blueprintRef: "autoverse-classic" }) });
      if (created.status !== 201) throw Error("Actual Autoverse authoring target unavailable");
      const p = await created.json();
      const [docid, document] = Object.entries(p.documents)[0] as [string, {content: string, format: string}];
      const bad = await fetch(`/api/v1/projects/${p.projectId}/documents/${docid}`, { method: "PUT",
        headers: { ...headers, "If-Match": String(p.revision) },
        body: JSON.stringify({ content: document.content + "\n# csrfToken: owned-browser-private-marker\n", format: document.format }) });
      const problem = await bad.json();
      const malformed = await fetch("/api/v1/projects", { method: "POST", headers,
        body: JSON.stringify({ name: "Autoverse", blueprintRef: "autoverse-classic",
          "sessionToken=owned-browser-private-marker": true }) });
      const schema = await malformed.json();
      const current = await fetch(`/api/v1/projects/${p.projectId}`).then(r => r.json());
      localStorage.setItem("studio.projectId", p.projectId);
      return { projectId: p.projectId, name: p.name, credentialStatus: bad.status,
        credentialCode: problem.code, schemaStatus: malformed.status,
        locationRedacted: schema.diagnostics?.[0]?.location?.redacted === true,
        markerEchoed: JSON.stringify([problem, schema]).includes("owned-browser-private-marker"),
        sourcePreserved: current.revision === p.revision && current.documents[docid].content === document.content };
    }, name);
    expect(proof.credentialStatus).toBe(422);
    expect(proof.credentialCode).toBe("CREDENTIAL_REJECTED");
    expect(proof.schemaStatus).toBe(422);
    expect(proof.locationRedacted).toBe(true);
    expect(proof.markerEchoed).toBe(false);
    expect(proof.sourcePreserved).toBe(true);
    await page.reload();
    await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
    await expect(page.locator("img[data-studio-untrusted]")).toHaveCount(0);
    expect(await page.evaluate(() => (window as unknown as Record<string, unknown>).__studioSecurityFlag)).toBeUndefined();
    expect((await context.cookies()).some(c => c.name === "studio_session" && c.httpOnly && c.sameSite === "Strict")).toBe(true);
    expect(await page.evaluate(() => document.cookie.includes("studio_session"))).toBe(false);
    await context.clearCookies();
    const denied = await page.evaluate(async () => {
      const response = await fetch("/api/v1/projects", { method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": "invalid" },
        body: JSON.stringify({ name: "Unauthorized Autoverse", blueprintRef: "autoverse-classic" }) });
      return { status: response.status, code: (await response.json()).code,
        noStore: response.headers.get("cache-control") === "no-store" };
    });
    expect(denied).toEqual({ status: 401, code: "UNAUTHORIZED", noStore: true });
    await info.attach("autoverse-security", { body: JSON.stringify({ target: "actual enrolled Autoverse",
      viewport, untrustedDisplayInert: true, sourcePreserved: true, credentialRejected: true,
      schemaLocationRedacted: true, sessionCookieHttpOnly: true, unauthorizedMutationRefused: true,
      runtimeStarted: false }), contentType: "application/json" });
  });
}
