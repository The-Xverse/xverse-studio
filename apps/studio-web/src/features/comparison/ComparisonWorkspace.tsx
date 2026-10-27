import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, ApiError } from "../../api/client";
import type { Data, Run } from "../../api/types";
import { KeyValues } from "../../app/ui";
import {
  comparisonHistory,
  comparisonReport,
  configurationLabels,
} from "./comparison-report";
import "./comparison.css";

type Read = { abort: AbortController; sequence: number };
export function ComparisonWorkspace({
  run,
  onPlayback,
  onPreflight,
}: {
  run: Run;
  onPlayback: () => void;
  onPreflight: () => Promise<void>;
}) {
  const [history, setHistory] = useState<Data | null>(null),
    [baseline, setBaseline] = useState<Data | null>(null),
    [report, setReport] = useState<Data | null>(null),
    [busy, setBusy] = useState<Record<string, boolean>>({}),
    [errors, setErrors] = useState<Record<string, string>>({}),
    [completion, setCompletion] = useState<{
      target: string;
      origin: Element;
      intent: number;
    } | null>(null);
  const alive = useRef(false),
    sequence = useRef(0),
    intent = useRef(0),
    reads = useRef(new Map<string, Read>()),
    selected = useRef(""),
    reportHeading = useRef<HTMLHeadingElement>(null),
    historyHeading = useRef<HTMLHeadingElement>(null),
    errorHeading = useRef<HTMLParagraphElement>(null);
  useLayoutEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      for (const r of reads.current.values()) r.abort.abort();
      reads.current.clear();
    };
  }, []);
  useEffect(() => {
    void loadHistory(0);
  }, []);
  useEffect(() => {
    if (!completion) return;
    setCompletion(null);
    if (
      !alive.current ||
      completion.intent !== intent.current ||
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== completion.origin)
    )
      return;
    (completion.target === "report"
      ? reportHeading
      : completion.target === "history"
        ? historyHeading
        : errorHeading
    ).current?.focus();
  }, [completion]);
  async function read(
    channel: string,
    operation: (signal: AbortSignal) => Promise<Data>,
    accept: (v: Data) => void,
    origin?: Element,
  ) {
    if (channel === "report" && reads.current.has(channel)) return;
    reads.current.get(channel)?.abort.abort();
    const slot = { abort: new AbortController(), sequence: ++sequence.current },
      submitted = intent.current;
    reads.current.set(channel, slot);
    setBusy((b) => ({ ...b, [channel]: true }));
    setErrors((e) => ({ ...e, [channel]: "" }));
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      slot.abort.abort();
    }, 30000);
    const active = () => alive.current && reads.current.get(channel) === slot;
    try {
      const value = await operation(slot.abort.signal);
      if (active() && !slot.abort.signal.aborted) {
        accept(value);
        if (origin)
          setCompletion({ target: channel, origin, intent: submitted });
      }
    } catch (error) {
      if (active() && (!slot.abort.signal.aborted || timedOut)) {
        setErrors((e) => ({
          ...e,
          [channel]: timedOut
            ? "The recorded comparison read timed out. Retry inspection."
            : `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The recorded read could not be confirmed."}`.slice(
                0,
                1000,
              ),
        }));
        if (origin)
          setCompletion({ target: "error", origin, intent: submitted });
      }
    } finally {
      clearTimeout(timeout);
      if (reads.current.get(channel) === slot) {
        reads.current.delete(channel);
        if (alive.current) setBusy((b) => ({ ...b, [channel]: false }));
      }
    }
  }
  function loadHistory(offset: number, origin?: Element) {
    return read(
      "history",
      async (signal) =>
        comparisonHistory(
          await api(`/runs?limit=20&cursor=${offset}`, { signal }),
          offset,
        ),
      setHistory,
      origin,
    );
  }
  function choose(id: string) {
    intent.current++;
    selected.current = id;
    reads.current.get("report")?.abort.abort();
    reads.current.delete("report");
    setBaseline(
      history?.items.find((r: Data) => r.runId === id) ||
        (baseline?.runId === id ? baseline : null),
    );
    setReport(null);
    setErrors((e) => ({ ...e, report: "" }));
    setBusy((b) => ({ ...b, report: false }));
    setCompletion(null);
  }
  function inspect(origin: Element) {
    if (
      !baseline ||
      baseline.runId === run.runId ||
      reads.current.has("report")
    )
      return;
    const left = baseline,
      right = {
        runId: run.runId,
        snapshotId: run.snapshotId,
        projectId: run.projectId,
      };
    intent.current++;
    setReport(null);
    void read(
      "report",
      async (signal) =>
        comparisonReport(
          await api("/comparisons", {
            method: "POST",
            body: { leftRunId: left.runId, rightRunId: right.runId },
            signal,
          }),
          {
            runId: left.runId,
            snapshotId: left.snapshotId,
            projectId: left.projectId,
          },
          right,
        ),
      (value) => {
        if (selected.current === left.runId) setReport(value);
      },
      origin,
    );
  }
  const candidates: Data[] =
    history?.items.filter((r: Data) => r.runId !== run.runId) || [];
  if (baseline && !candidates.some((r) => r.runId === baseline.runId))
    candidates.unshift(baseline);
  return (
    <div className="comparison-workspace">
      <section className="panel" aria-label="Recorded comparison selection">
        <h3 tabIndex={-1} ref={historyHeading}>
          Baseline comparison
        </h3>
        <p>
          Compare protected inputs and recorded observations. Configuration
          differences are shown separately from quantity, time and evidence
          compatibility.
        </p>
        <p>
          Selected run: <code>{run.runId}</code> · snapshot{" "}
          <code>{run.snapshotId}</code>
        </p>
        <div className="form-actions">
          <button
            className="button"
            disabled={busy.history}
            onClick={(e) => {
              intent.current++;
              void loadHistory(0, e.currentTarget);
            }}
          >
            Refresh recorded runs
          </button>
          <button
            className="small-button"
            disabled={busy.history || !history || !history.offset}
            onClick={(e) => {
              intent.current++;
              void loadHistory(
                Math.max(0, history!.offset - 20),
                e.currentTarget,
              );
            }}
          >
            Previous runs page
          </button>
          <button
            className="small-button"
            disabled={busy.history || !history?.nextCursor}
            onClick={(e) => {
              intent.current++;
              void loadHistory(Number(history!.nextCursor), e.currentTarget);
            }}
          >
            Next runs page
          </button>
        </div>
        {busy.history && (
          <p role="status">Reading a bounded page of recorded runs…</p>
        )}
        {history && (
          <p>
            {history.items.length
              ? `Workspace records ${history.offset + 1}–${history.offset + history.items.length}.`
              : "No workspace records on this page."}{" "}
            Each baseline keeps its own frozen project identity.
          </p>
        )}
        {history && !candidates.length && (
          <p role="status">
            No other recorded runs on this page. Refresh or choose another page.
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const origin =
              (e.nativeEvent as SubmitEvent).submitter ||
              document.activeElement ||
              document.body;
            inspect(origin);
          }}
        >
          <label>
            Baseline run
            <select
              aria-label="Baseline run"
              value={baseline?.runId || ""}
              onChange={(e) => choose(e.target.value)}
              required
            >
              <option value="">Select a recorded run</option>
              {candidates.map((r) => (
                <option key={r.runId} value={r.runId}>
                  {r.runId} · {r.projectId} · {r.state}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button primary"
            disabled={!baseline || busy.report}
          >
            Inspect compatibility
          </button>
        </form>
        {busy.report && (
          <p role="status">
            Reading this exact baseline and selected run. No new workload is
            requested.
          </p>
        )}
      </section>
      {report && (
        <section
          className="panel"
          role="region"
          aria-label="Recorded comparison report"
        >
          <h3 tabIndex={-1} ref={reportHeading}>
            Comparison report
          </h3>
          <p role="status">
            <strong>
              {report.compatible
                ? "Compatible recorded windows"
                : "Pairing blocked"}
            </strong>
            . Compatibility is a metadata and evidence check, not an assertion
            verdict.
          </p>
          <div className="comparison-identities">
            {["left", "right"].map((side) => (
              <div key={side}>
                <h4>
                  {side === "left" ? "Frozen baseline" : "Frozen selected run"}
                </h4>
                <KeyValues
                  values={{
                    Run: report[side].runId,
                    Snapshot: report[side].snapshotId,
                    "Snapshot digest": report[side].snapshotDigest,
                    Project: report[side].projectId,
                    Revision: report[side].revision,
                    "Execution state": report[side].state,
                    Cleanup: report[side].cleanup,
                    "Snapshot integrity": report[side].snapshotIntegrity,
                    "Evidence integrity": report[side].evidenceIntegrity,
                    "Evidence status": report[side].evidenceStatus,
                    "Effective inputs verified":
                      report[side].effectiveInputsMatch,
                  }}
                />
              </div>
            ))}
          </div>
          {report.diagnostics.length > 0 && (
            <ul aria-label="Comparison blockers">
              {report.diagnostics.map((code: string) => (
                <li key={code}>
                  <code>{code}</code> — {reason(code)}
                </li>
              ))}
            </ul>
          )}
          <div className="table-scroll">
            <table>
              <caption>Frozen configuration differences</caption>
              <thead>
                <tr>
                  <th>Input / status</th>
                  <th>Baseline</th>
                  <th>Selected run</th>
                </tr>
              </thead>
              <tbody>
                {report.configuration.map((row: Data) => (
                  <tr key={row.field}>
                    <th scope="row">
                      {configurationLabels[row.field]}
                      <br />
                      {row.status}
                    </th>
                    {["left", "right"].map((side) => (
                      <td key={side}>
                        <Value
                          value={row[side]}
                          label={`${side === "left" ? "Baseline" : "Selected"} ${configurationLabels[row.field]}`}
                          open={
                            row.status === "different" &&
                            ["parameters", "clockDefinitions"].includes(
                              row.field,
                            )
                          }
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            Results below keep each side's original units, source ticks and
            coverage. Blocked pairs are shown independently; no interpolation,
            alignment or numeric delta is invented.
          </p>
          <div className="table-scroll">
            <table>
              <caption>Recorded field results</caption>
              <thead>
                <tr>
                  <th>Observer / field</th>
                  <th>Baseline result</th>
                  <th>Selected result</th>
                </tr>
              </thead>
              <tbody>
                {report.fields.map((field: Data, i: number) => (
                  <tr key={i}>
                    <th scope="row">
                      <code>{field.observerRef || "Unknown observer"}</code>
                      <br />
                      {field.field || "Unknown field"}
                      <p>
                        {field.compatible
                          ? "Field checks pass"
                          : "Field checks blocked"}
                      </p>
                      {field.reasons.map((r: string) => (
                        <p key={r}>
                          <code>{r}</code>
                        </p>
                      ))}
                    </th>
                    <td>
                      <Recorded value={field.left} />
                    </td>
                    <td>
                      <Recorded value={field.right} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!report.fields.length && (
            <p role="status">
              No recorded fields are available for comparison.
            </p>
          )}
          <ul aria-label="Comparison limits">
            {report.limitations.map((s: string) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </section>
      )}
      <aside className="panel">
        <h3>Recorded playback and fresh execution</h3>
        <p>
          Playback only re-presents the selected run's recorded observations. It
          does not execute a model or establish deterministic or physical
          replay.
        </p>
        <button className="button" onClick={onPlayback}>
          Open recorded playback
        </button>
        <p>
          A new run from the current draft needs fresh preflight and a
          separately accepted Start. Rerun frozen inputs, above, also creates a
          new identity through backend admission.
        </p>
        <button className="button" onClick={() => void onPreflight()}>
          Preflight a new run
        </button>
      </aside>
      {Object.values(errors).some(Boolean) && (
        <p role="alert" tabIndex={-1} ref={errorHeading}>
          {Object.values(errors).filter(Boolean).join(" ")}{" "}
          {errors.history
            ? "Previous history observations have not been refreshed. "
            : ""}
          No new workload was requested by inspection.
        </p>
      )}
    </div>
  );
}
function Value({
  value,
  label,
  open,
}: {
  value: any;
  label: string;
  open: boolean;
}) {
  if (value === null) return <>Unavailable</>;
  if (typeof value !== "object") return <code>{String(value)}</code>;
  return (
    <details open={open}>
      <summary>Inspect {label}</summary>
      <pre tabIndex={0} aria-label={label}>
        {JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}
function Recorded({ value }: { value: Data }) {
  if (!value.available) return <p>No observation on this side.</p>;
  const s = value.summary,
    c = value.coverage;
  return (
    <div>
      <p>
        Quantity: {value.quantity || "Unknown"}; unit: {value.unit || "Unknown"}
        .
      </p>
      <p>
        Unit identity:{" "}
        <code>{value.unitDefinitionDigest || "Unavailable"}</code>
      </p>
      <p>
        Clock: <code>{value.clockDomainRef || "Unknown"}</code>. Resolution:{" "}
        {value.sourceTime?.resolution || "Unknown"}; uncertainty:{" "}
        {value.sourceTime?.uncertainty ?? "Unknown"}.
      </p>
      <p>
        Window:{" "}
        <code>
          {c.startTick ?? "Unknown"} → {c.endTick ?? "Unknown"}
        </code>
        . Coverage {c.complete ? "complete" : "incomplete"},{" "}
        {c.verified ? "verified" : "unverified"}; reported gaps:{" "}
        {c.gapCount ?? "unknown"}.
      </p>
      {s.status === "available" ? (
        <p>
          {s.sampleCount} recorded samples. Range {s.minimum}…{s.maximum}; last
          value {s.lastValue}. Sample ticks{" "}
          <code>
            {s.firstTick} → {s.lastTick}
          </code>
          .
        </p>
      ) : (
        <p>
          Numeric summary unavailable. Original evidence quality remains
          separate from run state.
        </p>
      )}
    </div>
  );
}
function reason(code: string) {
  const known: Record<string, string> = {
    OBSERVATION_IDENTITY_UNVERIFIED:
      "Recorded observer units or clock do not match its frozen compiled declaration.",
    CONFIGURATION_PROVENANCE_UNAVAILABLE:
      "A frozen configuration fact is unavailable; missing facts are not equivalence.",
    OBSERVATION_WINDOW_INCOMPATIBLE: "The complete source-time windows differ.",
    OBSERVATION_WINDOW_UNAVAILABLE:
      "Exact source-time bounds could not be established.",
    OBSERVATION_WINDOW_MISMATCH:
      "Recorded sample ticks do not fit the declared coverage window.",
    QUANTITY_INCOMPATIBLE:
      "Physical quantity or unit definitions do not agree.",
    CLOCK_ALIGNMENT_UNPROVEN:
      "Source clock alignment or uncertainty is unproven.",
    CLOCK_DEFINITION_INCOMPATIBLE: "Frozen clock definitions differ.",
    OBSERVATION_COVERAGE_INCOMPLETE:
      "Coverage is incomplete, unverified or gapped.",
    EVIDENCE_INTEGRITY_UNPROVEN:
      "Canonical evidence integrity is not established.",
  };
  return (
    known[code] ||
    "A required recorded identity, source-quality or compatibility check is not established. Inspect the original run evidence."
  );
}
