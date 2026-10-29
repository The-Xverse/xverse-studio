import { useEffect, useRef, useState } from "react";
import { api, ApiError, mutationKey } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge, Json, KeyValues, Modal, statusTone } from "../../app/ui";

export type RetentionTarget = {
  kind: "project" | "artifact" | "run";
  id: string;
  name: string;
};
function identity(row: Data) {
  return row.projectId || row.artifactId || row.runId || "Unknown identity";
}
function kind(row: Data) {
  return row.projectId
    ? "Project"
    : row.artifactId
      ? "Artifact registration"
      : "Run files";
}

/** A plan is a backend proof; eligibility is never inferred from the current UI. */
export function RetentionDialog({
  target,
  onClose,
  onChanged,
  restoreFocusSelector,
}: {
  target: RetentionTarget;
  onClose: () => void;
  onChanged?: (result: Data) => Promise<void>;
  restoreFocusSelector?: string;
}) {
  const [plan, setPlan] = useState<Data | null>(null),
    [result, setResult] = useState<Data | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [now, setNow] = useState(Date.now());
  const applyKey = useRef(mutationKey()),
    reported = useRef("");
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  async function report(value: Data) {
    value = {
      ...value,
      status: ["unknown", "rejected", "failed"].includes(value.operationStatus)
        ? value.operationStatus
        : value.status || value.operationStatus,
    };
    setResult(value);
    if (
      ["complete", "partial", "rejected", "unknown"].includes(
        value.status || value.operationStatus,
      ) &&
      reported.current !== value.operationId
    ) {
      reported.current = value.operationId;
      await onChanged?.(value);
    }
  }
  useEffect(() => {
    if (
      !result?.operationId ||
      !["accepted", "running", "pending"].includes(result.operationStatus)
    )
      return;
    let alive = true;
    const timer = setInterval(async () => {
      try {
        const operation = await api(
          `/operations/${encodeURIComponent(result.operationId)}`,
        );
        if (alive)
          await report({
            ...result,
            ...operation.result,
            operationStatus: operation.status,
          });
      } catch (e) {
        if (alive)
          setError(
            e instanceof Error
              ? e.message
              : "Unable to reconcile the apply operation.",
          );
      }
    }, 1000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [result?.operationId, result?.operationStatus]);
  async function preview() {
    setBusy(true);
    setError("");
    setPlan(null);
    setResult(null);
    applyKey.current = mutationKey();
    try {
      const value = await api("/retention/plans", {
        method: "POST",
        body: { [target.kind + "Ids"]: [target.id], rule: "explicit" },
      });
      if (
        value.dependencyReportComplete !== true ||
        !Array.isArray(value.removals) ||
        !Array.isArray(value.protected) ||
        !Array.isArray(value.dependencyEdges)
      )
        throw new Error(
          "The backend did not return a complete dependency report. No deletion can be requested.",
        );
      setPlan(value);
    } catch (e) {
      setError(e instanceof ApiError ? `${e.code}: ${e.message}` : String(e));
    } finally {
      setBusy(false);
    }
  }
  async function apply() {
    if (!plan) return;
    setBusy(true);
    setError("");
    try {
      const value = await api(
        `/retention/plans/${encodeURIComponent(plan.planId)}/apply`,
        {
          method: "POST",
          body: { fingerprint: plan.fingerprint },
          key: applyKey.current,
        },
      );
      await report(value);
      setPlan(await api(`/retention/plans/${encodeURIComponent(plan.planId)}`));
    } catch (e) {
      setError(e instanceof ApiError ? `${e.code}: ${e.message}` : String(e));
    } finally {
      setBusy(false);
    }
  }
  const expired = !!plan && now >= Number(plan.expiresAt) * 1000;
  const applied = !!result;
  return (
    <Modal
      title="Review explicit retention"
      wide
      onClose={onClose}
      restoreFocusSelector={restoreFocusSelector}
    >
      <div className="retention-review">
        <p>
          Preview the dependencies of this exact selection. Applying a plan
          removes only eligible Studio-owned data; protected dependencies are
          retained.
        </p>
        <KeyValues
          values={{
            Selection: target.name,
            Kind: target.kind,
            "Exact ID": target.id,
          }}
        />
        {target.kind === "artifact" && (
          <p className="notice">
            Artifact retention removes catalog registration metadata only.
            External artifact bytes and providers are preserved.
          </p>
        )}
        {target.kind === "run" && (
          <p className="field-hint">
            Historical outcomes and snapshot identities remain recorded. This
            action concerns owned run files.
          </p>
        )}
        <button
          className="button"
          disabled={busy}
          onClick={() => void preview()}
        >
          {plan || result
            ? "Refresh dependency preview"
            : "Preview removal dependencies"}
        </button>
        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}
        {plan && (
          <>
            <KeyValues
              values={{
                Plan: plan.planId,
                Fingerprint: plan.fingerprint,
                Expires: new Date(
                  Number(plan.expiresAt) * 1000,
                ).toLocaleString(),
                "Dependency report": "Complete",
                "Eligible selections": plan.removals.length,
                "Protected selections": plan.protected.length,
              }}
            />
            <h3>Eligible removals</h3>
            {plan.removals.length ? (
              <div className="table-scroll">
                <table aria-label="Eligible retention removals">
                  <thead>
                    <tr>
                      <th>Kind</th>
                      <th>Exact ID</th>
                      <th>Removal scope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.removals.map((row: Data) => (
                      <tr key={identity(row)}>
                        <td>{kind(row)}</td>
                        <td>
                          <code>{identity(row)}</code>
                        </td>
                        <td>
                          {row.scope}
                          {row.externalArtifactPreserved && (
                            <small> · External bytes preserved</small>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No selected data is eligible for removal.</p>
            )}
            <h3>Protected selections</h3>
            {plan.protected.length ? (
              <ul className="retention-protected">
                {plan.protected.map((row: Data) => (
                  <li key={identity(row)}>
                    <strong>{kind(row)}</strong> <code>{identity(row)}</code>
                    <ul>
                      {(row.reasons || []).map((reason: string) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No selected data is protected by this report.</p>
            )}
            <h3>Dependency reasons</h3>
            {plan.dependencyEdges.length ? (
              <div className="table-scroll retention-edges">
                <table aria-label="Retention dependency reasons">
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Depends on</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.dependencyEdges.map((edge: Data, index: number) => (
                      <tr key={index}>
                        <td>
                          {edge.source.kind}
                          <br />
                          <code>{edge.source.id}</code>
                        </td>
                        <td>
                          {edge.target.kind}
                          <br />
                          <code>{edge.target.id}</code>
                        </td>
                        <td>{edge.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No dependency edges were found for the selected data.</p>
            )}
            {expired && !applied && (
              <p role="status" className="notice">
                This preview has expired. Refresh it before applying.
              </p>
            )}
            <button
              className="button danger-button"
              disabled={
                busy ||
                expired ||
                applied ||
                !plan.removals.length ||
                plan.status !== "planned"
              }
              onClick={() => void apply()}
            >
              Apply deletion of {plan.removals.length} eligible selection(s)
            </button>
            <Json value={plan} />
          </>
        )}
        {result && (
          <section aria-label="Retention apply outcome" aria-live="polite">
            <h3>
              Apply outcome{" "}
              <Badge tone={statusTone(result.status || result.operationStatus)}>
                {result.status || result.operationStatus}
              </Badge>
            </h3>
            <KeyValues
              values={{
                Operation: result.operationId,
                "Operation status": result.operationStatus,
              }}
            />
            {result.operationStatus === "unknown" && (
              <p className="notice">
                The outcome is uncertain. Inspect the recorded per-item outcomes
                and refresh the dependency preview before considering another
                action.
              </p>
            )}
            <ul>
              {(result.outcomes || []).map((row: Data) => (
                <li key={identity(row)}>
                  <code>{identity(row)}</code> · {row.status}
                  {row.reason ? ` · ${row.reason}` : ""}
                  {row.externalArtifactPreserved &&
                    " · External bytes preserved"}
                </li>
              ))}
            </ul>
            <Json value={result} />
          </section>
        )}
        <div className="modal-actions">
          <button className="button" onClick={onClose}>
            Close retention review
          </button>
        </div>
      </div>
    </Modal>
  );
}
