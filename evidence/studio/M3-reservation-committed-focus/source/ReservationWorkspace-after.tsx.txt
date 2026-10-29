import { createContext, useContext, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { api, ApiError, mutationKey } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge, KeyValues } from "../../app/ui";
import { operationReceipt, reservationHistory, reservationOptions, restoredAttempt,
  type Attempt, type Scope } from "./reservation-observations";

const savedKey = "studio.lab.pending-request.v1";
const errorText = (error: unknown) => `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The request failed."}`.slice(0, 1000);
type Mutations = { busy: boolean; working: boolean; principal: string; revision: number;
  submit: (request: Omit<Attempt, "key">) => void };
const Workspace = createContext<Mutations | null>(null);
function useWorkspace() { return useContext(Workspace)!; }

/** Serial mutation identity survives a reload in this tab; it is never an authority grant. */
export function ReservationWorkspace({ children }: { children: ReactNode }) {
  const [attempt, setAttempt] = useState<Attempt | null>(null),
    [loading, setLoading] = useState(true), [blocked, setBlocked] = useState(false), [working, setWorking] = useState(false),
    [error, setError] = useState(""), [receipt, setReceipt] = useState<Data | null>(null),
    [revision, setRevision] = useState(0), [principal, setPrincipal] = useState("");
  const alive = useRef(false), pending = useRef<Attempt | null>(null),
    running = useRef(false), abort = useRef<AbortController | null>(null),
    resultHeading = useRef<HTMLHeadingElement>(null), generation = useRef(0);
  useEffect(() => {
    alive.current = true;
    try {
      pending.current = restoredAttempt(sessionStorage.getItem(savedKey));
      setAttempt(pending.current);
    } catch (e) { setError(errorText(e)); setBlocked(true); }
    setLoading(false);
    return () => { alive.current = false; generation.current++; abort.current?.abort(); };
  }, []);

  async function send(value: Attempt, retry = true) {
    if (running.current || !alive.current || value.principal !== principal) return;
    running.current = true;
    const request = ++generation.current;
    setWorking(true); setError(""); setReceipt(null);
    const controller = new AbortController();
    const origin = document.activeElement;
    abort.current = controller;
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
      const result = operationReceipt(await api(value.path, { ...value, signal: controller.signal }), value);
      if (!alive.current || generation.current !== request || controller.signal.aborted) return;
      // Clear only this exact acknowledged attempt, including after a same-key retry.
      sessionStorage.removeItem(savedKey);
      pending.current = null; setAttempt(null); setReceipt(result); setRevision((v) => v + 1);
    } catch (e) {
      if (!alive.current || generation.current !== request) return;
      let message = errorText(e);
      // A refusal of a retry does not settle the earlier unconfirmed attempt.
      if (!retry && e instanceof ApiError && e.status >= 400 && e.status < 500) {
        try {
          sessionStorage.removeItem(savedKey); pending.current = null; setAttempt(null);
        } catch (storageError) {
          message += ` The saved request could not be cleared: ${errorText(storageError)}`;
        }
      }
      setError(message); setRevision((v) => v + 1);
    } finally {
      clearTimeout(timer); running.current = false;
      if (alive.current) {
        setWorking(false);
        requestAnimationFrame(() => {
          if (!alive.current || generation.current !== request || document.querySelector('[role="dialog"]') ||
            (document.activeElement !== document.body && document.activeElement !== origin)) return;
          resultHeading.current?.focus();
        });
      }
    }
  }
  function submit(request: Omit<Attempt, "key">) {
    if (pending.current || running.current || loading || blocked || !principal || request.principal !== principal) return;
    const value = { ...request, key: mutationKey() };
    try {
      restoredAttempt(JSON.stringify(value));
      sessionStorage.setItem(savedKey, JSON.stringify(value));
    } catch (e) { setError(errorText(e)); return; }
    pending.current = value; setAttempt(value); void send(value, false);
  }
  return <Workspace.Provider value={{ busy: loading || blocked || working || !!attempt, working, principal, revision, submit }}>
    <section className="panel" aria-label="Reservation requests" aria-busy={working}>
      <h2 ref={resultHeading} tabIndex={-1}>Reservation requests</h2>
      <p>Reserve an explicitly granted scope without sending a physical command. Observation is the default;
        stimulation and destructive scopes each require their own grant. Connection observations require
        their own installation and permission; physical commands and automatic run renewal are unavailable.</p>
      {error && <p role="alert">{error}</p>}
      {attempt && <div role="status">
        <p>{attempt.label}: {working ? "Waiting for the backend." : "The response is unconfirmed. Retry this same request to recover its durable operation identity."}
          Leaving this view does not cancel the backend operation.</p>
        <button className="button" disabled={working || !principal || principal !== attempt.principal}
          onClick={() => void send(attempt)}>Retry same reservation request</button>
        {principal && principal !== attempt.principal && <p>This saved request belongs to another principal. Its owner must reconcile the outcome.</p>}
      </div>}
      {receipt && <div role="status"><p>Operation {receipt.operationId}: {receipt.status}.
        {receipt.code ? ` ${receipt.code}.` : ""} The receipt is historical; current ownership is shown below.</p>
        <p>Reservation identity: {receipt.reservationId}</p></div>}
    </section>
    <ReservationHistory onPrincipal={setPrincipal} />
    {children}
  </Workspace.Provider>;
}

