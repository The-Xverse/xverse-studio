import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge, Icon } from "../../app/ui";

// Renders backend explanation 1.0 without adding inference: every fact shows its
// evidence, consequences cite their facts, hypotheses stay unconfirmed.

const CLASS_LABELS: Record<string, string> = {
  invalid_model: "Invalid model",
  unsupported_capability: "Unsupported capability",
  missing_artifact: "Missing artifact",
  stale_plan: "Stale plan",
  incompatible_time_mapping: "Incompatible time mapping",
  resource_limit: "Resource limit",
  authority_unavailable: "Authority unavailable",
  readiness_unknown: "Unestablished readiness",
  process_exit: "Process exit",
  lost_connection: "Lost connection",
  failed_cleanup: "Cleanup",
  unavailable_evidence: "Evidence",
  telemetry_gap: "Telemetry gap",
  observation_conflict: "Stale or conflicting observation",
  command_failure: "Command outcome",
  no_traffic: "No traffic observed",
  liveness_only: "Liveness only",
};

function evidenceLabel(ref: Data) {
  switch (ref.kind) {
    case "event":
      return `Event #${ref.sequence} · ${ref.type}`;
    case "run":
      return `Run ${ref.field} = ${JSON.stringify(ref.value ?? null)}`;
    case "preflight":
      return ref.dimension
        ? `Preflight ${ref.dimension}: ${ref.status}`
        : `Preflight ${ref.field} = ${JSON.stringify(ref.value ?? null)}`;
    case "operation":
      return `Operation ${ref.operationId}: ${ref.status}${ref.code ? ` (${ref.code})` : ""}`;
    case "source_diagnostic":
      return `Source ${ref.code}${ref.documentId ? ` · ${ref.documentId}` : ""}${ref.location ? ` · ${typeof ref.location === "string" ? ref.location : JSON.stringify(ref.location)}` : ""}`;
    case "projection":
      return `Projection ${ref.name}${ref.observerRef ? ` (${ref.observerRef})` : ""} = ${JSON.stringify(ref.value ?? null)}`;
    default:
      return JSON.stringify(ref);
  }
}

export function DiagnosticExplanations({
  url,
  refreshKey,
  title,
  actions = {},
  emptyText,
}: {
  url: string;
  refreshKey: string;
  title: string;
  actions?: Record<string, () => unknown>;
  emptyText: string;
}) {
  const [loaded, setLoaded] = useState<{ url: string; value: Data } | null>(
      null,
    ),
    [failure, setFailure] = useState(""),
    [nonce, setNonce] = useState(0),
    shownUrl = useRef("");
  // Never show another subject's explanation while this one loads.
  const explanation = loaded?.url === url ? loaded.value : null;
  useEffect(() => {
    const controller = new AbortController(),
      changedSubject = shownUrl.current !== url;
    shownUrl.current = url;
    if (changedSubject) setFailure("");
    // Re-reads of the same subject are coalesced while evidence is arriving.
    const timer = window.setTimeout(
      () => {
        api(url, { signal: controller.signal })
          .then((value) => {
            if (controller.signal.aborted) return;
            setLoaded({ url, value });
            setFailure("");
          })
          .catch((error) => {
            if (!controller.signal.aborted)
              setFailure(
                error instanceof Error
                  ? error.message
                  : "The explanation is unavailable.",
              );
          });
      },
      changedSubject ? 0 : 1000,
    );
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [url, refreshKey, nonce]);
  const available: Record<string, () => unknown> = {
    refresh_evidence: () => setNonce((value) => value + 1),
    ...actions,
  };
  async function perform(name: string) {
    try {
      await available[name]();
    } catch (error) {
      setFailure(
        error instanceof Error ? error.message : "The action did not complete.",
      );
    }
  }
  const findings: Data[] = Array.isArray(explanation?.findings)
    ? explanation!.findings
    : [];
  return (
    <section
      className="diagnostic-explanations"
      aria-label={title}
      data-explanation-state={
        failure ? "unavailable" : explanation ? "loaded" : "loading"
      }
    >
      <h3>{title}</h3>
      <p className="hint">
        Facts cite retained evidence. Studio does not infer root causes;
        hypotheses are unconfirmed and unknowns stay unknown.
      </p>
      {failure && (
        <p className="control-failure" role="alert">
          Explanation unavailable: {failure}
        </p>
      )}
      {explanation && findings.length === 0 && (
        <p className="diagnostic-none">{emptyText}</p>
      )}
      {explanation && !explanation.findingsComplete && (
        <p className="notice warning">
          Showing {findings.length} of {explanation.findingCount} findings.
        </p>
      )}
      {findings.map((finding, index) => (
        <article
          className="diagnostic-finding"
          key={`${finding.code}-${index}`}
          data-diagnostic-class={finding.class}
        >
          <header>
            <h4>{finding.title}</h4>
            <Badge
              tone={
                finding.severity === "error"
                  ? "danger"
                  : finding.severity === "warning"
                    ? "warning"
                    : "neutral"
              }
            >
              {finding.severity}
            </Badge>
            <span className="diagnostic-class">
              {CLASS_LABELS[finding.class] || finding.class}
            </span>
            <code>{finding.code}</code>
          </header>
          {finding.elementRefs?.length > 0 && (
            <p className="diagnostic-refs">
              Affected:{" "}
              {finding.elementRefs.map((ref: string) => (
                <code key={ref}>{ref}</code>
              ))}
            </p>
          )}
          <h5>Observed facts</h5>
          <ol className="diagnostic-facts">
            {finding.facts.map((fact: Data) => (
              <li key={fact.id} id={`${finding.code}-${index}-${fact.id}`}>
                <span className="fact-id">{fact.id.toUpperCase()}</span>{" "}
                {fact.statement}
                <ul className="diagnostic-evidence" aria-label="Evidence">
                  {fact.evidence.map((ref: Data, i: number) => (
                    <li key={i}>
                      <Icon name="arrow" size={12} /> {evidenceLabel(ref)}
                    </li>
                  ))}
                  {fact.evidenceOmitted > 0 && (
                    <li>
                      …and {fact.evidenceOmitted} more retained references
                    </li>
                  )}
                </ul>
              </li>
            ))}
          </ol>
          {finding.consequences.length > 0 && (
            <>
              <h5>Inferred consequences</h5>
              <ul>
                {finding.consequences.map((item: Data, i: number) => (
                  <li key={i}>
                    {item.statement}{" "}
                    <span className="hint">
                      (from{" "}
                      {item.basis
                        .map((b: string) => b.toUpperCase())
                        .join(", ")}
                      )
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}
          {finding.hypotheses.length > 0 && (
            <>
              <h5>Hypotheses · unconfirmed</h5>
              <ul>
                {finding.hypotheses.map((item: Data, i: number) => (
                  <li key={i}>{item.statement}</li>
                ))}
              </ul>
            </>
          )}
          {finding.unknowns.length > 0 && (
            <>
              <h5>Unknown</h5>
              <ul>
                {finding.unknowns.map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </>
          )}
          {finding.nextActions.length > 0 && (
            <>
              <h5>Next actions</h5>
              <ul className="diagnostic-actions">
                {finding.nextActions.map((item: Data) => (
                  <li key={item.action}>
                    {available[item.action] ? (
                      <button
                        className="small-button"
                        onClick={() => void perform(item.action)}
                      >
                        {item.label}
                      </button>
                    ) : (
                      item.label
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
        </article>
      ))}
    </section>
  );
}
