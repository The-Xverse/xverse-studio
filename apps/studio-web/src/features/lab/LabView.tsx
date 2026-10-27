import { useEffect, useState, useRef, useId } from "react";
import { api, ApiError, mutationKey } from "../../api/client";
import type { Data, Diagnostic } from "../../api/types";
import type { DoAction } from "../../app/App";
import { Icon, Badge, Json, KeyValues, Diagnostics } from "../../app/ui";

type Observation = {
  status: "loading" | "available" | "unavailable";
  items: Data[];
  cursor: string;
  previous: string[];
  request: number;
  origin?: Element | null;
  complete?: boolean;
  truncated?: boolean;
  nextCursor?: string | null;
  diagnostics?: Diagnostic[];
  error?: string;
};

function inventoryPage(value: Data, cursor: string): Data {
  const text = (v: unknown, max = 256) =>
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
      Object.entries(v).every(
        ([key, val]) => fields.includes(key) && text(val),
      ),
    revision = (v: Data) =>
      v &&
      ["observed", "unknown"].includes(v.status) &&
      Object.entries(v).every(
        ([key, val]) =>
          ["status", "version", "digest", "observedAt"].includes(key) &&
          text(val),
      ),
    diagnostics = (v: unknown, max: number) =>
      Array.isArray(v) &&
      v.length <= max &&
      v.every(
        (d) =>
          d &&
          typeof d === "object" &&
          typeof d.code === "string" &&
          /^[A-Z][A-Z0-9_]{0,127}$/.test(d.code) &&
          (d.providerId === undefined || id(d.providerId)),
      );
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
    (value.truncated && value.complete) ||
    value.items.some(
      (a: Data) =>
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
        !diagnostics(a.diagnostics, 100),
    ) ||
    new Set(value.items.map((a: Data) => a.assetId)).size !== value.items.length
  )
    throw new Error(
      "The public inventory observation is incomplete, malformed or unsupported.",
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
  return {
    items: value.items.map((a: Data) => ({
      ...Object.fromEntries(fields.map((key) => [key, a[key]])),
      metadata: {
        status: a.metadata.status,
        limitations: a.metadata.limitations,
      },
      diagnostics: a.diagnostics.map((d: Data) => ({
        code: d.code,
        message: d.providerId
          ? `Provider observation: ${d.providerId}`
          : "Asset observation diagnostic",
        ...(d.providerId ? { providerId: d.providerId } : {}),
      })),
    })),
    complete: value.complete,
    truncated: value.truncated,
    nextCursor: value.nextCursor,
    diagnostics: value.diagnostics.map((d: Data) => ({
      code: d.code,
      message: d.providerId
        ? `Provider observation: ${d.providerId}`
        : "Inventory observation diagnostic",
      ...(d.providerId ? { providerId: d.providerId } : {}),
    })),
  };
}

function revisionText(value: Data) {
  return value.status === "observed"
    ? `Observed · ${value.version || value.digest || "revision metadata available"}`
    : "Unknown";
}