/** Reads have an independent generation, timeout and lifetime per mounted context. */
function useObservation() {
  const [value, setValue] = useState<Data | null>(null), [error, setError] = useState(""),
    [pending, setPending] = useState(false),
    [focusRequest, setFocusRequest] = useState<{ request: number; origin?: Element | null; failed: boolean } | null>(null);
  const alive = useRef(false), sequence = useRef(0), abort = useRef<AbortController | null>(null),
    heading = useRef<HTMLHeadingElement>(null), failure = useRef<HTMLParagraphElement>(null);
  useEffect(() => { alive.current = true; return () => { alive.current = false; sequence.current++; abort.current?.abort(); }; }, []);
  useEffect(() => {
    if (!focusRequest || pending) return;
    const { request, origin, failed } = focusRequest;
    const frame = requestAnimationFrame(() => {
      if (!alive.current || sequence.current !== request || !origin || document.querySelector('[role="dialog"]') ||
        (document.activeElement !== document.body && document.activeElement !== origin)) return;
      (failed ? failure.current : heading.current)?.focus();
    });
    return () => cancelAnimationFrame(frame);
  }, [focusRequest, pending]);
  async function read(path: string, validate: (v: Data) => Data, origin?: Element | null) {
    abort.current?.abort();
    const controller = new AbortController(), request = ++sequence.current;
    abort.current = controller;
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 30000);
    setValue(null); setError(""); setPending(true);
    function focus(failed: boolean) {
      setFocusRequest({ request, origin, failed });
    }
    try {
      const result = validate(await api(path, { signal: controller.signal }));
      if (!alive.current || sequence.current !== request || controller.signal.aborted) return;
      setValue(result); focus(false);
    } catch (e) {
      if (!alive.current || sequence.current !== request || (controller.signal.aborted && !timedOut)) return;
      setError(timedOut ? "The reservation read timed out. Refresh to make a new observation." : errorText(e)); focus(true);
    } finally {
      clearTimeout(timer);
      if (alive.current && sequence.current === request) setPending(false);
    }
  }
  return { value, error, pending, read, heading, failure };
}

