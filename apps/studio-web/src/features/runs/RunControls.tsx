import { useCallback, useEffect, useRef, useState } from "react";
import { api, mutationKey } from "../../api/client";
import type { Run } from "../../api/types";
import { Badge, Icon, statusTone } from "../../app/ui";
import {
  clearPendingCommand,
  commandRequest,
  controlAvailability,
  isDefinitiveRejection,
  isPendingCommandStorageKey,
  operationMeaning,
  readPendingCommand,
  settledOperation,
  writePendingCommand,
  type PendingCommand,
} from "./control";

const CONTROLS = [
  {
    kind: "stop",
    label: "Stop",
    purpose: "Request the declared orderly shutdown.",
  },
  {
    kind: "cancel",
    label: "Cancel",
    purpose: "Request the admitted cancellation policy.",
  },
  {
    kind: "pause",
    label: "Pause",
    purpose:
      "Pause the owned simulation clock within its declared wall-time budget.",
  },
  {
    kind: "resume",
    label: "Resume",
    purpose: "Resume the owned simulation from its current simulation time.",
  },
];
const OPTIONAL = ["step", "reset", "set_parameter"];

export function RunControls({
  run,
  onRunUpdated,
}: {
  run: Run;
  onRunUpdated: (run: Run) => void;
}) {
  const [pending, setPending] = useState<PendingCommand | null>(() =>
      readPendingCommand(run.runId),
    ),
    [sending, setSending] = useState(false),
    [failure, setFailure] = useState(""),
    [reconciling, setReconciling] = useState(false);
  // In-flight responses may settle after another run is selected; they update only
  // their own run's durable receipt, never the displayed run's state.
  const shownRun = useRef(run.runId),
    runUpdated = useRef(onRunUpdated);
  shownRun.current = run.runId;
  runUpdated.current = onRunUpdated;
  const store = useCallback((value: PendingCommand) => {
    writePendingCommand(value);
    if (value.runId === shownRun.current) setPending(value);
  }, []);
  const forget = useCallback((runId: string) => {
    clearPendingCommand(runId);
    if (runId === shownRun.current) setPending(null);
  }, []);
  useEffect(() => {
    setPending(readPendingCommand(run.runId));
    setFailure("");
    // Another tab shares the same durable receipt and its request identity.
    const synchronize = (event: StorageEvent) => {
      if (isPendingCommandStorageKey(event.key, run.runId))
        setPending(readPendingCommand(run.runId));
    };
    window.addEventListener("storage", synchronize);
    return () => window.removeEventListener("storage", synchronize);
  }, [run.runId]);
  const refresh = useCallback(
    async (operationId: string | undefined) => {
      if (operationId) {
        const operation = await api(
          `/operations/${encodeURIComponent(operationId)}`,
        );
        const current = readPendingCommand(run.runId);
        if (current?.operationId === operationId)
          store({ ...current, status: operation.status, code: operation.code });
      }
      runUpdated.current(
        await api<Run>(`/runs/${encodeURIComponent(run.runId)}`),
      );
    },
    [run.runId, store],
  );
  const operationId = pending?.operationId,
    awaiting =
      Boolean(operationId) &&
      ["accepted", "delegated"].includes(String(pending?.status));
  useEffect(() => {
    if (!awaiting) return;
    let stopped = false,
      timer = 0;
    const poll = async () => {
      try {
        await refresh(operationId);
      } catch {
        /* A failed read leaves the operation state unchanged; poll again. */
      }
      if (!stopped) timer = window.setTimeout(poll, 500);
    };
    timer = window.setTimeout(poll, 300);
    return () => {
      stopped = true;
      window.clearTimeout(timer);
    };
  }, [awaiting, operationId, refresh]);
  async function deliver(request: PendingCommand) {
    const shown = () => request.runId === shownRun.current;
    setSending(true);
    setFailure("");
    try {
      const accepted = await commandRequest(request);
      store({
        ...request,
        operationId: accepted.operationId,
        status: accepted.status || "accepted",
      });
    } catch (error) {
      if (isDefinitiveRejection(error)) {
        forget(request.runId);
        const current = await api<Run>(
          `/runs/${encodeURIComponent(request.runId)}`,
        ).catch(() => null);
        if (current) runUpdated.current(current);
      }
      if (shown())
        setFailure(
          error instanceof Error
            ? error.message
            : "The request was not acknowledged.",
        );
    } finally {
      setSending(false);
    }
  }
  function send(kind: string) {
    const request: PendingCommand = {
      key: mutationKey(),
      runId: run.runId,
      kind,
      expectedStateVersion: run.stateVersion,
      sentAt: Date.now(),
    };
    // Persist the request identity before sending so a lost response is retryable.
    store(request);
    void deliver(request);
  }
  async function reconcile() {
    setReconciling(true);
    try {
      await refresh(pending?.operationId);
    } catch (error) {
      setFailure(
        error instanceof Error ? error.message : "Reconciliation failed.",
      );
    } finally {
      setReconciling(false);
    }
  }
  const phase = pending
    ? pending.operationId
      ? String(pending.status || "accepted")
      : sending
        ? "sending"
        : "unacknowledged"
    : "";
  const state = String(run.state || run.status || "unknown"),
    cleanup =
      typeof run.cleanup === "object"
        ? run.cleanup?.status || run.cleanup?.state
        : run.cleanup,
    capabilities: string[] = Array.isArray(run.capabilities)
      ? run.capabilities
      : [],
    admitted = CONTROLS.filter(({ kind }) => capabilities.includes(kind)),
    notAdmitted = [...CONTROLS.map(({ kind }) => kind), ...OPTIONAL].filter(
      (kind) => !capabilities.includes(kind),
    ),
    unresolved =
      state === "unknown" ||
      ["unknown", "failed", "partial"].includes(String(cleanup));
  return (
    <section className="panel run-controls" aria-label="Run controls">
      <div className="run-controls-actions">
        {admitted.map(({ kind, label, purpose }) => {
          const availability = controlAvailability(run, kind, pending),
            reasonId = `control-reason-${kind}`;
          return (
            <div className="run-control" key={kind}>
              <button
                className={
                  kind === "cancel" ? "button danger-button" : "button"
                }
                disabled={!availability.available || sending}
                aria-describedby={reasonId}
                onClick={() => send(kind)}
              >
                {kind === "stop" && <Icon name="stop" />}
                {label}
              </button>
              <small id={reasonId}>
                {availability.available ? purpose : availability.reason}
              </small>
            </div>
          );
        })}
        {notAdmitted.length > 0 && (
          <p className="run-controls-scope">
            Not admitted for this run: {notAdmitted.join(", ")}. The backend
            rejects them; absence of a button is not support.
          </p>
        )}
      </div>
      {capabilities.includes("pause") && (
        <p className="hint">
          Simulation pause preserves the current model step; it does not pause
          physical equipment.
          {typeof run.controlLimits?.maxPausedWallSeconds === "number" && (
            <>
              {" "}
              Total pause budget: {run.controlLimits.maxPausedWallSeconds} wall
              seconds. Exhaustion stops the model with incomplete simulation
              coverage.
            </>
          )}
        </p>
      )}
      {pending && (
        <div className="control-operation" data-control-operation={phase}>
          <div className="section-heading">
            <h3>
              {CONTROLS.find((control) => control.kind === pending.kind)
                ?.label || pending.kind}{" "}
              request{" "}
              <Badge
                tone={
                  phase === "unacknowledged" ? "warning" : statusTone(phase)
                }
              >
                {phase}
              </Badge>
            </h3>
            {pending.operationId && <code>{pending.operationId}</code>}
          </div>
          <p>{operationMeaning[phase] || operationMeaning.unknown}</p>
          {pending.code && (
            <p>
              Reported reason: <code>{pending.code}</code>
            </p>
          )}
          <div className="button-row">
            {phase === "unacknowledged" && (
              <button
                className="button primary"
                disabled={sending}
                onClick={() => void deliver(pending)}
              >
                Retry same request
              </button>
            )}
            {phase === "unknown" && (
              <button
                className="button"
                disabled={reconciling}
                onClick={() => void reconcile()}
              >
                <Icon name="refresh" />
                Reconcile
              </button>
            )}
            {(settledOperation(phase) || phase === "unacknowledged") && (
              <button
                className="button"
                onClick={() => {
                  forget(run.runId);
                  setFailure("");
                }}
              >
                Dismiss
              </button>
            )}
          </div>
          {phase === "unacknowledged" && (
            <p className="hint">
              Dismissing forgets this browser receipt only; it does not withdraw
              a request the backend may already hold.
            </p>
          )}
        </div>
      )}
      {failure && (
        <p className="control-failure" role="alert">
          {failure}
        </p>
      )}
      {unresolved && (
        <div className="ownership-unresolved" role="status">
          <h3>Unresolved owned resources</h3>
          <p>
            {state === "unknown"
              ? `Ownership is unconfirmed (${run.reason || "reason not reported"}). The backend could not prove that the recorded process is still the owned workload, so its effects and cleanup are unknown.`
              : `Cleanup is ${cleanup}. Owned resources may remain allocated.`}
          </p>
          <dl className="ownership-facts">
            <dt>Reported reason</dt>
            <dd>{String(run.reason || "not reported")}</dd>
            <dt>Ownership record</dt>
            <dd>
              Held by the backend; process identity is withheld from the
              browser.
            </dd>
            <dt>Cleanup</dt>
            <dd>{String(cleanup || "unknown")}</dd>
            <dt>Evidence</dt>
            <dd>{String(run.evidence || run.evidenceStatus || "unknown")}</dd>
          </dl>
          <p>
            Studio never cleans up by process name, PID alone, port or address:
            PID reuse is not ownership. Reconcile to re-read the verified
            ownership record, inspect the retained events and logs, and follow
            the recovery guide's native shutdown procedure before starting a
            replacement run.
          </p>
          <button
            className="button"
            disabled={reconciling}
            onClick={() => void reconcile()}
          >
            <Icon name="refresh" />
            Reconcile ownership
          </button>
        </div>
      )}
    </section>
  );
}
