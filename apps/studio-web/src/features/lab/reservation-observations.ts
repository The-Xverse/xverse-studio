import type { Data } from "../../api/types";
import { id, text } from "./public-observations";

export const scopes = ["observe", "stimulate", "destructive"] as const;
export type Scope = (typeof scopes)[number];
const finite = (v: unknown) => typeof v === "number" && Number.isFinite(v);
const code = (v: unknown) => typeof v === "string" && /^[A-Z][A-Z0-9_]{0,63}$/.test(v);

function context(v: Data) {
  return v && v.contractVersion === "1.0" && id(v.principal) && finite(v.observedAt) &&
    v.runtimeAdmission === "unavailable" && Array.isArray(v.physicalCommands) && !v.physicalCommands.length;
}

export function reservationOptions(value: Data, assetId: string): Data {
  if (!context(value) || value.assetId !== assetId ||
    !["configured", "unavailable"].includes(value.status) ||
    !(value.providerId === null || id(value.providerId)) ||
    !["fixture", "admitted_integration", "unknown", "unavailable"].includes(value.evidenceScope) ||
    value.maximumDurationSeconds !== 300 || !Array.isArray(value.scopes) || value.scopes.length !== 3 ||
    !scopes.every((scope, i) => {
      const row = value.scopes[i];
      return row && row.scope === scope && typeof row.eligible === "boolean" &&
        Array.isArray(row.reasons) && row.reasons.length <= 4 && row.reasons.every(code) &&
        row.eligible === (row.reasons.length === 0) &&
        (!row.eligible || (value.status === "configured" && id(value.providerId)));
    })) throw new Error("Reservation options are incomplete, malformed or unsupported.");
  return { contractVersion: value.contractVersion, assetId, principal: value.principal,
    observedAt: value.observedAt, status: value.status, providerId: value.providerId,
    evidenceScope: value.evidenceScope, maximumDurationSeconds: value.maximumDurationSeconds,
    scopes: value.scopes.map((row: Data) => ({ scope: row.scope, eligible: row.eligible, reasons: row.reasons })) };
}

export function lease(value: Data): Data {
  if (!value || !id(value.reservationId) || !id(value.assetId) || !id(value.providerId) || !id(value.owner) ||
    !scopes.includes(value.scope) || !finite(value.expiry) ||
    !["owned", "unknown", "released", "expired"].includes(value.status) ||
    !(value.fencingIdentity === null || text(value.fencingIdentity)) ||
    (value.status === "owned" && !text(value.fencingIdentity)) ||
    !(value.lastRenewal === null || finite(value.lastRenewal)) ||
    !["fixture", "prototype", "admitted_integration", "unavailable", "unknown"].includes(value.evidenceScope) ||
    (value.reason !== undefined && !code(value.reason)))
    throw new Error("Reservation ownership is incomplete, malformed or unsupported.");
  return Object.fromEntries(["reservationId", "assetId", "providerId", "owner", "scope", "expiry", "status",
    "fencingIdentity", "lastRenewal", "evidenceScope", "reason"].map((key) => [key, value[key]]));
}

export function reservationHistory(value: Data, cursor: string): Data {
  if (!context(value) || !Array.isArray(value.items) || value.items.length > 200 ||
    !(value.nextCursor === null || (typeof value.nextCursor === "string" && /^\d{1,4}$/.test(value.nextCursor) &&
      Number(value.nextCursor) > Number(cursor || "0") && Number(value.nextCursor) <= 1000)))
    throw new Error("Reservation history is incomplete, malformed or unsupported.");
  const seen = new Set<string>();
  const items = value.items.map((row: Data) => {
    const record = lease(row), flags = row.requests;
    if (record.owner !== value.principal || seen.has(record.reservationId) || !flags ||
      !["renew", "release", "reconcile"].every((key) => typeof flags[key] === "boolean") ||
      (record.status !== "owned" && flags.renew) ||
      (record.status === "unknown" && flags.release) ||
      (["released", "expired"].includes(record.status) && flags.reconcile))
      throw new Error("Reservation history contains inconsistent ownership or request eligibility.");
    seen.add(record.reservationId);
    return { ...record, requests: { renew: flags.renew, release: flags.release, reconcile: flags.reconcile } };
  });
  return { principal: value.principal, observedAt: value.observedAt, items, nextCursor: value.nextCursor };
}

export type Attempt = { principal: string; path: string; method: "POST" | "DELETE"; key: string;
  body?: Data; label: string; kind: "lab_reserve" | "lab_renew" | "lab_release" | "lab_reconcile"; reservationId?: string };

export function restoredAttempt(raw: string | null): Attempt | null {
  if (raw === null) return null;
  if (raw.length > 8192) throw new Error("The saved reservation request exceeds its bound.");
  const a = JSON.parse(raw) as Attempt;
  const asset = /^\/assets\/([A-Za-z0-9:._-]{1,253})\/reservations$/.exec(a?.path),
    reservation = /^\/reservations\/([A-Za-z0-9:._-]{1,253})(?:\/(renewals|reconciliations))?$/.exec(a?.path);
  const duration = a?.body?.durationSeconds;
  const validDuration = Number.isInteger(duration) && duration >= 1 && duration <= 300;
  if (!a || !id(a.principal) || !/^[a-f0-9-]{36}$/.test(a.key) || !text(a.label, 100) ||
    !(asset ? a.kind === "lab_reserve" && a.method === "POST" && id(asset[1]) && !a.reservationId &&
      a.body && Object.keys(a.body).length === 2 && scopes.includes(a.body.scope) && validDuration :
      reservation && id(reservation[1]) && a.reservationId === reservation[1] &&
      (reservation[2] === "renewals" ? a.kind === "lab_renew" && a.method === "POST" && a.body &&
        Object.keys(a.body).length === 2 && text(a.body.fencingIdentity) && validDuration :
        reservation[2] === "reconciliations" ? a.kind === "lab_reconcile" && a.method === "POST" &&
          a.body && Object.keys(a.body).length === 0 : a.kind === "lab_release" && a.method === "DELETE" && a.body === undefined)))
    throw new Error("The saved reservation request is malformed. Its outcome requires operator review.");
  return a;
}

export function operationReceipt(value: Data, attempt: Attempt): Data {
  if (!value || !id(value.operationId) || !id(value.reservationId) ||
    value.principal !== attempt.principal || value.kind !== attempt.kind ||
    value.route !== `${attempt.method} ${attempt.path}` ||
    (attempt.reservationId && value.reservationId !== attempt.reservationId) ||
    !["accepted", "delegated", "completed", "rejected", "failed", "unknown"].includes(value.status) ||
    !finite(value.createdAt) || !value.result || value.result.reservationId !== value.reservationId ||
    (value.result.status !== undefined && !["owned", "unknown", "released", "expired"].includes(value.result.status)) ||
    (value.code !== undefined && !code(value.code)))
    throw new Error("The operation receipt is incomplete, malformed or belongs to another request.");
  return { operationId: value.operationId, reservationId: value.reservationId, status: value.status,
    code: value.code, result: { reservationId: value.reservationId, status: value.result.status } };
}
