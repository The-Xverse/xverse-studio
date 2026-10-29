import type { Data } from "../../api/types";

/** Reported startup facts never establish current ownership or functional success. */
export function RunStartupStatus({ run }: { run: Data }) {
  const state = String(run.state || run.status || "unknown");
  const reason = typeof run.reason === "string" ? run.reason.slice(0, 128) : "";
  const startRecorded =
    typeof run.startedAt === "number" && Number.isFinite(run.startedAt);
  let summary = "Startup history unavailable";
  let detail =
    "No workload start time is reported. Inspect the immutable inputs and retained diagnosis.";
  if (["unknown", "reconciling"].includes(state)) {
    summary = "Startup or ownership unresolved";
    detail = startRecorded
      ? "An earlier workload start is recorded. Current ownership and cleanup require reconciliation."
      : "A workload start has not been established. Current ownership and cleanup require reconciliation.";
  } else if (startRecorded) {
    summary =
      state === "failed"
        ? "Start recorded; execution failed"
        : "Workload start recorded";
    detail =
      "The recorded start is separate from the execution outcome, cleanup, evidence integrity and assertion verdict.";
  } else if (
    state === "failed" &&
    [
      "PREPARATION_FAILED",
      "EVIDENCE_OPEN_FAILED",
      "LAUNCH_FAILED",
      "EFFECTIVE_INPUT_MISMATCH",
    ].includes(reason)
  ) {
    summary = "Startup rejected";
    detail =
      reason === "PREPARATION_FAILED"
        ? "The backend could not prepare the local run files and did not attempt a workload launch. Retain this run, check local storage access and capacity, then recheck preflight before a fresh request."
        : reason === "EVIDENCE_OPEN_FAILED"
          ? "The provider could not create its canonical evidence journal and did not start the workload. Retain the run, check local storage access and capacity, then recheck preflight before a fresh request."
          : reason === "EFFECTIVE_INPUT_MISMATCH"
            ? "The provider rejected effective inputs before the workload started. Inspect the frozen inputs and diagnosis before making a fresh request."
            : "The backend reported a launch failure before a workload start was recorded. Cleanup and evidence remain separate reported outcomes.";
  } else if (
    ["requested", "accepted", "preparing", "ready", "starting"].includes(state)
  ) {
    summary = "Startup pending";
    detail =
      "The backend is preparing the owned workload. Acceptance does not establish that execution has started.";
  }
  return (
    <section className="panel" aria-label="Reported startup">
      <h3>Reported startup</h3>
      <p role="status">{summary}</p>
      <p>{detail}</p>
      {reason && (
        <p>
          Reported reason: <code>{reason}</code>
        </p>
      )}
    </section>
  );
}
