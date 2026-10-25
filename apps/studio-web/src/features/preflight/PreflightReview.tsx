import "./preflight.css";
import { useEffect, useMemo, useState } from "react";
import type { Data, Preflight } from "../../api/types";
import { ApiError } from "../../api/client";
import { Badge, Json, KeyValues, Modal, statusTone } from "../../app/ui";
import { admittedStatuses, planIdentity, readinessFacts } from "./readiness";
function text(value: unknown) {
  return typeof value === "string"
    ? value
    : value === undefined || value === null
      ? "Not reported"
      : JSON.stringify(value);
}
function expiry(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return value * 1000;
  if (typeof value === "string") {
    const result = Date.parse(value);
    return Number.isFinite(result) ? result : NaN;
  }
  return NaN;
}
export function PreflightReview({
  preflight,
  providers,
  onClose,
  onStart,
  onRecheck,
  currentRevision,
}: {
  currentRevision: number;
  preflight: Preflight;
  providers: Data[];
  onClose: () => void;
  onStart: () => Promise<unknown>;
  onRecheck: (providerId: string) => Promise<unknown>;
}) {
  const [selectedProvider, setSelectedProvider] = useState(
      typeof preflight.providerId === "string"
        ? preflight.providerId
        : "studio.reference",
    ),
    [pending, setPending] = useState(false),
    [error, setError] = useState<Data | null>(null),
    [inspectPlan, setInspectPlan] = useState(false),
    [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    setSelectedProvider(
      typeof preflight.providerId === "string"
        ? preflight.providerId
        : "studio.reference",
    );
    setError(null);
    setInspectPlan(false);
  }, [preflight.preflightId]);
  const facts = useMemo(() => readinessFacts(preflight), [preflight]),
    identity = useMemo(() => planIdentity(preflight), [preflight]);
  const expires = expiry(preflight.expiresAt),
    expired = !Number.isFinite(expires) || now >= expires,
    providerChanged = selectedProvider !== preflight.providerId;
  const draftChanged = preflight.revision !== currentRevision;
  const canStart =
    !draftChanged &&
    preflight.status === "ready" &&
    !expired &&
    !providerChanged &&
    identity.matches &&
    facts.every((fact) => admittedStatuses.has(fact.status));
  const limits =
    preflight.limits &&
    typeof preflight.limits === "object" &&
    !Array.isArray(preflight.limits)
      ? Object.entries(preflight.limits)
      : [];
  const planText = useMemo(
    () =>
      inspectPlan && identity.matches
        ? JSON.stringify(preflight.planPreview.plan, null, 2)
        : "",
    [inspectPlan, identity.matches, preflight.planPreview],
  );
  async function perform(action: () => Promise<unknown>) {
    setPending(true);
    setError(null);
    try {
      await action();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? {
              code: e.code,
              message: e.message,
              diagnostics: e.details.diagnostics,
            }
          : {
              code: "REQUEST_UNAVAILABLE",
              message:
                e instanceof Error
                  ? e.message
                  : "The request could not be completed.",
            },
      );
    } finally {
      setPending(false);
    }
  }
  function downloadPlan() {
    const blob = new Blob(
        [JSON.stringify(preflight.planPreview.plan, null, 2)],
        { type: "application/json" },
      ),
      url = URL.createObjectURL(blob),
      anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "compiled-plan.json";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <Modal
      title="Execution preflight"
      restoreFocusSelector="[data-preflight-trigger]"
      wide
      onClose={onClose}
    >
      <div className="preflight-review">
        <div className="preflight-heading">
          <div>
            <span className="eyebrow">FROZEN EXECUTION REQUEST</span>
            <h3>
              Admission decision: <span>{text(preflight.status)}</span>
            </h3>
          </div>
          <p>
            These checks apply to this request and provider. Execution,
            observations, assertions, cleanup and evidence integrity have
            separate outcomes.
          </p>
        </div>
        <div className="preflight-provider-choice">
          <label>
            Execution provider
            <select
              aria-label="Execution provider"
              value={selectedProvider}
              disabled={pending}
              onChange={(event) => setSelectedProvider(event.target.value)}
            >
              {providers.map((provider) => (
                <option key={provider.providerId} value={provider.providerId}>
                  {provider.name || provider.providerId} · {provider.providerId}
                  {provider.available === false ? " · unavailable" : ""}
                </option>
              ))}
              {!providers.some(
                (provider) => provider.providerId === selectedProvider,
              ) && <option value={selectedProvider}>{selectedProvider}</option>}
            </select>
          </label>
          <button
            className="button"
            disabled={pending}
            onClick={() => void perform(() => onRecheck(selectedProvider))}
          >
            Recheck readiness
          </button>
        </div>
        {providerChanged && (
          <p role="status" className="notice">
            Provider choice changed. Recheck readiness to obtain a frozen
            request for this provider. The report below still belongs to{" "}
            {text(preflight.providerId)}.
          </p>
        )}
        <div className="preflight-request-summary">
          <span>
            Snapshot <code>{preflight.snapshotId}</code>
          </span>
          <span>
            Revision <strong>{text(preflight.revision)}</strong>
          </span>
          <span>
            Expires{" "}
            <strong>
              {Number.isFinite(expires)
                ? new Date(expires).toLocaleString()
                : "Not reported"}
            </strong>
          </span>
          <span>
            Scope{" "}
            <strong>
              {text(
                preflight.providerIdentity?.evidenceScope ||
                  preflight.evidenceScope ||
                  preflight.dimensions?.evidenceScope,
              )}
            </strong>
          </span>
        </div>
        <details className="preflight-identities">
          <summary>Frozen request identities</summary>
          <KeyValues
            values={{
              "Preflight ID": preflight.preflightId,
              "Frozen snapshot": preflight.snapshotId,
              "Snapshot identity": preflight.snapshotDigest,
              "Plan identity": preflight.planDigest,
              "Semantic identity": preflight.semanticDigest,
              Provider: preflight.providerId,
              "Provider version": preflight.providerIdentity?.providerVersion,
              "Evidence scope":
                preflight.providerIdentity?.evidenceScope ||
                preflight.evidenceScope ||
                preflight.dimensions?.evidenceScope,
              "Capability identity": preflight.capabilityDigest,
              Expires: Number.isFinite(expires)
                ? new Date(expires).toLocaleString()
                : "Not reported",
            }}
          />
        </details>
        {draftChanged && (
          <p className="notice" role="status">
            The current draft revision differs from this frozen request. Recheck
            readiness before Start.
          </p>
        )}
        {expired && (
          <p className="notice" role="status">
            {Number.isFinite(expires)
              ? "This preflight expired. Recheck readiness before Start."
              : "No usable preflight expiry was reported. Recheck readiness before Start."}
          </p>
        )}
        <section>
          <h3>Readiness checks</h3>
          <div className="table-scroll">
            <table
              className="readiness-table"
              aria-label="Independent readiness dimensions"
            >
              <thead>
                <tr>
                  <th>Dimension</th>
                  <th>Reported state</th>
                  <th>Evidence and next action</th>
                </tr>
              </thead>
              <tbody>
                {facts.map((fact) => (
                  <tr key={fact.id}>
                    <th scope="row">{fact.label}</th>
                    <td>
                      <Badge
                        tone={
                          admittedStatuses.has(fact.status)
                            ? "success"
                            : statusTone(fact.status)
                        }
                      >
                        {fact.status === "not_reported"
                          ? "Not reported"
                          : fact.status}
                      </Badge>
                    </td>
                    <td>
                      <p>{fact.message}</p>
                      {!!fact.elementRefs.length && (
                        <ul className="readiness-references">
                          {fact.elementRefs.map((ref) => (
                            <li key={ref}>
                              <code>{ref}</code>
                            </li>
                          ))}
                        </ul>
                      )}
                      {!!fact.diagnosticCodes.length && (
                        <p className="field-hint">
                          Diagnostic codes: {fact.diagnosticCodes.join(", ")}
                        </p>
                      )}
                      {fact.remediation && (
                        <p>
                          <strong>Next action:</strong> {fact.remediation}
                        </p>
                      )}
                      {fact.facts && <Json value={fact.facts} />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section>
          <h3>Advertised execution limits</h3>
          <p className="field-hint">
            These are the backend-reported bounds for{" "}
            {text(preflight.providerId)}. Limits are rechecked by the backend
            before execution.
          </p>
          {limits.length ? (
            <div className="table-scroll">
              <table aria-label="Advertised execution limits">
                <thead>
                  <tr>
                    <th>Contract limit</th>
                    <th>Exact advertised value</th>
                  </tr>
                </thead>
                <tbody>
                  {limits.map(([name, value]) => (
                    <tr key={name}>
                      <td>
                        <code>{name}</code>
                      </td>
                      <td>{text(value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="notice">
              No execution limits reported for this provider.
            </p>
          )}
        </section>
        <section role="region" aria-label="Readiness diagnostics">
          <h3>Diagnostic explanations</h3>
          {preflight.diagnostics?.length ? (
            <ul className="preflight-diagnostics">
              {preflight.diagnostics.map((diagnostic, index) => (
                <li key={`${diagnostic.code}-${index}`}>
                  <div>
                    <code>{diagnostic.code}</code>{" "}
                    <Badge
                      tone={
                        diagnostic.severity === "error" ? "danger" : "warning"
                      }
                    >
                      {diagnostic.severity || "Unspecified severity"}
                    </Badge>
                  </div>
                  <p>{diagnostic.message}</p>
                  {diagnostic.elementRef && (
                    <p>
                      Affected reference:{" "}
                      <code>{text(diagnostic.elementRef)}</code>
                    </p>
                  )}
                  {Array.isArray(diagnostic.elementRefs) &&
                    diagnostic.elementRefs.length > 0 && (
                      <ul className="readiness-references">
                        {diagnostic.elementRefs
                          .filter(
                            (ref: unknown) =>
                              typeof ref === "string" &&
                              ref !== diagnostic.elementRef,
                          )
                          .map((ref: string) => (
                            <li key={ref}>
                              <code>{ref}</code>
                            </li>
                          ))}
                      </ul>
                    )}
                  {diagnostic.location && (
                    <p className="field-hint">
                      Source: {text(diagnostic.location.documentId)}
                      {diagnostic.location.line
                        ? ` · line ${diagnostic.location.line}`
                        : ""}
                      {diagnostic.pointer ? ` · ${diagnostic.pointer}` : ""}
                    </p>
                  )}
                  {(diagnostic.remediation || diagnostic.correction) && (
                    <p>
                      <strong>Next action:</strong>{" "}
                      {text(diagnostic.remediation || diagnostic.correction)}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>No diagnostics reported for this request.</p>
          )}
        </section>
        <section className="frozen-plan-preview">
          <div className="section-heading">
            <h3>Compiled plan</h3>
            <button
              className="button"
              aria-expanded={inspectPlan}
              disabled={!identity.matches}
              onClick={() => setInspectPlan((value) => !value)}
            >
              {inspectPlan ? "Hide compiled plan" : "Inspect compiled plan"}
            </button>
          </div>
          <p className={identity.matches ? "field-hint" : "notice"}>
            {identity.reason}
          </p>
          {identity.matches && (
            <p className="field-hint">
              The identity fields match the backend's frozen preflight. Platform
              compiler output is read-only. Start rechecks mutable admission
              facts.
            </p>
          )}
          {inspectPlan && identity.matches && (
            <>
              {planText.length <= 1048576 ? (
                <pre
                  tabIndex={0}
                  role="region"
                  aria-label="Compiled execution plan (read-only)"
                  className="compiled-plan-text"
                >
                  {planText}
                </pre>
              ) : (
                <p className="notice">
                  The plan exceeds the 1 MiB inline display bound. Download its
                  frozen JSON for inspection.
                </p>
              )}
              <button className="button" onClick={downloadPlan}>
                Download frozen plan JSON
              </button>
            </>
          )}
        </section>
        {error && (
          <div role="alert" className="notice error">
            <div>
              <strong>{error.code}</strong>
              <p>{error.message}</p>
              {error.diagnostics && <Json value={error.diagnostics} />}
            </div>
          </div>
        )}
        {!canStart &&
          preflight.status === "ready" &&
          !expired &&
          !providerChanged && (
            <p role="status" className="notice">
              Start requires a matching frozen plan and a usable reported result
              for every readiness dimension. Recheck to obtain missing or
              changed facts.
            </p>
          )}
        <div className="form-actions preflight-actions">
          <button className="button" onClick={onClose}>
            Back to draft
          </button>
          <button
            className="button primary"
            disabled={!canStart || pending}
            onClick={() => void perform(onStart)}
          >
            {pending ? "Checking request…" : "Start frozen snapshot"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
