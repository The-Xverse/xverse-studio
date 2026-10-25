import { test, expect } from "@playwright/test";
import {
  admittedStatuses,
  dimensions,
  planIdentity,
  readinessFacts,
} from "../../apps/studio-web/src/features/preflight/readiness";
import type { Preflight } from "../../apps/studio-web/src/api/types";
function report(): Preflight {
  const digest = "sha256:" + "a".repeat(64),
    selection = {
      systemRef: "xdl://org.example/system/display",
      deploymentRef: "xdl://org.example/deployment/display",
      scenarioRef: "xdl://org.example/scenario/display",
    };
  return {
    preflightId: "display-fixture",
    snapshotId: "display-snapshot",
    snapshotDigest: "sha256:" + "b".repeat(64),
    revision: 1,
    status: "ready",
    planDigest: digest,
    semanticDigest: "sha256:" + "c".repeat(64),
    readinessVersion: "1.0",
    readiness: Object.fromEntries(
      dimensions.map(([id]) => [
        id,
        {
          status: "ready",
          message: "Display contract fixture, no runtime admission",
          elementRefs: [],
          diagnosticCodes: [],
          remediation: "",
        },
      ]),
    ),
    diagnostics: [],
    selection,
    planPreview: {
      snapshotId: "display-snapshot",
      snapshotDigest: "sha256:" + "b".repeat(64),
      revision: 1,
      selection,
      planDigest: digest,
      semanticDigest: "sha256:" + "c".repeat(64),
      scope: "declared_intent_only",
      plan: { digest: { algorithm: "sha256", value: "a".repeat(64) } },
    },
  };
}
test("readiness display contract never promotes a ready aggregate into missing or unknown facts", () => {
  const value = report();
  delete value.readiness;
  expect(
    readinessFacts(value).every(
      (row) =>
        row.status === "not_reported" && !admittedStatuses.has(row.status),
    ),
  ).toBe(true);
  value.readiness = {
    backend: { status: "unknown", message: "No probe result" },
    model: { status: { malformed: true } },
  };
  const facts = readinessFacts(value);
  expect(facts.find((row) => row.id === "backend")?.status).toBe("unknown");
  expect(facts.find((row) => row.id === "model")?.status).toBe("not_reported");
  value.readinessVersion = "2.0";
  expect(
    readinessFacts(value).every((row) => row.status === "not_reported"),
  ).toBe(true);
});
test("readiness display contract rejects a plan from another snapshot, revision or resource selection", () => {
  const value = report();
  expect(planIdentity(value).matches).toBe(true);
  for (const patch of [
    { snapshotId: "other" },
    { snapshotDigest: "sha256:other" },
    { revision: 2 },
    {
      selection: {
        ...value.selection,
        scenarioRef: "xdl://org.example/scenario/other",
      },
    },
    { planDigest: "sha256:other" },
    { semanticDigest: "sha256:other" },
    { plan: { digest: { algorithm: "sha256", value: "d".repeat(64) } } },
  ])
    expect(
      planIdentity({
        ...value,
        planPreview: { ...value.planPreview, ...patch },
      }).matches,
    ).toBe(false);
  expect(planIdentity({ ...value, planPreview: null }).matches).toBe(false);
});
