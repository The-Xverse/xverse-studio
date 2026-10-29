import type { Data } from "../../api/types";
import { id, text } from "./public-observations";

export type ComparisonContext = {
  projectId: string;
  revision: number;
  providerId: string;
  leftId: string;
  rightId: string;
  leftRef: string;
  rightRef: string;
  systemRef: string;
};
const object = (v: unknown): v is Data =>
  !!v && typeof v === "object" && !Array.isArray(v);
const hash = (v: unknown) =>
  typeof v === "string" && /^sha256:[a-f0-9]{64}$/.test(v);
const ref = (v: unknown) =>
  text(v, 1024) &&
  (v as string).startsWith("xdl://") &&
  !/[\x00-\x1f\x7f]/.test(v as string);
const list = (v: unknown, max: number): v is any[] =>
  Array.isArray(v) && v.length <= max;
const finite = (v: unknown) => typeof v === "number" && Number.isFinite(v);
const error = () =>
  new Error(
    "Comparison metadata is incomplete, too large, inconsistent or unsupported. Reopen the current project and compare again.",
  );
const statuses = [
  "compatible",
  "pass",
  "declared",
  "authored",
  "default",
  "overridden",
  "unset",
  "fail",
  "unknown",
  "unsupported",
  "ambiguous",
  "unresolved",
];
function boundedValue(value: unknown) {
  const stack: [unknown, number][] = [[value, 0]];
  let nodes = 0;
  while (stack.length) {
    const [v, depth] = stack.pop()!;
    if (
      ++nodes > 20000 ||
      depth > 32 ||
      (typeof v === "string" && v.length > 8192) ||
      (typeof v === "number" && !Number.isFinite(v))
    )
      throw error();
    if (v !== null && typeof v === "object") {
      for (const x of Object.values(v)) stack.push([x, depth + 1]);
    } else if (
      !["string", "number", "boolean"].includes(typeof v) &&
      v !== null
    )
      throw error();
  }
}
export function hybridComparison(
  value: Data,
  context: ComparisonContext,
): Data {
  const v = value;
  if (
    !object(v) ||
    v.comparisonVersion !== "1.0" ||
    v.scope !== "static_deployment_comparison" ||
    v.projectId !== context.projectId ||
    v.revision !== context.revision ||
    v.providerId !== context.providerId ||
    !hash(v.providerDigest) ||
    !object(v.sharedSystem) ||
    v.sharedSystem.ref !== context.systemRef ||
    !id(v.sharedSystem.documentId) ||
    !hash(v.sharedSystem.sourceDigest) ||
    v.physicalState !== "unknown" ||
    v.cleanup !== "unknown" ||
    v.fidelity !== "unverified" ||
    v.runtimeAdmission !== "preflight_required" ||
    !object(v.synchronization) ||
    v.synchronization.status !== "unmeasured" ||
    v.synchronization.preciseLatencyAvailable !== false ||
    !list(v.limitations, 16) ||
    !v.limitations.every((s: unknown) => text(s, 1024))
  )
    throw error();
  const p = v.provider;
  if (
    !object(p) ||
    p.providerId !== context.providerId ||
    !text(p.providerVersion) ||
    !text(p.maturity) ||
    !text(p.evidenceScope) ||
    typeof p.available !== "boolean" ||
    typeof p.hostCompatible !== "boolean" ||
    !(p.implementationDigest === null || hash(p.implementationDigest)) ||
    (p.available && !hash(p.implementationDigest))
  )
    throw error();
  const provider: Data = Object.fromEntries(
    [
      "providerId",
      "providerVersion",
      "implementationDigest",
      "maturity",
      "evidenceScope",
      "available",
      "hostCompatible",
    ].map((key) => [key, p[key]]),
  );
  for (const key of [
    "operations",
    "clockDomains",
    "realizationClasses",
    "targetClasses",
    "supportedHostOS",
    "architectures",
    "limitations",
  ]) {
    if (
      p[key] !== null &&
      (!list(p[key], 64) || !p[key].every((s: unknown) => text(s, 1024)))
    )
      throw error();
    provider[key] = p[key] === null ? null : [...p[key]];
  }
  function side(raw: Data, documentId: string, deploymentRef: string) {
    if (
      !object(raw) ||
      !object(raw.resolution) ||
      !list(raw.declaredTargets, 1000) ||
      !list(raw.declaredMappings, 1000)
    )
      throw error();
    const r = raw.resolution;
    if (
      r.resolutionVersion !== "1.0" ||
      r.sourceValid !== true ||
      r.documentId !== documentId ||
      r.revision !== context.revision ||
      r.deploymentRef !== deploymentRef ||
      r.systemRef !== context.systemRef ||
      r.providerId !== context.providerId ||
      !list(r.bindings, 1000) ||
      !list(r.parameters, 1000) ||
      !list(r.diagnostics, 1000) ||
      !object(r.portableIntent) ||
      !list(r.portableIntent.bindings, 1000)
    )
      throw error();
    const seen = new Set<string>();
    const bindings = r.bindings.map((b: Data) => {
      if (
        !object(b) ||
        !id(b.bindingId) ||
        seen.has(b.bindingId) ||
        !(b.elementId === null || id(b.elementId)) ||
        !text(b.realizationClass) ||
        !id(b.targetId) ||
        !(b.targetClass === null || text(b.targetClass)) ||
        !statuses.includes(b.status)
      )
        throw error();
      seen.add(b.bindingId);
      return Object.fromEntries(
        [
          "bindingId",
          "elementId",
          "realizationClass",
          "targetId",
          "targetClass",
          "status",
        ].map((key) => [key, b[key]]),
      );
    });
    const intentSeen = new Set<string>();
    const intent = r.portableIntent.bindings.map((b: Data) => {
      if (
        !object(b) ||
        !id(b.bindingId) ||
        intentSeen.has(b.bindingId) ||
        !seen.has(b.bindingId) ||
        !list(b.artifactIds, 1000) ||
        !b.artifactIds.every(id) ||
        !list(b.resourceIds, 1000) ||
        !b.resourceIds.every(id)
      )
        throw error();
      const binding = bindings.find(
        (row: Data) => row.bindingId === b.bindingId,
      )!;
      if (
        b.elementId !== binding.elementId ||
        b.targetId !== binding.targetId ||
        b.realizationClass !== binding.realizationClass
      )
        throw error();
      intentSeen.add(b.bindingId);
      return {
        bindingId: b.bindingId,
        artifactIds: [...b.artifactIds],
        resourceIds: [...b.resourceIds],
      };
    });
    if (intentSeen.size !== seen.size) throw error();
    const parameters = r.parameters.map((p: Data) => {
      if (
        !object(p) ||
        !id(p.parameterId) ||
        !(p.elementId === null || id(p.elementId)) ||
        (p.elementId === null && !ref(p.scenarioRef)) ||
        !statuses.includes(p.status) ||
        !list(p.chain, 16)
      )
        throw error();
      const chain = p.chain.map((l: Data) => {
        if (!object(l) || !text(l.layer) || !("value" in l)) throw error();
        boundedValue(l.value);
        return { layer: l.layer, value: l.value };
      });
      return {
        elementId: p.elementId,
        scenarioRef: p.scenarioRef,
        parameterId: p.parameterId,
        status: p.status,
        chain,
      };
    });
    const diagnostics = r.diagnostics.map((d: Data) => {
      if (
        !object(d) ||
        typeof d.code !== "string" ||
        !/^[A-Z][A-Z0-9_-]{0,127}$/.test(d.code)
      )
        throw error();
      return { code: d.code };
    });
    const targetSeen = new Set<string>();
    const targets = raw.declaredTargets.map((t: Data) => {
      if (
        !object(t) ||
        !id(t.targetId) ||
        targetSeen.has(t.targetId) ||
        !text(t.targetClass) ||
        !list(t.capabilities, 64) ||
        !t.capabilities.every((c: unknown) => text(c)) ||
        !Number.isSafeInteger(t.omittedCapabilities) ||
        t.omittedCapabilities < 0 ||
        t.omittedCapabilities > 64
      )
        throw error();
      targetSeen.add(t.targetId);
      return {
        targetId: t.targetId,
        targetClass: t.targetClass,
        capabilities: [...t.capabilities],
        omittedCapabilities: t.omittedCapabilities,
      };
    });
    const mappings = raw.declaredMappings.map((m: Data) => {
      if (
        !object(m) ||
        !(m.mappingId === null || id(m.mappingId)) ||
        !["deployment", "scenario"].includes(m.origin) ||
        (m.origin === "deployment" ? !id(m.mappingId) : m.mappingId !== null) ||
        typeof m.pointer !== "string" ||
        !/^\/spec\/timeMappings\/(?:0|[1-9][0-9]{0,2})$/.test(m.pointer) ||
        !ref(m.ownerRef) ||
        !ref(m.sourceClock) ||
        !ref(m.targetClock) ||
        !object(m.tolerance) ||
        !finite(m.tolerance.value) ||
        !text(m.tolerance.unit)
      )
        throw error();
      return {
        mappingId: m.mappingId,
        pointer: m.pointer,
        origin: m.origin,
        ownerRef: m.ownerRef,
        sourceClock: m.sourceClock,
        targetClock: m.targetClock,
        tolerance: { value: m.tolerance.value, unit: m.tolerance.unit },
      };
    });
    return {
      resolution: {
        documentId,
        revision: context.revision,
        deploymentRef,
        systemRef: context.systemRef,
        bindings,
        parameters,
        diagnostics,
        portableIntent: { bindings: intent },
      },
      declaredTargets: targets,
      declaredMappings: mappings,
    };
  }
  return {
    projectId: context.projectId,
    revision: context.revision,
    providerDigest: v.providerDigest,
    provider,
    sharedSystem: {
      ref: v.sharedSystem.ref,
      documentId: v.sharedSystem.documentId,
      sourceDigest: v.sharedSystem.sourceDigest,
    },
    left: side(v.left, context.leftId, context.leftRef),
    right: side(v.right, context.rightId, context.rightRef),
    limitations: [...v.limitations],
  };
}
