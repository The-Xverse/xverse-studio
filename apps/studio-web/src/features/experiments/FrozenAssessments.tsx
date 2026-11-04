import { useEffect, useRef, useState } from "react";
import type { Evaluation } from "../../../../../packages/contracts/api";
import { api, mutationKey } from "../../api/client";
import type { Data, Run } from "../../api/types";
import type { DoAction } from "../../app/App";
import { Badge, Json, KeyValues, statusTone } from "../../app/ui";

type Report = {
  snapshot: Data;
  support: Data;
  definitions: Data[];
  results: Data[];
  nextCursor: string | null;
};
type State = {
  status: "loading" | "available" | "unavailable";
  report?: Report;
  error?: string;
};
const hash = (v: unknown) =>
  typeof v === "string" && /^sha256:[a-f0-9]{64}$/.test(v);
const text = (v: unknown, limit = 4096): v is string =>
  typeof v === "string" && v.length > 0 && v.length <= limit;
const hashes = (v: unknown) =>
  Array.isArray(v) && v.length <= 64 && v.every(hash);
const object = (v: any): v is Data =>
  !!v && typeof v === "object" && !Array.isArray(v);

/** Display guards; the backend remains authoritative for XDL and evaluation. */
export function assessmentReport(
  snapshot: Data,
  definitions: Data,
  results: Data,
  run: Run,
  projectId: string,
  support: Data,
): Report {
  const fail = (): never => {
    throw new Error(
      "Assessment inputs are malformed or belong to another run or snapshot. Inspect again to retry.",
    );
  };
  const frozen = snapshot?.snapshot;
  if (
    snapshot?.integrity !== "valid" ||
    snapshot?.readOnly !== true ||
    !object(frozen) ||
    frozen.snapshotId !== run.snapshotId ||
    frozen.projectId !== projectId ||
    run.projectId !== projectId ||
    !Number.isSafeInteger(frozen.revision) ||
    frozen.revision < 1 ||
    !hash(frozen.snapshotDigest) ||
    !object(frozen.selection) ||
    !["systemRef", "scenarioRef", "deploymentRef"].every(
      (k) =>
        text(frozen.selection[k]) && frozen.selection[k].startsWith("xdl://"),
    ) ||
    !Array.isArray(definitions?.items) ||
    definitions.items.length > 32 ||
    definitions.nextCursor !== null ||
    !Array.isArray(results?.items) ||
    results.items.length > 100 ||
    !(
      results.nextCursor === null ||
      (typeof results.nextCursor === "string" &&
        /^[0-9]{1,16}$/.test(results.nextCursor))
    )
  )
    fail();
  if (
    !object(support) ||
    support.formatVersion !== "1.0" ||
    support.runId !== run.runId ||
    support.snapshotId !== run.snapshotId ||
    support.projectId !== projectId ||
    support.snapshotDigest !== frozen.snapshotDigest ||
    support.providerId !== frozen.providerIdentity?.providerId ||
    support.evidenceScope !== frozen.providerIdentity?.evidenceScope ||
    !["supported", "unsupported"].includes(support.status) ||
    !Array.isArray(support.reasons) ||
    support.reasons.length > 32 ||
    !support.reasons.every((reason: unknown) => text(reason, 256)) ||
    !(support.evidenceReader === null || text(support.evidenceReader, 128)) ||
    !(support.evidenceId === null || text(support.evidenceId, 512)) ||
    (support.status === "supported" &&
      (!text(support.evidenceId, 512) || support.reasons.length !== 0)) ||
    (support.status === "unsupported" && !support.reasons.length)
  )
    fail();
  const known = new Map<string, Data>();
  for (const entry of definitions.items) {
    const d = entry?.definition;
    if (
      !object(entry) ||
      !text(entry.definitionRef, 256) ||
      JSON.stringify(entry).length > 65536 ||
      entry.profileNamespace !== "io.xverse.studio.experiments" ||
      entry.profileVersion !== "1.0.0" ||
      !hash(entry.definitionDigest) ||
      !hash(entry.schemaDigest) ||
      !object(d) ||
      d.evaluationId !== entry.definitionRef ||
      !["assertion", "metric"].includes(d.kind) ||
      !text(d.name) ||
      d.version !== "1.0" ||
      d.coveragePolicy !== "complete" ||
      ![d.systemRef, d.scenarioRef].every(
        (v) => text(v) && v.startsWith("xdl://"),
      ) ||
      !object(d.window) ||
      ![d.window.startTick, d.window.endTick].every(
        (v) => typeof v === "string" && /^-?(0|[1-9][0-9]{0,31})$/.test(v),
      ) ||
      BigInt(d.window.startTick) >= BigInt(d.window.endTick) ||
      !text(d.window.clockDomainRef, 512) ||
      known.has(entry.definitionRef)
    )
      fail();
    known.set(entry.definitionRef, entry);
  }
  const ids = new Set();
  for (const row of results.items) {
    const definition = known.get(row?.definitionRef);
    if (
      !object(row) ||
      row.runId !== run.runId ||
      row.snapshotId !== run.snapshotId ||
      !definition ||
      row.definitionDigest !== definition.definitionDigest ||
      !text(row.evaluationId, 256) ||
      JSON.stringify(row).length > 262144 ||
      (row.evidenceDigests !== undefined && !hashes(row.evidenceDigests)) ||
      (row.inputEvidenceDigests !== undefined &&
        !hashes(row.inputEvidenceDigests)) ||
      (row.evaluatorIdentity !== undefined &&
        (!object(row.evaluatorIdentity) ||
          !Object.values(row.evaluatorIdentity).every((v) => text(v, 512)))) ||
      (row.unit !== undefined && row.unit !== null && !text(row.unit, 512)) ||
      (row.coverage !== undefined &&
        ![null, "complete", "incomplete", "invalid"].includes(row.coverage)) ||
      (row.partial !== undefined &&
        row.partial !== null &&
        typeof row.partial !== "boolean") ||
      ids.has(row.evaluationId) ||
      !["not_started", "running", "complete", "unavailable", "error"].includes(
        row.status,
      ) ||
      ![null, "pass", "fail", "indeterminate"].includes(row.verdict) ||
      (row.verdict !== null &&
        (row.status !== "complete" ||
          definition.definition.kind !== "assertion")) ||
      (["pass", "fail"].includes(row.verdict) &&
        (row.coverage !== "complete" || row.partial !== false)) ||
      (row.reasons !== undefined &&
        (!Array.isArray(row.reasons) ||
          row.reasons.length > 1000 ||
          row.reasons.some((r: unknown) => !text(r, 256)))) ||
      (row.value !== undefined &&
        row.value !== null &&
        typeof row.value !== "boolean" &&
        !(typeof row.value === "number" && Number.isFinite(row.value)))
    )
      fail();
    ids.add(row.evaluationId);
  }
  return {
    snapshot: frozen,
    support,
    definitions: definitions.items,
    results: results.items,
    nextCursor: results.nextCursor,
  };
}