export function ReservationRequest({ assetId }: { assetId: string }) {
  const observation = useObservation(), workspace = useWorkspace(),
    [scope, setScope] = useState<Scope>("observe"), [duration, setDuration] = useState(30),
    scopeId = useId(), durationId = useId();
  const value = observation.value, selected = value?.scopes.find((row: Data) => row.scope === scope),
    eligible = selected?.eligible && value?.principal === workspace.principal;
  const guidance = `reservation-guidance-${assetId}`;
  return <div className="reservation-request" aria-busy={observation.pending}>
    <h4 ref={observation.heading} tabIndex={-1}>Reservation eligibility</h4>
    <p id={guidance}>Physical activity requires durable ownership and permitted actions.
      Eligibility is an observation, not a lease. The backend rechecks current grants,
      identity, conflicts and limits on each request.</p>
    <button className="button" disabled={observation.pending || workspace.busy}
      onClick={(e) => void observation.read(`/assets/${encodeURIComponent(assetId)}/reservation-options`,
        (v) => reservationOptions(v, assetId), e.currentTarget)}>Check reservation options</button>
    {observation.error && <p ref={observation.failure} tabIndex={-1} role="alert">Reservation eligibility is unknown. {observation.error}</p>}
    {value && <><p>Lease service: {value.status} · Evidence scope: {value.evidenceScope}</p>
      <label htmlFor={scopeId}>Reservation scope</label><select id={scopeId} value={scope} onChange={(e) => setScope(e.target.value as Scope)}>
        {value.scopes.map((row: Data) => <option key={row.scope} value={row.scope}>{row.scope}{row.eligible ? "" : " — unavailable"}</option>)}
      </select>
      <p role="status">{selected?.eligible ? "This scope is eligible to request; acquisition may still be refused." :
        `This scope is unavailable: ${selected?.reasons.join(", ")}.`}</p>
      <label htmlFor={durationId}>Reservation duration (seconds)</label><input id={durationId} type="number" min={1} max={300} step={1}
        value={Number.isNaN(duration) ? "" : duration} onChange={(e) => setDuration(e.target.valueAsNumber)} /></>}
    <button className="button" aria-describedby={guidance}
      disabled={workspace.busy || observation.pending || !eligible || !Number.isInteger(duration) || duration < 1 || duration > 300}
      onClick={() => workspace.submit({ principal: value!.principal,
        path: `/assets/${assetId}/reservations`, method: "POST", kind: "lab_reserve",
        label: `Reserve ${scope}`, body: { scope, durationSeconds: duration } })}>
      {scope === "observe" ? "Reserve observe-only" : `Reserve ${scope} scope`}
    </button>
  </div>;
}

function ReservationHistory({ onPrincipal }: { onPrincipal: (v: string) => void }) {
  const observation = useObservation(), workspace = useWorkspace(),
    [cursor, setCursor] = useState(""), [previous, setPrevious] = useState<string[]>([]);
  function read(next = "", prior: string[] = [], origin?: Element | null) {
    setCursor(next); setPrevious(prior); onPrincipal("");
    return observation.read(`/reservations?limit=50${next ? `&cursor=${next}` : ""}`, (v) => reservationHistory(v, next), origin);
  }
  useEffect(() => { void read(); }, [workspace.revision]);
  useEffect(() => { if (observation.value) onPrincipal(observation.value.principal); }, [observation.value]);
  const value = observation.value;
  return <section className="panel" aria-label="Reservation history" aria-busy={observation.pending}>
    <div className="section-heading"><h2 ref={observation.heading} tabIndex={-1}>Your reservations</h2>
      <button className="button" disabled={observation.pending || workspace.working}
        onClick={(e) => void read("", [], e.currentTarget)}>Refresh reservations</button></div>
    <p>Local ownership history for the signed-in principal. Reading this history contacts no provider.
      Explicit reconciliation inspects the original provider and fence; it never reacquires.
      Each page is a separate observation; records may change between requests.</p>
    {observation.pending && <p role="status">Reading reservation history…</p>}
    {observation.error && <p ref={observation.failure} tabIndex={-1} role="alert">Reservation history is unavailable. {observation.error}</p>}
    {value && <><p>Principal: {value.principal} · Server observation time: {value.observedAt}</p>
      {!value.items.length && <p>No reservations returned on this page.</p>}
      {value.items.map((record: Data) => <ReservationRecord key={`${record.reservationId}:${value.observedAt}:${workspace.revision}`}
        record={record} observedAt={value.observedAt} />)}
      <div className="form-actions"><button className="button" disabled={workspace.busy || !previous.length}
        onClick={(e) => void read(previous.at(-1)!, previous.slice(0, -1), e.currentTarget)}>Previous reservation page</button>
        <span>Page {previous.length + 1} · {value.items.length} reservations</span>
        <button className="button" disabled={workspace.busy || !value.nextCursor || previous.length >= 19}
          onClick={(e) => void read(value.nextCursor, [...previous, cursor], e.currentTarget)}>Next reservation page</button></div>
      {value.nextCursor && previous.length >= 19 && <p>The bounded history page limit was reached. Refresh to start again.</p>}
    </>}
  </section>;
}

