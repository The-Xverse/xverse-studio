import { useEffect, useState, useMemo, useRef } from "react";
import { api, items, mutationKey } from "../../api/client";
import type { Data, Run, RunEvent } from "../../api/types";
import type { DoAction } from "../../app/App";
import { Icon, Badge, Empty, Json, KeyValues, statusTone } from "../../app/ui";
import { FrozenInputs } from "./FrozenInputs";
export function ResultsView({
  run,
  events,
  omitted,
  streamState,
  selected,
  setSelected,
  doAction,
  command,
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
  command: (kind: string) => Promise<void>;
  onRun: () => Promise<void>;
  rerunEnabled: boolean;
  onSelectRun: (run: Run) => void;
}) {
  const [tab, setTab] = useState("Observations"),
    [filter, setFilter] = useState(""),
    [observations, setObservations] = useState<Data>({}),
    [evidence, setEvidence] = useState<Data>({}),
    [history, setHistory] = useState<Run[]>([]),
    [annotations, setAnnotations] = useState<Data[]>([]),
    [annotation, setAnnotation] = useState(""),
    [baseline, setBaseline] = useState(""),
    [comparison, setComparison] = useState<Data | null>(null),
    [replay, setReplay] = useState(false),
    [showTable, setShowTable] = useState(false),
    [cursor, setCursor] = useState(0),
    [editingAnnotation, setEditingAnnotation] = useState<Data | null>(null),
    [eventSource, setEventSource] = useState<"retained" | "live">("retained"),
    [retainedEvents, setRetainedEvents] = useState<RunEvent[]>([]),
    [historyLoading, setHistoryLoading] = useState(false),
    [historyIntegrity, setHistoryIntegrity] = useState("unknown"),
    [historyEpoch, setHistoryEpoch] = useState(0),
    [historyError, setHistoryError] = useState(""),
    [nextCursor, setNextCursor] = useState<string | null>(null),
    [cursorTrail, setCursorTrail] = useState<string[]>([""]),
    [eventType, setEventType] = useState(""),
    [severity, setSeverity] = useState(""),
    [frozenInputs, setFrozenInputs] = useState<Data | null>(null),
    [rerunBusy, setRerunBusy] = useState(false),
    [rerunOperation, setRerunOperation] = useState<Data | null>(null);
  const historyRequest = useRef<AbortController | null>(null);
  async function inspectFrozenInputs() {
    if (!run) return;
    const response = await api(`/runs/${run.runId}/snapshot`);
    if (response.integrity !== "valid" || response.readOnly !== true)
      throw new Error(
        "The backend could not verify the immutable snapshot for read-only inspection.",
      );
    setFrozenInputs(response.snapshot);
  }
  async function rerunFrozenInputs() {
    if (!run || !rerunEnabled) return;
    const keyName = "studio.pendingRerun." + run.runId;
    const key = localStorage.getItem(keyName) || mutationKey();
    localStorage.setItem(keyName, key);
    setRerunBusy(true);
    try {
      const accepted = await api(`/runs/${run.runId}/reruns`, {
        method: "POST",
        body: {},
        key,
      });
      const deadline = performance.now() + 15000;
      while (performance.now() < deadline) {
        const operation = await api(`/operations/${accepted.operationId}`);
        setRerunOperation(operation);
        if (operation.status === "completed" && operation.result?.runId) {
          const created = await api<Run>(`/runs/${operation.result.runId}`);
          onSelectRun(created);
          localStorage.removeItem(keyName);
          return;
        }
        if (["failed", "rejected", "unknown"].includes(operation.status))
          throw new Error(
            `${operation.error?.code || "RERUN_NOT_ACKNOWLEDGED"}: ${operation.error?.message || "The new run could not be acknowledged."} Retrying retains the same operation identity.`,
          );
        await new Promise((resolve) => setTimeout(resolve, 250));
      }
      throw new Error(
        "Rerun acknowledgment is still pending. Retrying uses the same operation key; no second start is requested.",
      );
    } finally {
      setRerunBusy(false);
    }
  }
  async function loadHistory(after = "") {
    if (!run) return;
    historyRequest.current?.abort();
    const request = new AbortController();
    historyRequest.current = request;
    setHistoryLoading(true);
    setHistoryError("");
    setRetainedEvents([]);
    const query = new URLSearchParams({ limit: "200" });
    if (after) query.set("cursor", after);
    if (eventType) query.set("type", eventType);
    if (severity) query.set("severity", severity);
    if (selected) query.set("elementRef", selected);
    try {
      const page = await api(`/runs/${run.runId}/history?${query}`, {
        signal: request.signal,
      });
      if (request.signal.aborted) return;
      const records = items<RunEvent>(page);
      if (records.length > 200)
        throw new Error(
          "The server returned an incompatible oversized history page.",
        );
      setRetainedEvents(records);
      setNextCursor(page.nextCursor || null);
      setHistoryIntegrity(page.integrity || "unknown");
      setHistoryEpoch((epoch) => epoch + 1);
    } catch (error) {
      if (request.signal.aborted) return;
      setHistoryError(
        error instanceof Error ? error.message : "History unavailable.",
      );
      setNextCursor(null);
    } finally {
      if (!request.signal.aborted) setHistoryLoading(false);
    }
  }
  useEffect(() => {
    if (tab !== "Events & logs" || eventSource !== "retained") return;
    setCursorTrail([""]);
    void loadHistory();
    return () => historyRequest.current?.abort();
  }, [run?.runId, tab, eventSource, eventType, severity, selected]);
  async function loadEvidence() {
    if (!run) return;
    const [obs, ev] = await Promise.all([
      api(`/runs/${run.runId}/observations`),
      api(`/runs/${run.runId}/evidence`),
    ]);
    setObservations(obs);
    setEvidence(ev);
  }
  useEffect(() => {
    void api("/runs")
      .then((r) => setHistory(items(r)))
      .catch(() => {});
  }, [run?.runId]);
  useEffect(() => {
    if (!run) return;
    void doAction("Reading immutable evidence", loadEvidence);
    void api(`/runs/${run.runId}/annotations`)
      .then((r) => setAnnotations(items(r)))
      .catch(() => {});
  }, [run?.runId, run?.status, run?.state]);
  const filtered = useMemo(
    () =>
      (eventSource === "retained" ? retainedEvents : events).filter(
        (e) =>
          (!selected || e.elementRefs?.includes(selected)) &&
          (!filter ||
            JSON.stringify(e).toLowerCase().includes(filter.toLowerCase())),
      ),
    [events, retainedEvents, eventSource, filter, selected],
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
          <button
            className="button"
            data-frozen-inputs-trigger=""
            onClick={() =>
              void doAction(
                "Verifying immutable run inputs",
                inspectFrozenInputs,
              )
            }
          >
            <Icon name="code" />
            Frozen inputs
          </button>
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
            onClick={() => void doAction("Refreshing evidence", loadEvidence)}
          >
            <Icon name="refresh" />
            Refresh
          </button>
          {active && (
            <>
              <button
                className="button"
                onClick={() =>
                  void doAction("Stopping owned run", () => command("stop"))
                }
              >
                <Icon name="stop" />
                Stop
              </button>
              <button
                className="button danger-button"
                onClick={() =>
                  void doAction("Cancelling owned run", () => command("cancel"))
                }
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
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
            typeof run.evidenceStatus === "string"
              ? run.evidenceStatus
              : evidence.status || evidence.integrity || "pending"
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
          "Evidence",
          "Compare",
          "Annotations",
        ].map((t) => (
          <button
            role="tab"
            aria-selected={tab === t}
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
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
            {replay && (
              <div className="notice">
                <Icon name="info" />
                Recorded observation playback · no workload is running because
                of playback.
              </div>
            )}
            {samples.length ? (
              showTable ? (
                <ObservationTable samples={samples.slice(0, 200)} />
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
            <div className="plot-metadata">
              <span>
                Clock:{" "}
                <strong>
                  {observations.clockDomain ||
                    observations.clockDomainRef ||
                    samples[0]?.clockDomain ||
                    "Source clock not declared"}
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
          aria-busy={historyLoading}
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
              aria-label="Event source"
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
                Text search applies to the displayed page; kind, severity, and
                element filters apply on the backend.
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
            <button className="small-button" onClick={() => setSelected("")}>
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
                  <time>{new Date(e.recordedAt).toLocaleTimeString()}</time>
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
        <div className="connection-layout">
          <section className="panel">
            <h3>Baseline comparison</h3>
            <p>
              Check model, deployment, parameters, capabilities, units, and
              clocks before interpreting differences.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void doAction("Comparing runs", async () =>
                  setComparison(
                    await api("/comparisons", {
                      method: "POST",
                      body: { leftRunId: baseline, rightRunId: run.runId },
                    }),
                  ),
                );
              }}
            >
              <label>
                Baseline run
                <select
                  required
                  value={baseline}
                  onChange={(e) => setBaseline(e.target.value)}
                >
                  <option value="">Select a recorded run</option>
                  {history
                    .filter((r) => r.runId !== run.runId)
                    .map((r) => (
                      <option key={r.runId} value={r.runId}>
                        {r.runId.slice(0, 16)} · {r.status || r.state}
                      </option>
                    ))}
                </select>
              </label>
              <button className="button primary" disabled={!baseline}>
                Inspect compatibility
              </button>
            </form>
            {comparison && <Json value={comparison} expanded />}
          </section>
          <aside className="panel">
            <h3>Replay and rerun</h3>
            <p>
              Replay re-presents recorded observations. It does not execute the
              model or establish determinism.
            </p>
            <p>
              A rerun creates a new identity after fresh preflight of the
              current draft.
            </p>
            <button
              className="button"
              onClick={() => void doAction("Checking new-run readiness", onRun)}
            >
              <Icon name="play" />
              Preflight a new run
            </button>
          </aside>
        </div>
      ) : (
        <div className="connection-layout">
          <section className="panel">
            <h3>Separate annotations</h3>
            <p>
              User commentary and trace links do not modify the historical
              evidence.
            </p>
            {annotations.map((a) => (
              <article className="annotation" key={a.annotationId}>
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
                          setAnnotations(
                            items(await api(`/runs/${run.runId}/annotations`)),
                          );
                        })
                      }
                    >
                      Remove note
                    </button>
                  </div>
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
                  setEditingAnnotation(null);
                  setAnnotations(
                    items(await api(`/runs/${run.runId}/annotations`)),
                  );
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
          </aside>
        </div>
      )}
      {frozenInputs && (
        <FrozenInputs
          snapshot={frozenInputs}
          onClose={() => setFrozenInputs(null)}
        />
      )}
    </div>
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
function numericValues(sample: Data): Data {
  const payload = sample.values ?? sample.value ?? sample.payload ?? sample;
  return typeof payload === "number"
    ? { value: payload }
    : payload && typeof payload === "object"
      ? payload
      : {};
}
function sourceTick(sample: Data, index: number): number {
  const value =
    sample.time ?? sample.t ?? sample.sourceTime?.tick ?? sample.tick ?? index;
  return Number(value);
}
function ObservationPlot({
  samples,
  observations,
}: {
  samples: Data[];
  observations: Data;
}) {
  const keys = Array.from(
    new Set(
      samples.flatMap((sample) =>
        Object.entries(numericValues(sample))
          .filter(
            ([key, value]) =>
              typeof value === "number" &&
              ![
                "time",
                "t",
                "tick",
                "sequence",
                "index",
                "sourceTick",
              ].includes(key),
          )
          .map(([key]) => key),
      ),
    ),
  ).slice(0, 4);
  const all = samples.flatMap((sample) =>
    keys
      .map((key) => numericValues(sample)[key])
      .filter((value) => typeof value === "number" && Number.isFinite(value)),
  );
  if (!keys.length || !all.length)
    return <ObservationTable samples={samples.slice(0, 200)} />;
  const min = Math.min(0, ...all),
    max = Math.max(...all, 1),
    range = max - min || 1,
    width = 900,
    height = 270,
    left = 55,
    right = 25,
    top = 20,
    bottom = 38,
    lastTime = Math.max(...samples.map(sourceTick), 1),
    firstTime = Math.min(...samples.map(sourceTick), 0),
    timeRange = lastTime - firstTime || 1,
    colors = ["#477ee7", "#2aa396", "#c89330", "#9769c3"];
  const sx = (value: number) =>
      left + ((value - firstTime) / timeRange) * (width - left - right),
    sy = (value: number) =>
      height - bottom - ((value - min) / range) * (height - top - bottom);
  return (
    <div className="plot-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Recorded observation chart. Series ${keys.join(", ")}. Use Table view for exact data.`}
      >
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line
              x1={left}
              x2={width - right}
              y1={sy(min + f * range)}
              y2={sy(min + f * range)}
              stroke="#e7edf5"
            />
            <text
              x={left - 10}
              y={sy(min + f * range) + 4}
              textAnchor="end"
              fill="#76859a"
              fontSize={11}
            >
              {(min + f * range).toFixed(2)}
            </text>
          </g>
        ))}
        {[0, 0.2, 0.4, 0.6, 0.8, 1].map((f) => (
          <g key={f}>
            <text
              x={sx(firstTime + f * timeRange)}
              y={height - 15}
              textAnchor="middle"
              fill="#76859a"
              fontSize={11}
            >
              {(firstTime + f * timeRange).toFixed(1)}
            </text>
          </g>
        ))}
        {keys.map((key, k) => {
          if (
            (observations.gaps || []).some(
              (g: Data) => g.startTick === undefined && g.start === undefined,
            )
          )
            return (
              <g key={key}>
                {samples.map((sample, index) => {
                  const value = numericValues(sample)[key];
                  return typeof value === "number" && Number.isFinite(value) ? (
                    <circle
                      key={index}
                      cx={sx(sourceTick(sample, index))}
                      cy={sy(value)}
                      r={2}
                      fill={colors[k]}
                    />
                  ) : null;
                })}
              </g>
            );
          const segments: string[][] = [[]];
          const gaps = observations.gaps || [];
          samples.forEach((sample, index) => {
            const values = numericValues(sample),
              v = values[key],
              t = sourceTick(sample, index);
            if (
              typeof v !== "number" ||
              !Number.isFinite(v) ||
              sample.gap ||
              gaps.some(
                (g: Data) =>
                  t >= Number(g.startTick ?? g.start) &&
                  t < Number(g.endTick ?? g.end),
              )
            ) {
              if (segments[segments.length - 1].length) segments.push([]);
              return;
            }
            segments[segments.length - 1].push(`${sx(t)},${sy(v)}`);
          });
          return segments
            .filter((s) => s.length)
            .map((segment, i) => (
              <polyline
                key={`${key}-${i}`}
                points={segment.join(" ")}
                fill="none"
                stroke={colors[k]}
                strokeWidth={2.4}
              />
            ));
        })}
      </svg>
      <div className="plot-legend">
        {keys.map((key, i) => (
          <span key={key}>
            <i style={{ background: colors[i] }} />
            {key}
          </span>
        ))}
      </div>
    </div>
  );
}
function ObservationTable({ samples }: { samples: Data[] }) {
  const keys = Array.from(
    new Set(samples.flatMap((s) => Object.keys(numericValues(s)))),
  ).slice(0, 8);
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Source tick</th>
            {keys.map((key) => (
              <th key={key}>{key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {samples.map((s, i) => (
            <tr key={i}>
              <td>
                {String(
                  s.time ??
                    s.t ??
                    s.sourceTime?.tick ??
                    s.tick ??
                    "Unavailable",
                )}
              </td>
              {keys.map((key) => (
                <td key={key}>
                  {typeof numericValues(s)[key] === "object"
                    ? JSON.stringify(numericValues(s)[key])
                    : String(numericValues(s)[key] ?? "Missing")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RetentionPanel({ run, doAction }: { run: Run; doAction: DoAction }) {
  const [plan, setPlan] = useState<Data | null>(null);
  return (
    <div className="retention-panel">
      <h3>Explicit retention</h3>
      <p className="field-hint">
        Preview dependencies before requesting removal. Active inputs,
        evaluations, annotations, and campaign references can protect run files.
        Historical outcomes and snapshot identities remain recorded.
      </p>
      <button
        className="button"
        onClick={() =>
          void doAction("Planning retention without changes", async () =>
            setPlan(
              await api("/retention/plans", {
                method: "POST",
                body: { runIds: [run.runId] },
              }),
            ),
          )
        }
      >
        Preview removal dependencies
      </button>
      {plan && (
        <>
          <KeyValues
            values={{
              Plan: plan.planId,
              "Eligible removals": plan.removals?.length || 0,
              "Protected runs": plan.protected?.length || 0,
              Expires: new Date(Number(plan.expiresAt) * 1000).toLocaleString(),
              Status: plan.status,
            }}
          />
          {(plan.protected || []).map((p: Data) => (
            <div className="notice" key={p.runId}>
              <Icon name="info" />
              <span>{(p.reasons || []).join(" · ")}</span>
            </div>
          ))}
          <Json value={plan} />
          <button
            className="button danger-button"
            disabled={!plan.removals?.length || plan.status !== "planned"}
            onClick={() =>
              void doAction(
                "Applying the selected retention plan",
                async () => {
                  await api(`/retention/plans/${plan.planId}/apply`, {
                    method: "POST",
                    body: { fingerprint: plan.fingerprint },
                    key: mutationKey(),
                  });
                  setPlan(await api(`/retention/plans/${plan.planId}`));
                },
              )
            }
          >
            Delete {plan.removals?.length || 0} eligible run file set(s)
          </button>
        </>
      )}
    </div>
  );
}
