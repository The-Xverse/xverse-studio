import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { Data, Run } from "../../api/types";

type Lease = { leaseToken: string; generation: number };
type Pedals = { throttle: number; brake: number; steer: number };
const stopped: Pedals = { throttle: 0, brake: 1, steer: 0 };

/** Capability-selected normalized input surface; lifecycle remains in the backend. */
export function DriverControls({ run }: { run: Run }) {
  const [enabled, setEnabled] = useState(false);
  const [values, setValues] = useState<Pedals>(stopped);
  const [failure, setFailure] = useState("");
  const [observed, setObserved] = useState<Data>({});
  const [message, setMessage] = useState("");
  const lease = useRef<Lease | null>(null);
  const pedals = useRef<Pedals>(stopped);
  const discrete = useRef<Data | null>(null);
  const sequence = useRef(0);
  const scope = useRef(0);
  const running = run.state === "running";
  const prefix = `/runs/${encodeURIComponent(run.runId)}/input`;

  function change(next: Pedals) {
    pedals.current = next;
    setValues(next);
  }

  function release() {
    const previous = lease.current;
    lease.current = null;
    discrete.current = null;
    change(stopped);
    setEnabled(false);
    setMessage("Driver released; brake and cruise-off requested. Check observed speed.");
    if (previous)
      void api(`${prefix}/release`, { method: "POST", body: previous }).catch(() => {
        // The backend/adapter lease expires independently of this browser.
      });
  }

  async function acquire() {
    const current = scope.current;
    setFailure("");
    try {
      const acquired = await api<Lease>(`${prefix}/acquire`, { method: "POST", body: {} });
      if (scope.current !== current || document.hidden || !document.hasFocus()) {
        await api(`${prefix}/release`, { method: "POST", body: { leaseToken: acquired.leaseToken, generation: acquired.generation } });
        return;
      }
      const owner = { leaseToken: acquired.leaseToken, generation: acquired.generation };
      lease.current = owner;
      sequence.current = 0;
      change(stopped);
      setEnabled(true);
      setMessage("Driver enabled. Input acceptance records publication separately from vehicle effect.");
    } catch (error) {
      setFailure(error instanceof Error ? error.message : "Driver acquisition failed.");
    }
  }

  useEffect(() => {
    scope.current++;
    let ended = false;
    let sending = false;
    let timer = 0;
    const currentScope = scope.current;
    const heartbeat = async () => {
      const owner = lease.current;
      if (owner && running && !sending && !document.hidden) {
        sending = true;
        const request = discrete.current;
        discrete.current = null;
        try {
          const result = await api(`${prefix}/frame`, {
            method: "POST",
            body: { ...owner, frame: { ...pedals.current, ...request, sequence: ++sequence.current } },
          });
          if (!ended && scope.current === currentScope && lease.current === owner)
            setMessage(`Input ${result.publicationSequence} staged; awaiting interface publication and vehicle observations.`);
        } catch (error) {
          if (!ended && lease.current === owner) {
            release();
            setFailure(error instanceof Error ? error.message : "Driver connection lost; lease will expire.");
          }
        } finally {
          sending = false;
        }
      }
      if (!ended) timer = window.setTimeout(heartbeat, 100);
    };
    timer = window.setTimeout(heartbeat, 100);
    const loseFocus = () => release();
    window.addEventListener("blur", loseFocus);
    const visibility = () => { if (document.hidden) release(); };
    document.addEventListener("visibilitychange", visibility);
    return () => {
      ended = true;
      scope.current++;
      window.clearTimeout(timer);
      window.removeEventListener("blur", loseFocus);
      document.removeEventListener("visibilitychange", visibility);
      release();
    };
    // The lease belongs to exactly one selected run and running state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run.runId, running]);

  useEffect(() => {
    let ended = false;
    let timer = 0;
    const poll = async () => {
      try {
        const current = await api<Run>(`/runs/${encodeURIComponent(run.runId)}`);
        if (!ended) setObserved(current.state === "running" ? current.inputTelemetry || {} : {});
      } catch {
        if (!ended) setObserved({});
      }
      if (!ended) timer = window.setTimeout(poll, 300);
    };
    void poll();
    return () => { ended = true; window.clearTimeout(timer); };
  }, [run.runId]);

  const items = observed.items || {};
  const fresh = (key: string) => running && items[key]?.status === "observed";
  const speed = fresh("speed") ? items.speed.value : null;
  const cruise = fresh("cruiseEngaged") ? items.cruiseEngaged.value : null;
  const reverse = fresh("reverseEngaged") ? items.reverseEngaged.value : null;
  const pendingRequest = discrete.current !== null;
  function request(value: Data) {
    if (!enabled || discrete.current) return;
    discrete.current = value;
    setMessage("Discrete request queued once; observe controller status for its effect.");
  }

  return (
    <section className="panel driver-controls" aria-label="Browser driving controls">
      <h3>Browser driving controls</h3>
      {run.inputSurface?.companionUrl === "https://localhost:8443" && <p><a href="https://localhost:8443" target="_blank" rel="noreferrer noopener">{run.inputSurface.companionLabel || "Open companion view"}</a></p>}
      <p>Vehicle speed: <strong data-testid="driver-speed">{speed === null ? "Unknown or stale" : `${Number(speed).toFixed(1)} km/h`}</strong></p>
      <p>Cruise: {cruise === null ? "Unknown or stale" : cruise ? "Engaged" : "Disengaged"}. Reverse: {reverse === null ? "Unknown or stale" : reverse ? "Engaged" : "Disengaged"}.</p>
      <p>Target speed: {fresh("cruiseTargetSpeed") ? `${Number(items.cruiseTargetSpeed.value).toFixed(1)} km/h` : "Unknown or stale"}.</p>
      <div className="run-controls-actions">
        <button className="button" disabled={!running || enabled} onClick={() => void acquire()}>Enable browser driver</button>
        <button className="button" disabled={!enabled} onClick={release}>Release driver and brake</button>
      </div>
      {(["throttle", "brake", "steer"] as const).map((name) => (
        <label key={name} style={{ display: "block", margin: "0.6rem 0" }}>
          {name === "steer" ? "Steering" : name === "throttle" ? "Throttle" : "Brake"}: {values[name].toFixed(2)}
          <input type="range" aria-label={name === "steer" ? "Steering" : name === "throttle" ? "Throttle" : "Brake"}
            min={name === "steer" ? -1 : 0} max={1} step={0.05} value={values[name]} disabled={!enabled}
            onChange={(event) => {
              const value = Number(event.target.value);
              change({ ...pedals.current, [name]: value,
                ...(name === "throttle" && value > 0 ? { brake: 0 } : {}),
                ...(name === "brake" && value > 0 ? { throttle: 0 } : {}) });
            }} />
        </label>
      ))}
      <button className="button" disabled={!enabled} onClick={() => change({ throttle: 0, brake: 0, steer: 0 })}>Coast / release pedals</button>
      <div tabIndex={enabled ? 0 : -1} role="group" aria-label="Keyboard driving pad"
        style={{ padding: "1rem", border: "1px solid currentColor", margin: "0.75rem 0" }}
        onBlur={() => { if (enabled) change(stopped); }}
        onKeyDown={(event) => {
          if (!enabled || !("wasd".includes(event.key.toLowerCase()) || event.key === " ")) return;
          event.preventDefault();
          const key = event.key.toLowerCase();
          change(key === "w" ? { ...pedals.current, throttle: 0.65, brake: 0 } : key === "s" || key === " " ? stopped : { ...pedals.current, steer: key === "a" ? -0.45 : 0.45 });
        }}
        onKeyUp={(event) => {
          if (!enabled) return;
          const key = event.key.toLowerCase();
          if (key === "w") change({ ...pedals.current, throttle: 0 });
          if (key === "s" || key === " ") change({ ...pedals.current, brake: 0 });
          if (key === "a" || key === "d") change({ ...pedals.current, steer: 0 });
        }}>
        Focus here to drive: W throttle, S or Space brake, A/D steering. Losing browser focus releases the driver.
      </div>
      <div className="run-controls-actions">
        <button className="button" disabled={!enabled || pendingRequest || speed === null || cruise === null || (!cruise && (speed < 10 || values.brake > 0))}
          onClick={() => request({ cruise: !cruise })}>{cruise ? "Disengage cruise" : "Engage cruise"}</button>
        <button className="button" disabled={!enabled || pendingRequest || cruise !== true} onClick={() => request({ deltaSpeed: -5 })}>Cruise −5 km/h</button>
        <button className="button" disabled={!enabled || pendingRequest || cruise !== true} onClick={() => request({ deltaSpeed: 5 })}>Cruise +5 km/h</button>
        <button className="button" disabled={!enabled || pendingRequest || speed === null || speed > 5 || reverse === null}
          onClick={() => request({ reverse: !reverse })}>{reverse ? "Request forward" : "Request reverse"}</button>
      </div>
      <p role="status">{message}</p>
      {failure && <p role="alert">{failure}</p>}
      <small>Input lease: 0.75 s. Expiry requests zero throttle, brake and cruise-off. Interface observations use host receipt time; simulation time and vehicle acknowledgement are unavailable.</small>
    </section>
  );
}
