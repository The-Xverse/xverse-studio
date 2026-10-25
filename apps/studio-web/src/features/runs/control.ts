import { ApiError, api } from "../../api/client";
import type { Run } from "../../api/types";
import type { Command, Start } from "../../../../../packages/contracts/api";

// Durable browser receipts for side-effecting run requests. A lost acknowledgement
// is retried only with the original idempotency key and payload, so a retry from
// a refreshed page or another tab resolves the same backend run or operation.

export interface PendingStart {
  key: string;
  projectId: string;
  snapshotId: string;
  preflightId: string;
  sentAt: number;
}

export interface PendingCommand {
  key: string;
  runId: string;
  kind: string;
  expectedStateVersion: number;
  sentAt: number;
  operationId?: string;
  status?: string;
  code?: string;
}

export type OperationStatus =
  "accepted" | "delegated" | "completed" | "rejected" | "failed" | "unknown";

const OPERATION_STATUSES = [
  "accepted",
  "delegated",
  "completed",
  "rejected",
  "failed",
  "unknown",
];
const startName = (projectId: string) => "studio.pendingStart." + projectId,
  commandName = (runId: string) => "studio.pendingCommand." + runId;

function read(name: string): any {
  try {
    const value = JSON.parse(localStorage.getItem(name) || "null");
    return value && typeof value === "object" ? value : null;
  } catch {
    return null;
  }
}

function write(name: string, value: unknown) {
  try {
    localStorage.setItem(name, JSON.stringify(value));
  } catch {
    /* Storage loss only removes the browser receipt; the backend keeps the request. */
  }
}

export function readPendingStart(projectId: string): PendingStart | null {
  const value = read(startName(projectId));
  return value &&
    typeof value.key === "string" &&
    value.projectId === projectId &&
    typeof value.snapshotId === "string" &&
    typeof value.preflightId === "string" &&
    Number.isFinite(value.sentAt)
    ? value
    : null;
}

export function writePendingStart(value: PendingStart) {
  write(startName(value.projectId), value);
}

export function clearPendingStart(projectId: string) {
  localStorage.removeItem(startName(projectId));
}

export function readPendingCommand(runId: string): PendingCommand | null {
  const value = read(commandName(runId));
  return value &&
    typeof value.key === "string" &&
    value.runId === runId &&
    ["stop", "cancel"].includes(value.kind) &&
    Number.isInteger(value.expectedStateVersion) &&
    Number.isFinite(value.sentAt) &&
    (value.operationId === undefined ||
      typeof value.operationId === "string") &&
    (value.status === undefined || OPERATION_STATUSES.includes(value.status)) &&
    (value.code === undefined || typeof value.code === "string")
    ? value
    : null;
}

export function writePendingCommand(value: PendingCommand) {
  write(commandName(value.runId), value);
}

export function clearPendingCommand(runId: string) {
  localStorage.removeItem(commandName(runId));
}

export function isPendingCommandStorageKey(name: string | null, runId: string) {
  return name === null || name === commandName(runId);
}

// A typed rejection of the request itself is a definitive answer. Transport failure,
// timeout, throttling, server errors and session/origin refusals (checked before the
// idempotency record) say nothing about an earlier delivery, so the receipt stays.
export function isDefinitiveRejection(error: unknown) {
  return (
    error instanceof ApiError &&
    error.status >= 400 &&
    error.status < 500 &&
    ![401, 403, 408, 425, 429].includes(error.status)
  );
}

export function startRequest(pending: PendingStart) {
  return api<Run>("/runs", {
    method: "POST",
    body: {
      snapshotId: pending.snapshotId,
      preflightId: pending.preflightId,
    } satisfies Start,
    key: pending.key,
  });
}

export function commandRequest(pending: PendingCommand) {
  return api<{ operationId: string; status: OperationStatus }>(
    `/runs/${encodeURIComponent(pending.runId)}/commands`,
    {
      method: "POST",
      body: {
        kind: pending.kind as Command["kind"],
        expectedStateVersion: pending.expectedStateVersion,
        parameters: {},
      } satisfies Command,
      key: pending.key,
    },
  );
}

export const settledOperation = (status: unknown) =>
  ["completed", "rejected", "failed"].includes(String(status));

export const operationMeaning: Record<string, string> = {
  sending: "Sent. Waiting for the backend to acknowledge this request.",
  unacknowledged:
    "The acknowledgement was not received. The backend may or may not have accepted it; retrying reuses the same request identity and cannot issue a second command.",
  accepted:
    "Durably accepted by the backend. Acceptance is not execution; it has not yet been delegated to the owned workload.",
  delegated:
    "Delivered to the owned workload. Its effect is not yet confirmed.",
  completed: "The owned workload confirmed that this request took effect.",
  rejected: "The backend rejected this request; nothing was executed.",
  failed:
    "Accepted, but it did not take effect. The run's lifecycle outcome is reported separately.",
  unknown:
    "The backend cannot prove whether this request took effect. It is not replayed automatically; reconcile before acting again.",
};

// Mirrors the backend's owned command admission; the backend re-checks every request.
const COMMAND_STATES = ["running", "preparing", "ready", "paused"];

export function controlAvailability(
  run: Run,
  kind: string,
  pending: PendingCommand | null,
): { available: boolean; reason: string } {
  const capabilities: unknown[] = Array.isArray(run.capabilities)
    ? run.capabilities
    : [];
  const state = String(run.state || run.status || "unknown");
  if (!capabilities.includes(kind))
    return {
      available: false,
      reason: `The run's provider does not admit ${kind}.`,
    };
  if (!COMMAND_STATES.includes(state))
    return {
      available: false,
      reason:
        state === "unknown"
          ? "Ownership is unconfirmed, so Studio cannot send controls. Reconcile first."
          : `Not available while the run is ${state}.`,
    };
  if (pending && !settledOperation(pending.status))
    return {
      available: false,
      reason: `A ${pending.kind} request must settle before another control.`,
    };
  return { available: true, reason: "" };
}
