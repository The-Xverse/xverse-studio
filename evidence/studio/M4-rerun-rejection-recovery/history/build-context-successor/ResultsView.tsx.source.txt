import { useEffect, useState, useMemo, useRef, useLayoutEffect } from "react";
import { api, items, mutationKey } from "../../api/client";
import type { Data, Run, RunEvent } from "../../api/types";
import type { DoAction } from "../../app/App";
import { Icon, Badge, Empty, Json, KeyValues, statusTone } from "../../app/ui";
import { ComparisonWorkspace } from "../comparison/ComparisonWorkspace";
import { EvidenceFilterControls } from "./EvidenceFilterControls";
import {
  emptyFilters,
  queryFilters,
  liveMatches,
  receipt,
  type EvidenceFilters,
} from "./evidenceFilters";
import { ObservationPlot, ObservationTable } from "./ObservationDisplay";
import { RetentionDialog } from "../retention/RetentionDialog";
import { FrozenInputsControl } from "./FrozenInputsControl";
import { RunControls } from "../runs/RunControls";
import { DiagnosticExplanations } from "../diagnostics/DiagnosticExplanations";
import { projectDisplay } from "../model/projection";
import type { Project } from "../../api/types";
export function ResultsView({
  run,
  events,
  omitted,
  streamState,
  selected: selectedModel,
  setSelected,
  doAction,
  onRunUpdated,
  onRun,
  rerunEnabled,
  onSelectRun,
}: {
  run: Run | null;
  events: RunEvent[];
  omitted: number;
  streamState: string;
  selected: string;
  setSelected: (id: string) => void;
  doAction: DoAction;
  onRunUpdated: (run: Run) => void;
  onRun: () => Promise<void>;
  rerunEnabled: boolean;
  onSelectRun: (run: Run) => void;
}) {
  const [selected, setEvidenceSelected] = useState(selectedModel),
    [tab, setTab] = useState("Observations"),
    [filter, setFilter] = useState(""),
    [observationData, setObservations] = useState<Data>({}),
    [evidenceData, setEvidence] = useState<Data>({}),
    [history, setHistory] = useState<Run[]>([]),
    [annotations, setAnnotations] = useState<Data[]>([]),
    [annotation, setAnnotation] = useState(""),
    [replay, setReplay] = useState(false),
    [showTable, setShowTable] = useState(false),
    [cursor, setCursor] = useState(0),
    [editingAnnotation, setEditingAnnotation] = useState<Data | null>(null),
    [editingTrace, setEditingTrace] = useState<Data | null>(null),
    [eventSource, setEventSource] = useState<"retained" | "live">("retained"),
    [retainedData, setRetainedEvents] = useState<RunEvent[]>([]),
    [historyLoading, setHistoryLoading] = useState(false),
    [historyIntegrityData, setHistoryIntegrity] = useState("unknown"),
    [historyIdentity, setHistoryIdentity] = useState(""),
    [historyEpoch, setHistoryEpoch] = useState(0),
    [historyErrorData, setHistoryError] = useState(""),
    [nextCursorData, setNextCursor] = useState<string | null>(null),
    [cursorTrail, setCursorTrail] = useState<string[]>([""]),
    [eventType, setEventType] = useState(""),
    [severity, setSeverity] = useState(""),
    [readFilters, setReadFilters] = useState<EvidenceFilters>(emptyFilters),
    [historyProjectionData, setHistoryProjection] = useState<Data>({}),
    [observationIdentity, setObservationIdentity] = useState(""),
    [observationLoading, setObservationLoading] = useState(false),
    [observationError, setObservationError] = useState(""),
    [observationNext, setObservationNext] = useState<string | null>(null),
    [observationTrail, setObservationTrail] = useState<string[]>([""]),
    [rerunBusy, setRerunBusy] = useState(false),
    [rerunOperation, setRerunOperation] = useState<Data | null>(null);
  useEffect(() => {
    setEvidenceSelected(selectedModel);
  }, [selectedModel]);
  const historyRequest = useRef<AbortController | null>(null),
    observationRequest = useRef<AbortController | null>(null),
    observationGeneration = useRef(0),
    readContext = useRef(""),
    historyContext = useRef(""),
    eventsTab = useRef<HTMLButtonElement | null>(null),
    observationsTab = useRef<HTMLButtonElement | null>(null);
  const queryIdentity = JSON.stringify([
    run?.runId,
    run?.snapshotId,
    readFilters,
    selected,
  ]);
  readContext.current = queryIdentity;
  const observations =
      observationIdentity === queryIdentity ? observationData : {},
    evidence = observationIdentity === queryIdentity ? evidenceData : {};
  const historyQueryIdentity = JSON.stringify([
    queryIdentity,
    eventType,
    severity,
    eventSource,
    tab,
  ]);
  historyContext.current = historyQueryIdentity;
  const historyCurrent = historyIdentity === historyQueryIdentity,
    retainedEvents = historyCurrent ? retainedData : [],
    historyProjection = historyCurrent ? historyProjectionData : {},
    historyIntegrity = historyCurrent ? historyIntegrityData : "unknown",
    nextCursor = historyCurrent ? nextCursorData : null,
    historyError = historyCurrent ? historyErrorData : "";
  const annotationContext = useRef({ runId: run?.runId });
  if (annotationContext.current.runId !== run?.runId)
    annotationContext.current = { runId: run?.runId };
  const renderedAnnotationContext = annotationContext.current;
  // The backend owns execution; this component may select an acknowledged child
  // only while the original run/tab and the user's focus intent are still current.
  const rerunMounted = useRef(false),
    rerunPending = useRef(false),
    rerunSignature = JSON.stringify([run?.runId, run?.snapshotId, tab]),
    rerunContext = useRef({ signature: rerunSignature });
  if (rerunContext.current.signature !== rerunSignature)
    rerunContext.current = { signature: rerunSignature };
  useLayoutEffect(() => {
    rerunMounted.current = true;
    return () => {
      rerunMounted.current = false;
    };
  }, []);
  async function rerunFrozenInputs() {
    if (!run || !rerunEnabled || rerunPending.current) return;
    rerunPending.current = true;
    const submitted = rerunContext.current,
      origin = document.activeElement,
      current = () =>
        rerunMounted.current && rerunContext.current === submitted,
      keyName = "studio.pendingRerun." + run.runId,
      abort = new AbortController(),
      deadline = performance.now() + 15000,
      timer = setTimeout(() => abort.abort(), 15000);
    const id = (value: unknown): value is string =>
      typeof value === "string" && value.length > 0 && value.length <= 128;
    setRerunBusy(true);
    try {
      const key = localStorage.getItem(keyName) || mutationKey();
      localStorage.setItem(keyName, key);
      const accepted = await api(`/runs/${run.runId}/reruns`, {
        method: "POST",
        body: {},
        key,
        signal: abort.signal,
      });
      if (!id(accepted.operationId))
        throw new Error(
          "The rerun acknowledgement cannot be identified. Retry retains the same request key.",
        );
      while (performance.now() < deadline) {
        const operation: Data = await api(
          `/operations/${accepted.operationId}`,
          {
            signal: abort.signal,
          },
        );
        if (
          operation.operationId !== accepted.operationId ||
          operation.kind !== "rerun" ||
          operation.sourceRunId !== run.runId ||
          operation.parentSnapshotId !== run.snapshotId ||
          !id(operation.snapshotId) ||
          operation.snapshotId === run.snapshotId ||
          ![
            "accepted",
            "delegated",
            "completed",
            "failed",
            "rejected",
            "unknown",
          ].includes(operation.status)
        )
          throw new Error(
            "The rerun operation does not match its original run and snapshot. Retry retains the same request key.",
          );
        if (current()) setRerunOperation(operation);
        if (operation.status === "completed") {
          if (
            !id(operation.result?.runId) ||
            operation.result.runId === run.runId ||
            operation.runId !== operation.result.runId ||
            !id(operation.result.startOperationId)
          )
            throw new Error(
              "The rerun's new child identity cannot be verified. Retry retains the same request key.",
            );
          const created = await api<Run>(`/runs/${operation.result.runId}`, {
            signal: abort.signal,
          });
          if (
            created.runId !== operation.result.runId ||
            created.snapshotId !== operation.snapshotId ||
            created.projectId !== run.projectId ||
            created.operationId !== operation.result.startOperationId ||
            created.providerId !== "studio.reference" ||
            created.evidenceScope !== "owned_reference"
          )
            throw new Error(
              "The acknowledged child does not match this rerun. Retry retains the same request key.",
            );
          // Settling this receipt never forgets another tab's newer submission.
          if (localStorage.getItem(keyName) === key)
            localStorage.removeItem(keyName);
          if (
            current() &&
            !document.querySelector('[role="dialog"]') &&
            (document.activeElement === origin ||
              document.activeElement === document.body)
          )
            onSelectRun(created);
          return;
        }
        if (operation.status === "rejected") {
          if (
            operation.evidenceScope !== "owned_reference" ||
            operation.runId != null ||
            operation.result != null ||
            !id(operation.error?.code) ||
            typeof operation.error?.message !== "string" ||
            !operation.error.message.length ||
            operation.error.retryable !== false
          )
            throw new Error(
              "The rejected rerun receipt cannot confirm that no child was admitted. Retry retains the same request key.",
            );
          // A verified rejection settled this request before child admission.
          // Only another explicit click can request fresh admission; uncertain
          // outcomes still retain their original operation identity below.
          const retainedKey = localStorage.getItem(keyName);
          if (retainedKey === key) localStorage.removeItem(keyName);
          throw new Error(
            `${operation.error.code}: ${operation.error.message.slice(0, 1000)} This attempt was rejected. ${
              retainedKey && retainedKey !== key
                ? "A newer request is retained. Rerun frozen inputs will check that request."
                : "Select Rerun frozen inputs for a new admission attempt."
            }`,
          );
        }
        if (["failed", "unknown"].includes(operation.status))
          throw new Error(
            `${operation.error?.code || "RERUN_NOT_ACKNOWLEDGED"}: ${operation.error?.message || "The new run could not be acknowledged."} Retrying retains the same operation identity.`,
          );
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
      throw new Error(
        "Rerun acknowledgment is still pending. Retrying uses the same operation key; no second start is requested.",
      );
    } catch (error) {
      if (current()) {
        if (abort.signal.aborted)
          throw new Error(
            "Rerun acknowledgment is still pending. Retrying uses the same operation key; no second start is requested.",
          );
        throw error;
      }
    } finally {
      clearTimeout(timer);
      rerunPending.current = false;
      if (rerunMounted.current) setRerunBusy(false);
    }
  }
  async function loadHistory(after = "") {
    if (!run) return;
    historyRequest.current?.abort();
    const request = new AbortController();
    historyRequest.current = request;
    const context = historyQueryIdentity;
    setHistoryIdentity("");
    setHistoryLoading(true);
    setHistoryError("");
    setHistoryProjection({});
    setHistoryIntegrity("unknown");
    setNextCursor(null);
    setRetainedEvents([]);
    const query = queryFilters(readFilters, selected, false);
    if (after) query.set("cursor", after);
    if (eventType) query.set("type", eventType);
    if (severity) query.set("severity", severity);

    try {
      const page = await api(`/runs/${run.runId}/history?${query}`, {
        signal: request.signal,
      });
      if (request.signal.aborted || historyContext.current !== context) return;
      const records = items<RunEvent>(page);
      if (records.length > 200)
        throw new Error(
          "The server returned an incompatible oversized history page.",
        );
      setHistoryIdentity(context);
      setRetainedEvents(records);
      setHistoryProjection(page);
      setNextCursor(page.nextCursor || null);
      setHistoryIntegrity(page.integrity || "unknown");
      setHistoryEpoch((epoch) => epoch + 1);
    } catch (error) {
      if (request.signal.aborted || historyContext.current !== context) return;
      setHistoryIdentity(context);
      setHistoryError(
        error instanceof Error ? error.message : "History unavailable.",
      );
      setNextCursor(null);
    } finally {
      if (!request.signal.aborted && historyContext.current === context)
        setHistoryLoading(false);
    }
  }
  useEffect(() => {
    if (tab !== "Events & logs" || eventSource !== "retained") return;
    setCursorTrail([""]);
    void loadHistory();
    return () => historyRequest.current?.abort();
  }, [
    run?.runId,
    tab,
    eventSource,
    eventType,
    severity,
    selected,
    readFilters,
  ]);
  async function loadEvidence(after = "") {
    if (!run) return;
    observationRequest.current?.abort();
    const request = new AbortController();
    observationRequest.current = request;
    const generation = ++observationGeneration.current,
      context = queryIdentity,
      runId = run.runId;
    setObservationLoading(true);
    setObservationIdentity("");
    setObservationError("");
    setObservations({});
    setEvidence({});
    setObservationNext(null);
    const query = queryFilters(readFilters, selected, true);
    if (after) query.set("cursor", after);
    try {
      const [obs, ev] = await Promise.all([
        api(`/runs/${runId}/observations?${query}`, { signal: request.signal }),
        api(`/runs/${runId}/evidence`, { signal: request.signal }),
      ]);
      if (
        request.signal.aborted ||
        generation !== observationGeneration.current ||
        context !== readContext.current
      )
        return;
      if (!Array.isArray(obs.items) || obs.items.length > 200)
        throw new Error(
          "The reader returned an incompatible oversized observation page.",
        );
      setObservationIdentity(context);
      setObservations(obs);
      setEvidence(ev);
      setObservationNext(obs.nextCursor || null);
    } catch (error) {
      if (
        !request.signal.aborted &&
        generation === observationGeneration.current &&
        context === readContext.current
      )
        setObservationError(
          error instanceof Error ? error.message : "Evidence unavailable.",
        );
    } finally {
      if (
        !request.signal.aborted &&
        generation === observationGeneration.current &&
        context === readContext.current
      )
        setObservationLoading(false);
    }
  }
  useEffect(() => {
    setObservationTrail([""]);
    void loadEvidence();
    return () => {
      observationGeneration.current++;
      observationRequest.current?.abort();
    };
  }, [
    run?.runId,
    run?.snapshotId,
    run?.state,
    run?.evidence,
    run?.evidenceStatus,
    run?.evidenceAvailability,
    queryIdentity,
  ]);
  useEffect(() => {
    void api("/runs")
      .then((r) => setHistory(items(r)))
      .catch(() => {});
  }, [run?.runId]);
  useEffect(() => {
    setEditingTrace(null);
    setEditingAnnotation(null);
    setAnnotation("");
    setAnnotations([]);
  }, [run?.runId]);
  useEffect(() => {
    if (!run) return;
    let current = true;
    void api(`/runs/${run.runId}/annotations`)
      .then((r) => {
        if (current) setAnnotations(items(r));
      })
      .catch(() => {});
    return () => {
      current = false;
    };
  }, [run?.runId, run?.status, run?.state]);
  const filtered = useMemo(
    () =>
      (eventSource === "retained" ? retainedEvents : events).filter(
        (e) =>
          (!selected || e.elementRefs?.includes(selected)) &&
          (eventSource !== "live" ||
            liveMatches(
              e,
              readFilters,
              eventType,
              severity,
              historyProjection.presentation,
            )) &&
          (!filter ||
            JSON.stringify(e).toLowerCase().includes(filter.toLowerCase())),
      ),
    [
      events,
      retainedEvents,
      eventSource,
      filter,
      selected,
      readFilters,
      eventType,
      severity,
      historyProjection.presentation,
    ],
  );
  const samples = useMemo(() => {
    const source =
      observations.samples ||
      observations.items ||
      observations.observations ||
      [];
    return Array.isArray(source) ? source : [];
  }, [observations]);
  useEffect(() => {
    setReplay(false);
    setCursor(0);
  }, [run?.runId, run?.snapshotId]);
  useEffect(() => {
    if (!replay || !samples.length) return;
    setCursor(0);
    const timer = setInterval(
      () =>
        setCursor((n) => {
          if (n >= samples.length) {
            setReplay(false);
            return n;
          }
          return n + 1;
        }),
      100,
    );
    return () => clearInterval(timer);
  }, [replay, samples.length]);
  if (!run)
    return (
      <div className="view-page">
        <Empty title="Your evidence starts with a run" icon="results">
          Validate the draft and run preflight to create an immutable input
          snapshot.
          <div className="form-actions">
            <button
              className="button primary"
              onClick={() => void doAction("Checking readiness", onRun)}
            >
              <Icon name="play" />
              Preflight & run
            </button>
          </div>
        </Empty>
      </div>
    );
  const status = String(run.status || run.state || "unknown"),
    active = [
      "accepted",
      "preparing",
      "starting",
      "running",
      "stopping",
    ].includes(status);
  return (
    <div className="view-page results-view">
      <div className="section-heading">
        <div>
          <h2>
            Run results <Badge tone={statusTone(status)}>{status}</Badge>
          </h2>
          <p className="run-identity">
            <code>{run.runId}</code>
            <span>
              Snapshot <code>{run.snapshotId.slice(0, 18)}</code>
            </span>
          </p>
        </div>
        <div className="header-actions">
          <label>
            Recorded run
            <select
              aria-label="Recorded run"
              value={run.runId}
              onChange={(event) => {
                const chosen = history.find(
                  (item) =>
                    item.runId === event.target.value &&
                    item.projectId === run.projectId,
                );
                if (chosen) {
                  setReplay(false);
                  setReadFilters(emptyFilters());
                  onSelectRun(chosen);
                }
              }}
            >
              {[
                ...new Map(
                  [
                    run,
                    ...history.filter(
                      (item) => item.projectId === run.projectId,
                    ),
                  ].map((item) => [item.runId, item]),
                ).values(),
              ].map((item) => (
                <option key={item.runId} value={item.runId}>
                  {item.runId} · {item.state}
                </option>
              ))}
            </select>
          </label>
          <FrozenInputsControl
            key={JSON.stringify([
              run.runId,
              run.snapshotId,
              run.projectId,
              run.revision,
              run.planDigest,
              run.semanticDigest,
              tab,
            ])}
            run={run}
          />
          {run.providerId === "studio.reference" &&
            run.evidenceScope === "owned_reference" && (
              <button
                className="button"
                disabled={!rerunEnabled || rerunBusy}
                onClick={() =>
                  void doAction(
                    "Freshly admitting frozen inputs",
                    rerunFrozenInputs,
                  )
                }
              >
                <Icon name="play" />
                Rerun frozen inputs
              </button>
            )}
          <button
            className="button"
            onClick={() => {
              setObservationTrail([""]);
              void loadEvidence();
            }}
          >
            <Icon name="refresh" />
            Refresh
          </button>
        </div>
      </div>
      <RunControls run={run} onRunUpdated={onRunUpdated} />
      {rerunOperation && (
        <section className="panel">
          <div className="section-heading">
            <h3>Fresh execution request</h3>
            <Badge tone={statusTone(rerunOperation.status)}>
              {rerunOperation.status}
            </Badge>
          </div>
          <p>
            A rerun creates a new run and snapshot after current admission
            checks. Recorded observation playback remains read-only.
          </p>
          <Json value={rerunOperation} />
        </section>
      )}
      <div className="result-status-grid">
        <StatusCard
          label="Execution"
          value={status}
          detail="Lifecycle outcome"
        />
        <StatusCard
          label="Assertion verdict"
          value={run.verdict || run.assertionVerdict || "Not evaluated"}
          detail="Separate assessment result"
        />
        <StatusCard
          label="Cleanup"
          value={
            typeof run.cleanup === "object"
              ? run.cleanup.status || run.cleanup.state
              : run.cleanup || run.cleanupStatus || "unknown"
          }
          detail="Owned-resource release"
        />
        <StatusCard
          label="Evidence"
          value={
            typeof run.evidence === "string"
              ? run.evidence
              : typeof run.evidenceStatus === "string"
                ? run.evidenceStatus
                : evidence.status || "unknown"
          }
          detail="Integrity and completeness"
        />
      </div>
      <div className="results-scope">
        <Badge>
          {run.evidenceScope === "recorded_fixture"
            ? "Recorded fixture scope"
            : run.evidenceScope || "Scope not declared"}
        </Badge>
        <span>
          {run.evidenceScope || run.providerId || "Provider-scoped evidence"} ·
          Source clocks retained · Browser presentation is bounded
        </span>
        <span className="context-spacer" />
        <span className="stream-indicator">
          <span
            className={`tiny-dot ${streamState === "Connected" ? "connected" : ""}`}
          />
          {streamState}
        </span>
      </div>
      <div className="sub-tabs" role="tablist" aria-label="Result sections">
        {[
          "Observations",
          "Events & logs",
          "Diagnosis",
          "Evidence",
          "Compare",
          "Annotations",
        ].map((t) => (
          <button
            role="tab"
            ref={
              t === "Events & logs"
                ? eventsTab
                : t === "Observations"
                  ? observationsTab
                  : undefined
            }
            aria-selected={tab === t}
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => {
              if (t !== "Observations") setReplay(false);
              setTab(t);
            }}
          >
            {t}
            {t === "Events & logs" && (
              <span className="tab-count">{events.length}</span>
            )}
          </button>
        ))}
      </div>
      {tab === "Observations" ? (
        <>
          <section className="panel">
            <div className="section-heading">
              <div>
                <h3>Recorded observations</h3>
                <p>
                  Original source time and quantity semantics are preserved.
                </p>
              </div>
              <div className="header-actions">
                <button
                  className="small-button"
                  onClick={() => setShowTable(!showTable)}
                >
                  {showTable ? "Plot view" : "Table view"}
                </button>
                <button
                  className="small-button"
                  disabled={!samples.length}
                  onClick={() => setReplay(!replay)}
                >
                  {replay ? "Stop playback" : "Replay observations"}
                </button>
              </div>
            </div>
            <EvidenceFilterControls
              value={readFilters}
              selected={selected}
              onApply={(value, elementRef) => {
                setEvidenceSelected(elementRef);
                setReplay(false);
                setReadFilters(value);
              }}
              facets={observations.facets || {}}
              complete={observations.facetsComplete}
              observation
              loading={observationLoading}
            />
            {observationLoading && (
              <p role="status">
                Loading observations for this exact run and filter…
              </p>
            )}
            {observationError && (
              <p className="notice error observation-query-error" role="alert">
                {observationError}
              </p>
            )}
            {selected && (
              <p className="field-hint">
                Selected element: <code>{selected}</code>{" "}
                <button
                  className="text-button"
                  onClick={() => setEvidenceSelected("")}
                >
                  Clear selected element filter
                </button>
              </p>
            )}
            <ReadQuality projection={observations} />
            {replay && (
              <div className="notice">
                <Icon name="info" />
                Recorded observation playback · no workload is running because
                of playback.
              </div>
            )}
            {samples.length ? (
              showTable ? (
                <ObservationTable
                  samples={samples.slice(0, 200)}
                  observations={observations}
                />
              ) : (
                <ObservationPlot
                  samples={replay ? samples.slice(0, cursor) : samples}
                  observations={observations}
                />
              )
            ) : (
              <Empty title="No observations available" icon="results">
                {active
                  ? "The provider is still collecting. Refresh after execution or inspect events for progress."
                  : "No measured signal was returned by the admitted evidence reader. A missing signal is not a measured zero."}
              </Empty>
            )}
            {samples.length > 200 && showTable && (
              <p className="field-hint">
                Showing the first 200 samples. Evaluation uses canonical
                evidence rather than this display selection.
              </p>
            )}
            <div className="history-pagination">
              <button
                className="small-button"
                disabled={observationLoading || observationTrail.length < 2}
                onClick={() => {
                  const trail = observationTrail.slice(0, -1);
                  setObservationTrail(trail);
                  void loadEvidence(trail.at(-1));
                }}
              >
                Previous observation page
              </button>
              <button
                className="small-button"
                disabled={observationLoading || !observationNext}
                onClick={() => {
                  if (observationNext) {
                    setObservationTrail((trail) => [
                      ...trail.slice(-127),
                      observationNext,
                    ]);
                    void loadEvidence(observationNext);
                  }
                }}
              >
                Next observation page
              </button>
            </div>
            <div className="plot-metadata">
              <span>
                Clock:{" "}
                <strong>
                  {observations.clockDomain ||
                    (observations.facets?.clockDomains?.length > 1
                      ? "Multiple original clocks; not aligned"
                      : "Source clock not declared")}
                </strong>
              </span>
              <span>
                Unit:{" "}
                <strong>
                  {observations.unit ||
                    observations.unitSemantics ||
                    samples[0]?.unit ||
                    Object.values(samples[0]?.units || {}).join(", ") ||
                    "Not declared"}
                </strong>
              </span>
              <span>
                Reduction:{" "}
                <strong>
                  {observations.reduction?.method ||
                    observations.reduction ||
                    "No interpolation"}
                </strong>
              </span>
            </div>
            {(observations.gaps || []).length > 0 && (
              <div className="notice error">
                Observation gaps are present. Continuous coverage cannot be
                inferred.
                <Json value={observations.gaps} />
              </div>
            )}
          </section>
          <section className="panel">
            <h3>Input and evidence provenance</h3>
            <KeyValues
              values={{
                Snapshot: run.snapshotId,
                "Plan digest": run.planDigest || "Not returned",
                Provider: run.providerId || "Not declared",
                "Clock uncertainty":
                  observations.uncertainty ??
                  observations.mapping?.uncertainty ??
                  "Not declared",
                Coverage:
                  typeof observations.coverage === "object"
                    ? JSON.stringify(observations.coverage)
                    : observations.coverage || "Unknown",
              }}
            />
            <Json value={observations} />
          </section>
        </>
      ) : tab === "Events & logs" ? (
        <section
          className="panel retained-history"
          data-testid="retained-history"
          data-history-epoch={historyEpoch}
          data-integrity={historyIntegrity}
          aria-busy={eventSource === "retained" && historyLoading}
        >
          <div className="section-heading">
            <div>
              <h3>Events and permitted logs</h3>
              <p>
                Delivery order does not establish causality across different
                clocks.
              </p>
            </div>
            <div className="search-field compact">
              <Icon name="search" size={16} />
              <input
                aria-label="Filter events and logs"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Search the displayed page"
              />
            </div>
          </div>
          <div className="history-toolbar">
            <div
              className="history-source"
              role="group"
              aria-label="Delivery view"
            >
              <button
                className={
                  eventSource === "retained"
                    ? "small-button active"
                    : "small-button"
                }
                aria-pressed={eventSource === "retained"}
                onClick={() => setEventSource("retained")}
              >
                Retained history
              </button>
              <button
                className={
                  eventSource === "live"
                    ? "small-button active"
                    : "small-button"
                }
                aria-pressed={eventSource === "live"}
                onClick={() => setEventSource("live")}
              >
                Live buffer · at most 200
              </button>
            </div>
            {eventSource === "retained" && (
              <>
                <label>
                  Event kind
                  <select
                    aria-label="Event kind"
                    value={eventType}
                    onChange={(event) => setEventType(event.target.value)}
                  >
                    <option value="">All registered kinds</option>
                    {[
                      "log.appended",
                      "run.state_changed",
                      "command.accepted",
                      "command.completed",
                      "observation.available",
                      "observation.gap",
                      "cleanup.updated",
                      "evidence.updated",
                    ].map((kind) => (
                      <option value={kind} key={kind}>
                        {kind}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Severity
                  <select
                    aria-label="Severity"
                    value={severity}
                    onChange={(event) => setSeverity(event.target.value)}
                  >
                    <option value="">All severities</option>
                    {["debug", "info", "warning", "error"].map((level) => (
                      <option key={level}>{level}</option>
                    ))}
                  </select>
                </label>
                <button
                  className="small-button"
                  disabled={historyLoading}
                  onClick={() => {
                    setCursorTrail([""]);
                    void loadHistory();
                  }}
                >
                  Reload retained first page
                </button>
              </>
            )}
          </div>
          <EvidenceFilterControls
            value={readFilters}
            selected={selected}
            onApply={(value, elementRef) => {
              setEvidenceSelected(elementRef);
              setReplay(false);
              setReadFilters(value);
            }}
            facets={historyProjection.facets || observations.facets || {}}
            complete={
              historyProjection.facetsComplete ?? observations.facetsComplete
            }
            observation={false}
            loading={eventSource === "retained" && historyLoading}
          />
          {eventSource === "live" && (
            <p className="notice">
              Emitter/time predicates apply only to the current live buffer (at
              most 200). Numeric receipt times without reader metadata remain
              unavailable for receipt filtering. Use retained history for a
              complete query.
            </p>
          )}
          <ReadQuality projection={historyProjection} />
          {eventSource === "retained" && (
            <div className="history-page-status" aria-live="polite">
              <span>
                {historyLoading
                  ? "Loading retained page…"
                  : `${retainedEvents.length} retained records in this page`}
              </span>
              <span>
                Integrity: <strong>{historyIntegrity}</strong>
              </span>
              <span>
                Text search applies to the displayed page. Emitter, observer,
                kind, severity, element and time filters apply before backend
                pagination.
              </span>
            </div>
          )}
          {historyError && (
            <div className="notice error" role="alert">
              {historyError} Reload retained history to obtain a current cursor.
              No missing records have been synthesized.
            </div>
          )}
          {omitted > 0 && (
            <div className="notice">
              <Icon name="info" />
              {omitted} earlier display event(s) omitted or unavailable.
              Canonical evidence remains with its provider; refresh evidence for
              retained records.
            </div>
          )}
          {selected && (
            <button
              className="small-button"
              onClick={() => setEvidenceSelected("")}
            >
              Clear selected element filter: {selected}
            </button>
          )}
          <div
            className="event-list"
            aria-label={
              eventSource === "retained"
                ? "Retained event page"
                : "Bounded live event buffer"
            }
          >
            {filtered.length ? (
              filtered.slice().map((e) => (
                <article
                  className="event-row"
                  key={e.eventId}
                  data-history-record={
                    eventSource === "retained" ? "true" : undefined
                  }
                  data-event-id={e.eventId}
                  data-sequence={e.sequence}
                >
                  <span className="event-marker" />
                  <time
                    className="evidence-time"
                    dateTime={
                      receipt(e, historyProjection.presentation).utc ||
                      undefined
                    }
                  >
                    {receipt(e, historyProjection.presentation).label}
                  </time>
                  <div>
                    <div>
                      <strong>{e.type}</strong>
                      <Badge>{e.evidenceClass || "unknown"}</Badge>
                    </div>
                    <p>
                      {e.payload?.message ||
                        e.payload?.status ||
                        e.payload?.state ||
                        JSON.stringify(e.payload)}
                    </p>
                    {e.elementRefs?.map((ref) => (
                      <button
                        className="text-button"
                        key={ref}
                        onClick={() => setSelected(ref)}
                      >
                        {ref}
                      </button>
                    ))}
                    <small>
                      {e.sourceTime
                        ? `Source time: ${JSON.stringify(e.sourceTime)}`
                        : "Source timestamp not available"}{" "}
                      · sequence {e.sequence}
                    </small>
                    <Json value={e} />
                  </div>
                </article>
              ))
            ) : (
              <Empty title="No matching events" icon="results">
                The stream will reconnect independently of lifecycle controls.
                Reconnect never submits another Start request.
              </Empty>
            )}
          </div>
          {eventSource === "retained" && (
            <div className="history-pagination">
              <span>
                At most 200 records are rendered. Original timestamps, sequence
                and evidence identities remain attached.
              </span>
              <button
                className="small-button"
                disabled={historyLoading || cursorTrail.length < 2}
                onClick={() => {
                  const previous = cursorTrail.slice(0, -1);
                  setCursorTrail(previous);
                  void loadHistory(previous[previous.length - 1]);
                }}
              >
                Previous retained page
              </button>
              <button
                className="small-button"
                disabled={historyLoading || !nextCursor}
                onClick={() => {
                  if (nextCursor) {
                    setCursorTrail((trail) => [
                      ...trail.slice(-127),
                      nextCursor,
                    ]);
                    void loadHistory(nextCursor);
                  }
                }}
              >
                Next retained page
              </button>
            </div>
          )}
        </section>
      ) : tab === "Diagnosis" ? (
        <DiagnosticExplanations
          title="Run diagnosis"
          url={`/runs/${encodeURIComponent(run.runId)}/diagnostics`}
          refreshKey={`${run.stateVersion}:${run.state}:${run.evidence}:${run.cleanup}:${events[events.length - 1]?.sequence ?? ""}`}
          emptyText="No findings for the evaluated classes. Completion and liveness are not evidence of functional health."
          actions={{
            inspect_events: () => {
              setTab("Events & logs");
              eventsTab.current?.focus();
            },
            reconcile_ownership: async () =>
              onRunUpdated(
                await api<Run>(`/runs/${encodeURIComponent(run.runId)}`),
              ),
          }}
        />
      ) : tab === "Evidence" ? (
        <section className="panel">
          <div className="section-heading">
            <h3>Canonical evidence inventory</h3>
            <button
              className="button"
              onClick={() =>
                void doAction("Exporting selected evidence", async () => {
                  const exported = await api(`/runs/${run.runId}/exports`, {
                    method: "POST",
                    key: mutationKey(),
                  });
                  const downloadUrl =
                    exported.downloadUrl || exported.result?.downloadUrl;
                  if (!downloadUrl)
                    throw new Error("The export has no download handle.");
                  const a = document.createElement("a");
                  a.href = downloadUrl;
                  a.download = "studio-evidence.zip";
                  a.click();
                })
              }
            >
              <Icon name="download" />
              Export evidence bundle
            </button>
          </div>
          <p>
            The index is a read-only projection. Reader integrity verdicts and
            missing inputs remain visible.
          </p>
          <Json value={evidence} expanded />
          <h3>Owned-run details</h3>
          <Json value={run} expanded />
          <RetentionPanel run={run} doAction={doAction} />
        </section>
      ) : tab === "Compare" ? (
        <ComparisonWorkspace
          key={`${run.runId}:${run.snapshotId}`}
          run={run}
          onPlayback={() => {
            setReplay(false);
            setTab("Observations");
            observationsTab.current?.focus();
          }}
          onPreflight={() => doAction("Checking new-run readiness", onRun)}
        />
      ) : (
        <div className="connection-layout">
          <section className="panel">
            <h3>Separate annotations</h3>
            <p>
              User commentary and trace links do not modify the historical
              evidence.
            </p>
            {annotations.map((a) => (
              <article
                className="annotation"
                key={a.annotationId}
                aria-label={
                  a.kind === "trace_link"
                    ? `External reference ${a.target?.uri || a.annotationId}`
                    : undefined
                }
              >
                <div>
                  <strong>{a.kind || "comment"}</strong>
                  <span>rev {a.revision}</span>
                </div>
                <p>
                  {a.deleted
                    ? "Annotation removed; historical revisions retained."
                    : a.text || a.content}
                </p>
                <small>{a.createdAt || a.timestamp}</small>
                {a.kind === "trace_link" && (
                  <TraceReferenceDetails annotation={a} />
                )}
                {!a.deleted && a.kind === "comment" && (
                  <div className="annotation-actions">
                    <button
                      className="small-button"
                      onClick={() => {
                        setEditingAnnotation(a);
                        setAnnotation(a.text);
                      }}
                    >
                      Edit note
                    </button>
                    <button
                      className="small-button"
                      onClick={() =>
                        void doAction("Removing annotation", async () => {
                          await api(`/annotations/${a.annotationId}`, {
                            method: "DELETE",
                            revision: String(a.revision),
                          });
                          const rows = items<Data>(
                            await api(`/runs/${run.runId}/annotations`),
                          );
                          if (
                            annotationContext.current ===
                            renderedAnnotationContext
                          )
                            setAnnotations(rows);
                        })
                      }
                    >
                      Remove note
                    </button>
                  </div>
                )}
                {!a.deleted && a.kind === "trace_link" && (
                  <div className="annotation-actions">
                    <button
                      className="small-button"
                      onClick={() => setEditingTrace(a)}
                    >
                      Edit external reference
                    </button>
                    <button
                      className="small-button"
                      onClick={() =>
                        void doAction(
                          "Removing external reference",
                          async () => {
                            await api(`/annotations/${a.annotationId}`, {
                              method: "DELETE",
                              revision: String(a.revision),
                            });
                            const rows = items<Data>(
                              await api(`/runs/${run.runId}/annotations`),
                            );
                            if (
                              annotationContext.current !==
                              renderedAnnotationContext
                            )
                              return;
                            setAnnotations(rows);
                            if (editingTrace?.annotationId === a.annotationId)
                              setEditingTrace(null);
                          },
                        )
                      }
                    >
                      Remove external reference
                    </button>
                  </div>
                )}
                {!!a.history?.length && (
                  <details>
                    <summary>Revision history ({a.history.length})</summary>
                    {a.history.map((previous: Data) => (
                      <section key={previous.revision}>
                        <strong>Revision {previous.revision}</strong>
                        {previous.kind === "trace_link" ? (
                          <TraceReferenceDetails annotation={previous} />
                        ) : (
                          <p>{previous.text}</p>
                        )}
                      </section>
                    ))}
                  </details>
                )}
                <Json value={a} />
              </article>
            ))}
            {!annotations.length && (
              <p className="field-hint">No annotations on this run.</p>
            )}
          </section>
          <aside className="panel">
            <h3>
              {editingAnnotation ? "Edit review note" : "Add a review note"}
            </h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void doAction("Saving annotation", async () => {
                  if (editingAnnotation) {
                    await api(
                      `/annotations/${editingAnnotation.annotationId}`,
                      {
                        method: "PUT",
                        revision: String(editingAnnotation.revision),
                        body: {
                          kind: "comment",
                          text: annotation,
                          revision: editingAnnotation.revision,
                        },
                      },
                    );
                  } else {
                    await api(`/runs/${run.runId}/annotations`, {
                      method: "POST",
                      body: { kind: "comment", text: annotation },
                      key: mutationKey(),
                    });
                  }
                  if (annotationContext.current !== renderedAnnotationContext)
                    return;
                  const rows = items<Data>(
                    await api(`/runs/${run.runId}/annotations`),
                  );
                  if (annotationContext.current !== renderedAnnotationContext)
                    return;
                  setEditingAnnotation(null);
                  setAnnotations(rows);
                  setAnnotation("");
                });
              }}
            >
              <label>
                Comment
                <textarea
                  value={annotation}
                  onChange={(e) => setAnnotation(e.target.value)}
                  rows={5}
                  maxLength={4000}
                  required
                />
              </label>
              <button className="button primary" disabled={!annotation.trim()}>
                {editingAnnotation
                  ? "Save annotation revision"
                  : "Save separate annotation"}
              </button>
              {editingAnnotation && (
                <button
                  type="button"
                  className="button"
                  onClick={() => {
                    setEditingAnnotation(null);
                    setAnnotation("");
                  }}
                >
                  Cancel edit
                </button>
              )}
            </form>
            <p className="field-hint">
              An external requirement reference is traceability, not proof that
              the requirement passed.
            </p>
            <TraceLinkEditor
              key={run.runId}
              run={run}
              editing={editingTrace?.runId === run.runId ? editingTrace : null}
              doAction={doAction}
              onCancel={() => {
                if (annotationContext.current === renderedAnnotationContext)
                  setEditingTrace(null);
              }}
              onSaved={async () => {
                if (annotationContext.current !== renderedAnnotationContext)
                  return;
                const rows = items<Data>(
                  await api(`/runs/${run.runId}/annotations`),
                );
                if (annotationContext.current !== renderedAnnotationContext)
                  return;
                setEditingTrace(null);
                setAnnotations(rows);
              }}
            />
          </aside>
        </div>
      )}
    </div>
  );
}
function TraceReferenceDetails({ annotation }: { annotation: Data }) {
  return (
    <section
      className="trace-reference-details"
      style={{ overflowWrap: "anywhere" }}
    >
      <dl className="key-values">
        <div>
          <dt>External URI</dt>
          <dd>{annotation.target?.uri}</dd>
        </div>
        <div>
          <dt>Referenced revision</dt>
          <dd>{annotation.target?.revision}</dd>
        </div>
        <div>
          <dt>Reported claim status</dt>
          <dd>
            <span
              className="trace-reported-status"
              style={{ whiteSpace: "pre-wrap" }}
            >
              {annotation.target?.claimStatus ?? "Not supplied"}
            </span>
          </dd>
        </div>
      </dl>
      <p className="field-hint">
        Reported metadata only. Studio has not verified this external claim.
      </p>
      {!!annotation.elementRefs?.length && (
        <p>Model / Scenario: {annotation.elementRefs.join(", ")}</p>
      )}
      {!!annotation.definitionRefs?.length && (
        <p>
          Frozen definitions:{" "}
          {annotation.definitionRefs
            .map(
              (ref: Data) => `${ref.definitionRef} (${ref.definitionDigest})`,
            )
            .join(", ")}
        </p>
      )}
      {!!annotation.evidenceRefs?.length && (
        <p>Evidence: {annotation.evidenceRefs.join(", ")}</p>
      )}
    </section>
  );
}
function TraceLinkEditor({
  run,
  editing,
  doAction,
  onSaved,
  onCancel,
}: {
  run: Run;
  editing: Data | null;
  doAction: DoAction;
  onSaved: () => Promise<void>;
  onCancel: () => void;
}) {
  const [open, setOpen] = useState(false),
    [uri, setUri] = useState(""),
    [revision, setRevision] = useState(""),
    [includeClaim, setIncludeClaim] = useState(false),
    [claim, setClaim] = useState(""),
    [note, setNote] = useState(""),
    [elements, setElements] = useState<string[]>([]),
    [definitions, setDefinitions] = useState<string[]>([]),
    [journal, setJournal] = useState(true),
    [subjects, setSubjects] = useState<Data[]>([]),
    [definitionOptions, setDefinitionOptions] = useState<Data[]>([]),
    [snapshotId, setSnapshotId] = useState(""),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [saving, setSaving] = useState(false);
  const uriInput = useRef<HTMLInputElement | null>(null),
    addButton = useRef<HTMLButtonElement | null>(null);
  const hasOpened = useRef(false);
  useEffect(() => {
    if (!editing) return;
    setUri(editing.target.uri);
    setRevision(editing.target.revision);
    setIncludeClaim(Object.hasOwn(editing.target, "claimStatus"));
    setClaim(editing.target.claimStatus ?? "");
    setNote(editing.text || "");
    setElements(editing.elementRefs || []);
    setDefinitions(
      (editing.definitionRefs || []).map((ref: Data) => ref.definitionRef),
    );
    setJournal(
      (editing.evidenceRefs || []).includes(run.runId + ":reference-journal"),
    );
    setOpen(true);
  }, [editing?.annotationId, editing?.revision]);
  useEffect(() => {
    if (open) {
      hasOpened.current = true;
      uriInput.current?.focus();
    } else if (hasOpened.current) addButton.current?.focus();
  }, [open, editing?.annotationId]);
  useEffect(() => {
    if (!open) return;
    let current = true;
    setLoading(true);
    setError("");
    setSnapshotId("");
    setSubjects([]);
    setDefinitionOptions([]);
    void Promise.all([
      api(`/runs/${run.runId}/snapshot`),
      api(`/runs/${run.runId}/definitions`),
    ])
      .then(([response, admitted]) => {
        if (!current) return;
        const snapshot = response.snapshot;
        if (
          response.integrity !== "valid" ||
          response.readOnly !== true ||
          snapshot?.snapshotId !== run.snapshotId
        )
          throw new Error(
            "The backend could not verify the selected run's frozen subjects.",
          );
        const projection = projectDisplay({
          projectId: run.projectId || "",
          name: "Frozen inputs",
          revision: snapshot.projectRevision || 1,
          documents: snapshot.documents,
        } as Project);
        if (projection.parseErrors.length)
          throw new Error("Frozen subject source is unavailable for display.");
        const options = new Map<string, Data>();
        for (const resource of projection.resources) {
          const ref = `xdl://${resource.metadata.namespace}/${resource.kind.toLowerCase()}/${resource.metadata.name}`;
          options.set(ref, {
            ref,
            label: `${resource.kind} · ${resource.metadata.name}`,
          });
          if (resource.kind === "System")
            for (const [collection, kind] of [
              ["nodes", "node"],
              ["componentInstances", "componentInstance"],
              ["devices", "device"],
              ["sensors", "sensor"],
              ["actuators", "actuator"],
              ["models", "model"],
              ["flows", "flow"],
            ])
              for (const item of resource.spec[collection] || [])
                options.set(ref + "#" + item.id, {
                  ref: ref + "#" + item.id,
                  label: `${kind} · ${item.id}`,
                });
        }
        setSubjects([...options.values()]);
        setDefinitionOptions(items(admitted));
        setSnapshotId(snapshot.snapshotId);
      })
      .catch((reason) => {
        if (current)
          setError(
            reason instanceof Error
              ? reason.message
              : "Frozen subjects are unavailable.",
          );
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [open, run.runId, run.snapshotId]);
  function reset() {
    setUri("");
    setRevision("");
    setIncludeClaim(false);
    setClaim("");
    setNote("");
    setElements([]);
    setDefinitions([]);
    setJournal(true);
  }
  function close() {
    setOpen(false);
    reset();
    onCancel();
    addButton.current?.focus();
  }
  const toggle = (values: string[], value: string, checked: boolean) =>
    checked ? [...values, value] : values.filter((item) => item !== value);
  const unavailable =
    elements.some((ref) => !subjects.some((item) => item.ref === ref)) ||
    definitions.some(
      (ref) => !definitionOptions.some((item) => item.definitionRef === ref),
    ) ||
    (editing?.definitionRefs || []).some(
      (saved: Data) =>
        definitions.includes(saved.definitionRef) &&
        !definitionOptions.some(
          (item) =>
            item.definitionRef === saved.definitionRef &&
            item.definitionDigest === saved.definitionDigest,
        ),
    );
  const requiresSource = elements.length > 0 || definitions.length > 0;
  return (
    <section>
      <h3>
        {editing
          ? "Edit external reference"
          : "External requirement / test reference"}
      </h3>
      {!open ? (
        <button
          ref={addButton}
          className="button"
          onClick={() => {
            reset();
            setOpen(true);
          }}
        >
          Add external reference
        </button>
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (saving) return;
            setSaving(true);
            void doAction("Saving external reference", async () => {
              try {
                if (loading || unavailable || (requiresSource && !snapshotId))
                  throw new Error("Verified frozen subjects are required.");
                const body: Data = {
                  kind: "trace_link",
                  text: note,
                  target: {
                    uri,
                    revision,
                    ...(includeClaim ? { claimStatus: claim } : {}),
                  },
                  elementRefs: elements,
                  definitionRefs: definitions.map((ref) => {
                    const item = definitionOptions.find(
                      (value) => value.definitionRef === ref,
                    )!;
                    return {
                      definitionRef: ref,
                      definitionDigest: item.definitionDigest,
                    };
                  }),
                  evidenceRefs: journal
                    ? [run.runId + ":reference-journal"]
                    : [],
                };
                if (editing)
                  await api(`/annotations/${editing.annotationId}`, {
                    method: "PUT",
                    revision: String(editing.revision),
                    body: { ...body, revision: editing.revision },
                  });
                else
                  await api(`/runs/${run.runId}/annotations`, {
                    method: "POST",
                    body,
                    key: mutationKey(),
                  });
                await onSaved();
                close();
              } finally {
                setSaving(false);
              }
            });
          }}
        >
          <p className="field-hint">
            These associations use this run's immutable inputs. They do not
            change source, definitions, evaluation verdicts or evidence.
          </p>
          <label>
            Requirement or test URI
            <input
              ref={uriInput}
              value={uri}
              onChange={(event) => setUri(event.target.value)}
              required
              maxLength={2048}
              placeholder="urn:requirements:example:17"
            />
          </label>
          <label>
            Referenced revision
            <input
              value={revision}
              onChange={(event) => setRevision(event.target.value)}
              required
              maxLength={256}
              placeholder="Pinned revision, or unknown"
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeClaim}
              onChange={(event) => setIncludeClaim(event.target.checked)}
            />
            Include reported claim status
          </label>
          {includeClaim && (
            <>
              <label>
                Reported claim status
                <input
                  value={claim}
                  onChange={(event) => setClaim(event.target.value)}
                  required
                  maxLength={256}
                  aria-describedby="reported-claim-hint"
                />
              </label>
              <small id="reported-claim-hint">
                Preserved as reported text. Studio does not verify it or infer a
                pass.
              </small>
            </>
          )}
          <label>
            Reference note (optional)
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              maxLength={4096}
              rows={2}
            />
          </label>
          {loading && <p role="status">Reading verified frozen subjects…</p>}
          {error && (
            <p role="alert">
              Frozen model/assertion references are unavailable: {error}{" "}
              Journal-only references remain available. Close and reopen to
              retry subject inspection.
            </p>
          )}
          {snapshotId && (
            <p className="field-hint">Frozen snapshot: {snapshotId}</p>
          )}
          <fieldset className="provider-checkboxes">
            <legend>Frozen model and Scenario references</legend>
            {subjects.map((item) => (
              <label key={item.ref} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={elements.includes(item.ref)}
                  disabled={
                    !elements.includes(item.ref) && elements.length >= 32
                  }
                  onChange={(event) =>
                    setElements(
                      toggle(elements, item.ref, event.target.checked),
                    )
                  }
                />
                {item.label}
              </label>
            ))}
            {!loading &&
              elements
                .filter((ref) => !subjects.some((item) => item.ref === ref))
                .map((ref) => (
                  <label key={ref} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked
                      onChange={() =>
                        setElements(elements.filter((value) => value !== ref))
                      }
                    />
                    Retained unavailable subject · {ref}
                  </label>
                ))}
          </fieldset>
          <fieldset className="provider-checkboxes">
            <legend>Frozen assertions and metrics</legend>
            {definitionOptions.map((item) => (
              <label key={item.definitionRef} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={definitions.includes(item.definitionRef)}
                  disabled={
                    !definitions.includes(item.definitionRef) &&
                    definitions.length >= 32
                  }
                  onChange={(event) =>
                    setDefinitions(
                      toggle(
                        definitions,
                        item.definitionRef,
                        event.target.checked,
                      ),
                    )
                  }
                />
                {item.definition?.kind || "Definition"} ·{" "}
                {item.definition?.name || item.definitionRef}
              </label>
            ))}
            {!loading &&
              definitions
                .filter(
                  (ref) =>
                    !definitionOptions.some(
                      (item) => item.definitionRef === ref,
                    ),
                )
                .map((ref) => (
                  <label key={ref} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked
                      onChange={() =>
                        setDefinitions(
                          definitions.filter((value) => value !== ref),
                        )
                      }
                    />
                    Retained unavailable definition · {ref}
                  </label>
                ))}
            {!loading && !definitionOptions.length && (
              <p>No admitted frozen definitions were reported.</p>
            )}
          </fieldset>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={journal}
              onChange={(event) => setJournal(event.target.checked)}
            />
            Owned run journal
          </label>
          {unavailable && !loading && (
            <p role="alert">
              A saved subject is unavailable or its digest differs. Cancel to
              preserve it, or explicitly remove that association before saving.
            </p>
          )}
          <div className="form-actions">
            <button
              className="button primary"
              disabled={
                saving ||
                loading ||
                unavailable ||
                (requiresSource && !snapshotId) ||
                !uri ||
                !revision ||
                (includeClaim && !claim.trim())
              }
            >
              {editing ? "Save reference revision" : "Save external reference"}
            </button>
            <button type="button" className="button" onClick={close}>
              Cancel reference edit
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
function StatusCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: unknown;
  detail: string;
}) {
  const display = typeof value === "string" ? value : JSON.stringify(value);
  return (
    <section className="status-card">
      <span>{label}</span>
      <strong>
        <i className={`status-square ${statusTone(display)}`} />
        {display || "Unknown"}
      </strong>
      <small>{detail}</small>
    </section>
  );
}
function ReadQuality({ projection }: { projection: Data }) {
  return (
    <>
      <div
        role="status"
        aria-label="Evidence read quality"
        className="evidence-quality"
      >
        {projection.counts && (
          <span>
            Matched: {projection.counts.matchedRecords} · Returned:{" "}
            {projection.counts.returnedRecords} · Omitted from page:{" "}
            {projection.counts.omittedRecords}
          </span>
        )}
        {Object.entries(projection.quality || {}).map(([key, value]) => (
          <span key={key}>
            {key}: {String(value)}
          </span>
        ))}
        {projection.integrity && (
          <span>Reader integrity: {projection.integrity}</span>
        )}
      </div>
      {projection.gaps?.length > 0 && (
        <div className="notice">
          The reader reports collection gaps. Filtering does not restore
          canonical coverage.
          <Json value={projection.gaps} />
        </div>
      )}
    </>
  );
}

function RetentionPanel({ run }: { run: Run; doAction: DoAction }) {
  const [review, setReview] = useState(false);
  return (
    <div className="retention-panel">
      <h3>Explicit retention</h3>
      <p className="field-hint">
        Preview dependencies before requesting removal. Active inputs,
        evaluations, annotations, and campaign references can protect run files.
        Historical outcomes and snapshot identities remain recorded.
      </p>
      <button className="button" onClick={() => setReview(true)}>
        Review run file retention
      </button>
      {review && (
        <RetentionDialog
          target={{ kind: "run", id: run.runId, name: "Run " + run.runId }}
          onClose={() => setReview(false)}
        />
      )}
    </div>
  );
}
