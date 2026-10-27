import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { connectStudio } from "./connect-studio";
import { traceApi } from "./trace-claims-flow";

for (const mode of [
  "normal",
  "new run",
  "Model",
  "Home",
  "tab",
  "focus",
  "back",
  "HTTP503",
  "wrong snapshot",
  "wrong plan",
  "malformed documents",
  "unverified",
  "missing authored",
  "superseded",
  "duplicate",
])
  for (const width of [1024, 1440]) {
    test(`frozen input inspection ${mode} at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      let project = (
        await traceApi(page, "/projects", "POST", {
          name: "Frozen inspection context " + width,
        })
      ).body;
      const runs: any[] = [];
      for (const gain of [0.8, 1.2]) {
        const saved = await traceApi(
          page,
          `/projects/${project.projectId}/edits`,
          "POST",
          {
            baseRevision: project.revision,
            edits: [
              { kind: "set_parameter", parameterId: "duration", value: 0.2 },
              { kind: "set_parameter", parameterId: "gain", value: gain },
            ],
          },
          project.revision,
        );
        expect(saved.status).toBe(200);
        project = saved.body;
        const pf = (
          await traceApi(
            page,
            `/projects/${project.projectId}/preflights`,
            "POST",
            { revision: project.revision },
          )
        ).body;
        expect(pf.status).toBe("ready");
        const started = await traceApi(page, "/runs", "POST", {
          snapshotId: pf.snapshotId,
          preflightId: pf.preflightId,
        });
        expect(started.status).toBe(202);
        await expect
          .poll(
            async () =>
              (await traceApi(page, "/runs/" + started.body.runId)).body.state,
            { timeout: 20000 },
          )
          .toBe("stopped");
        runs.push((await traceApi(page, "/runs/" + started.body.runId)).body);
      }
      const [original, newer] = runs;
      const digest = (name: string) =>
        createHash("sha256")
          .update(
            readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, name)),
          )
          .digest("hex");
      const names = runs.flatMap((run) => [
        `runs/${run.runId}/evidence.jsonl`,
        `snapshots/${run.snapshotId}/snapshot.json`,
      ]);
      const before = Object.fromEntries(
        names.map((name) => [name, digest(name)]),
      );
      await page.evaluate(
        ({ pid, rid }) => {
          localStorage.setItem("studio.projectId", pid);
          localStorage.setItem("studio.lastRun", rid);
          localStorage.setItem("studio.lastRun." + pid, rid);
        },
        { pid: project.projectId, rid: original.runId },
      );
      await page.reload();
      await page.getByRole("tab", { name: "Results", exact: false }).click();
      const selected = page.getByLabel("Recorded run", { exact: true });
      await expect(selected).toHaveValue(original.runId);
      let release!: () => void, ready!: () => void, complete!: () => void;
      const held = new Promise<void>((r) => (release = r)),
        actual = new Promise<void>((r) => (ready = r)),
        delivered = new Promise<void>((r) => (complete = r));
      let returned: any,
        delivery = "pending",
        calls = 0;
      let observed = await traceApi(page, `/runs/${newer.runId}/snapshot`);
      expect(observed.status).toBe(200);
      const other = observed.body;
      const sourceJson = JSON.stringify(
        (await traceApi(page, `/runs/${original.runId}/snapshot`)).body
          .snapshot,
      );
      await page.route(
        `**/api/v1/runs/${original.runId}/snapshot`,
        async (route) => {
          calls++;
          if (calls > 1) {
            await route.continue();
            return;
          }
          const response = await route.fetch();
          expect(response.status()).toBe(200);
          const bodyText = await response.text();
          returned = JSON.parse(bodyText);
          const headers = { ...response.headers() };
          delete headers["content-length"];
          expect(returned.integrity).toBe("valid");
          expect(returned.readOnly).toBe(true);
          expect(returned.snapshot.snapshotId).toBe(original.snapshotId);
          ready();
          await held;
          try {
            if (mode === "HTTP503")
              await route.fulfill({
                status: 503,
                contentType: "application/json",
                body: JSON.stringify({
                  code: "LABELLED_INSPECTION_UNAVAILABLE",
                  message: "Labelled frozen-input read unavailable.",
                }),
              });
            else if (
              [
                "wrong snapshot",
                "wrong plan",
                "malformed documents",
                "unverified",
                "missing authored",
              ].includes(mode)
            ) {
              const body = structuredClone(returned);
              if (mode === "wrong snapshot") body.snapshot = other.snapshot;
              if (mode === "wrong plan")
                body.snapshot.planDigest = other.snapshot.planDigest;
              if (mode === "malformed documents")
                body.snapshot.documents = ["labelled-not-a-source-map"];
              if (mode === "unverified") body.integrity = "unknown";
              if (mode === "missing authored")
                delete body.snapshot.projectDocuments;
              await route.fulfill({ status: 200, headers, json: body });
            } else
              await route.fulfill({ status: 200, headers, body: bodyText });
            delivery = "fulfilled";
          } catch (error) {
            if (!route.request().failure()) throw error;
            delivery = "browser aborted";
          } finally {
            complete();
          }
        },
      );
      const workloads: string[] = [];
      page.on("request", (request) => {
        const url = new URL(request.url());
        if (
          request.method() === "POST" &&
          (/\/api\/v1\/(runs|campaigns)$/.test(url.pathname) ||
            /\/(reruns|commands|evaluations)$/.test(url.pathname))
        )
          workloads.push(url.pathname);
      });
      const button = page.getByRole("button", {
        name: "Frozen inputs",
        exact: true,
      });
      await button.focus();
      await page.keyboard.press("Enter");
      await actual;
      await expect(button).toBeDisabled();
      let focused = page.getByRole("button", { name: "Refresh", exact: true });
      if (mode === "new run" || mode === "back" || mode === "superseded") {
        const beforeOptions = await selected
          .locator("option")
          .evaluateAll((nodes) =>
            nodes.map((node) => (node as HTMLOptionElement).value),
          );
        await expect(
          selected.locator("option").filter({ hasText: newer.runId }),
        ).toHaveCount(1);
        const readyOptions = await selected
          .locator("option")
          .evaluateAll((nodes) =>
            nodes.map((node) => (node as HTMLOptionElement).value),
          );
        await info.attach("history-selection-precondition", {
          contentType: "application/json",
          body: JSON.stringify({
            mode,
            beforeOptions,
            readyOptions,
            target: newer.runId,
          }),
        });
        await selected.focus();
        await page.keyboard.press("End");
        await expect(selected).toHaveValue(newer.runId);
        if (mode === "back") {
          await selected.focus();
          await page.keyboard.press("End");
          await expect(selected).toHaveValue(original.runId);
        }
        if (mode === "superseded") {
          await button.click();
          await expect(page.getByRole("dialog")).toContainText(
            newer.snapshotId,
          );
        }
      } else if (mode === "Model")
        await page.getByRole("tab", { name: "Model", exact: true }).click();
      else if (mode === "Home")
        await page
          .getByRole("button", { name: "X-Verse Studio home", exact: true })
          .click();
      else if (mode === "tab")
        await page.getByRole("tab", { name: /^Events & logs/ }).click();
      else if (mode === "focus") await focused.focus();
      else if (mode === "duplicate") {
        await button.evaluate((element) =>
          element.dispatchEvent(new MouseEvent("click", { bubbles: true })),
        );
      }
      release();
      await delivered;
      await expect(
        page.getByText("Verifying immutable run inputs…", { exact: true }),
      ).toHaveCount(0);
      const dialog = page.getByRole("dialog");
      if (
        [
          "HTTP503",
          "wrong snapshot",
          "wrong plan",
          "malformed documents",
          "unverified",
        ].includes(mode)
      ) {
        await expect(
          page
            .getByRole("alert")
            .filter({ hasText: /selected run|Labelled frozen/ }),
        ).toBeVisible();
        await expect(dialog).toHaveCount(0);
        await expect(selected).toHaveValue(original.runId);
        await page.unroute(`**/api/v1/runs/${original.runId}/snapshot`);
        await button.click();
        await expect(dialog).toContainText(original.snapshotId);
      } else if (
        mode === "normal" ||
        mode === "duplicate" ||
        mode === "missing authored"
      ) {
        await expect(dialog).toContainText(original.snapshotId);
        await expect(dialog).toContainText(original.runId);
        await expect(dialog).toContainText(project.projectId);
        if (mode === "missing authored") {
          await expect(
            dialog.getByText(
              "The complete authored revision was not recorded. Compiled contributing inputs remain available.",
              { exact: true },
            ),
          ).toBeVisible();
          await expect(
            dialog.getByRole("option", {
              name: "Complete authored revision · unavailable",
              exact: true,
            }),
          ).toHaveAttribute("disabled", "");
          await dialog.getByLabel("Frozen input set", { exact: true }).focus();
          await page.keyboard.press("End");
          await expect(
            dialog.getByLabel("Frozen input set", { exact: true }),
          ).toHaveValue("documents");
        }
        const document = await dialog
          .getByLabel("Frozen document", { exact: true })
          .inputValue();
        await expect(
          dialog.getByLabel("Frozen source text (read-only)", { exact: true }),
        ).toHaveValue(JSON.parse(sourceJson).documents[document]);
        expect(
          await dialog
            .getByLabel("Frozen source text (read-only)", { exact: true })
            .evaluate((node: HTMLTextAreaElement) => node.readOnly),
        ).toBe(true);
        if (mode === "normal") {
          const authored = JSON.parse(sourceJson).projectDocuments;
          await dialog
            .getByLabel("Frozen input set", { exact: true })
            .selectOption("projectDocuments");
          const name = await dialog
            .getByLabel("Frozen document", { exact: true })
            .inputValue();
          await expect(
            dialog.getByLabel("Frozen source text (read-only)", {
              exact: true,
            }),
          ).toHaveValue(authored[name]);
          await page.screenshot({
            path: info.outputPath("frozen-inputs-" + width + ".png"),
            fullPage: true,
          });
        }
        await page.keyboard.press("Escape");
        await expect(dialog).toHaveCount(0);
        await expect(button).toBeFocused();
        expect(calls).toBe(1);
      } else if (mode === "superseded") {
        await expect(dialog).toHaveCount(1);
        await expect(dialog).toContainText(newer.snapshotId);
        expect(
          (await dialog.textContent())?.includes(original.snapshotId),
        ).toBe(false);
        await page.keyboard.press("Escape");
        await expect(button).toBeFocused();
      } else {
        await page.evaluate(
          () =>
            new Promise<void>((resolve) =>
              requestAnimationFrame(() =>
                requestAnimationFrame(() => resolve()),
              ),
            ),
        );
        await expect(dialog).toHaveCount(0);
        if (mode === "Model")
          await expect(
            page.getByRole("tab", { name: "Model", exact: true }),
          ).toHaveAttribute("aria-selected", "true");
        if (mode === "Home")
          await expect(
            page.getByRole("heading", {
              name: "Start with an example",
              exact: true,
            }),
          ).toBeVisible();
        if (mode === "tab")
          await expect(
            page.getByRole("tab", { name: /^Events & logs/ }),
          ).toHaveAttribute("aria-selected", "true");
        if (mode === "focus") await expect(focused).toBeFocused();
      }
      const facts = {
        scope:
          "Two actual native owned runs. DTO/HTTP-negative modes substitute explicitly labelled response fields only; all protected files remain unchanged.",
        mode,
        width,
        originalRunId: original.runId,
        originalSnapshotId: original.snapshotId,
        newerRunId: newer.runId,
        newerSnapshotId: newer.snapshotId,
        delivery,
        calls,
        canonicalBytesUnchanged: names.every(
          (name) => digest(name) === before[name],
        ),
        workloads,
      };
      await info.attach("frozen-input-inspection-control", {
        contentType: "application/json",
        body: JSON.stringify(facts),
      });
      expect(facts.canonicalBytesUnchanged).toBe(true);
      expect(workloads).toEqual([]);
    });
  }
