import type { Data } from "../../api/types";
import { id, text } from "./public-observations";

const finite = (v: unknown) => typeof v === "number" && Number.isFinite(v);
const hash = (v: unknown) => typeof v === "string" && /^sha256:[a-f0-9]{64}$/.test(v);
const code = (v: unknown) => typeof v === "string" && /^[A-Z][A-Z0-9_]{0,63}$/.test(v);
const object = (v: unknown): v is Data => !!v && typeof v === "object" && !Array.isArray(v);
const noAuthority = (v: Data) => v.runtimeAdmission === "unavailable" && Array.isArray(v.physicalCommands) && v.physicalCommands.length === 0;
const resources = (v: unknown): v is string[] => Array.isArray(v) && v.length <= 8 && v.every(id) && new Set(v).size === v.length;
const error = () => new Error("Connection observation metadata is incomplete, inconsistent or unsupported.");

export type ProbeAttempt = {
  principal: string; assetId: string; providerId: string; bindingDigest: string;
  identityDigest: string; evidenceScope: "fixture" | "admitted_integration";
  contactedResources: string[]; key: string;
};
export type ProbeReference = { attempt: ProbeAttempt; operationId: string };
export type ProbeStore = { version: 1; pending: ProbeAttempt | null; history: ProbeReference[] };

export function probeOptions(v: Data, assetId: string): Data {
  if (!object(v) || v.contractVersion !== "1.0" || v.assetId !== assetId || !id(v.principal) ||
    v.scope !== "observe" || !finite(v.observedAt) || typeof v.allowed !== "boolean" || !noAuthority(v) ||
    !(v.reason === null || code(v.reason)) || v.allowed !== (v.reason === null)) throw error();
  const d = v.installation;
  if (d !== null && (!object(d) || d.contractVersion !== "1.0" || d.assetId !== assetId ||
    !id(d.providerId) || !text(d.providerVersion) || !id(d.bindingRef) || !hash(d.bindingDigest) ||
    !hash(d.identityDigest) || !hash(d.implementationDigest) || !id(d.conformanceRef) || !id(d.authorizationRef) ||
    !["fixture", "admitted_integration"].includes(d.evidenceScope) || !resources(d.contactedResources) ||
    d.contactedResources.length === 0 || !Array.isArray(d.scopes) || d.scopes.length !== 1 || d.scopes[0] !== "observe" ||
    !["Linux", "Windows"].includes(d.hostOS) || !id(d.hostArchitecture) ||
    !Array.isArray(d.declaredSupportedOS) || !d.declaredSupportedOS.length || d.declaredSupportedOS.length > 2 ||
    !d.declaredSupportedOS.every((value: unknown) => ["Linux", "Windows"].includes(value as string)) ||
    !d.declaredSupportedOS.includes(d.hostOS) || !Array.isArray(d.declaredArchitectures) ||
    !d.declaredArchitectures.length || d.declaredArchitectures.length > 8 || !d.declaredArchitectures.every(id) ||
    !d.declaredArchitectures.includes(d.hostArchitecture) || !noAuthority(d))) throw error();
  if (v.allowed && !d) throw error();
  return { contractVersion: "1.0", assetId, principal: v.principal, scope: "observe", observedAt: v.observedAt,
    allowed: v.allowed, reason: v.reason, installation: d === null ? null : Object.fromEntries([
      "providerId", "providerVersion", "bindingRef", "bindingDigest", "identityDigest", "evidenceScope",
      "contactedResources", "hostOS", "hostArchitecture", "declaredSupportedOS", "declaredArchitectures",
    ].map((key) => [key, d[key]])) };
}

export function probeAttempt(v: unknown): ProbeAttempt {
  if (!object(v) || Object.keys(v).some((key) => !["principal", "assetId", "providerId", "bindingDigest", "identityDigest", "evidenceScope", "contactedResources", "key"].includes(key)) ||
    !id(v.principal) || !id(v.assetId) || !id(v.providerId) || !hash(v.bindingDigest) || !hash(v.identityDigest) ||
    !["fixture", "admitted_integration"].includes(v.evidenceScope) || !resources(v.contactedResources) ||
    v.contactedResources.length === 0 || typeof v.key !== "string" || !/^[a-f0-9-]{36}$/.test(v.key)) throw error();
  return { principal: v.principal, assetId: v.assetId, providerId: v.providerId, bindingDigest: v.bindingDigest,
    identityDigest: v.identityDigest, evidenceScope: v.evidenceScope, contactedResources: [...v.contactedResources], key: v.key };
}

