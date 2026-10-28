import { test, expect, authenticate, keyboard } from "./run-failure-fixture";

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  for (const scenario of [
    "mismatch",
    "launch_denied",
    "active_failure",
    "normal",
  ]) {
    test.describe(`run startup ${scenario} at ${viewport.width}`, () => {
      test.use({ viewport, scenario });
      test("actual startup and cleanup facts preserve immutable inputs", async ({
        page,
        failureHost,
      }, info) => {
        test.skip(
          scenario === "active_failure" && process.platform !== "linux",
          "Owned Linux SIGINT/sleep fault; no native Windows claim",
        );
        await authenticate(page, failureHost);
        const project = await page.evaluate(
          async (duration) => {
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
              body: JSON.stringify({ name: "Owned startup outcome" }),
            });
            if (created.status !== 201)
              throw Error("Owned project setup failed");
            const p = await created.json();
            const edited = await fetch(
              `/api/v1/projects/${p.projectId}/edits`,
              {
                method: "POST",
                headers: { ...headers, "If-Match": String(p.revision) },
                body: JSON.stringify({
                  baseRevision: p.revision,
                  edits: [
                    {
                      kind: "set_parameter",
                      parameterId: "duration",
                      value: duration,
                    },
                    {
                      kind: "set_parameter",
                      parameterId: "timestep",
                      value: 1,
                    },
                  ],
                }),
              },
            );
            if (edited.status !== 200)
              throw Error("Owned parameter setup failed");
            const result = await edited.json();
            localStorage.setItem("studio.projectId", result.projectId);
            return result;
          },
          scenario === "normal" ? 10 : 5,
        );
        await page.reload();
        await expect(
          page.getByRole("heading", { name: project.name, exact: true }),
        ).toBeVisible();
        await keyboard(
          page,
          page.getByRole("button", { name: "Preflight & run", exact: true }),
        );
        const dialog = page.getByRole("dialog", {
          name: "Execution preflight",
          exact: true,
        });
        await expect(dialog).toBeVisible();
        const originalSnapshots = await page.evaluate(async (id) => {
          const runList = await fetch(`/api/v1/runs?projectId=${id}`).then(
            (r) => r.json(),
          );
          return runList.items.length;
        }, project.projectId);
        expect(originalSnapshots).toBe(0);
        await keyboard(
          page,
          dialog.getByRole("button", {
            name: "Start frozen snapshot",
            exact: true,
          }),
        );
        const startup = page.getByRole("region", {
          name: "Reported startup",
          exact: true,
        });
        await expect(startup).toBeVisible();
        if (scenario === "normal") {
          await expect(startup).toContainText("Workload start recorded");
          await keyboard(
            page,
            page
              .getByRole("region", { name: "Run controls", exact: true })
              .getByRole("button", { name: "Stop", exact: true }),
          );
        } else if (scenario === "active_failure") {
          await expect(startup).toContainText(
            "Start recorded; execution failed",
          );
          await expect(startup).toContainText("REFERENCE_WORKER_ERROR");
        } else {
          await expect(startup).toContainText("Startup rejected");
          await expect(startup).toContainText(
            scenario === "mismatch"
              ? "EFFECTIVE_INPUT_MISMATCH"
              : "LAUNCH_FAILED",
          );
        }
        const expected = scenario === "normal" ? "stopped" : "failed";
        await expect
          .poll(async () => {
            const response = await page.request.get(
              failureHost.origin +
                `/api/v1/runs?projectId=${project.projectId}`,
            );
            const rows = (await response.json()).items;
            expect(rows).toHaveLength(1);
            return rows[0].state;
          })
          .toBe(expected);
        const run = (
          await (
            await page.request.get(
              failureHost.origin +
                `/api/v1/runs?projectId=${project.projectId}`,
            )
          ).json()
        ).items[0];
        const cleanup =
          scenario === "normal" || scenario === "mismatch"
            ? "complete"
            : "unknown";
        expect(run.cleanup).toBe(cleanup);
        expect(run.verdict).toBeNull();
        await expect(
          page
            .locator(".result-status-grid .status-card")
            .filter({ hasText: "Cleanup" }),
        ).toContainText(cleanup);
        if (cleanup === "unknown")
          await expect(
            page.getByRole("heading", {
              name: "Unresolved owned resources",
              exact: true,
            }),
          ).toBeVisible();
        const frozen = await (
          await page.request.get(
            failureHost.origin + `/api/v1/runs/${run.runId}/snapshot`,
          )
        ).json();
        expect(frozen.integrity).toBe("valid");
        expect(frozen.snapshot.revision).toBe(project.revision);
        expect(
          await (
            await page.request.get(
              failureHost.origin + `/api/v1/projects/${project.projectId}`,
            )
          ).json(),
        ).toEqual(project);
        const denied = await page.evaluate(async (run) => {
          const { csrfToken } = await fetch("/api/v1/session").then((r) =>
            r.json(),
          );
          const response = await fetch(`/api/v1/runs/${run.runId}/commands`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrfToken,
              "Idempotency-Key": "owned-unsupported-pause",
            },
            body: JSON.stringify({
              kind: "pause",
              expectedStateVersion: run.stateVersion,
            }),
          });
          return { status: response.status, value: await response.json() };
        }, run);
        expect(denied.status).toBe(422);
        await expect(
          page.getByRole("region", { name: "Run controls", exact: true }),
        ).toContainText("Not admitted for this run");
        await info.attach("owned-startup-outcome", {
          body: JSON.stringify({
            scope: "Owned native fixture; no equipment",
            scenario,
            state: run.state,
            cleanup: run.cleanup,
            evidence: run.evidence,
            reason: run.reason ?? null,
            startRecorded: typeof run.startedAt === "number",
            snapshotId: run.snapshotId,
            projectUnchanged: true,
          }),
          contentType: "application/json",
        });
      });
    });
  }
}
