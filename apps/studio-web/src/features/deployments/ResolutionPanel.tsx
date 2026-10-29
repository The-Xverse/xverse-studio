import { useEffect, useLayoutEffect, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge } from "../../app/ui";

// Presents deployment resolution 1.0 (ADR-0015). Studio never orders values, converts units or
// resolves environment references here; unknown stays visible as unknown.

export function useResolution(
  projectId: string,
  revision: number,
  documentId: string | undefined,
  providerId: string,
) {
  const [state, setState] = useState<{
    key: string;
    value?: Data;
    failure?: string;
  } | null>(null);
  const key = JSON.stringify([projectId, revision, documentId, providerId]);
  useLayoutEffect(() => {
    setState(null);
  }, [key]);
  useEffect(() => {
    if (!documentId) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      if (!controller.signal.aborted) {
        controller.abort();
        setState({
          key,
          failure:
            "The deployment resolution read timed out. Reopen the current project to read it again.",
        });
      }
    }, 30000);
    api(
      `/projects/${encodeURIComponent(projectId)}/deployment-variants/${encodeURIComponent(documentId)}/resolution?providerId=${encodeURIComponent(providerId)}&revision=${revision}`,
      { signal: controller.signal },
    )
      .then((value) => {
        if (controller.signal.aborted) return;
        if (
          !value ||
          value.resolutionVersion !== "1.0" ||
          value.documentId !== documentId ||
          value.revision !== revision ||
          typeof value.sourceValid !== "boolean" ||
          (value.sourceValid && value.providerId !== providerId)
        )
          throw new Error(
            "Deployment resolution metadata does not match the requested revision, document or provider. Reopen the current project.",
          );
        if (!controller.signal.aborted) setState({ key, value });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({
            key,
            failure:
              error instanceof Error
                ? error.message
                : "Resolution unavailable.",
          });
      })
      .finally(() => clearTimeout(timer));
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [key]);
  return state?.key === key ? state : null;
}

// Blocking statuses mirror the backend BLOCKING set; declared, unset and pass never block.
const BLOCKING = new Set([
  "fail",
  "unknown",
  "unsupported",
  "ambiguous",
  "unresolved",
]);
export const resolutionTone = (status: string) =>
  BLOCKING.has(status)
    ? "danger"
    : ["pass", "compatible", "default", "overridden", "authored"].includes(
          status,
        )
      ? "success"
      : "neutral";

const canonical = (value: unknown): string =>
  value === null || typeof value !== "object"
    ? JSON.stringify(value)
    : Array.isArray(value)
      ? `[${value.map(canonical).join(",")}]`
      : `{${Object.keys(value as object)
          .sort()
          .map(
            (key) =>
              `${JSON.stringify(key)}:${canonical((value as Data)[key])}`,
          )
          .join(",")}}`;

const parameterKey = (entry: Data) =>
  `${entry.elementId ?? `scenario ${String(entry.scenarioRef).split("/").pop()}`}.${entry.parameterId}`;

const show = (value: unknown) =>
  value === undefined || value === null
    ? "—"
    : typeof value === "string"
      ? value
      : JSON.stringify(value);