export function LabView({
  providers,
  doAction,
}: {
  providers: Data[];
  doAction: DoAction;
}) {
  const [observation, setObservation] = useState<Observation>({
      status: "loading",
      items: [],
      cursor: "",
      previous: [],
      request: 0,
    }),
    [reservation, setReservation] = useState<Data | null>(null);
  const mounted = useRef(false),
    sequence = useRef(0),
    controller = useRef<AbortController | null>(null),
    focused = useRef(0),
    heading = useRef<HTMLHeadingElement>(null),
    failure = useRef<HTMLParagraphElement>(null),
    guidanceId = useId(),
    authorityId = useId();
  const assets = observation.items,
    pending = observation.status === "loading";
  async function readPage(
    cursor = "",
    previous: string[] = [],
    origin?: Element | null,
  ) {
    controller.current?.abort();
    const abort = new AbortController(),
      request = ++sequence.current;
    controller.current = abort;
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      abort.abort();
    }, 30000);
    setObservation({
      status: "loading",
      items: [],
      cursor,
      previous,
      request,
      origin,
    });
    try {
      const value = inventoryPage(
        await api(
          `/assets${cursor ? "?cursor=" + encodeURIComponent(cursor) : ""}`,
          { signal: abort.signal },
        ),
        cursor,
      );
      if (
        mounted.current &&
        sequence.current === request &&
        !abort.signal.aborted
      )
        setObservation({
          ...value,
          status: "available",
          cursor,
          previous,
          request,
          origin,
        } as Observation);
    } catch (error) {
      if (
        mounted.current &&
        sequence.current === request &&
        (!abort.signal.aborted || timedOut)
      )
        setObservation({
          status: "unavailable",
          items: [],
          cursor,
          previous,
          request,
          origin,
          error: timedOut
            ? "The inventory request timed out. Retry to make a new observation."
            : `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The inventory request failed."}`.slice(
                0,
                1000,
              ),
        });
    } finally {
      clearTimeout(timeout);
    }
  }
  useEffect(() => {
    mounted.current = true;
    void readPage();
    return () => {
      mounted.current = false;
      sequence.current++;
      controller.current?.abort();
    };
  }, []);
  useEffect(() => {
    if (
      pending ||
      !observation.origin ||
      focused.current === observation.request
    )
      return;
    focused.current = observation.request;
    if (
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== observation.origin)
    )
      return;
    (observation.status === "unavailable"
      ? failure.current
      : heading.current
    )?.focus();
  }, [observation, pending]);
  return (
    <div className="page lab-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">HYBRID LABORATORY</span>
          <h1>Physical assets</h1>
          <p>
            Inspect identity and metadata from registered provider observations.
          </p>
        </div>
        <button
          className="button"
          disabled={pending}
          aria-describedby={guidanceId}
          onClick={(event) => void readPage("", [], event.currentTarget)}
        >
          <Icon name="refresh" />
          Refresh inventory
        </button>
      </div>
      <section className="panel">
        <h2>No physical provider admitted</h2>
        <p id={authorityId}>
          Inventory is read-only. Reservations and active operations are
          unavailable until a physical provider with durable ownership and
          permitted actions is admitted. Declared capabilities and observed
          availability do not grant permission.
        </p>
      </section>
      <div className="notice">
        <Icon name="info" />
        <span>
          Observe-only is the default. No device scanning, flashing, reset, or
          physical stimulation is implied by opening this view.
        </span>
      </div>
      <section
        className="panel"
        aria-busy={pending}
        aria-label="Inventory observation"
      >
        <h2 ref={heading} tabIndex={-1}>
          Inventory observation
        </h2>
        <p id={guidanceId} className="field-hint">
          Refresh starts a new observation at the first page. Each page is a
          separate read; the inventory may change between requests. Provider OS
          declarations and fixture scope are separate from active-operation
          readiness.
        </p>
        {pending && <p role="status">Reading inventory observations…</p>}
        {observation.status === "unavailable" && (
          <p ref={failure} tabIndex={-1} role="alert" className="notice error">
            Inventory availability is unknown. {observation.error} Refresh
            inventory to retry.
          </p>
        )}
        {observation.status === "available" && (
          <>
            <p role="status">
              {observation.complete
                ? "Provider inventory observation is complete."
                : "Inventory observation is incomplete; availability of missing assets is unknown."}
              {observation.truncated
                ? " The provider observation is truncated."
                : ""}
              {observation.nextCursor
                ? " More assets are available on another page."
                : ""}
            </p>
            <Diagnostics diagnostics={observation.diagnostics} />
            {!assets.length && (
              <p>
                {observation.complete && !observation.truncated
                  ? "No assets were returned on this page."
                  : "No asset records were returned; this incomplete observation does not establish absence."}
              </p>
            )}
            <div className="form-actions">
              <button
                className="button"
                disabled={!observation.previous.length}
                aria-describedby={guidanceId}
                onClick={(event) =>
                  void readPage(
                    observation.previous.at(-1)!,
                    observation.previous.slice(0, -1),
                    event.currentTarget,
                  )
                }
              >
                Previous inventory page
              </button>
              <span>
                Page {observation.previous.length + 1} · {assets.length}{" "}
                observed records
              </span>
              <button
                className="button"
                disabled={
                  !observation.nextCursor || observation.previous.length >= 9
                }
                aria-describedby={guidanceId}
                onClick={(event) =>
                  void readPage(
                    observation.nextCursor!,
                    [...observation.previous, observation.cursor],
                    event.currentTarget,
                  )
                }
              >
                Next inventory page
              </button>
            </div>
            {observation.nextCursor && observation.previous.length >= 9 && (
              <p role="status">
                The bounded page limit was reached. Refresh to start a new
                inventory observation.
              </p>
            )}
          </>
        )}
      </section>
      {assets.length ? (
        <div className="catalog-grid">
          {assets.map((a) => (
            <section className="panel" key={a.assetId}>
              <div className="section-heading">
                <h3>{a.name || a.assetId}</h3>
                <Badge>{a.evidenceScope}</Badge>
              </div>
              <KeyValues
                values={{
                  Identity: a.assetId,
                  Provider: a.providerId,
                  "Provider version": a.providerVersion || "Unknown",
                  "Physical declaration": a.physical
                    ? "Declared physical asset"
                    : "Not confirmed physical",
                  "Identity observation": a.identityStatus,
                  "Observed identity": a.identity || "Unknown",
                  Firmware: revisionText(a.firmware),
                  "Artifact revision": revisionText(a.artifactRevision),
                  "Metadata coverage": a.metadata.status,
                  Interfaces:
                    a.interfacesStatus === "declared"
                      ? Object.keys(a.interfaces).join(", ") ||
                        "No declared interfaces returned"
                      : "Unknown",
                  "Provider OS declaration": a.supportedOS.length
                    ? a.supportedOS.join(", ")
                    : "Unknown",
                  "Declared capabilities":
                    a.capabilities.join(", ") || "Unknown",
                  "Permission scope": a.permissionScope,
                  Availability: a.available
                    ? "Observed available"
                    : "Not confirmed available",
                  "Physical state": "Unknown",
                  "Provider admission": a.providerAdmission,
                  "Active-operation readiness": a.activeReady
                    ? "Ready"
                    : "Blocked",
                }}
              />
              {a.observationTruncated && (
                <p role="status">
                  This asset's metadata observation is truncated; omitted
                  metadata remains unknown.
                </p>
              )}
              <Diagnostics diagnostics={a.diagnostics} />
              <button
                className="button"
                disabled={!a.reservable || !a.activeReady}
                aria-describedby={authorityId}
                onClick={() =>
                  void doAction("Reserving observe-only access", async () => {
                    setReservation(
                      await api(
                        `/assets/${encodeURIComponent(a.assetId)}/reservations`,
                        {
                          method: "POST",
                          key: mutationKey(),
                          body: { scope: "observe", durationSeconds: 30 },
                        },
                      ),
                    );
                  })
                }
              >
                Reserve observe-only
              </button>
              <Json value={a} />
            </section>
          ))}
        </div>
      ) : null}
      {reservation && (
        <section className="panel">
          <h2>Reservation ownership</h2>
          <KeyValues
            values={{
              ID: reservation.reservationId,
              Scope: reservation.scope,
              Expires: reservation.expiresAt,
              Ownership:
                reservation.ownership || reservation.status || "Unknown",
            }}
          />
          <div className="form-actions">
            <button
              className="button"
              onClick={() =>
                void doAction("Renewing reservation", async () =>
                  setReservation(
                    await api(
                      `/reservations/${reservation.reservationId}/renewals`,
                      {
                        method: "POST",
                        key: mutationKey(),
                        body: {
                          fencingIdentity: reservation.fencingIdentity,
                          durationSeconds: 30,
                        },
                      },
                    ),
                  ),
                )
              }
            >
              Renew same scope
            </button>
            <button
              className="button"
              onClick={() =>
                void doAction("Releasing reservation", async () => {
                  await api(`/reservations/${reservation.reservationId}`, {
                    method: "DELETE",
                    key: mutationKey(),
                  });
                  setReservation(null);
                })
              }
            >
              Release reservation
            </button>
          </div>
          <Json value={reservation} />
        </section>
      )}
      <h2 className="section-title">Provider capability boundaries</h2>
      <div className="catalog-grid">
        {providers.map((p) => (
          <section className="panel" key={p.providerId || p.id}>
            <h3>{p.name || p.providerId || p.id}</h3>
            <Badge>
              {p.evidenceScope || p.scope || p.maturity || "Unknown scope"}
            </Badge>
            <p>
              {p.reason ||
                p.description ||
                "Inspect the descriptor for supported operations and host compatibility."}
            </p>
            <Json value={p} />
          </section>
        ))}
      </div>
    </div>
  );
}
