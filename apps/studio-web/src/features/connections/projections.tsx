import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge } from "../../app/ui";

// Declared, resolved and observed communication are separate facts (FR-036). The perspective switch
// never merges them: a declaration is not a route, and a route is not traffic.

const PERSPECTIVES = ["declared", "resolved", "observed"] as const;
type Perspective = (typeof PERSPECTIVES)[number];

export function useCommunication(
  projectId: string,
  revision: number,
  runId?: string,
  runState?: string,
) {
  // Re-project when the run changes state, and periodically while it is live.
  const [tick, setTick] = useState(0);
  const live = ["running", "starting", "stopping"].includes(runState || "");
  useEffect(() => {
    if (!live) return;
    const timer = window.setInterval(() => setTick((value) => value + 1), 2000);
    return () => window.clearInterval(timer);
  }, [live]);
  const [state, setState] = useState<{
    key: string;
    value?: Data;
    failure?: string;
  } | null>(null);
  const key = `${projectId}:${revision}:${runId || ""}:${runState || ""}:${tick}`;
  useEffect(() => {
    const controller = new AbortController();
    api(
      `/projects/${encodeURIComponent(projectId)}/communication${runId ? `?runId=${encodeURIComponent(runId)}` : ""}`,
      { signal: controller.signal },
    )
      .then((value) => {
        if (!controller.signal.aborted) setState({ key, value });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({
            key,
            failure:
              error instanceof Error
                ? error.message
                : "Projection unavailable.",
          });
      });
    return () => controller.abort();
  }, [key]);
  return state?.key === key ? state : null;
}

const tone = (status: string) =>
  ["declared", "resolved", "observed"].includes(status)
    ? "success"
    : ["not_observed", "unverified"].includes(status)
      ? "danger"
      : ["not_resolved", "collected_none"].includes(status)
        ? "warning"
        : "neutral";

const LABEL: Record<string, string> = {
  declared: "declared",
  pending: "resolved at run start",
  resolved: "resolved",
  not_resolved: "not resolved",
  no_run: "no run selected",
  not_collected: "not collected",
  collected_none: "no samples yet",
  not_observed: "not observed (expectation unmet)",
  unverified: "evidence unverified",
  observed: "observed",
};

function Cell({ perspective, flow }: { perspective: Perspective; flow: Data }) {
  const value = flow[perspective];
  if (perspective === "declared")
    return (
      <>
        <Badge tone="success">declared</Badge>{" "}
        <code>{flow.sourceEndpointId}</code> →{" "}
        <code>{flow.destinationEndpointIds.join(", ")}</code> ·{" "}
        {flow.interfaceId}
        {" · "}
        {flow.deliveryIntent} · {flow.timeDomainId}
        {flow.contract?.causality && <> · unit delay</>}
        {flow.contract?.converter && (
          <>
            {" "}
            · converter {flow.contract.converter.fromUnit} →{" "}
            {flow.contract.converter.toUnit}
          </>
        )}
        <div>
          <small>Source: {flow.source}</small>
        </div>
      </>
    );
  return (
    <>
      <Badge tone={tone(value.status)}>
        {LABEL[value.status] || value.status}
      </Badge>{" "}
      {perspective === "resolved" && value.status === "resolved" && (
        <>
          via {value.transport} · provider <code>{value.providerId}</code> ·
          scope {value.evidenceScope}
        </>
      )}
      {perspective === "observed" && value.status === "observed" && (
        <>
          {value.samples} sample(s), ticks {value.firstTick}–{value.lastTick} (
          {value.clockDomain}) · <Badge>{value.freshness}</Badge>{" "}
          {value.freshness !== "final" && <>age {value.ageSeconds}s · </>}
          source <code>{value.source?.providerId}</code> (
          {value.source?.evidenceClass}) · scope {value.evidenceScope} ·
          integrity {value.integrity}
        </>
      )}
      {value.reason && (
        <div>
          <small>{value.reason}</small>
        </div>
      )}
      {(value.limitations || []).map((text: string) => (
        <div key={text}>
          <small>Limitation: {text}</small>
        </div>
      ))}
    </>
  );
}

export function CommunicationProjections({
  projectId,
  revision,
  runId,
  runState,
}: {
  projectId: string;
  revision: number;
  runId?: string;
  runState?: string;
}) {
  const [perspective, setPerspective] = useState<Perspective>("declared");
  const state = useCommunication(projectId, revision, runId, runState),
    report = state?.value;
  return (
    <section
      className="communication-projections"
      aria-labelledby="communication-heading"
    >
      <h3 id="communication-heading">Communication projections</h3>
      <div role="radiogroup" aria-label="Perspective" className="segmented">
        {PERSPECTIVES.map((value) => (
          <label key={value}>
            <input
              type="radio"
              name="communication-perspective"
              value={value}
              checked={perspective === value}
              onChange={() => setPerspective(value)}
            />
            {value[0].toUpperCase() + value.slice(1)}
          </label>
        ))}
      </div>
      {state?.failure ? (
        <p className="control-failure" role="alert">
          Communication projection unavailable: {state.failure}
        </p>
      ) : !report ? (
        <p className="muted" role="status">
          Projecting communication…
        </p>
      ) : (
        <>
          <p role="status">
            {report.runId
              ? `Run ${report.runId} (${report.runState}) on provider ${report.providerId}, transport: ${report.transport}.`
              : "Draft only: routes resolve and traffic is observed only within a run."}
          </p>
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Flow</th>
                <th scope="col">
                  {perspective[0].toUpperCase() + perspective.slice(1)}
                </th>
              </tr>
            </thead>
            <tbody>
              {report.flows.map((flow: Data) => (
                <tr key={flow.ref}>
                  <th scope="row">{flow.flowId}</th>
                  <td>
                    <Cell perspective={perspective} flow={flow} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <ul className="field-hint">
            {report.limitations.map((text: string) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
