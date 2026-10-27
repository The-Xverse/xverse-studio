import type { Data } from "../../api/types";
import {
  text,
  id,
  record,
  publicAsset,
  publicDiagnostics,
} from "./public-observations";

export type PlacementContext = {
  projectId: string;
  documentId: string;
  revision: number;
  deploymentRef: string;
  systemRef?: string;
};

const reference = (value: unknown) =>
  text(value, 4096) && (value as string).startsWith("xdl://");
const codes = (value: unknown) =>
  Array.isArray(value) &&
  value.length <= 100 &&
  value.every((code) => text(code, 128));

// Response-shape adapter for ADR0018. The backend owns source validation,
// identity/interface resolution and admission; this adapter never joins assets.
export function physicalPlacementReport(
  value: Data,
  context: PlacementContext,
): Data {
  const fail = () => {
    throw new Error(
      "The physical placement observation is incomplete, malformed or belongs to another context.",
    );
  };
  if (
    !value ||
    value.bindingObservationVersion !== "1.0" ||
    value.projectId !== context.projectId ||
    value.documentId !== context.documentId ||
    value.revision !== context.revision ||
    value.scope !== "read_only_placement_observation" ||
    value.activeReady !== false ||
    value.runtimeAdmission !== "unavailable" ||
    typeof value.sourceValid !== "boolean" ||
    !Array.isArray(value.bindings) ||
    value.bindings.length > 1000 ||
    !Array.isArray(value.limitations) ||
    value.limitations.length > 100 ||
    !value.limitations.every((v: unknown) => text(v, 1000))
  )
    fail();
  const diagnostics = publicDiagnostics(
    value.diagnostics,
    100,
    "Placement/source validation diagnostic",
    /^[A-Z][A-Z0-9_-]{0,127}$/,
  );
  const base = {
    bindingObservationVersion: "1.0",
    projectId: context.projectId,
    documentId: context.documentId,
    revision: context.revision,
    sourceValid: value.sourceValid,
    scope: value.scope,
    activeReady: false,
    runtimeAdmission: "unavailable",
    diagnostics,
    limitations: value.limitations,
  };
  if (!value.sourceValid) {
    if (value.bindings.length) fail();
    return { ...base, bindings: [] };
  }
  if (
    !reference(value.systemRef) ||
    !reference(value.deploymentRef) ||
    value.deploymentRef !== context.deploymentRef ||
    (context.systemRef && value.systemRef !== context.systemRef) ||
    typeof value.inventoryComplete !== "boolean" ||
    typeof value.inventoryTruncated !== "boolean" ||
    (value.inventoryComplete && value.inventoryTruncated)
  )
    fail();
  const bindings = value.bindings.map((row: Data) => {
    if (
      !row ||
      !text(row.bindingId, 256) ||
      !reference(row.logicalRef) ||
      !text(row.targetId, 256) ||
      !["physical", "hybrid"].includes(row.realizationClass) ||
      (row.assetId !== null && !id(row.assetId)) ||
      row.ready !== false ||
      row.activeReady !== false ||
      !codes(row.diagnostics) ||
      !row.requiredInterfaces ||
      typeof row.requiredInterfaces !== "object" ||
      Array.isArray(row.requiredInterfaces) ||
      Object.keys(row.requiredInterfaces).length > 64 ||
      Object.entries(row.requiredInterfaces).some(
        ([key, v]) =>
          !id(key) ||
          (v !== null &&
            !record(v, [
              "id",
              "direction",
              "payloadSchema",
              "unitSemantics",
              "compatibility",
            ])),
      ) ||
      typeof row.requiredInterfacesTruncated !== "boolean" ||
      ![
        "fixture",
        "prototype",
        "admitted_integration",
        "unavailable",
        "unknown",
      ].includes(row.evidenceScope) ||
      !row.readiness ||
      !["resolved", "unknown"].includes(row.readiness.identity) ||
      !["compatible", "incompatible", "unknown"].includes(
        row.readiness.interfaces,
      ) ||
      !["observed", "unknown"].includes(row.readiness.availability) ||
      !["partial", "unknown"].includes(row.readiness.metadata) ||
      row.readiness.providerAdmission !== "unavailable" ||
      row.readiness.permission !== "unknown" ||
      row.readiness.activeOperation !== "blocked"
    )
      fail();
    const asset = row.asset === null ? null : publicAsset(row.asset);
    if (
      asset &&
      (asset.assetId !== row.assetId ||
        asset.evidenceScope !== row.evidenceScope)
    )
      fail();
    return {
      bindingId: row.bindingId,
      logicalRef: row.logicalRef,
      targetId: row.targetId,
      realizationClass: row.realizationClass,
      assetId: row.assetId,
      asset,
      requiredInterfaces: row.requiredInterfaces,
      requiredInterfacesTruncated: row.requiredInterfacesTruncated,
      evidenceScope: row.evidenceScope,
      ready: false,
      activeReady: false,
      diagnostics: row.diagnostics,
      readiness: Object.fromEntries(
        [
          "identity",
          "interfaces",
          "availability",
          "metadata",
          "providerAdmission",
          "permission",
          "activeOperation",
        ].map((key) => [key, row.readiness[key]]),
      ),
    };
  });
  if (new Set(bindings.map((r: Data) => r.bindingId)).size !== bindings.length)
    fail();
  return {
    ...base,
    systemRef: value.systemRef,
    deploymentRef: value.deploymentRef,
    inventoryComplete: value.inventoryComplete,
    inventoryTruncated: value.inventoryTruncated,
    bindings,
  };
}
