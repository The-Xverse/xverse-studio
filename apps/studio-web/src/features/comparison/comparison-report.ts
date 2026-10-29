import type { Data } from "../../api/types";
const object = (v: any): v is Data =>
  !!v && typeof v === "object" && !Array.isArray(v);
const text = (v: any, max = 512) =>
  typeof v === "string" && v.length > 0 && v.length <= max;
const integer = (v: any, max = Number.MAX_SAFE_INTEGER) =>
  Number.isSafeInteger(v) && v >= 0 && v <= max;
const hash = (v: any) =>
  typeof v === "string" && /^sha256:[0-9a-f]{64}$/.test(v);
const tick = (v: any) =>
  typeof v === "string" && v.length <= 32 && /^-?(?:0|[1-9][0-9]*)$/.test(v);
const number = (v: any) => typeof v === "number" && Number.isFinite(v);
const fail = (): never => {
  throw new Error(
    "The comparison response is malformed, unsupported or belongs to another run selection. Retry inspection.",
  );
};
export const configurationLabels: Record<string, string> = {
  semanticDigest: "Model digest",
  planDigest: "Plan digest",
  model: "Model resources",
  deployment: "Deployment and bindings",
  scenario: "Scenario",
  parameters: "Parameters",
  artifactIdentities: "Artifacts",
  profileIdentities: "Profiles",
  providerIdentity: "Provider",
  capabilityDigest: "Capabilities",
  clockDefinitions: "Clocks and mappings",
  compiler: "Compiler",
};
function bounded(value: any) {
  const todo: [any, number][] = [[value, 0]];
  let nodes = 0;
  while (todo.length) {
    const [v, depth] = todo.pop()!;
    if (++nodes > 8192 || depth > 20) fail();
    if (v === null || typeof v === "boolean" || number(v)) continue;
    if (typeof v === "string") {
      if (v.length > 65536) fail();
      continue;
    }
    if (!object(v) && !Array.isArray(v)) fail();
    const entries = Object.entries(v);
    if (entries.length > 2048 || entries.some(([k]) => k.length > 4096)) fail();
    for (const [, item] of entries) todo.push([item, depth + 1]);
  }
  if (JSON.stringify(value).length > 65536) fail();
  return value;
}
function canonical(value: any): string {
  return JSON.stringify(value, (_, v) =>
    object(v)
      ? Object.fromEntries(
          Object.keys(v)
            .sort()
            .map((k) => [k, v[k]]),
        )
      : v,
  );
}
function identity(
  v: any,
  expected: { runId: string; snapshotId: string; projectId?: string },
) {
  if (
    !object(v) ||
    v.runId !== expected.runId ||
    v.snapshotId !== expected.snapshotId ||
    (expected.projectId !== undefined && v.projectId !== expected.projectId) ||
    !hash(v.snapshotDigest) ||
    !text(v.projectId, 80) ||
    !integer(v.revision) ||
    v.revision < 1 ||
    !text(v.state) ||
    !text(v.cleanup) ||
    !text(v.snapshotIntegrity) ||
    !text(v.evidenceIntegrity) ||
    !text(v.evidenceStatus) ||
    typeof v.effectiveInputsMatch !== "boolean"
  )
    fail();
  return Object.fromEntries(
    [
      "runId",
      "snapshotId",
      "snapshotDigest",
      "projectId",
      "revision",
      "state",
      "cleanup",
      "snapshotIntegrity",
      "evidenceIntegrity",
      "evidenceStatus",
      "effectiveInputsMatch",
    ].map((k) => [k, v[k]]),
  );
}
const codes = (v: any) =>
  Array.isArray(v) &&
  v.length <= 32 &&
  new Set(v).size === v.length &&
  v.every((c) => text(c, 100) && /^[A-Z_]+$/.test(c));
