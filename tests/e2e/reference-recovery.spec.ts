import { test, expect, authenticate, keyboard } from "./run-failure-fixture";
import { writeFileSync, rmSync } from "node:fs";
import path from "node:path";

for (const viewport of [
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
]) {
  test.describe(`owned observation recovery at ${viewport.width}`, () => {
    test.use({ viewport, scenario: "ownership_recovery" });
    test("same worker version updates unknown and recovered ownership without restarting", async ({
      page,
      failureHost,
    }, info) => {
      await authenticate(page, failureHost);
      const project = await page.evaluate(async () => {
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
          body: JSON.stringify({ name: "Owned observation recovery" }),
        });
        if (created.status !== 201) throw Error("Project setup failed");
        const p = await created.json();
        const edited = await fetch(`/api/v1/projects/${p.projectId}/edits`, {
          method: "POST",
          headers: { ...headers, "If-Match": String(p.revision) },
          body: JSON.stringify({
            baseRevision: p.revision,
            edits: [
              { kind: "set_parameter", parameterId: "duration", value: 15 },
            ],
          }),
        });
        if (edited.status !== 200) throw Error("Owned duration setup failed");
        const result = await edited.json();
        localStorage.setItem("studio.projectId", result.projectId);
        return result;
      });
      await page.reload();
      await expect(
        page.getByRole("heading", { name: project.name, exact: true }),
      ).toBeVisible();
      await keyboard(
        page,
        page.getByRole("button", { name: "Preflight & run", exact: true }),
      );
      await keyboard(
        page,
        page
          .getByRole("dialog", { name: "Execution preflight", exact: true })
          .getByRole("button", { name: "Start frozen snapshot", exact: true }),
      );
      const controls = page.getByRole("region", {
        name: "Run controls",
        exact: true,
      });
      const startup = page.getByRole("region", {
        name: "Reported startup",
        exact: true,
      });
      await expect(
        controls.getByRole("button", { name: "Pause", exact: true }),
      ).toBeEnabled();
      const listed = (
        await (
          await page.request.get(
            failureHost.origin + `/api/v1/runs?projectId=${project.projectId}`,
          )
        ).json()
      ).items;
      expect(listed).toHaveLength(1);
      const before = listed[0];
      const readRun = async () =>
        await (
          await page.request.get(
            failureHost.origin + `/api/v1/runs/${before.runId}`,
          )
        ).json();
      const frozen = await (
        await page.request.get(
          failureHost.origin + `/api/v1/runs/${before.runId}/snapshot`,
        )
      ).json();
      expect(before.state).toBe("running");
      const marker = path.join(failureHost.data, "deny-owned-observation");
      let unknown: any;
      try {
        writeFileSync(marker, "Owned fixture observation denial only");
        await expect(startup).toContainText("Startup or ownership unresolved");
        await expect(
          controls.getByRole("button", { name: "Pause", exact: true }),
        ).toBeDisabled();
        unknown = await readRun();
        expect(unknown.state).toBe("unknown");
        expect(unknown.reason).toBe("OWNERSHIP_UNKNOWN");
        expect(unknown.stateVersion).toBe(before.stateVersion);
        expect(unknown.observationVersion).toBeGreaterThan(
          before.observationVersion,
        );
      } finally {
        rmSync(marker, { force: true });
      }
      // Ordinary metadata polling, without direct replacement through a control callback.
      await expect(
        controls.getByRole("button", { name: "Pause", exact: true }),
      ).toBeEnabled();
      await expect(startup).toContainText("Workload start recorded");
      await expect(startup).not.toContainText("OWNERSHIP_UNKNOWN");
      const recovered = await readRun();
      expect(recovered.state).toBe("running");
      expect(recovered.stateVersion).toBe(before.stateVersion);
      expect(recovered.observationVersion).toBeGreaterThan(
        unknown.observationVersion,
      );
      expect(recovered).not.toHaveProperty("reason");
      expect(recovered.runId).toBe(before.runId);
      expect(recovered.snapshotId).toBe(before.snapshotId);
      await keyboard(
        page,
        controls.getByRole("button", { name: "Pause", exact: true }),
      );
      await expect(
        controls.locator('[data-control-operation="completed"]'),
      ).toContainText("Pause request");
      await keyboard(
        page,
        controls.getByRole("button", { name: "Stop", exact: true }),
      );
      await expect(
        controls.locator('[data-control-operation="completed"]'),
      ).toContainText("Stop request");
      const ended = await readRun();
      expect(ended.state).toBe("stopped");
      expect(ended.cleanup).toBe("complete");
      expect(ended.evidence).toBe("complete");
      expect(ended.verdict).toBeNull();
      expect(
        await (
          await page.request.get(
            failureHost.origin + `/api/v1/runs/${before.runId}/snapshot`,
          )
        ).json(),
      ).toEqual(frozen);
      expect(
        await (
          await page.request.get(
            failureHost.origin + `/api/v1/projects/${project.projectId}`,
          )
        ).json(),
      ).toEqual(project);
      expect(
        (
          await (
            await page.request.get(
              failureHost.origin +
                `/api/v1/runs?projectId=${project.projectId}`,
            )
          ).json()
        ).items,
      ).toHaveLength(1);
      await info.attach("owned-observation-ordering", {
        body: JSON.stringify({
          scope:
            "Actual owned native worker/backend/browser; injected observation denial, no equipment",
          viewport,
          runId: before.runId,
          snapshotId: before.snapshotId,
          workerStateVersion: before.stateVersion,
          observationVersions: [
            before.observationVersion,
            unknown.observationVersion,
            recovered.observationVersion,
          ],
        }),
        contentType: "application/json",
      });
    });
  });
}
