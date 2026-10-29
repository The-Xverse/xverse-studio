import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Data, Run } from "../../api/types";
import { api, ApiError } from "../../api/client";
import { Json, KeyValues } from "../../app/ui";
import { timelineCoordinates, timelineReport } from "./timeline-report";
import "./scenarioTimeline.css";

type Page = { cursor: string | null; offset: number; identity?: string };
type State = {
  key: string;
  status: "idle" | "loading" | "available" | "unavailable";
  report?: Data;
  error?: string;
};

export function ScenarioTimeline({
  projectId,
  revision,
  scenarioRef,
  run,
}: {
  projectId: string;
  revision: number;
  scenarioRef?: string;
  run: Run | null;
}) {
  const [clock, setClock] = useState(""),
    [clocks, setClocks] = useState<Data[]>([]),
    [state, setState] = useState<State>({ key: "", status: "idle" }),
    [pages, setPages] = useState<Page[]>([{ cursor: null, offset: 0 }]),
    [index, setIndex] = useState(0),
    [focus, setFocus] = useState<{
      key: string;
      request: number;
      origin: Element | null;
    } | null>(null);
  const key = JSON.stringify([
      projectId,
      revision,
      scenarioRef,
      run?.runId,
      run?.snapshotId,
      clock,
    ]),
    current = useRef(key),
    mounted = useRef(false),
    sequence = useRef(0),
    pending = useRef(false),
    controller = useRef<AbortController | null>(null),
    heading = useRef<HTMLHeadingElement>(null),
    failure = useRef<HTMLParagraphElement>(null);
  current.current = key;
  const visible = state.key === key ? state : { key, status: "idle" as const },
    report = visible.report,
    enabled = !!run?.runId && !!run.snapshotId && run.projectId === projectId;
  useLayoutEffect(() => {
    mounted.current = true;
    pending.current = false;
    setState({ key, status: "idle" });
    setFocus(null);
    setPages([{ cursor: null, offset: 0 }]);
    setIndex(0);
    return () => {
      mounted.current = false;
      sequence.current++;
      pending.current = false;
      controller.current?.abort();
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
    (visible.status === "unavailable"
      ? failure.current
      : heading.current
    )?.focus();
  }, [focus, key, visible.status]);
  async function read(
    origin: Element | null,
    target: Page = { cursor: null, offset: 0 },
    nextIndex = 0,
  ) {
    if (!enabled || pending.current || !run) return;
    const request = ++sequence.current,
      submitted = key,
      abort = new AbortController();
    controller.current?.abort();
    controller.current = abort;
    pending.current = true;
    setState({ key, status: "loading" });
    setFocus({ key, request, origin });
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      abort.abort();
    }, 30000);
    try {
      const query = new URLSearchParams({
        snapshotId: run.snapshotId,
        limit: "100",
      });
      if (clock) query.set("clockDomain", clock);
      if (target.cursor) query.set("cursor", target.cursor);
      const value = timelineReport(
        await api(`/runs/${encodeURIComponent(run.runId)}/timeline?${query}`, {
          signal: abort.signal,
        }),
        {
          projectId,
          runId: run.runId,
          snapshotId: run.snapshotId,
          clock: clock || undefined,
          offset: target.offset,
          inputIdentity: target.identity,
        },
      );
      if (
        mounted.current &&
        current.current === submitted &&
        request === sequence.current &&
        !abort.signal.aborted
      ) {
        setState({ key: submitted, status: "available", report: value });
        setClocks(value.clockDomains);
        setPages((old) =>
          target.cursor
            ? [...old.slice(0, nextIndex), target]
            : [{ cursor: null, offset: 0, identity: value.inputIdentity }],
        );
        setIndex(nextIndex);
      }
    } catch (error) {
      if (
        mounted.current &&
        current.current === submitted &&
        request === sequence.current &&
        (!abort.signal.aborted || timedOut)
      )
        setState({
          key: submitted,
          status: "unavailable",
          error: timedOut
            ? "The timeline read timed out. Inspect again to retry."
            : `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The timeline could not be read."}`.slice(
                0,
                1000,
              ),
        });
    } finally {
      clearTimeout(timer);
      if (sequence.current === request) pending.current = false;
    }
  }
  return (
    <section
      className="panel scenario-timeline"
      aria-label="Selected run timeline"
      aria-busy={visible.status === "loading"}
    >
      <div className="section-heading">
        <div>
          <h3 ref={heading} tabIndex={-1}>
            Selected run timeline
          </h3>
          <p>
            Frozen intentions, recorded events and immutable evaluation windows.
          </p>
        </div>
        <button
          className="button"
          disabled={!enabled || visible.status === "loading"}
          onClick={(e) => void read(e.currentTarget)}
        >
          Inspect selected run timeline
        </button>
      </div>
      <p className="field-hint">
        Read-only inspection. Same-axis placement does not prove causality or an
        intended effect. Source time and receipt time remain separate.
      </p>
      {!enabled ? (
        <p role="status">
          Select a run belonging to this project to inspect its timeline. A
          current draft cannot substitute for a frozen snapshot.
        </p>
      ) : (
        <>
          <label>
            Timeline clock
            <select
              aria-label="Timeline clock"
              disabled={visible.status === "loading"}
              value={clock}
              onChange={(e) => setClock(e.target.value)}
            >
              <option value="">Frozen System default</option>
              {clocks.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} · {c.declared ? "declared" : "observed only"}
                </option>
              ))}
            </select>
          </label>
          {visible.status === "idle" && (
            <p>
              Inspect to read the exact run inputs and available clocks.
              Changing the clock requires a new inspection.
            </p>
          )}
        </>
      )}
      {visible.status === "loading" && (
        <p role="status">Reading the selected run timeline…</p>
      )}
      {visible.status === "unavailable" && (
        <p ref={failure} tabIndex={-1} className="notice error" role="alert">
          Timeline availability is unknown. {visible.error} Inspect again to
          read the first page.
        </p>
      )}
      {report && (
        <>
          <KeyValues
            values={{
              Run: report.runId,
              Snapshot: report.snapshotId,
              "Snapshot digest": report.snapshotDigest,
              "Executed project revision": report.projectRevision,
              "Frozen Scenario": report.selection.scenarioRef,
              "Frozen Deployment": report.selection.deploymentRef,
              "Source clock": report.clockDomain || "Unknown",
              "Admitted axis unit": report.tickUnit || "Unknown",
              "Intent display codec": report.intentClockCodec || "Unavailable",
              "Evidence scope": report.evidenceScope,
              "Journal integrity": report.recorded.integrity,
              "Evidence collection": report.recorded.collectionStatus,
              "Timeline coverage": "Not attested",
            }}
          />
          {(revision !== report.projectRevision ||
            (scenarioRef && scenarioRef !== report.selection.scenarioRef)) && (
            <p className="notice">
              Current draft differs from the executed revision or Scenario. This
              timeline uses only the frozen run inputs; current draft revision{" "}
              {revision} is separate.
            </p>
          )}
          <p role="status">
            Showing rows{" "}
            {report.items.length ? report.reduction.pageStart + 1 : 0}–
            {report.reduction.pageStart + report.items.length} of{" "}
            {report.counts.matchedRows}. {report.counts.unplacedRows} unplaced
            rows across the projection.
          </p>
          <p className="field-hint">
            Input completeness: intentions{" "}
            {report.inputsComplete.intents ? "complete" : "incomplete"};
            recorded evidence{" "}
            {report.inputsComplete.recorded ? "complete" : "incomplete"};
            evaluation lookup{" "}
            {report.inputsComplete.evaluations ? "complete" : "incomplete"}.
            Clock list {report.clockDomainsComplete ? "complete" : "incomplete"}
            .
          </p>
          <p className="notice">
            Recorded gaps: {report.recorded.gapCount}. Gap list{" "}
            {report.recorded.gapsComplete ? "complete" : "incomplete"}. No line
            bridges missing observations; an empty page does not establish
            absence.
          </p>
          <KeyValues
            values={{
              "Missing source times": report.recorded.quality.missingSourceTime,
              "Malformed source times":
                report.recorded.quality.malformedSourceTime,
              "Missing receipt times":
                report.recorded.quality.missingReceiptTime,
              "Unsupported receipt encodings":
                report.recorded.quality.unsupportedReceiptEncoding,
            }}
          />
          {report.recorded.gaps.map((gap: Data, i: number) => (
            <p key={i}>
              Gap {i + 1}: {gap.reason || "Reason unavailable"}
            </p>
          ))}
          {report.diagnostics.map((d: Data, i: number) => (
            <p className="notice" key={i}>
              {d.code}
            </p>
          ))}
          {!report.diagnosticsComplete && (
            <p>Additional projection diagnostics were omitted.</p>
          )}
          <section aria-label="Frozen assessment definitions">
            <h4>Frozen assessment definitions</h4>
            <p>
              Inspection does not evaluate these definitions. These declarations
              belong to the selected frozen Scenario; results and verdicts
              appear separately below.
            </p>
            {report.assessmentDefinitions.status === "unavailable" ? (
              <p role="status">
                Assessment definitions are unavailable. Their absence is not
                established; inspect the projection diagnostics.
              </p>
            ) : (
              <>
                {!report.assessmentDefinitions.complete && (
                  <p role="status">
                    The definition list is incomplete. Omitted declarations
                    remain in frozen source.
                  </p>
                )}
                {!report.assessmentDefinitions.items.length ? (
                  <p>
                    No admitted assessment definitions were returned. Opaque
                    imported expressions remain preserved and unevaluated.
                  </p>
                ) : (
                  <details>
                    <summary>
                      Inspect frozen definitions (
                      {report.assessmentDefinitions.items.length})
                    </summary>
                    <div
                      className="table-scroll"
                      tabIndex={0}
                      role="region"
                      aria-label="Scrollable frozen assessment definitions"
                    >
                      <table aria-label="Frozen assessment definitions">
                        <thead>
                          <tr>
                            <th>Declared definition</th>
                            <th>Clock / window / policy</th>
                            <th>Identity / typed declaration</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.assessmentDefinitions.items.map(
                            (entry: Data) => (
                              <tr
                                key={entry.definitionRef}
                                data-definition-ref={entry.definitionRef}
                              >
                                <td>
                                  <strong>{entry.definition.name}</strong>
                                  <span>
                                    {entry.definition.kind} ·{" "}
                                    {entry.definitionRef}
                                  </span>
                                  <small>
                                    Declared intent; no verdict from inspection
                                  </small>
                                </td>
                                <td>
                                  <span>
                                    {entry.definition.window.clockDomainRef}
                                  </span>
                                  <span>
                                    [{entry.definition.window.startTick},{" "}
                                    {entry.definition.window.endTick}) source
                                    ticks
                                  </span>
                                  <small>
                                    Declared coverage policy:{" "}
                                    {entry.definition.coveragePolicy}
                                  </small>
                                  {entry.definition.resultUnit && (
                                    <small>
                                      Declared result unit:{" "}
                                      {entry.definition.resultUnit}
                                    </small>
                                  )}
                                </td>
                                <td>
                                  <span>{entry.definitionDigest}</span>
                                  <small>
                                    Profile: {entry.profileNamespace} ·{" "}
                                    {entry.profileVersion}
                                  </small>
                                  <small>Schema: {entry.schemaDigest}</small>
                                  <Json value={entry} />
                                </td>
                              </tr>
                            ),
                          )}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
              </>
            )}
          </section>
          <TimelinePlot report={report} />
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Scrollable timeline records"
          >
            <table aria-label="Timeline records">
              <thead>
                <tr>
                  <th>Layer / identity</th>
                  <th>Original time / placement</th>
                  <th>Observation or assessment</th>
                  <th>Scope / provenance</th>
                </tr>
              </thead>
              <tbody>
                {report.items.map((row: Data) => (
                  <tr key={row.id} data-timeline-id={row.id}>
                    <td>
                      <strong>
                        {row.layer} · {row.kind}
                      </strong>
                      <code>
                        {row.intentId || row.eventId || row.evaluationId}
                      </code>
                    </td>
                    <td>
                      {row.position.endTick !== undefined
                        ? `[${row.position.tick}, ${row.position.endTick})`
                        : (row.position.tick ?? "No source tick")}
                      <small>
                        {row.position.clockDomain || "Clock unknown"} ·{" "}
                        {row.position.tickUnit || "Unit unknown"}
                      </small>
                      <span>
                        {row.position.status === "aligned"
                          ? "Placed in selected clock"
                          : `Unplaced: ${row.position.reason}`}
                      </span>
                      {row.schedule && (
                        <small>
                          Declared schedule: {row.schedule.at}{" "}
                          {row.schedule.unit}
                        </small>
                      )}
                      {row.sourceTime && (
                        <small>
                          Original metadata: {JSON.stringify(row.sourceTime)}
                        </small>
                      )}
                      {row.layer === "recorded" && (
                        <small>
                          Receipt UTC: {row.recordedAtUtc || "Unavailable"} ·{" "}
                          {row.receiptEncoding}
                        </small>
                      )}
                    </td>
                    <td>
                      {row.layer === "evaluation" ? (
                        <>
                          <span>Execution: {row.executionStatus}</span>
                          <span>
                            {row.verdict === null
                              ? "No verdict"
                              : `Assertion verdict: ${row.verdict}`}
                          </span>
                          <span>
                            Value:{" "}
                            {row.value === null
                              ? "Unavailable"
                              : String(row.value)}{" "}
                            {row.unit}
                          </span>
                          <small>
                            Coverage: {row.coverage ?? "Unknown"}; partial:{" "}
                            {row.partial === null
                              ? "Unknown"
                              : String(row.partial)}
                          </small>
                          <small>
                            Reasons: {row.reasons.join(", ") || "None reported"}
                            {row.reasonsComplete ? "" : " (incomplete list)"}
                          </small>
                          <small>
                            Evidence match:{" "}
                            {row.matchesCurrentEvidence
                              ? "Current verified evidence"
                              : "Not established against current evidence"}
                          </small>
                        </>
                      ) : row.layer === "recorded" ? (
                        <>
                          <span>
                            {Object.entries(row.facts)
                              .map(([k, v]) => `${k}: ${v}`)
                              .join(" · ") || "Recorded event"}
                          </span>
                          {row.values && (
                            <span>
                              Measurements:{" "}
                              {Object.entries(row.values)
                                .map(
                                  ([k, v]) =>
                                    `${k}: ${v} ${row.units[k] || "unit unknown"}`,
                                )
                                .join(" · ") || "Unavailable"}
                            </span>
                          )}
                          {!!row.unsupportedValueCount && (
                            <small>
                              {row.unsupportedValueCount} unsupported
                              measurement fields omitted.
                            </small>
                          )}
                        </>
                      ) : (
                        <span>
                          {row.configurationParameter && (
                            <>
                              Frozen provider parameter:{" "}
                              {row.configurationParameter} = {row.declaredValue}
                              . No authored position is inferred.{" "}
                            </>
                          )}
                          Declared intent only. Opaque actions and fault
                          activation/recovery remain in frozen source; this view
                          does not execute them.
                        </span>
                      )}
                    </td>
                    <td>
                      <span>{row.evidenceScope}</span>
                      {row.source && (
                        <small>
                          Source provider: {row.source.providerId || "Unknown"}{" "}
                          · {row.source.version || "Version unknown"}
                        </small>
                      )}
                      <span>
                        {row.logicalRef ||
                          row.definitionRef ||
                          row.evidenceRefs.join(", ") ||
                          "No evidence reference"}
                      </span>
                      {row.layer === "evaluation" && (
                        <small>Definition digest: {row.definitionDigest}</small>
                      )}
                      <Json value={row} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!report.items.length && (
            <p>
              No timeline rows were returned for these inputs. Review integrity
              and completeness before interpreting an empty result.
            </p>
          )}
          <div className="form-actions">
            <button
              className="button"
              disabled={index === 0}
              onClick={(e) =>
                void read(e.currentTarget, pages[index - 1], index - 1)
              }
            >
              Previous timeline page
            </button>
            <button
              className="button"
              disabled={!report.nextCursor}
              onClick={(e) =>
                void read(
                  e.currentTarget,
                  {
                    cursor: report.nextCursor,
                    offset: report.reduction.pageStart + report.items.length,
                    identity: report.inputIdentity,
                  },
                  index + 1,
                )
              }
            >
              Next timeline page
            </button>
          </div>
          <ul className="field-hint">
            {report.limitations.map((v: string, i: number) => (
              <li key={i}>{v}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function TimelinePlot({ report }: { report: Data }) {
  const coordinates = timelineCoordinates(report.items);
  if (!coordinates)
    return (
      <p>
        No rows in this page have an admitted position in the selected source
        clock. Unplaced rows remain in the table.
      </p>
    );
  const placed = report.items.filter(
      (r: Data) => r.position.status === "aligned",
    ),
    shown = placed.slice(0, 100);
  return (
    <figure className="timeline-plot">
      <figcaption>
        Selected-page markers · {report.clockDomain} · {report.tickUnit}.
        Independent markers and half-open evaluation ranges; exact ticks are in
        the table.
      </figcaption>
      <svg
        viewBox="0 0 900 175"
        role="img"
        aria-label="Scenario intent, recorded events and evaluation windows; structured alternative in Timeline records table"
      >
        {["intent", "recorded", "evaluation"].map((layer, i) => (
          <g key={layer}>
            <text x="5" y={35 + i * 48}>
              {layer}
            </text>
            <path d={`M 115 ${30 + i * 48} H 880`} className="timeline-axis" />
          </g>
        ))}
        {shown.map((row: Data) => {
          const x = 120 + coordinates.position(row.position.tick) * 7.5,
            y =
              30 + ["intent", "recorded", "evaluation"].indexOf(row.layer) * 48;
          return (
            <g key={row.id} className={`timeline-marker ${row.layer}`}>
              <title>
                {row.kind}: {row.position.tick}
                {row.position.endTick === undefined
                  ? ""
                  : ` to ${row.position.endTick} (end exclusive)`}
              </title>
              {row.position.endTick === undefined ? (
                <circle cx={x} cy={y} r="5" />
              ) : (
                <rect
                  x={x}
                  y={y - 6}
                  width={Math.max(
                    1,
                    (coordinates.position(row.position.endTick) -
                      coordinates.position(row.position.tick)) *
                      7.5,
                  )}
                  height="12"
                />
              )}
            </g>
          );
        })}
        <text x="115" y="166">
          {coordinates.start}
        </text>
        <text x="880" y="166" textAnchor="end">
          {coordinates.end}
        </text>
      </svg>
      <p className="field-hint">
        {shown.length} of {placed.length} placed page rows drawn. Overlapping
        markers retain separate identities in the table. This page is a display
        projection, not canonical coverage.
      </p>
    </figure>
  );
}
