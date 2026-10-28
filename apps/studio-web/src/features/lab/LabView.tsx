import { useEffect, useState, useRef, useId } from "react";
import { api, ApiError } from "../../api/client";
import type { Data, Diagnostic } from "../../api/types";
import type { DoAction } from "../../app/App";
import { Icon, Badge, Json, KeyValues, Diagnostics } from "../../app/ui";

import { inventoryPage, revisionText } from "./public-observations";
import { ReservationWorkspace, ReservationRequest } from "./ReservationWorkspace";
import { ProbeWorkspace, ConnectionRequest } from "./ProbeWorkspace";

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

export function LabView({
  providers,
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
    });
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
      <ReservationWorkspace>
      <ProbeWorkspace>
      <section className="panel">
        <h2>No physical provider admitted</h2>
        <p id={authorityId}>
          Inventory observations do not grant permission. Physical runtime and
          active commands are unavailable. A separately configured lease service
          can accept explicitly granted reservation requests; check its eligibility
          and evidence scope below.
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
              <ReservationRequest assetId={a.assetId} />
              <ConnectionRequest assetId={a.assetId} />
              <Json value={a} />
            </section>
          ))}
        </div>
      ) : null}
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
      </ProbeWorkspace>
      </ReservationWorkspace>
    </div>
  );
}
