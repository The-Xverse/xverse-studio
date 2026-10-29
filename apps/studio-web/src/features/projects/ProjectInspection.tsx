import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge } from "../../app/ui";

// Read-only inspection of declared dependencies, example scope and unresolved authored content.
// Nothing here fetches, installs or runs a dependency; unresolved content is shown as preserved.

export function useProjectInspection(projectId: string, revision: number) {
  const [report, setReport] = useState<{ key: string; value: Data } | null>(
      null,
    ),
    [failure, setFailure] = useState("");
  const key = `${projectId}:${revision}`;
  useEffect(() => {
    const controller = new AbortController();
    setFailure("");
    api(`/projects/${encodeURIComponent(projectId)}/inspection`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setReport({ key, value });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setFailure(
            error instanceof Error ? error.message : "Inspection unavailable.",
          );
      });
    return () => controller.abort();
  }, [key, projectId]);
  return { report: report?.key === key ? report.value : null, failure };
}

const tone = (status: string) =>
  status === "admitted"
    ? "success"
    : status === "conflict"
      ? "danger"
      : "warning";

export function ProjectInspection({
  report,
  failure,
  onOpenSource,
}: {
  report: Data | null;
  failure: string;
  onOpenSource: (documentId: string) => void;
}) {
  if (failure)
    return (
      <p className="control-failure" role="alert">
        Project inspection unavailable: {failure}
      </p>
    );
  if (!report) return <p className="muted">Inspecting the authored project…</p>;
  const { example, provenance, dependencies, unresolved, unparsed } = report;
  return (
    <div className="project-inspection">
      <section aria-labelledby="inspection-scope">
        <h3 id="inspection-scope">Scope</h3>
        {example ? (
          <>
            <p>
              Created from <strong>{example.name}</strong> {example.version}{" "}
              <Badge>{example.scope}</Badge> <Badge>{example.maturity}</Badge>
            </p>
            <ul>
              {(example.expectedObservations || []).map((text: string) => (
                <li key={"d" + text}>Demonstrates: {text}</li>
              ))}
              <li>
                Runs on provider <code>{example.providerId}</code> only.
              </li>
              {example.limitations.map((text: string) => (
                <li key={"l" + text}>Scope limit: {text}</li>
              ))}
            </ul>
          </>
        ) : provenance?.imported ? (
          <p>
            Imported archive. {(provenance.limitations || []).join(" ")} Nothing
            in it has been executed.
          </p>
        ) : (
          <p>Authored in this workspace.</p>
        )}
      </section>
      <section aria-labelledby="inspection-dependencies">
        <h3 id="inspection-dependencies">Declared dependencies</h3>
        {dependencies.profileLocks.length ? (
          <ul className="inspection-list">
            {dependencies.profileLocks.map((lock: Data) => (
              <li key={lock.index}>
                <Badge tone={tone(lock.status)}>{lock.status}</Badge>{" "}
                <code>{lock.namespace ?? "malformed lock"}</code> {lock.version}{" "}
                <small>{lock.reason}</small>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No profile locks are declared.</p>
        )}
        {dependencies.supportingFiles.length > 0 && (
          <ul className="inspection-list" aria-label="Supporting files">
            {dependencies.supportingFiles.map((file: Data) => (
              <li key={file.path}>
                <code>{file.path}</code> {file.bytes} bytes{" "}
                <code title={file.digest}>{file.digest.slice(0, 19)}…</code>{" "}
                <small>stored, never executed</small>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section aria-labelledby="inspection-unresolved">
        <h3 id="inspection-unresolved">
          Unresolved content{" "}
          <Badge tone={unresolved.length ? "warning" : "success"}>
            {unresolved.length}
          </Badge>
        </h3>
        {unresolved.length === 0 && unparsed.length === 0 ? (
          <p className="muted">
            Every extension namespace is declared by an admitted profile.
          </p>
        ) : (
          <>
            <p>
              The authored bytes stay unchanged in their source documents; below
              is a parsed view of each payload. Execution remains unavailable
              until a matching profile is authored and admitted.
            </p>
            <ul className="inspection-unresolved">
              {unresolved.map((item: Data) => (
                <li key={`${item.documentId}${item.pointer}`}>
                  <div>
                    <Badge tone={tone(item.status)}>{item.status}</Badge>{" "}
                    <code>{item.namespace}</code> in{" "}
                    <button
                      className="link-button"
                      onClick={() => onOpenSource(item.documentId)}
                    >
                      {item.path}
                    </button>{" "}
                    <code>{item.pointer}</code>
                  </div>
                  <small>{item.reason}</small>
                  <pre
                    className="inspection-content"
                    tabIndex={0}
                    aria-label={`Preserved content of ${item.namespace}`}
                  >
                    {item.content}
                  </pre>
                  {item.truncated && (
                    <small>
                      Excerpt truncated; the full source is preserved.
                    </small>
                  )}
                </li>
              ))}
              {unparsed.map((item: Data) => (
                <li key={item.documentId}>
                  <Badge tone="danger">unparsed</Badge>{" "}
                  <button
                    className="link-button"
                    onClick={() => onOpenSource(item.documentId)}
                  >
                    {item.path}
                  </button>{" "}
                  <small>Kept as authored; it cannot be interpreted.</small>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
      <p className="inspection-status" role="status">
        {report.executionBlocked
          ? `Execution is blocked by this content${report.sourceIntegrity !== "intact" ? " and by modified source integrity" : ""}; authoring and inspection remain available.`
          : "Nothing here blocks execution; preflight still checks provider readiness."}
      </p>
      <p className="field-hint">{report.limitations.join(" ")}</p>
    </div>
  );
}

/** Header entry point; the count reflects unresolved or unparsed authored content. */
export function InspectionButton({
  projectId,
  revision,
  onOpen,
}: {
  projectId: string;
  revision: number;
  onOpen: () => void;
}) {
  const { report, failure } = useProjectInspection(projectId, revision);
  const count = report ? report.unresolved.length + report.unparsed.length : 0;
  return (
    <button
      className="button"
      onClick={onOpen}
      aria-label={
        failure
          ? "Dependencies: inspection unavailable"
          : count
            ? `Dependencies: ${count} unresolved item${count === 1 ? "" : "s"}`
            : report
              ? "Dependencies: none unresolved"
              : "Dependencies"
      }
    >
      Dependencies
      {failure ? (
        <Badge tone="danger">!</Badge>
      ) : (
        count > 0 && <Badge tone="warning">{count}</Badge>
      )}
    </button>
  );
}