export function probeStore(raw: string | null): ProbeStore {
  if (raw === null) return { version: 1, pending: null, history: [] };
  if (raw.length > 131072) throw error();
  const v = JSON.parse(raw);
  if (!object(v) || v.version !== 1 || Object.keys(v).some((key) => !["version", "pending", "history"].includes(key)) ||
    !Array.isArray(v.history) || v.history.length > 20) throw error();
  const pending = v.pending === null ? null : probeAttempt(v.pending);
  const seen = new Set<string>();
  const history = v.history.map((ref: Data) => {
    if (!object(ref) || Object.keys(ref).length !== 2 || !id(ref.operationId) || seen.has(ref.operationId)) throw error();
    seen.add(ref.operationId);
    return { attempt: probeAttempt(ref.attempt), operationId: ref.operationId };
  });
  return { version: 1, pending, history };
}

export function probeReceipt(v: Data, attempt: ProbeAttempt, expectedId?: string): Data {
  if (!object(v) || !noAuthority(v) || !id(v.operationId) || (expectedId && v.operationId !== expectedId) ||
    v.kind !== "lab_probe" || v.principal !== attempt.principal || v.assetId !== attempt.assetId ||
    v.providerId !== attempt.providerId || v.bindingDigest !== attempt.bindingDigest || v.identityDigest !== attempt.identityDigest ||
    v.evidenceScope !== attempt.evidenceScope || v.scope !== "observe" || !finite(v.createdAt) || !finite(v.deadline) ||
    !(v.deadline - v.createdAt > 0 && v.deadline - v.createdAt <= 5) ||
    !["accepted", "delegated", "completed", "rejected", "unknown"].includes(v.status) ||
    (v.code !== undefined && !code(v.code))) throw error();
  let result = null;
  if (v.result !== null) {
    const r = v.result;
    if (!object(r) || !["observed", "unavailable", "unknown"].includes(r.status) || r.identityDigest !== attempt.identityDigest ||
      !resources(r.contactedResources) || !r.contactedResources.every((resource: string) => attempt.contactedResources.includes(resource)) ||
      !finite(r.receivedAt) || !object(r.metadata) || !["firmwareVersion", "artifactRevision"].every((key) => r.metadata[key] === null || text(r.metadata[key])) ||
      !Array.isArray(r.diagnostics) || r.diagnostics.length > 16 || !r.diagnostics.every(code)) throw error();
    const t = r.sourceTime;
    if (t !== null && (!object(t) || !id(t.clockDomain) || typeof t.tick !== "string" ||
      !/^-?(?:0|[1-9][0-9]{0,38})$/.test(t.tick) || !["ns", "us", "ms", "s"].includes(t.unit) ||
      !(t.uncertaintySeconds === null || (finite(t.uncertaintySeconds) && t.uncertaintySeconds >= 0)))) throw error();
    result = { status: r.status, identityDigest: r.identityDigest, contactedResources: [...r.contactedResources],
      receivedAt: r.receivedAt, sourceTime: t === null ? null : { clockDomain: t.clockDomain, tick: t.tick, unit: t.unit, uncertaintySeconds: t.uncertaintySeconds },
      metadata: { firmwareVersion: r.metadata.firmwareVersion, artifactRevision: r.metadata.artifactRevision }, diagnostics: [...r.diagnostics] };
  }
  if ((v.status === "completed" && (!result || result.status === "unknown")) ||
    (["accepted", "delegated", "rejected"].includes(v.status) && result !== null) ||
    (v.status === "unknown" && result !== null && result.status !== "unknown")) throw error();
  return { operationId: v.operationId, principal: v.principal, assetId: v.assetId, providerId: v.providerId,
    bindingDigest: v.bindingDigest, identityDigest: v.identityDigest, evidenceScope: v.evidenceScope,
    createdAt: v.createdAt, deadline: v.deadline, status: v.status, code: v.code, result };
}
