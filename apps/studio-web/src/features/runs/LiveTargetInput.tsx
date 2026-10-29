import { useEffect, useState } from "react";
import type { Run } from "../../api/types";
import type { PendingCommand } from "./control";

export function LiveTargetInput({
  run,
  pending,
  disabled,
  reason,
  apply,
}: {
  run: Run;
  pending: PendingCommand | null;
  disabled: boolean;
  reason: string;
  apply: (parameters: Record<string, unknown>, version: number) => void;
}) {
  const observed = run.liveValues?.target,
    valid = typeof observed === "number" && Number.isFinite(observed),
    [draft, setDraft] = useState(() => ({
      runId: run.runId,
      text: valid ? String(observed) : "",
      basis: observed,
      version: run.stateVersion,
      edited: false,
    }));
  useEffect(() => {
    setDraft((previous) => {
      const ownApplied =
        pending?.kind === "set_parameter" &&
        pending.status === "completed" &&
        pending.parameters?.value === observed &&
        Number(previous.text) === observed;
      if (previous.runId === run.runId && previous.edited && !ownApplied)
        return previous;
      return {
        runId: run.runId,
        text: valid ? String(observed) : "",
        basis: observed,
        version: run.stateVersion,
        edited: false,
      };
    });
  }, [
    run.runId,
    run.stateVersion,
    observed,
    valid,
    pending?.key,
    pending?.status,
    pending?.parameters?.value,
  ]);
  const stale =
      draft.runId !== run.runId ||
      draft.version !== run.stateVersion ||
      draft.basis !== observed,
    value = Number(draft.text),
    allowed =
      valid &&
      draft.text.trim() !== "" &&
      Number.isFinite(value) &&
      Math.abs(value) <= 100 &&
      value !== observed,
    awaitingObservation =
      pending?.kind === "set_parameter" &&
      pending.status === "completed" &&
      run.stateVersion <= pending.expectedStateVersion,
    exhausted = run.liveMutationCount >= run.controlLimits?.maxLiveMutations;
  return (
    <section className="run-control" aria-label="Live model input">
      <h3>Live model target</h3>
      <p>
        Observed target: <strong>{valid ? observed : "unavailable"}</strong>{" "}
        (dimensionless).
      </p>
      <p>
        Changes applied: {run.liveMutationCount ?? "unknown"} /{" "}
        {run.controlLimits?.maxLiveMutations ?? "unknown"}.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (disabled || stale || !allowed || awaitingObservation || exhausted)
            return;
          apply(
            { inputId: "target", expectedValue: draft.basis, value },
            draft.version,
          );
        }}
      >
        <label>
          Proposed live target
          <input
            type="number"
            min={-100}
            max={100}
            step="any"
            required
            value={draft.text}
            disabled={disabled || awaitingObservation || exhausted}
            onChange={(event) =>
              setDraft((previous) => ({
                ...previous,
                text: event.target.value,
                edited: true,
              }))
            }
          />
        </label>
        <button
          className="button"
          disabled={
            disabled || stale || !allowed || awaitingObservation || exhausted
          }
        >
          Apply live target
        </button>
        {stale && (
          <p role="status">
            The observed state changed. Review the current target before
            applying this proposal.
            <button
              type="button"
              className="button"
              disabled={disabled || !valid}
              onClick={() =>
                setDraft((previous) => ({
                  ...previous,
                  basis: observed,
                  version: run.stateVersion,
                }))
              }
            >
              Review latest target
            </button>
          </p>
        )}
      </form>
      <small>
        {disabled
          ? reason
          : exhausted
            ? "This run's live-change budget is exhausted."
            : "Choose a finite target from −100 to 100. Only the declared model input changes. Frozen configuration and later draft edits remain separate."}
      </small>
    </section>
  );
}