function ReservationRecord({ record, observedAt }: { record: Data; observedAt: number }) {
  const workspace = useWorkspace(), [duration, setDuration] = useState(60), [elapsed, setElapsed] = useState(0), durationId = useId();
  useEffect(() => {
    if (["released", "expired"].includes(record.status)) return;
    const start = performance.now(), timer = setInterval(() => setElapsed((performance.now() - start) / 1000), 1000);
    return () => clearInterval(timer);
  }, []);
  const deadlinePassed = observedAt + elapsed >= record.expiry,
    terminal = ["released", "expired"].includes(record.status),
    base = { principal: record.owner, reservationId: record.reservationId };
  return <article className="panel reservation-record" aria-label={`Reservation ${record.reservationId}`}>
    <div className="section-heading"><h3>{record.assetId}</h3><Badge>{record.evidenceScope}</Badge></div>
    <KeyValues values={{ "Reservation identity": record.reservationId, Owner: record.owner, Scope: record.scope,
      "Observed ownership": record.status, "Expiry (server time)": record.expiry, "Last renewal": record.lastRenewal ?? "Not recorded",
      "Fencing identity": record.fencingIdentity ?? "Unknown", Reason: record.reason ?? "None recorded" }} />
    {deadlinePassed && !terminal && <p role="status">The observed deadline has passed. Refresh ownership before requesting renewal.</p>}
    {record.status === "unknown" && <p>Ownership is unknown. New active authority is disabled. Reconciliation cannot recover a lost original fencing identity.</p>}
    <p>Physical state remains unknown. A reservation or release does not certify device safety.</p>
    <label htmlFor={durationId}>Renewal duration (seconds)</label><input id={durationId} type="number" min={1} max={300} step={1} value={Number.isNaN(duration) ? "" : duration}
      disabled={terminal} onChange={(e) => setDuration(e.target.valueAsNumber)} />
    <div className="form-actions">
      <button className="button" disabled={workspace.busy || !record.requests.renew || deadlinePassed || !Number.isInteger(duration) || duration < 1 || duration > 300}
        onClick={() => workspace.submit({ ...base, path: `/reservations/${record.reservationId}/renewals`, method: "POST",
          kind: "lab_renew", label: "Renew same scope", body: { fencingIdentity: record.fencingIdentity, durationSeconds: duration } })}>Renew same scope</button>
      <button className="button" disabled={workspace.busy || !record.requests.reconcile}
        onClick={() => workspace.submit({ ...base, path: `/reservations/${record.reservationId}/reconciliations`, method: "POST",
          kind: "lab_reconcile", label: "Reconcile original ownership", body: {} })}>Reconcile original ownership</button>
      <button className="button" disabled={workspace.busy || !record.requests.release}
        onClick={() => workspace.submit({ ...base, path: `/reservations/${record.reservationId}`, method: "DELETE",
          kind: "lab_release", label: "Release reservation" })}>Release reservation</button>
    </div>
    {!terminal && !record.requests.renew && <p>Renewal is unavailable: ownership, installed provider binding or current scope grant is not confirmed.</p>}
    {!terminal && !record.requests.reconcile && <p>Reconciliation requires the original installed provider binding.</p>}
  </article>;
}
