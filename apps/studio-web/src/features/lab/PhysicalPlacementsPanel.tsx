import { useEffect, useLayoutEffect, useRef, useState, useId } from "react";
import type { Data } from "../../api/types";
import { api, ApiError } from "../../api/client";
import { Badge, Diagnostics, Json, KeyValues } from "../../app/ui";
import {
  physicalPlacementReport,
  type PlacementContext,
} from "./physical-placement-report";
import { revisionText } from "./public-observations";

type State = {
  key: string;
  status: "idle" | "loading" | "available" | "unavailable";
  report?: Data;
  error?: string;
  code?: string;
};

export function PhysicalPlacementsPanel({
  projectId,
  revision,
  documentId,
  deploymentRef,
  systemRef,
  loading = false,
}: {
  projectId: string;
  revision: number;
  documentId?: string;
  deploymentRef?: string;
  systemRef?: string;
  loading?: boolean;
}) {
  const key = JSON.stringify([
    projectId,
    revision,
    documentId,
    deploymentRef,
    systemRef,
    loading,
  ]);
  const [state, setState] = useState<State>({ key, status: "idle" }),
    [page, setPage] = useState(0),
    [focus, setFocus] = useState<{
      key: string;
      request: number;
      origin: Element | null;
    } | null>(null);
  const current = useRef(key),
    mounted = useRef(false),
    sequence = useRef(0),
    sending = useRef(false),
    controller = useRef<AbortController | null>(null),
    heading = useRef<HTMLHeadingElement>(null),
    failure = useRef<HTMLParagraphElement>(null),
    guidanceId = useId();
  current.current = key;
  const visible: State =
      state.key === key ? state : { key, status: "idle" as const },
    enabled =
      !loading &&
      !!documentId &&
      !!deploymentRef &&
      Number.isSafeInteger(revision) &&
      revision > 0,
    report = visible.report,
    rows: Data[] = report?.bindings || [],
    pages = Math.max(1, Math.ceil(rows.length / 50)),
    shown = rows.slice(page * 50, (page + 1) * 50);
  useLayoutEffect(() => {
    mounted.current = true;
    setState({ key, status: "idle" });
    setPage(0);
    setFocus(null);
    sending.current = false;
    return () => {
      mounted.current = false;
      sequence.current++;
      controller.current?.abort();
      sending.current = false;
    };
  }, [key]);
  useEffect(() => {
    if (!focus || visible.status === "loading") return;
    setFocus(null);
    if (
      focus.key !== key ||
      focus.request !== sequence.current ||
      !mounted.current ||
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== focus.origin)
    )
      return;
    (visible.status === "unavailable" || report?.sourceValid === false
      ? failure.current
      : heading.current
    )?.focus();
  }, [focus, key, visible.status, report, page]);

  async function inspect(origin: Element | null) {
    if (!enabled || sending.current) return;
    const context: PlacementContext = {
        projectId,
        documentId: documentId!,
        revision,
        deploymentRef: deploymentRef!,
        systemRef,
      },
      request = ++sequence.current,
      abort = new AbortController(),
      submitted = key;
    controller.current?.abort();
    controller.current = abort;
    sending.current = true;
    setPage(0);
    setState({ key, status: "loading" });
    setFocus({ key, request, origin });
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      abort.abort();
    }, 30000);
    try {
      const value = physicalPlacementReport(
        await api(
          `/projects/${encodeURIComponent(projectId)}/deployment-variants/${encodeURIComponent(documentId!)}/physical-bindings?revision=${revision}`,
          { signal: abort.signal },
        ),
        context,
      );
      if (
        mounted.current &&
        current.current === submitted &&
        sequence.current === request &&
        !abort.signal.aborted
      )
        setState({ key: submitted, status: "available", report: value });
    } catch (error) {
      if (
        mounted.current &&
        current.current === submitted &&
        sequence.current === request &&
        (!abort.signal.aborted || timedOut)
      )
        setState({
          key: submitted,
          status: "unavailable",
          code: error instanceof ApiError ? error.code : undefined,
          error: timedOut
            ? "The observation request timed out. Inspect again to make a new read."
            : `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The physical placement request failed."}`.slice(
                0,
                1000,
              ),
        });
    } finally {
      clearTimeout(timeout);
      if (sequence.current === request) sending.current = false;
    }
  }
  function changePage(next: number, origin: Element | null) {
    setPage(Math.min(pages - 1, Math.max(0, next)));
    setFocus({ key, request: sequence.current, origin });
  }
  return (
    <section
      className="panel physical-placements"
      aria-label="Physical placement observation"
      aria-busy={visible.status === "loading"}
    >
      <div className="section-heading">
        <h3 ref={heading} tabIndex={-1}>
          Physical placement observation
        </h3>
        <button
          type="button"
          className="button"
          disabled={!enabled || visible.status === "loading"}
          aria-describedby={guidanceId}
          onClick={(event) => void inspect(event.currentTarget)}
        >
          Inspect physical placements
        </button>
      </div>
      <p id={guidanceId} className="field-hint">
        Read-only observation of the selected Deployment and committed revision.
        Logical identity and authored source stay unchanged. Asset observations
        do not grant permission or make physical execution available.
      </p>
      {enabled && (
        <p className="field-hint">
          Authored Deployment for inspection: <code>{deploymentRef}</code>
        </p>
      )}
      {!enabled && (
        <p role="status">
          Choose a current authored Deployment before inspecting physical
          placements.
        </p>
      )}
      {enabled && visible.status === "idle" && (
        <p>
          Inspect the selected Deployment to read its physical and hybrid
          binding observations.
        </p>
      )}
      {visible.status === "loading" && (
        <p role="status">Reading physical placement observations…</p>
      )}
      {visible.status === "unavailable" && (
        <p ref={failure} tabIndex={-1} className="notice error" role="alert">
          Physical placement availability is unknown. {visible.error}
          {visible.code === "REVISION_CONFLICT"
            ? " Reopen the project to load its current revision, then inspect again."
            : " Inspect again to retry."}
        </p>
      )}
      {report && (
        <>
          <KeyValues
            values={{
              "Project revision": report.revision,
              "Deployment document": report.documentId,
              ...(report.sourceValid
                ? { System: report.systemRef, Deployment: report.deploymentRef }
                : {}),
              "Runtime admission": report.runtimeAdmission,
              "Active-operation readiness": "Blocked",
            }}
          />
          <Diagnostics diagnostics={report.diagnostics} />
          {!report.sourceValid ? (
            <p
              ref={failure}
              tabIndex={-1}
              className="notice error"
              role="alert"
            >
              The source set is invalid. Physical placements were not evaluated;
              fix the validator diagnostics before inspecting again.
            </p>
          ) : (
            <>
              <p role="status">
                {report.inventoryComplete
                  ? "Inventory observation is complete."
                  : "Inventory observation is incomplete; missing asset facts remain unknown."}
                {report.inventoryTruncated
                  ? " Inventory observations are truncated."
                  : ""}
              </p>
              {!rows.length && (
                <p>
                  No physical or hybrid bindings were returned for this
                  Deployment.
                </p>
              )}
              {rows.length > 50 && (
                <div className="form-actions">
                  <button
                    type="button"
                    className="button"
                    disabled={page === 0}
                    onClick={(event) =>
                      changePage(page - 1, event.currentTarget)
                    }
                  >
                    Previous placement page
                  </button>
                  <span>
                    Placement page {page + 1} of {pages} · {rows.length}{" "}
                    reported bindings
                  </span>
                  <button
                    type="button"
                    className="button"
                    disabled={page === pages - 1}
                    onClick={(event) =>
                      changePage(page + 1, event.currentTarget)
                    }
                  >
                    Next placement page
                  </button>
                </div>
              )}
              <div className="catalog-grid">
                {shown.map((row) => (
                  <article className="panel placement-row" key={row.bindingId}>
                    <div className="section-heading">
                      <h4>{row.bindingId}</h4>
                      <Badge>{row.evidenceScope}</Badge>
                    </div>
                    <KeyValues
                      values={{
                        "Logical reference": row.logicalRef,
                        "Authored realization": row.realizationClass,
                        "Target identity": row.targetId,
                        "Asset reference": row.assetId || "Unknown",
                        "Identity observation": row.readiness.identity,
                        "Interface observation": row.readiness.interfaces,
                        "Availability observation": row.readiness.availability,
                        "Metadata coverage": row.readiness.metadata,
                        "Provider admission": row.readiness.providerAdmission,
                        "Permission scope": row.readiness.permission,
                        "Active operation": row.readiness.activeOperation,
                        "Required interfaces":
                          Object.keys(row.requiredInterfaces).join(", ") ||
                          "Unknown",
                      }}
                    />
                    {row.requiredInterfacesTruncated && (
                      <p role="status">
                        Required interface observations are truncated; omitted
                        declarations are not displayed.
                      </p>
                    )}
                    {row.asset && (
                      <KeyValues
                        values={{
                          Provider: row.asset.providerId,
                          "Provider version":
                            row.asset.providerVersion || "Unknown",
                          "Physical declaration": row.asset.physical
                            ? "Declared physical asset"
                            : "Not confirmed physical",
                          "Observed identity": row.asset.identity || "Unknown",
                          Firmware: revisionText(row.asset.firmware),
                          "Artifact revision": revisionText(
                            row.asset.artifactRevision,
                          ),
                          "Provider OS declaration":
                            row.asset.supportedOS.join(", ") || "Unknown",
                          "Declared capabilities":
                            row.asset.capabilities.join(", ") || "Unknown",
                        }}
                      />
                    )}
                    {row.asset?.observationTruncated && (
                      <p role="status">
                        Asset metadata observations are truncated; omitted facts
                        remain unknown.
                      </p>
                    )}
                    <Diagnostics
                      diagnostics={row.diagnostics.map((code: string) => ({
                        code,
                        message: "Placement observation diagnostic",
                      }))}
                    />
                    <Json value={row} />
                  </article>
                ))}
              </div>
            </>
          )}
          <ul className="field-hint">
            {report.limitations.map((value: string, index: number) => (
              <li key={index}>{value}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