export function ResolutionPanel({
  report,
  failure,
}: {
  report: Data | null | undefined;
  failure?: string;
}) {
  if (failure)
    return (
      <p className="control-failure" role="alert">
        Deployment resolution unavailable: {failure}
      </p>
    );
  if (!report)
    return (
      <p className="muted" role="status">
        Resolving the selected deployment…
      </p>
    );
  if (!report.sourceValid)
    return (
      <p className="control-failure" role="status">
        The authored source set is invalid, so bindings, constraints and
        effective values cannot be resolved. Fix the validator diagnostics
        first.
      </p>
    );
  const blocking = report.diagnostics.length;
  return (
    <div className="resolution">
      <p role="status" className="resolution-summary">
        <Badge tone={blocking ? "danger" : "success"}>
          {blocking ? `${blocking} blocking` : "no blocking findings"}
        </Badge>{" "}
        Resolution {report.resolutionVersion} for{" "}
        <code>{report.deploymentRef.split("/").pop()}</code> on host{" "}
        {report.hostOS || "unknown"} with provider{" "}
        <code>{report.providerId || "none"}</code>.
      </p>
      {report.provider && (
        <div className="provider-scope">
          <p>
            Provider <code>{report.provider.providerId}</code>{" "}
            <Badge>{report.provider.maturity}</Badge> declares realization{" "}
            {(report.provider.realizationClasses || []).join(", ") || "none"} on
            targets {(report.provider.targetClasses || []).join(", ") || "none"}
            .
          </p>
          <ul className="field-hint">
            {(report.provider.limitations || []).map((text: string) => (
              <li key={text}>Fidelity limit: {text}</li>
            ))}
          </ul>
        </div>
      )}
      {report.connections && (
        <p className="resolution-connections" role="note">
          <Badge tone={report.connections.blocking ? "danger" : "success"}>
            {report.connections.blocking
              ? `${report.connections.blocking} connection finding(s)`
              : "connections admitted"}
          </Badge>{" "}
          Under provider <code>{report.connections.providerId}</code>:{" "}
          {report.connections.cycles.length
            ? `${report.connections.cycles.filter((c: Data) => c.status === "admitted").length} of ${report.connections.cycles.length} feedback cycle(s) admitted; `
            : ""}
          {report.connections.notAdmitted.length
            ? `not admitted: ${report.connections.notAdmitted.map((ref: string) => ref.split("#")[1]).join(", ")}.`
            : "every declared flow is admitted for its declared semantics."}{" "}
          See Connections for the checks.
        </p>
      )}
      <section aria-labelledby="resolution-bindings">
        <h4 id="resolution-bindings">Bindings</h4>
        <table className="data-table resolution-table">
          <thead>
            <tr>
              <th scope="col">Element</th>
              <th scope="col">Realization → target</th>
              <th scope="col">Status</th>
              <th scope="col">Checks</th>
            </tr>
          </thead>
          <tbody>
            {report.bindings.map((row: Data) => (
              <tr key={row.bindingId}>
                <th scope="row">
                  {row.elementId}
                  <small> via {row.bindingId}</small>
                </th>
                <td>
                  {row.realizationClass} → {row.targetId} ({row.targetClass})
                </td>
                <td>
                  <Badge tone={resolutionTone(row.status)}>{row.status}</Badge>
                </td>
                <td>
                  <ul className="resolution-checks">
                    {row.checks.map((check: Data, index: number) => (
                      <li key={index}>
                        <Badge tone={resolutionTone(check.status)}>
                          {check.status}
                        </Badge>{" "}
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
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {report.constraints.length > 0 && (
        <section aria-labelledby="resolution-constraints">
          <h4 id="resolution-constraints">
            Resource, time and network constraints
          </h4>
          <ul className="resolution-checks">
            {report.constraints.map((check: Data, index: number) => (
              <li key={index}>
                <Badge tone={resolutionTone(check.status)}>
                  {check.status}
                </Badge>{" "}
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
        </section>
      )}
      <section aria-labelledby="resolution-values">
        <h4 id="resolution-values">Effective values</h4>
        {report.parameters.length ? (
          <table className="data-table resolution-table">
            <thead>
              <tr>
                <th scope="col">Parameter</th>
                <th scope="col">Effective</th>
                <th scope="col">Status</th>
                <th scope="col">
                  Value sources{" "}
                  <small>
                    (a default applies only when nothing is authored; authored
                    layers have no defined precedence)
                  </small>
                </th>
              </tr>
            </thead>
            <tbody>
              {report.parameters.map((entry: Data) => (
                <tr key={parameterKey(entry)}>
                  <th scope="row">
                    {parameterKey(entry)}
                    {entry.unitSemantics && (
                      <small> [{entry.unitSemantics}]</small>
                    )}
                  </th>
                  <td>{show(entry.effective)}</td>
                  <td>
                    <Badge tone={resolutionTone(entry.status)}>
                      {entry.status}
                    </Badge>
                    {entry.code && (
                      <>
                        {" "}
                        <code>{entry.code}</code>
                      </>
                    )}
                    <div>
                      <small>{entry.message}</small>
                    </div>
                  </td>
                  <td>
                    <ol className="value-chain">
                      {entry.chain.map((layer: Data, index: number) => (
                        <li key={index}>
                          <strong>{layer.layer}</strong> {show(layer.value)}
                          {layer.documentId && (
                            <small>
                              {" "}
                              {layer.documentId}
                              {layer.pointer ? `#${layer.pointer}` : ""}
                            </small>
                          )}
                        </li>
                      ))}
                    </ol>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No parameters are declared or authored.</p>
        )}
      </section>
      <section
        aria-labelledby="resolution-portability"
        className="portability-split"
      >
        <h4 id="resolution-portability">Portable intent and environment</h4>
        <div className="portability-columns">
          <div>
            <h5>Portable intent</h5>
            <ul>
              {report.portableIntent.bindings.map((binding: Data) => (
                <li key={binding.bindingId}>
                  {binding.elementId}: {binding.realizationClass} on{" "}
                  {binding.targetId}
                  {binding.resourceIds.length > 0 &&
                    ` using ${binding.resourceIds.join(", ")}`}
                </li>
              ))}
              {report.portableIntent.timeMappings.map((mapping: Data) => (
                <li key={mapping.id}>time mapping {mapping.id}</li>
              ))}
              {report.portableIntent.networkBindings.map((network: Data) => (
                <li key={network.id}>network binding {network.id}</li>
              ))}
            </ul>
          </div>
          <div>
            <h5>Environment references</h5>
            {report.environment.length ? (
              <ul>
                {report.environment.map((item: Data, index: number) => (
                  <li key={index}>
                    <Badge tone={resolutionTone(item.status)}>
                      {item.status}
                    </Badge>{" "}
                    {item.kind} for {item.ownerId}:{" "}
                    <code>{item.reference}</code> <small>{item.message}</small>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">
                No asset or secret references; nothing environment-specific to
                resolve.
              </p>
            )}
            {report.portability.map((check: Data, index: number) => (
              <p key={index}>
                <Badge tone={resolutionTone(check.status)}>
                  {check.status}
                </Badge>{" "}
                <code>{check.pointer}</code> {check.message}
              </p>
            ))}
          </div>
        </div>
      </section>
      <ul className="field-hint">
        {report.limitations.map((text: string) => (
          <li key={text}>{text}</li>
        ))}
      </ul>
    </div>
  );
}

/** Side-by-side realization/placement comparison of two resolved variants of one logical System. */
export function VariantComparison({
  left,
  right,
  leftName,
  rightName,
}: {
  left: Data;
  right: Data;
  leftName: string;
  rightName: string;
}) {
  const elements = Array.from(
    new Set([
      ...left.bindings.map((b: Data) => b.elementId),
      ...right.bindings.map((b: Data) => b.elementId),
    ]),
  ) as string[];
  const intent = (report: Data, bindingId: string) =>
    report.portableIntent?.bindings.find(
      (b: Data) => b.bindingId === bindingId,
    ) || {};
  const cell = (report: Data, element: string) => {
    const rows = report.bindings.filter((b: Data) => b.elementId === element);
    return rows.length ? (
      rows.map((row: Data) => {
        const bound = intent(report, row.bindingId);
        return (
          <div key={row.bindingId}>
            {row.realizationClass} → {row.targetId} ({row.targetClass}){" "}
            <Badge tone={resolutionTone(row.status)}>{row.status}</Badge>
            <div>
              <small>
                artifacts {(bound.artifactIds || []).join(", ") || "none"};
                resources {(bound.resourceIds || []).join(", ") || "none"}
              </small>
            </div>
          </div>
        );
      })
    ) : (
      <span className="muted">not bound</span>
    );
  };
  const values = (report: Data) =>
    new Map<string, Data>(
      report.parameters.map((p: Data) => [parameterKey(p), p]),
    );
  // Compare every authored layer and the verdict, not only the effective value: two ambiguous
  // variants can differ in what they author while both have no effective value.
  const signature = (entry?: Data) =>
    entry
      ? canonical([
          entry.status,
          entry.chain.map((l: Data) => [l.layer, l.value]),
        ])
      : "absent";
  const leftValues = values(left),
    rightValues = values(right);
  const differing = Array.from(
    new Set([...leftValues.keys(), ...rightValues.keys()]),
  ).filter(
    (key) => signature(leftValues.get(key)) !== signature(rightValues.get(key)),
  );
  const describe = (entry?: Data) =>
    entry
      ? `${entry.chain.map((l: Data) => `${l.layer} ${show(l.value)}`).join(", ") || "no value"} (${entry.status})`
      : "absent";
  const sameSystem = left.systemRef === right.systemRef;
  return (
    <section
      aria-labelledby="variant-comparison"
      className="variant-comparison"
    >
      <h4 id="variant-comparison">Compare realization and placement</h4>
      <p role="status">
        {sameSystem
          ? `Both variants realize ${left.systemRef.split("/").pop()}; logical element identities are shared.`
          : "These variants realize different Systems; their elements are not comparable."}{" "}
        A shared logical identity does not establish behavioural equivalence or
        fidelity.
      </p>
      <table className="data-table resolution-table">
        <thead>
          <tr>
            <th scope="col">Element</th>
            <th scope="col">{leftName}</th>
            <th scope="col">{rightName}</th>
          </tr>
        </thead>
        <tbody>
          {elements.map((element) => (
            <tr key={element}>
              <th scope="row">{element}</th>
              <td>{cell(left, element)}</td>
              <td>{cell(right, element)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h5>Authored values that differ</h5>
      {differing.length ? (
        <ul className="value-differences">
          {differing.map((key) => (
            <li key={key}>
              <strong>{key}</strong>: {describe(leftValues.get(key))} →{" "}
              {describe(rightValues.get(key))}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">Every authored value and its verdict match.</p>
      )}
      <p>
        Blocking findings: {leftName} {left.diagnostics.length}, {rightName}{" "}
        {right.diagnostics.length}.
      </p>
    </section>
  );
}
