import { test, expect, type Locator, type Page } from "@playwright/test";
import { connectStudio } from "./connect-studio";
import { traceApi } from "./trace-claims-flow";

async function tabTo(page: Page, target: Locator) {
  await expect(target).toBeVisible();
  for (let i = 0; i < 160; i++) {
    if (await target.evaluate((node) => document.activeElement === node))
      return;
    await page.keyboard.press("Tab");
  }
  throw Error("Owned parameter control was not reachable by native Tab.");
}
for (const mode of ["apply", "field", "enum", "elsewhere", "dialog", "depart"])
  for (const width of [1024, 1440])
    test(`parameter presentation: ${mode} real regrouping preserves intent at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      const project = (
        await traceApi(page, "/projects", "POST", {
          name: "Late presentation keyboard control " + width,
        })
      ).body;
      await page.evaluate(
        (id) => localStorage.setItem("studio.projectId", id),
        project.projectId,
      );
      let release!: () => void, ready!: () => void, finish!: () => void;
      const held = new Promise<void>((r) => (release = r)),
        actual = new Promise<void>((r) => (ready = r)),
        delivered = new Promise<void>((r) => (finish = r));
      let presentation: any;
      const pattern = `**/api/v1/projects/${project.projectId}/presentation`;
      await page.route(pattern, async (route) => {
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        const text = await response.text();
        presentation = JSON.parse(text);
        const headers = { ...response.headers() };
        delete headers["content-length"];
        ready();
        await held;
        try {
          await route.fulfill({ status: 200, headers, body: text });
        } catch (error) {
          if (!route.request().failure()) throw error;
        } finally {
          finish();
        }
      });
      const edits: any[] = [];
      page.on("request", (request) => {
        if (
          request.method() === "POST" &&
          request.url().endsWith(`/projects/${project.projectId}/edits`)
        )
          edits.push(request.postDataJSON());
      });
      try {
        await page.reload();
        await actual;
        await expect(
          page.getByRole("heading", { name: project.name, exact: true }),
        ).toBeVisible();
        const field = page.getByLabel(
            mode === "enum" ? "Reference fault" : "Duration",
          ),
          expectedValue = mode === "enum" ? "stuck-sensor" : "7",
          button = field
            .locator("xpath=ancestor::form")
            .getByRole("button", { name: "Apply", exact: true });
        await tabTo(page, field);
        if (mode === "enum") await page.keyboard.press("End");
        else {
          await page.keyboard.press("ControlOrMeta+A");
          await page.keyboard.insertText("7");
        }
        await expect(field).toHaveValue(expectedValue);
        if (mode !== "field" && mode !== "enum") {
          await tabTo(page, button);
          await expect(button).toBeFocused();
        }
        const outside = page.getByRole("button", {
            name: "Validate",
            exact: true,
          }),
          home = page.getByRole("button", {
            name: "X-Verse Studio home",
            exact: true,
          });
        if (mode === "elsewhere") await tabTo(page, outside);
        if (mode === "dialog") {
          await tabTo(
            page,
            page.getByRole("button", { name: "XDL source", exact: true }),
          );
          await page.keyboard.press("Enter");
          await expect(page.getByRole("dialog")).toBeVisible();
        }
        if (mode === "depart") {
          await tabTo(page, home);
          await page.keyboard.press("Enter");
          await expect(
            page.getByRole("heading", { name: "Recent projects", exact: true }),
          ).toBeVisible();
        }
        expect(presentation.formGroups.length).toBeGreaterThan(0);
        release();
        await delivered;
        if (mode !== "depart")
          await expect(
            page.getByRole("group", { name: "Run horizon", exact: true }),
          ).toBeVisible();
        const beforeEnter = await page.evaluate(() => ({
          activeTag: document.activeElement?.tagName,
          inDialog: Boolean(document.activeElement?.closest("[role=dialog]")),
        }));
        await info.attach("native-presentation-focus", {
          contentType: "application/json",
          body: JSON.stringify({
            scope:
              "Actual owned presentation HTTP200 held; no DTO mutation. Native Tab reached Apply before actual metadata regrouped its form.",
            mode,
            width,
            projectId: project.projectId,
            beforeEnter,
            edits,
          }),
        });
        if (mode === "apply" || mode === "field" || mode === "enum") {
          await expect(mode === "apply" ? button : field).toBeFocused();
          if (mode === "enum") await tabTo(page, button);
          await page.keyboard.press("Enter");
          await expect(page.locator(".alerts")).toContainText("Draft saved");
          expect(edits).toHaveLength(1);
          expect(edits[0].edits).toContainEqual(
            expect.objectContaining({
              kind: "set_parameter",
              parameterId: mode === "enum" ? "fault" : "duration",
              value: mode === "enum" ? "stuck-sensor" : 7,
            }),
          );
          const saved = (await traceApi(page, "/projects/" + project.projectId))
            .body;
          expect(saved.revision).toBe(project.revision + 1);
          await expect(field).toHaveValue(expectedValue);
          await expect(field).toBeFocused();
        } else {
          if (mode === "elsewhere") await expect(outside).toBeFocused();
          if (mode === "dialog") {
            expect(
              await page
                .getByRole("dialog")
                .evaluate((node) => node.contains(document.activeElement)),
            ).toBe(true);
            await page.keyboard.press("Escape");
          }
          if (mode === "depart") {
            await expect(home).toBeFocused();
            await expect(
              page.getByRole("heading", {
                name: "Recent projects",
                exact: true,
              }),
            ).toBeVisible();
          }
          expect(edits).toEqual([]);
          const saved = (await traceApi(page, "/projects/" + project.projectId))
            .body;
          expect(saved.revision).toBe(project.revision);
          expect(saved.documents).toEqual(project.documents);
        }
        expect(
          (await traceApi(page, "/runs?projectId=" + project.projectId)).body
            .items,
        ).toEqual([]);
      } finally {
        release();
        await page.unrouteAll({ behavior: "wait" });
      }
    });
