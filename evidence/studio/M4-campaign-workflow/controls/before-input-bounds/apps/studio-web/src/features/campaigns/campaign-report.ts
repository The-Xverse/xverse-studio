import type { Data } from "../../api/types";
import { text } from "../lab/public-observations";

const object = (v: any): v is Data =>
  !!v && typeof v === "object" && !Array.isArray(v);
const hash = (v: any) =>
  typeof v === "string" && /^sha256:[a-f0-9]{64}$/.test(v);
const number = (v: any) => typeof v === "number" && Number.isFinite(v);
const integer = (v: any, min: number, max: number) =>
  Number.isSafeInteger(v) && v >= min && v <= max;
const matrix = (v: any) =>
  object(v) &&
  Object.keys(v).length > 0 &&
  Object.keys(v).length <= 8 &&
  Object.entries(v).every(
    ([k, a]) =>
      text(k, 256) &&
      Array.isArray(a) &&
      a.length > 0 &&
      a.length <= 16 &&
      a.every(number) &&
      new Set(a).size === a.length,
  );
export function canonical(value: any): string {
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
const fail = (): never => {
  throw new Error(
    "The campaign response is malformed, unsupported or belongs to another selection. Refresh to retry.",
  );
};

/** A display boundary, not an alternative planner or source validator. */
export function campaignReport(
  value: any,
  expectedId?: string,
  previewBody?: Data,
): Data {
  if (
    !object(value) ||
    value.campaignVersion !== "1.0" ||
    !text(value.baseSnapshotId, 80) ||
    !hash(value.baseSnapshotDigest) ||
    !object(value.baseInput) ||
    !["verified", "unavailable"].includes(value.baseInput.status) ||
    !matrix(value.matrix) ||
    !object(value.budget) ||
    !integer(value.budget.maxRuns, 1, 32) ||
    !number(value.budget.maxTotalSeconds) ||
    value.budget.maxTotalSeconds <= 0 ||
    !number(value.estimatedTotalSeconds) ||
    value.estimatedTotalSeconds <= 0 ||
    value.estimatedTotalSeconds > value.budget.maxTotalSeconds ||
    !integer(value.concurrency, 1, 1) ||
    !["continue", "stop_on_failure"].includes(value.stopPolicy) ||
    !integer(value.cardinality, 1, 32) ||
    value.cardinality > value.budget.maxRuns ||
    !Array.isArray(value.children) ||
    value.children.length !== value.cardinality
  )
    fail();
  const base = value.baseInput;
  if (base.status === "verified") {
    if (
      base.snapshotId !== value.baseSnapshotId ||
      !hash(base.snapshotDigest) ||
      !text(base.projectId, 80) ||
      !integer(base.revision, 1, Number.MAX_SAFE_INTEGER) ||
      !text(base.providerId, 256) ||
      !object(base.selection) ||
      !["systemRef", "deploymentRef", "scenarioRef"].every(
        (k) =>
          text(base.selection[k], 4096) &&
          base.selection[k].startsWith("xdl://"),
      )
    )
      fail();
  } else if (base.reason !== "SNAPSHOT_INTEGRITY") fail();
  const product = Object.values(value.matrix).reduce<number>(
    (n, v: any) => n * v.length,
    1,
  );
  if (product !== value.cardinality) fail();
  if (expectedId !== undefined && value.campaignId !== expectedId) fail();
  if (previewBody) {
    if (
      value.campaignId !== undefined ||
      base.status !== "verified" ||
      value.baseSnapshotId !== previewBody.snapshotId ||
      canonical(value.matrix) !== canonical(previewBody.matrix) ||
      canonical(value.budget) !== canonical(previewBody.budget) ||
      value.stopPolicy !== previewBody.stopPolicy ||
      value.concurrency !== previewBody.concurrency
    )
      fail();
  } else if (
    !text(value.campaignId, 80) ||
    !integer(value.revision, 1, Number.MAX_SAFE_INTEGER) ||
    !["pending", "running", "cancelling", "complete", "cancelled"].includes(
      value.status,
    ) ||
    typeof value.cancelRequested !== "boolean" ||
    !number(value.createdAt) ||
    !text(value.operationId, 80)
  )
    fail();
  const children = value.children.map((c: any, index: number) => {
    if (
      !object(c) ||
      c.index !== index ||
      !hash(c.childKey) ||
      !object(c.parameters) ||
      canonical(Object.keys(c.parameters).sort()) !==
        canonical(Object.keys(value.matrix).sort()) ||
      !Object.entries(c.parameters).every(
        ([k, v]) => number(v) && value.matrix[k].includes(v),
      ) ||
      ![
        "pending",
        "dispatching",
        "running",
        "unknown",
        "stopped",
        "failed",
        "cancelled",
        "rejected",
      ].includes(c.state) ||
      !(c.runId === null || text(c.runId, 80)) ||
      (["running", "stopped", "failed"].includes(c.state) &&
        !text(c.runId, 80)) ||
      (c.state === "pending" && c.runId !== null) ||
      (c.reason !== undefined && !text(c.reason, 256)) ||
      (previewBody && (c.state !== "pending" || c.runId !== null))
    )
      fail();
    return {
      index,
      childKey: c.childKey,
      parameters: c.parameters,
      state: c.state,
      runId: c.runId,
      reason: c.reason,
    };
  });
  if (
    new Set(children.map((c: Data) => c.childKey)).size !== children.length ||
    new Set(children.filter((c: Data) => c.runId).map((c: Data) => c.runId))
      .size !== children.filter((c: Data) => c.runId).length
  )
    fail();
  return { ...value, children };
}

export function campaignPage(value: any): Data {
  if (
    !object(value) ||
    !Array.isArray(value.items) ||
    value.items.length > 20 ||
    !(
      value.nextCursor === null ||
      (text(value.nextCursor, 16) && /^\d+$/.test(value.nextCursor))
    )
  )
    fail();
  const items = value.items.map((v: any) => campaignReport(v));
  if (new Set(items.map((v: Data) => v.campaignId)).size !== items.length)
    fail();
  return { items, nextCursor: value.nextCursor };
}