function observation(v: any) {
  if (!object(v) || typeof v.available !== "boolean") fail();
  if (!v.available) return { available: false };
  if (
    !["unit", "quantity", "unitDefinitionDigest", "clockDomainRef"].every(
      (k) => v[k] === null || text(v[k]),
    ) ||
    !object(v.coverage) ||
    typeof v.coverage.verified !== "boolean" ||
    typeof v.coverage.complete !== "boolean" ||
    !["startTick", "endTick"].every(
      (k) => v.coverage[k] === null || tick(v.coverage[k]),
    ) ||
    !(v.coverage.gapCount === null || integer(v.coverage.gapCount, 100000)) ||
    !object(v.summary) ||
    !["available", "unavailable"].includes(v.summary.status)
  )
    fail();
  if (
    v.sourceTime !== null &&
    (!object(v.sourceTime) ||
      !(v.sourceTime.resolution === null || text(v.sourceTime.resolution)) ||
      !(
        v.sourceTime.uncertainty === null ||
        (number(v.sourceTime.uncertainty) && v.sourceTime.uncertainty >= 0)
      ))
  )
    fail();
  if (
    v.summary.status === "available" &&
    (!integer(v.summary.sampleCount, 100000) ||
      !v.summary.sampleCount ||
      !tick(v.summary.firstTick) ||
      !tick(v.summary.lastTick) ||
      !["minimum", "maximum", "lastValue"].every((k) => number(v.summary[k])))
  )
    fail();
  return {
    available: true,
    ...Object.fromEntries(
      ["unit", "quantity", "unitDefinitionDigest", "clockDomainRef"].map(
        (k) => [k, v[k]],
      ),
    ),
    sourceTime:
      v.sourceTime === null
        ? null
        : {
            resolution: v.sourceTime.resolution,
            uncertainty: v.sourceTime.uncertainty,
          },
    coverage: Object.fromEntries(
      ["verified", "complete", "startTick", "endTick", "gapCount"].map((k) => [
        k,
        v.coverage[k],
      ]),
    ),
    summary:
      v.summary.status === "available"
        ? Object.fromEntries(
            [
              "status",
              "sampleCount",
              "firstTick",
              "lastTick",
              "minimum",
              "maximum",
              "lastValue",
            ].map((k) => [k, v.summary[k]]),
          )
        : { status: "unavailable" },
  };
}
export function comparisonReport(
  v: any,
  left: { runId: string; snapshotId: string; projectId?: string },
  right: { runId: string; snapshotId: string; projectId?: string },
): Data {
  if (
    !object(v) ||
    v.comparisonVersion !== "1.0" ||
    v.mode !== "recorded_observation_comparison" ||
    v.rerunRequiresFreshAdmission !== true ||
    v.leftRunId !== left.runId ||
    v.rightRunId !== right.runId ||
    typeof v.compatible !== "boolean" ||
    !codes(v.diagnostics) ||
    v.compatible !== (v.diagnostics.length === 0) ||
    !Array.isArray(v.configuration) ||
    v.configuration.length !== Object.keys(configurationLabels).length ||
    !Array.isArray(v.fields) ||
    v.fields.length > 32 ||
    !Array.isArray(v.limitations) ||
    v.limitations.length > 8 ||
    !v.limitations.every((s: any) => text(s))
  )
    fail();
  const configuration = v.configuration.map((r: any, index: number) => {
    if (
      !object(r) ||
      r.field !== Object.keys(configurationLabels)[index] ||
      typeof r.leftAvailable !== "boolean" ||
      typeof r.rightAvailable !== "boolean"
    )
      fail();
    bounded(r.left);
    bounded(r.right);
    if (
      r.leftAvailable !== (r.left !== null) ||
      r.rightAvailable !== (r.right !== null)
    )
      fail();
    const status =
      !r.leftAvailable || !r.rightAvailable
        ? "unavailable"
        : canonical(r.left) === canonical(r.right)
          ? "same"
          : "different";
    if (r.status !== status) fail();
    return {
      field: r.field,
      status,
      leftAvailable: r.leftAvailable,
      rightAvailable: r.rightAvailable,
      left: r.left,
      right: r.right,
    };
  });
  const fields = v.fields.map((f: any) => {
    if (
      !object(f) ||
      !(f.observerRef === null || text(f.observerRef)) ||
      !(f.field === null || text(f.field)) ||
      typeof f.compatible !== "boolean" ||
      !codes(f.reasons) ||
      f.compatible !== (f.reasons.length === 0)
    )
      fail();
    return {
      observerRef: f.observerRef,
      field: f.field,
      compatible: f.compatible,
      reasons: f.reasons,
      left: observation(f.left),
      right: observation(f.right),
    };
  });
  if (
    v.compatible &&
    (!fields.length ||
      configuration.some((r: Data) => r.status === "unavailable") ||
      fields.some(
        (f: Data) =>
          !f.compatible ||
          !f.left.available ||
          !f.right.available ||
          [f.left, f.right].some(
            (side) =>
              side.summary.status !== "available" ||
              !side.coverage.complete ||
              !side.coverage.verified ||
              side.coverage.startTick === null ||
              side.coverage.endTick === null,
          ),
      ))
  )
    fail();
  if (
    new Set(fields.map((f: Data) => canonical([f.observerRef, f.field])))
      .size !== fields.length
  )
    fail();
  return {
    comparisonVersion: "1.0",
    left: identity(v.left, left),
    right: identity(v.right, right),
    configuration,
    compatible: v.compatible,
    diagnostics: v.diagnostics,
    fields,
    limitations: v.limitations,
  };
}
export function comparisonHistory(v: any, offset: number): Data {
  if (
    !object(v) ||
    !Array.isArray(v.items) ||
    v.items.length > 20 ||
    !(
      v.nextCursor === null ||
      (typeof v.nextCursor === "string" &&
        /^\d{1,16}$/.test(v.nextCursor) &&
        Number.isSafeInteger(Number(v.nextCursor)) &&
        Number(v.nextCursor) === offset + 20 &&
        v.items.length === 20)
    )
  )
    fail();
  const items = v.items.map((r: any) => {
    if (
      !object(r) ||
      !text(r.runId, 80) ||
      !text(r.snapshotId, 80) ||
      !text(r.projectId, 80) ||
      !text(r.state)
    )
      fail();
    return {
      runId: r.runId,
      snapshotId: r.snapshotId,
      projectId: r.projectId,
      state: r.state,
    };
  });
  if (new Set(items.map((r: Data) => r.runId)).size !== items.length) fail();
  return { items, nextCursor: v.nextCursor, offset };
}
