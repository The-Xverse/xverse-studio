import type { Data, Preflight } from "../../api/types";
export const dimensions = [
  ["backend", "Studio backend"],
  ["provider", "Provider / host compatibility"],
  ["model", "Model validity"],
  ["artifacts", "Artifact availability"],
  ["capabilities", "Capability compatibility"],
  ["target", "Target readiness"],
  ["resources", "Resource availability"],
  ["ownership", "Execution ownership"],
  ["clocks", "Clock mappings"],
  ["authority", "Execution authority"],
] as const;
// Closed positive states from readinessVersion 1.0; unknown future states never enable Start.
export const admittedStatuses = new Set([
  "ready",
  "valid",
  "available",
  "compatible",
]);
export function readinessFacts(preflight: Preflight) {
  return dimensions.map(([id, label]) => {
    const record =
      preflight.readinessVersion === "1.0"
        ? preflight.readiness?.[id]
        : undefined;
    return {
      id,
      label,
      status:
        typeof record?.status === "string" ? record.status : "not_reported",
      message:
        typeof record?.message === "string"
          ? record.message
          : "The backend did not report this check. No result has been inferred from the admission decision.",
      elementRefs: Array.isArray(record?.elementRefs)
        ? (record.elementRefs.filter(
            (value: unknown) => typeof value === "string",
          ) as string[])
        : [],
      diagnosticCodes: Array.isArray(record?.diagnosticCodes)
        ? (record.diagnosticCodes.filter(
            (value: unknown) => typeof value === "string",
          ) as string[])
        : [],
      remediation:
        typeof record?.remediation === "string" ? record.remediation : "",
      facts:
        record?.facts &&
        typeof record.facts === "object" &&
        !Array.isArray(record.facts)
          ? (record.facts as Data)
          : undefined,
    };
  });
}
export function planIdentity(preflight: Preflight): {
  matches: boolean;
  reason: string;
} {
  const preview: Data | undefined = preflight.planPreview;
  if (
    !preview ||
    !preview.plan ||
    typeof preview.plan !== "object" ||
    Array.isArray(preview.plan)
  )
    return {
      matches: false,
      reason: "No frozen compiled plan was returned for this request.",
    };
  if (!preflight.planDigest || preview.planDigest !== preflight.planDigest)
    return {
      matches: false,
      reason:
        "The preview plan identity differs from the preflight identity. Recheck readiness.",
    };
  if (
    !preflight.snapshotDigest ||
    preview.snapshotDigest !== preflight.snapshotDigest ||
    preview.snapshotId !== preflight.snapshotId
  )
    return {
      matches: false,
      reason:
        "The preview snapshot identity cannot be matched to this frozen request. Recheck readiness.",
    };
  if (
    preview.revision !== preflight.revision ||
    !Number.isInteger(preview.revision)
  )
    return {
      matches: false,
      reason:
        "The preview revision differs from the preflight revision. Recheck readiness.",
    };
  const selected = ["systemRef", "deploymentRef", "scenarioRef"];
  if (
    !preview.selection ||
    !preflight.selection ||
    selected.some(
      (key) =>
        typeof preview.selection[key] !== "string" ||
        preview.selection[key] !== preflight.selection[key],
    )
  )
    return {
      matches: false,
      reason:
        "The preview selection differs from the preflight selection. Recheck readiness.",
    };
  if (preview.scope !== "declared_intent_only")
    return {
      matches: false,
      reason:
        "The backend did not declare a supported compiler-preview scope. Recheck readiness.",
    };
  const embedded = preview.plan.digest;
  if (
    !embedded ||
    embedded.algorithm !== "sha256" ||
    "sha256:" + embedded.value !== preflight.planDigest
  )
    return {
      matches: false,
      reason:
        "The compiled plan's embedded identity differs from its preview envelope. Recheck readiness.",
    };
  if (preview.semanticDigest !== preflight.semanticDigest)
    return {
      matches: false,
      reason:
        "The preview semantic identity differs from the preflight identity. Recheck readiness.",
    };
  return { matches: true, reason: "Frozen plan identities match" };
}
