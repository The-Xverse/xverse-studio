import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { connectStudio } from "./connect-studio";
import { traceApi } from "./trace-claims-flow";

for (const mode of [
  "failed",
  "unknown",
  "rejected with child",
  "rejected without error",
  "rejected retryable",
  "rejected foreign scope",
])
  for (const width of [1024, 1440])
    test(`rejected rerun receipt guard: ${mode} at ${width}`, async ({
      page,
    }, info) => {
      await page.setViewportSize({ width, height: width === 1024 ? 768 : 900 });
      await connectStudio(page, info);
      let project = (
        await traceApi(page, "/projects", "POST", {
          name: "Labelled rejected receipt guard " + width,
        })
      ).body;
      const edited = await traceApi(
        page,
        `/projects/${project.projectId}/edits`,
        "POST",
        {
          baseRevision: project.revision,
          edits: [
            { kind: "set_parameter", parameterId: "duration", value: 0.2 },
          ],
        },
        project.revision,
      );
      expect(edited.status).toBe(200);
      project = edited.body;
      const pf = (
        await traceApi(
          page,
          `/projects/${project.projectId}/preflights`,
          "POST",
          { revision: project.revision },
        )
      ).body;
      expect(pf.status).toBe("ready");
      const accepted = await traceApi(page, "/runs", "POST", {
        snapshotId: pf.snapshotId,
        preflightId: pf.preflightId,
      });
      expect(accepted.status).toBe(202);
      const original = accepted.body.runId;
      await expect
        .poll(
          async () => (await traceApi(page, "/runs/" + original)).body.state,
          { timeout: 20000 },
        )
        .toBe("stopped");
      await page.evaluate(
        ({ pid, rid }) => {
          localStorage.setItem("studio.projectId", pid);
          localStorage.setItem("studio.lastRun", rid);
          localStorage.setItem("studio.lastRun." + pid, rid);
        },
        { pid: project.projectId, rid: original },
      );
      await page.reload();
      await page.getByRole("tab", { name: "Results", exact: false }).click();
      await expect(
        page.getByLabel("Recorded run", { exact: true }),
      ).toHaveValue(original);
      const attempts: string[] = [];
      page.on("request", (request) => {
        if (
          request.method() === "POST" &&
          request.url().endsWith(`/runs/${original}/reruns`)
        )
          attempts.push(request.headers()["idempotency-key"] || "");
      });
      let actual: any;
      const originalSnapshot = (
        await traceApi(page, `/runs/${original}/snapshot`)
      ).body.snapshot;
      await page.route("**/api/v1/operations/*", async (route) => {
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        const body = await response.json();
        if (body.kind !== "rerun") {
          await route.fulfill({ response });
          return;
        }
        expect(body.status).toBe("completed");
        actual = body;
        const fixture = structuredClone(body);
        fixture.status =
          mode === "failed" || mode === "unknown" ? mode : "rejected";
        fixture.error = {
          code: "LABELLED_RECEIPT_UNCONFIRMED",
          message:
            "Labelled receipt does not prove rejection before child admission.",
          retryable: false,
        };
        if (mode !== "rejected with child") {
          delete fixture.runId;
          delete fixture.result;
        }
        if (mode === "rejected without error") delete fixture.error;
        if (mode === "rejected retryable") fixture.error.retryable = true;
        if (mode === "rejected foreign scope")
          fixture.evidenceScope = "labelled-foreign-scope";
        await route.fulfill({ status: 200, json: fixture });
      });
      const button = page.getByRole("button", {
        name: "Rerun frozen inputs",
        exact: true,
      });
      await button.focus();
      await page.keyboard.press("Enter");
      await expect.poll(() => actual?.result?.runId).toBeTruthy();
      await expect(button).toBeEnabled();
      await expect(page.getByRole("alert")).toContainText(
        /retains the same request key|same operation identity/,
      );
      await expect(
        page.getByLabel("Recorded run", { exact: true }),
      ).toHaveValue(original);
      const key = await page.evaluate(
        (rid) => localStorage.getItem("studio.pendingRerun." + rid),
        original,
      );
      expect(key).toBeTruthy();
      expect(key).toBe(attempts[0]);
      const child = actual.result.runId;
      await expect
        .poll(async () => (await traceApi(page, "/runs/" + child)).body.state, {
          timeout: 20000,
        })
        .toBe("stopped");
      const childSnapshot = (await traceApi(page, `/runs/${child}/snapshot`))
        .body.snapshot;
      const files = [
        `runs/${original}/evidence.jsonl`,
        `runs/${child}/evidence.jsonl`,
        `snapshots/${originalSnapshot.snapshotId}/snapshot.json`,
        `snapshots/${childSnapshot.snapshotId}/snapshot.json`,
      ];
      const hash = (n: string) =>
        createHash("sha256")
          .update(readFileSync(path.join(process.env.STUDIO_BROWSER_DATA!, n)))
          .digest("hex");
      const before = Object.fromEntries(files.map((n) => [n, hash(n)]));
      await button.focus();
      await page.keyboard.press("Enter");
      await expect.poll(() => attempts.length).toBe(2);
      await expect(button).toBeEnabled();
      expect(attempts[1]).toBe(key);
      expect(
        await page.evaluate(
          (rid) => localStorage.getItem("studio.pendingRerun." + rid),
          original,
        ),
      ).toBe(key);
      const runIds = (
        await traceApi(page, "/runs?projectId=" + project.projectId)
      ).body.items
        .map((r: any) => r.runId)
        .sort();
      expect(runIds).toEqual([original, child].sort());
      expect(files.every((n) => hash(n) === before[n])).toBe(true);
      await page.unroute("**/api/v1/operations/*");
      await button.focus();
      await page.keyboard.press("Enter");
      await expect(
        page.getByLabel("Recorded run", { exact: true }),
      ).toHaveValue(child);
      expect(attempts).toEqual([key, key, key]);
      expect(
        await page.evaluate(
          (rid) => localStorage.getItem("studio.pendingRerun." + rid),
          original,
        ),
      ).toBeNull();
      expect(
        (
          await traceApi(page, "/runs?projectId=" + project.projectId)
        ).body.items
          .map((r: any) => r.runId)
          .sort(),
      ).toEqual(runIds);
      expect(files.every((n) => hash(n) === before[n])).toBe(true);
      await info.attach("labelled-rejected-receipt-control", {
        contentType: "application/json",
        body: JSON.stringify({
          scope:
            "Labelled transport-only status/receipt faults after one actual owned child. Canonical files unchanged; valid retry acknowledges the same actual child.",
          mode,
          width,
          original,
          child,
          attempts,
          canonicalBytesUnchanged: true,
          exactlyOneChild: true,
        }),
      });
    });
