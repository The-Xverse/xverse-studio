import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { Json, Badge } from "../../app/ui";

export type PlatformView = "orchestration" | "communications" | "evidence";
type Row = {
  eventId: string;
  ingestionOrdinal: number;
  eventKind: string;
  producerId: string;
  correlationId?: string;
  causationId?: string;
  logicalId?: string;
  clocks?: Record<string, { domain: string; unit: string; value: number | string }>;
  sourceRef: { sourceId: string; runId: string; eventId: string; ingestionOrdinal: number };
  maestro?: { kind: string; phaseId?: string; logicalId?: string; operationId?: string; operation?: string; outcome?: string; readinessKind?: string; observation?: { cleanup?: string } };
  communication?: { routeId: string; endpointId: string; schemaId: string; sequence?: string | number; counters?: Record<string, number | string>; payload: { policy: string; value: string | boolean | null; decoding?: string } };
  input?: { routeId: string; endpointId: string; upstreamCausationId?: string | null };
  tapSnapshot?: { declaredTapId: string; coalesced: number | string; dropped: number | string; queued: number | string; validityState: string };
};
type Projection = {
  snapshotId: string;
  sourceId: string;
  sourceWitness: string;
  capturedAt: number;
  expiresInSeconds: number;
  identity: Record<string, string>;
  identityVerified: { runAndPlan: boolean; maestroInputs: boolean; installation: string };
  evidence: { recorded: string; assessed: string; recordedReasons: string[]; assessedReasons: string[] };
  diagnostics: { code: string; category: string; severity: string }[];
  policy: Record<string, string>;
  counts: Record<string, number>;
  matchedCount: number;
  offset: number;
  nextCursor: string | null;
  items: Row[];
};
type Selection = { eventId?: string; correlationId?: string; logicalId?: string };
const titles = { orchestration: "Orchestration", communications: "Communications", evidence: "Evidence" };