export function FrozenAssessments({
  projectId,
  run,
  doAction,
}: {
  projectId: string;
  run: Run | null;
  doAction: DoAction;
}) {
  const [state, setState] = useState<State>({ status: "loading" }),
    [definition, setDefinition] = useState(""),
    [cursor, setCursor] = useState<string | null>(null),
    [history, setHistory] = useState<(string | null)[]>([]),
    [refresh, setRefresh] = useState(0),
    [submitting, setSubmitting] = useState(false);
  const mounted = useRef(false),
    request = useRef(0),
    pending = useRef(false),
    retry = useRef<{ fingerprint: string; key: string } | null>(null);
  const enabled = !!run && run.projectId === projectId && !!run.snapshotId;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      request.current++;
    };
  }, []);
  useEffect(() => {
    if (!enabled || !run) return;
    const sequence = ++request.current,
      abort = new AbortController();
    setState({ status: "loading" });
    setDefinition("");
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      abort.abort();
    }, 30000);
    const route = `/runs/${encodeURIComponent(run.runId)}`;
    void Promise.all([
      api(`${route}/snapshot`, { signal: abort.signal }),
      api(`${route}/definitions`, { signal: abort.signal }),
      api(`${route}/assessment-support`, { signal: abort.signal }),
      api(
        `${route}/evaluations?${new URLSearchParams({ limit: "100", ...(cursor === null ? {} : { cursor }) })}`,
        { signal: abort.signal },
      ),
    ])
      .then(([snapshot, definitions, support, results]) => {
        const report = assessmentReport(
          snapshot,
          definitions,
          results,
          run,
          projectId,
          support,
        );
        if (
          mounted.current &&
          sequence === request.current &&
          !abort.signal.aborted
        )
          setState({ status: "available", report });
      })
      .catch((error) => {
        if (
          mounted.current &&
          sequence === request.current &&
          (!abort.signal.aborted || timedOut)
        )
          setState({
            status: "unavailable",
            error: timedOut
              ? "The assessment read timed out. Inspect again to retry."
              : String(
                  error instanceof Error
                    ? error.message
                    : "The assessment inputs could not be read.",
                ).slice(0, 1000),
          });
      })
      .finally(() => {
        clearTimeout(timer);
        abort.abort();
      });
    return () => {
      clearTimeout(timer);
      abort.abort();
      request.current++;
    };
  }, [enabled, run?.runId, run?.snapshotId, projectId, cursor, refresh]);
  const report = state.status === "available" ? state.report : undefined,
    selected = report?.definitions.find((d) => d.definitionRef === definition);
  return (
    <section
      className="panel"
      aria-label="Frozen assertions and metrics"
      aria-busy={state.status === "loading" && enabled}
    >
      <div className="section-heading">
        <h3>Frozen assertions and metrics</h3>
        <button
          className="button"
          disabled={!enabled || state.status === "loading" || submitting}
          onClick={() => {
            setCursor(null);
            setHistory([]);
            setRefresh((v) => v + 1);
          }}
        >
          Inspect frozen assessments
        </button>
      </div>
      {!enabled ? (
        <p role="status">
          Select a run belonging to this project to inspect its frozen
          assessments.
        </p>
      ) : (
        <>
          <p>
            Run {run!.runId} · Snapshot {run!.snapshotId}. Current drafts do not
            supply assessment definitions or results.
          </p>
          {state.status === "loading" && (
            <p role="status">
              Reading frozen definitions and evaluation results…
            </p>
          )}
          {state.status === "unavailable" && (
            <p role="alert">
              Assessment availability is unknown. {state.error}
            </p>
          )}
          {report && (
            <>
              <KeyValues
                values={{
                  "Snapshot digest": report.snapshot.snapshotDigest,
                  "Executed project revision": report.snapshot.revision,
                  "Frozen Scenario": report.snapshot.selection.scenarioRef,
                  "Frozen System": report.snapshot.selection.systemRef,
                }}
              />
              <KeyValues
                values={{
                  "Evaluation evidence support": report.support.status,
                  "Canonical evidence reader":
                    report.support.evidenceReader ?? "Unavailable",
                  "Canonical evidence identity":
                    report.support.evidenceId ?? "Unavailable",
                }}
              />
              {report.support.status === "unsupported" && (
                <p role="status">
                  Not evaluated: no admitted measurement, unit, clock and
                  coverage mapping for this provider's evidence reader. Original
                  evidence and historical results remain inspectable.{" "}
                  {report.support.reasons.join(", ")}
                </p>
              )}
              <h4>Frozen definitions</h4>
              {report.definitions.length ? (
                report.definitions.map((entry) => (
                  <article key={entry.definitionRef}>
                    <h5>{entry.definition.name}</h5>
                    <KeyValues
                      values={{
                        Kind: entry.definition.kind,
                        System: entry.definition.systemRef,
                        Scenario: entry.definition.scenarioRef,
                        Definition: entry.definitionRef,
                        "Definition digest": entry.definitionDigest,
                        "Clock domain": entry.definition.window.clockDomainRef,
                        "Window (source ticks)": `[${entry.definition.window.startTick}, ${entry.definition.window.endTick})`,
                        "Coverage policy": entry.definition.coveragePolicy,
                        Profile: `${entry.profileNamespace} · ${entry.profileVersion}`,
                        "Schema digest": entry.schemaDigest,
                      }}
                    />
                    <Json value={entry.definition} />
                  </article>
                ))
              ) : (
                <p>
                  No admitted assessment definitions in this frozen snapshot.
                  Opaque imported expressions remain preserved and not
                  evaluated.
                </p>
              )}
              <h4>Evaluation results</h4>
              <p>
                Execution status, assertion verdict and metric value are
                separate. A completed run does not create a passing assertion.
                Clock placement and fault markers are available in Timeline;
                placement does not prove causality.
              </p>
              {report.results.length ? (
                report.results.map((row) => (
                  <article className="evaluation-card" key={row.evaluationId}>
                    <h5>{row.definitionRef}</h5>
                    <Badge tone={statusTone(row.verdict || row.status)}>
                      {row.verdict ||
                        (row.status === "error"
                          ? "Evaluation error"
                          : row.status === "complete"
                            ? "Evaluation complete"
                            : row.status === "running"
                              ? "Evaluation running"
                              : "Not evaluated")}
                    </Badge>
                    <KeyValues
                      values={{
                        "Evaluation ID": row.evaluationId,
                        "Execution status": row.status,
                        "Assertion verdict": row.verdict ?? "No verdict",
                        Value: row.value ?? "Unavailable",
                        Unit: row.unit ?? "Unknown",
                        Coverage: row.coverage ?? "Unknown",
                        Partial:
                          row.partial == null ? "Unknown" : String(row.partial),
                        Reasons:
                          row.reasons?.slice(0, 100).join(", ") ||
                          "None reported",
                        "Definition digest": row.definitionDigest,
                        Evaluator:
                          row.evaluatorIdentity?.version ?? "Unavailable",
                        "Evaluator digest":
                          row.evaluatorIdentity?.implementationDigest ??
                          "Unavailable",
                        "Input evidence digests":
                          row.inputEvidenceDigests?.join(", ") || "Unavailable",
                        "Result evidence digests":
                          row.evidenceDigests?.join(", ") || "Unavailable",
                      }}
                    />
                    {row.reasons?.length > 100 && (
                      <p>
                        Additional reason codes are retained in the immutable
                        result.
                      </p>
                    )}
                    <Json value={row} />
                  </article>
                ))
              ) : (
                <p>
                  No evaluation results on this page. This does not establish a
                  pass or absence of results on other pages.
                </p>
              )}
              <div className="form-actions">
                <button
                  className="button"
                  disabled={!history.length || submitting}
                  onClick={() => {
                    setCursor(history[history.length - 1]);
                    setHistory((v) => v.slice(0, -1));
                  }}
                >
                  Previous assessment page
                </button>
                <button
                  className="button"
                  disabled={report.nextCursor === null || submitting}
                  onClick={() => {
                    setHistory((v) => [...v, cursor]);
                    setCursor(report.nextCursor);
                  }}
                >
                  Next assessment page
                </button>
              </div>
              <h4>Evaluate a frozen definition</h4>
              <p>
                Evaluation reads canonical evidence. Missing coverage or an
                unsupported clock remains indeterminate; an evaluation error is
                separate from runtime failure.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (
                    !run ||
                    !selected ||
                    pending.current ||
                    report.support.status !== "supported"
                  )
                    return;
                  const body: Evaluation = {
                    snapshotId: run.snapshotId,
                    definitionRef: selected.definitionRef,
                    definitionDigest: selected.definitionDigest,
                    evidenceRefs: [report.support.evidenceId],
                  };
                  const fingerprint = JSON.stringify(body);
                  if (retry.current?.fingerprint !== fingerprint)
                    retry.current = { fingerprint, key: mutationKey() };
                  const key = retry.current.key;
                  pending.current = true;
                  setSubmitting(true);
                  void doAction("Evaluating frozen definition", async () => {
                    try {
                      const result = await api(
                        `/runs/${encodeURIComponent(run.runId)}/evaluations`,
                        { method: "POST", key, body },
                      );
                      if (mounted.current) {
                        retry.current = null;
                        setCursor(null);
                        setHistory([]);
                        setRefresh((v) => v + 1);
                      }
                      return result;
                    } finally {
                      pending.current = false;
                      if (mounted.current) setSubmitting(false);
                    }
                  });
                }}
              >
                <label>
                  Snapshot definition reference
                  <select
                    value={definition}
                    disabled={submitting}
                    onChange={(e) => setDefinition(e.target.value)}
                    required
                  >
                    <option value="">
                      {report.definitions.length
                        ? "Select a frozen definition"
                        : "No admitted definitions in this snapshot"}
                    </option>
                    {report.definitions.map((entry) => (
                      <option
                        key={entry.definitionRef}
                        value={entry.definitionRef}
                      >
                        {entry.definition.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="button primary"
                  disabled={
                    !selected ||
                    submitting ||
                    report.support.status !== "supported"
                  }
                >
                  Evaluate assertion
                </button>
              </form>
            </>
          )}
        </>
      )}
    </section>
  );
}
