import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge } from "../../app/ui";

// Presents backend connection admission 1.0. Studio never converts, infers or proves
// executable correctness here; unknown and unsupported stay visible as such.

export function useConnectionAdmission(projectId: string, revision: number) {
  const [report, setReport] = useState<{ key: string; value: Data } | null>(
      null,
    ),
    [failure, setFailure] = useState("");
  const key = `${projectId}:${revision}`;
  useEffect(() => {
    const controller = new AbortController();
    setFailure("");
    api(`/projects/${encodeURIComponent(projectId)}/connections`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setReport({ key, value });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setFailure(
            error instanceof Error ? error.message : "Admission unavailable.",
          );
      });
    return () => controller.abort();
  }, [key, projectId]);
  return { report: report?.key === key ? report.value : null, failure };
}

const tone = (status: string) =>
  status === "admitted" || status === "pass"
    ? "success"
    : status === "rejected" || status === "fail"
      ? "danger"
      : status === "declared"
        ? "neutral"
        : "warning";

export function AdmissionCell({ connection }: { connection?: Data }) {
  const [open, setOpen] = useState(false);
  if (!connection) return <Badge>Not evaluated</Badge>;
  const panelId = `checks-${connection.ref.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  return (
    <div className="admission-cell">
      <button
        className="small-button"
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        aria-label={`Admission ${connection.admission}; show checks for ${connection.ref}`}
        onClick={() => setOpen((value) => !value)}
      >
        <Badge tone={tone(connection.admission)}>{connection.admission}</Badge>
      </button>
      {open && (
        <ul className="admission-checks" id={panelId}>
          {connection.checks.map((check: Data, index: number) => (
            <li key={index}>
              <Badge tone={tone(check.status)}>{check.status}</Badge>{" "}
              <strong>{check.check}</strong> {check.message}
              {check.code && (
                <>
                  {" "}
                  <code>{check.code}</code>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AdmissionSummary({
  report,
  failure,
}: {
  report: Data | null;
  failure: string;
}) {
  if (failure)
    return (
      <p className="control-failure" role="alert">
        Connection admission unavailable: {failure}
      </p>
    );
  if (!report) return null;
  const flows: Data[] = report.connections,
    blockedFlows = flows.filter((c) =>
      ["rejected", "unsupported"].includes(c.admission),
    ).length,
    unknownFlows = flows.filter((c) => c.admission === "unknown").length,
    endpointViolations = report.endpoints.filter((e: Data) =>
      ["fail", "unsupported"].includes(e.status),
    );
  const parts = [
    blockedFlows &&
      `${blockedFlows} of ${flows.length} flows cannot execute as declared`,
    unknownFlows && `${unknownFlows} flows are not established`,
    report.cycles.length &&
      `${report.cycles.length} feedback cycle(s) unsupported`,
    report.couplings.length &&
      `${report.couplings.length} model coupling(s) unsupported`,
    endpointViolations.length &&
      `${endpointViolations.length} endpoint multiplicity issue(s)`,
    report.limits.length && "the connection bound is exceeded",
  ].filter(Boolean);
  return (
    <section className="admission-summary" aria-label="Connection admission">
      <p>
        {!report.sourceValid &&
          "The source set is invalid; admission is incomplete. "}
        {parts.length
          ? `${parts.join("; ")}.`
          : `All ${flows.length} declared flows are admitted for their declared semantics.`}{" "}
        Admission evaluates declarations only; it does not prove routing,
        traffic or executable correctness.
      </p>
      {report.cycles.length > 0 && (
        <>
          <h4>Feedback cycles</h4>
          <ul>
            {report.cycles.map((cycle: Data, index: number) => (
              <li key={index}>
                <Badge tone="warning">{cycle.status}</Badge> members{" "}
                {cycle.members.map((m: string) => m.split("#")[1]).join(", ")}{" "}
                <small>{cycle.message}</small>
              </li>
            ))}
          </ul>
        </>
      )}
      {report.couplings.length > 0 && (
        <>
          <h4>Model couplings</h4>
          <ul className="relation-couplings">
            {report.couplings.map((coupling: Data) => (
              <li key={coupling.ref}>
                <Badge tone="warning">model coupling</Badge>{" "}
                <code>{coupling.ref.split("#")[1]}</code> ({coupling.modelKind}
                ): {coupling.inputs.join(", ")} → {coupling.outputs.join(", ")}{" "}
                <small>{coupling.message}</small>
              </li>
            ))}
          </ul>
        </>
      )}
      {endpointViolations.length > 0 && (
        <>
          <h4>Endpoint multiplicity</h4>
          <ul>
            {endpointViolations.map((endpoint: Data) => (
              <li key={endpoint.ref}>
                <Badge tone={tone(endpoint.status)}>{endpoint.status}</Badge>{" "}
                {endpoint.message}
              </li>
            ))}
          </ul>
        </>
      )}
      {report.links.length > 0 && (
        <>
          <h4>Network links</h4>
          <ul className="relation-links">
            {report.links.map((link: Data) => (
              <li key={link.ref}>
                <Badge>communication link</Badge>{" "}
                <code>{link.ref.split("#")[1]}</code> on{" "}
                <code>{link.networkId}</code> ({link.connectivity}):{" "}
                {link.participantEndpointIds.join(", ")}{" "}
                <small>{link.scope}</small>
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="field-hint">
        Admitted contracts:{" "}
        {Object.entries(report.admittedContracts)
          .map(([name, admitted]) => `${name} ${admitted ? "yes" : "no"}`)
          .join(", ")}
        . Communication flows are never presented as physical couplings.
      </p>
    </section>
  );
}

/** Destination guidance: same interface and input capability, with reasons otherwise. */
export function targetGuidance(
  endpoints: Data[],
  interfaces: Data[],
  sourceId: string,
) {
  const source = endpoints.find((e) => e.id === sourceId);
  const iface = interfaces.find((i) => i.id === source?.interfaceId);
  return endpoints
    .filter((e) => e.id !== sourceId)
    .map((e) => {
      const blocked = !source
        ? "Choose a source first."
        : !["input", "bidirectional"].includes(e.direction)
          ? "Not input-capable."
          : e.interfaceId !== source.interfaceId
            ? `Interface ${e.interfaceId} differs from ${source.interfaceId}; no converter is admitted.`
            : "";
      const note =
        !blocked && iface?.compatibility && iface.compatibility !== "exact"
          ? `Interface declares ${iface.compatibility}; this connection will not be admitted for execution.`
          : "";
      return { endpoint: e, compatible: !blocked, reason: blocked || note };
    })
    .sort((a, b) => Number(b.compatible) - Number(a.compatible));
}