export function PlatformViews({ runId, active, view, onView, onLogical }: {
  runId: string;
  active: boolean;
  view: PlatformView;
  onView: (view: PlatformView) => void;
  onLogical: (id: string) => void;
}) {
  const [selection, setSelection] = useState<Selection>({});
  const [paging, setPaging] = useState<{ view: PlatformView; trail: string[] }>({ view, trail: [""] });
  const trail = paging.view === view ? paging.trail : [""];
  function setTrail(value: string[] | ((values: string[]) => string[])) {
    setPaging(previous => ({ view, trail: typeof value === "function" ? value(previous.view === view ? previous.trail : [""]) : value }));
  }
  const [epoch, setEpoch] = useState(0);
  const [data, setData] = useState<{ context: string; value: Projection } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const snapshot = useRef<string | null>(null);
  const request = useRef(0);
  const context = JSON.stringify([runId, view, selection, trail.at(-1), epoch]);
  const current = useRef(context);
  current.current = context;
  const shown = data?.context === context ? data.value : null;
  const heading = useRef<HTMLHeadingElement>(null);
  const focusAfterRead = useRef(false);

  useEffect(() => {
    if (!active) return;
    const controller = new AbortController(), generation = ++request.current;
    const params = new URLSearchParams({ view, limit: "50" });
    if (snapshot.current) params.set("snapshot", snapshot.current);
    const cursor = trail.at(-1);
    if (cursor) params.set("cursor", cursor);
    Object.entries(selection).forEach(([key, value]) => { if (value) params.set(key, value); });
    setLoading(true);
    setError("");
    void api<Projection>(`/runs/${encodeURIComponent(runId)}/platform?${params}`, { signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted || generation !== request.current || current.current !== context) return;
        if (result.identity.runId !== runId || (snapshot.current && result.snapshotId !== snapshot.current))
          throw new Error("Platform evidence belongs to another run or snapshot. Refresh the views.");
        snapshot.current = result.snapshotId;
        setData({ context, value: result });
        if (focusAfterRead.current) { heading.current?.focus(); focusAfterRead.current = false; }
      })
      .catch((reason: Error) => {
        if (!controller.signal.aborted && generation === request.current && current.current === context) setError(reason.message);
      })
      .finally(() => {
        if (!controller.signal.aborted && generation === request.current && current.current === context) setLoading(false);
      });
    return () => controller.abort();
  }, [runId, active, view, context, epoch, selection]);

  function navigate(target: PlatformView, filter: Selection = {}) {
    setSelection(filter);
    setTrail([""]);
    setExpanded(null);
    focusAfterRead.current = true;
    onView(target);
  }
  function refresh() {
    snapshot.current = null;
    setData(null);
    setTrail([""]);
    setExpanded(null);
    setEpoch((value) => value + 1);
  }

  return <section className="panel platform-views" hidden={!active} aria-label="Linked platform views" aria-busy={loading}>
    <div className="section-heading">
      <h3 ref={heading} tabIndex={-1}>{titles[view]} · X-Verse platform</h3>
      <button className="button" onClick={refresh} disabled={loading}>Refresh all platform views</button>
    </div>
    <p>One immutable Argus capture links Maestro lifecycle facts and native X-COM observations. Refresh captures newer evidence for all three views.</p>
    {error && <p role="alert">{error}</p>}
    {loading && <p role="status">Reading platform evidence…</p>}
    {shown && <>
      <div className="results-scope">
        <Badge>Recorded: {shown.evidence.recorded}</Badge>
        <Badge>Assessed: {shown.evidence.assessed}</Badge>
        <span>{shown.counts.orchestration} lifecycle · {shown.counts.communications} communication · {shown.counts.retained} original records</span>
      </div>
      <p className="field-hint">Capture: {new Date(shown.capturedAt * 1000).toLocaleString()} · {shown.expiresInSeconds}s remaining when read. Historical observations do not establish current readiness or functional health.</p>
      <details><summary>Shared run, plan and evidence identities</summary>
        <Json value={{ ...shown.identity, verified: shown.identityVerified, sourceId: shown.sourceId, sourceWitness: shown.sourceWitness, snapshotId: shown.snapshotId, policy: shown.policy }} expanded />
      </details>
      {(shown.evidence.assessed !== "complete" || shown.diagnostics.length > 0) && <div className="notice">
        <p>Evidence coverage: {shown.evidence.assessed}. Coalesced observation samples, dropped observations and transport loss are distinct. No complete message trace or vehicle effect is inferred.</p>
        <ul>{Array.from(new Set([...shown.evidence.recordedReasons, ...shown.evidence.assessedReasons, ...shown.diagnostics.map(d => d.code)])).map(code => <li key={code}>{code}</li>)}</ul>
      </div>}
      <p className="field-hint">Original clock domains and units are retained. Ingestion order does not establish causation; no cross-clock latency or synchronization is inferred. Payloads use host-allowlisted scalar codecs; private logs are withheld.</p>
      {Object.keys(selection).length > 0 && <div className="results-scope"><span>Selected links: {JSON.stringify(selection)}</span><button className="button" onClick={() => navigate(view)}>Clear platform selection</button></div>}
      <div className="table-scroll"><table className="data-table">
        <caption>{titles[view]} records from the shared evidence snapshot</caption>
        <thead><tr><th scope="col">Original record</th><th scope="col">{view === "orchestration" ? "Maestro phase and outcome" : view === "communications" ? "Native communication" : "Source and kind"}</th><th scope="col">Original clocks</th><th scope="col">Linked views</th></tr></thead>
        <tbody>{shown.items.map(row => <tr key={`${row.ingestionOrdinal}:${row.eventId}`}>
          <td><button className="button" aria-expanded={expanded === row.eventId} onClick={() => setExpanded(expanded === row.eventId ? null : row.eventId)}>#{row.ingestionOrdinal} · {row.eventId}</button>
            {row.logicalId && <div><button className="button" onClick={() => onLogical(row.logicalId!)}>Select element {row.logicalId.split("#").at(-1)}</button></div>}
            {expanded === row.eventId && <Json value={row} expanded />}
          </td>
          <td>{row.maestro ? <><strong>{row.maestro.kind}</strong><div>{row.maestro.phaseId || "Run operation"} · {row.maestro.operation} · {row.maestro.outcome || "requested"}</div>{row.maestro.readinessKind && <div>Readiness: {row.maestro.readinessKind}</div>}{row.maestro.observation?.cleanup && <div>Cleanup: {row.maestro.observation.cleanup}</div>}</>
            : row.communication ? <><strong>{row.communication.routeId.split("#").at(-1)}</strong><div>Scalar: {row.communication.payload.value === null ? "unavailable" : String(row.communication.payload.value)}</div><div>Sequence: {row.communication.sequence ?? "not supplied"}</div><div>Retention counters: {JSON.stringify(row.communication.counters)}</div></>
            : row.tapSnapshot ? <><strong>Tap snapshot: {row.tapSnapshot.declaredTapId}</strong><div>Coalesced: {row.tapSnapshot.coalesced} · dropped: {row.tapSnapshot.dropped} · queued: {row.tapSnapshot.queued}</div><div>Validity: {row.tapSnapshot.validityState}</div></>
            : row.input ? <><strong>Native ingress fact</strong><div>{row.input.routeId.split("#").at(-1)}</div><div>Upstream cause: {row.input.upstreamCausationId ?? "unknown"}</div></>
            : <>{row.producerId} · {row.eventKind}</>}
          </td>
          <td>{Object.entries(row.clocks || {}).map(([kind, clock]) => <div key={kind}><strong>{kind}</strong>: {String(clock.value)} {clock.unit}<div className="field-hint">{clock.domain}</div></div>)}</td>
          <td><div className="button-row">
            <button className="button" onClick={() => navigate("evidence", { eventId: row.eventId })}>Evidence record</button>
            {row.causationId && <button className="button" onClick={() => navigate("evidence", { eventId: row.causationId })}>Original cause</button>}
            {row.correlationId && <>
              <button className="button" onClick={() => navigate("orchestration", { correlationId: row.correlationId })}>Correlated orchestration</button>
              <button className="button" onClick={() => navigate("communications", { correlationId: row.correlationId })}>Correlated communications</button>
            </>}
          </div></td>
        </tr>)}</tbody>
      </table></div>
      {shown.items.length === 0 && <p>No records match this view and selection in the pinned snapshot. A missing cause or correlation is not invented.</p>}
      <div className="button-row"><button className="button" disabled={trail.length <= 1 || loading} onClick={() => setTrail(values => values.slice(0, -1))}>Previous platform page</button>
        <span>{shown.matchedCount ? shown.offset + 1 : 0}–{shown.offset + shown.items.length} of {shown.matchedCount} matching records</span>
        <button className="button" disabled={!shown.nextCursor || loading} onClick={() => { if (shown.nextCursor) setTrail(values => [...values, shown.nextCursor!]); }}>Next platform page</button>
      </div>
    </>}
  </section>;
}
