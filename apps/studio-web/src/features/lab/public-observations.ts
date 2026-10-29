import type { Data, Diagnostic } from "../../api/types";

export const text = (v: unknown, max = 256) =>
    typeof v === "string" &&
    v.length > 0 &&
    v.length <= max * 2 &&
    Array.from(v).length <= max,
  id = (v: unknown) =>
    text(v, 253) && /^[A-Za-z0-9][A-Za-z0-9:._-]*$/.test(v as string),
  record = (v: unknown, fields: string[]) =>
    !!v &&
    typeof v === "object" &&
    !Array.isArray(v) &&
    Object.entries(v).every(([key, val]) => fields.includes(key) && text(val)),
  revision = (v: Data) =>
    v &&
    ["observed", "unknown"].includes(v.status) &&
    Object.entries(v).every(
      ([key, val]) =>
        ["status", "version", "digest", "observedAt"].includes(key) &&
        text(val),
    ),
  diagnostics = (
    v: unknown,
    max: number,
    codePattern = /^[A-Z][A-Z0-9_]{0,127}$/,
  ) =>
    Array.isArray(v) &&
    v.length <= max &&
    v.every(
      (d) =>
        d &&
        typeof d === "object" &&
        typeof d.code === "string" &&
        codePattern.test(d.code) &&
        (d.providerId === undefined || id(d.providerId)),
    );

const fields = [
  "assetId",
  "providerId",
  "providerVersion",
  "physical",
  "identity",
  "identityStatus",
  "firmware",
  "artifactRevision",
  "metadata",
  "interfaces",
  "interfacesStatus",
  "supportedOS",
  "observationTruncated",
  "capabilities",
  "permissionScope",
  "available",
  "evidenceScope",
  "providerAdmission",
  "activeReady",
  "reservable",
];

export function publicDiagnostics(
  value: unknown,
  maximum = 100,
  context = "Placement observation diagnostic",
  codePattern = /^[A-Z][A-Z0-9_]{0,127}$/,
): Diagnostic[] {
  if (!diagnostics(value, maximum, codePattern))
    throw new Error("The public diagnostics are incomplete or malformed.");
  return (value as Data[]).map((d) => ({
    code: d.code,
    message: d.providerId ? `Provider observation: ${d.providerId}` : context,
    ...(d.providerId ? { providerId: d.providerId } : {}),
  }));
}

export function publicAsset(value: unknown): Data {
  const a = value as Data;
  if (
    !a ||
    !id(a.assetId) ||
    !id(a.providerId) ||
    (a.providerVersion !== null && !text(a.providerVersion)) ||
    typeof a.physical !== "boolean" ||
    (a.identity !== null &&
      !record(a.identity, [
        "serial",
        "deviceId",
        "digest",
        "model",
        "manufacturer",
        "hardwareRevision",
      ])) ||
    !["observed", "unknown"].includes(a.identityStatus) ||
    !revision(a.firmware) ||
    !revision(a.artifactRevision) ||
    !a.metadata ||
    !["partial", "unknown"].includes(a.metadata.status) ||
    !Array.isArray(a.metadata.limitations) ||
    a.metadata.limitations.length > 100 ||
    !a.metadata.limitations.every((v: unknown) => text(v, 1000)) ||
    !a.interfaces ||
    typeof a.interfaces !== "object" ||
    Array.isArray(a.interfaces) ||
    Object.keys(a.interfaces).length > 64 ||
    Object.entries(a.interfaces).some(
      ([key, v]) =>
        !id(key) ||
        !(
          text(v) ||
          record(v, [
            "id",
            "direction",
            "payloadSchema",
            "unitSemantics",
            "compatibility",
          ])
        ),
    ) ||
    !["declared", "unknown"].includes(a.interfacesStatus) ||
    !Array.isArray(a.supportedOS) ||
    a.supportedOS.length > 2 ||
    !a.supportedOS.every((v: unknown) =>
      ["Linux", "Windows"].includes(v as string),
    ) ||
    typeof a.observationTruncated !== "boolean" ||
    !Array.isArray(a.capabilities) ||
    a.capabilities.length > 3 ||
    !a.capabilities.every((v: unknown) =>
      ["observe", "stimulate", "destructive"].includes(v as string),
    ) ||
    a.permissionScope !== "unknown" ||
    typeof a.available !== "boolean" ||
    ![
      "fixture",
      "prototype",
      "admitted_integration",
      "unavailable",
      "unknown",
    ].includes(a.evidenceScope) ||
    a.providerAdmission !== "unavailable" ||
    a.activeReady !== false ||
    a.reservable !== false ||
    !diagnostics(a.diagnostics, 100)
  )
    throw new Error(
      "The public asset observation is incomplete, malformed or unsupported.",
    );
  return {
    ...Object.fromEntries(fields.map((key) => [key, a[key]])),
    metadata: {
      status: a.metadata.status,
      limitations: a.metadata.limitations,
    },
    diagnostics: publicDiagnostics(
      a.diagnostics,
      100,
      "Asset observation diagnostic",
    ),
  };
}

export function inventoryPage(value: Data, cursor: string): Data {
  if (
    !value ||
    !Array.isArray(value.items) ||
    value.items.length > 200 ||
    typeof value.complete !== "boolean" ||
    typeof value.truncated !== "boolean" ||
    value.scope !== "explicitly_registered_inventory_observations" ||
    value.physicalProviderStatus !== "unavailable" ||
    value.activeReady !== false ||
    !diagnostics(value.diagnostics, 101) ||
    (value.nextCursor !== null &&
      !(
        typeof value.nextCursor === "string" &&
        /^\d{1,4}$/.test(value.nextCursor) &&
        Number(value.nextCursor) > Number(cursor || "0") &&
        Number(value.nextCursor) <= 1000
      )) ||
    (value.truncated && value.complete)
  )
    throw new Error(
      "The public inventory observation is incomplete, malformed or unsupported.",
    );
  const assets = value.items.map(publicAsset);
  if (new Set(assets.map((a: Data) => a.assetId)).size !== assets.length)
    throw new Error(
      "The public inventory observation is incomplete, malformed or unsupported.",
    );
  return {
    items: assets,
    complete: value.complete,
    truncated: value.truncated,
    nextCursor: value.nextCursor,
    diagnostics: publicDiagnostics(
      value.diagnostics,
      101,
      "Inventory observation diagnostic",
    ),
  };
}

export function revisionText(value: Data) {
  return value.status === "observed"
    ? `Observed · ${value.version || value.digest || "revision metadata available"}`
    : "Unknown";
}
