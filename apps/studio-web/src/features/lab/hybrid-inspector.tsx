import { useEffect, useId, useRef, useState } from "react";
import type { Data } from "../../api/types";
import { api, ApiError } from "../../api/client";
import { KeyValues } from "../../app/ui";
import { VariantComparison } from "../deployments/ResolutionPanel";
import { hybridComparison, type ComparisonContext } from "./hybrid-comparison";

function DeclarationTable({
  name,
  kind,
  rows,
}: {
  name: string;
  kind: "targets" | "mappings";
  rows: Data[];
}) {
  const [page, setPage] = useState(0),
    heading = useRef<HTMLHeadingElement>(null),
    title = useId();
  const pages = Math.max(1, Math.ceil(rows.length / 50)),
    shown = rows.slice(page * 50, (page + 1) * 50);
  function move(next: number) {
    setPage(next);
    heading.current?.focus();
  }
  return (
    <section aria-labelledby={title}>
      <h5 id={title} ref={heading} tabIndex={-1}>
        {name}: declared {kind}
      </h5>
      {!rows.length ? (
        <p>No {kind} declared for this variant.</p>
      ) : (
        <>
          <p>
            Showing {page * 50 + 1}–{Math.min(rows.length, (page + 1) * 50)} of{" "}
            {rows.length} declarations.
          </p>
          <table className="data-table resolution-table">
            <thead>
              <tr>
                {(kind === "targets"
                  ? ["Target", "Class", "Capability declarations"]
                  : ["Mapping", "Owner", "Clock relation", "Declared tolerance"]
                ).map((text) => (
                  <th key={text} scope="col">
                    {text}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {shown.map((r, index) => (
                <tr key={index}>
                  {kind === "targets" ? (
                    <>
                      <th scope="row">{r.targetId}</th>
                      <td>{r.targetClass}</td>
                      <td>
                        {r.capabilities.join(", ") || "None shown"}
                        {r.omittedCapabilities > 0 &&
                          `; ${r.omittedCapabilities} unavailable metadata value(s)`}
                      </td>
                    </>
                  ) : (
                    <>
                      <th scope="row">{r.mappingId ?? r.pointer}</th>
                      <td>
                        {r.origin}: {r.ownerRef}
                      </td>
                      <td>
                        {r.sourceClock} → {r.targetClock}
                      </td>
                      <td>
                        {String(r.tolerance.value)} {r.tolerance.unit}; accuracy
                        unmeasured
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          {pages > 1 && (
            <div className="button-row">
              <button
                className="button"
                disabled={page === 0}
                aria-label={`Previous declared ${kind} for ${name}`}
                onClick={() => move(page - 1)}
              >
                Previous {kind}
              </button>
              <span>
                Page {page + 1} of {pages}
              </span>
              <button
                className="button"
                disabled={page + 1 === pages}
                aria-label={`Next declared ${kind} for ${name}`}
                onClick={() => move(page + 1)}
              >
                Next {kind}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

/** One revision-bound backend read; it grants no operation or hardware capability. */
export function HybridInspector({
  context,
  leftName,
  rightName,
}: {
  context: ComparisonContext;
  leftName: string;
  rightName: string;
}) {
  const key = JSON.stringify(context),
    current = useRef(key);
  current.current = key;
  const [state, setState] = useState<{
    key: string;
    value?: Data;
    error?: string;
  } | null>(null);
  const value = state?.key === key ? state.value : null,
    failure = state?.key === key ? state.error : null;
  useEffect(() => {
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 30000);
    void api(
      `/projects/${encodeURIComponent(context.projectId)}/deployment-variants/${encodeURIComponent(context.leftId)}/comparison?otherDocumentId=${encodeURIComponent(context.rightId)}&revision=${context.revision}&providerId=${encodeURIComponent(context.providerId)}`,
      { signal: controller.signal },
    )
      .then((raw) => {
        if (controller.signal.aborted || current.current !== key) return;
        const value = hybridComparison(raw, context);
        if (!controller.signal.aborted && current.current === key)
          setState({ key, value });
      })
      .catch((error: unknown) => {
        if (current.current === key && (!controller.signal.aborted || timedOut))
          setState({
            key,
            error: timedOut
              ? "The comparison read timed out. Choose the comparison again to make a new read."
              : `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "Comparison is unavailable."}`.slice(
                  0,
                  1000,
                ),
          });
      })
      .finally(() => clearTimeout(timer));
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [key]);
  if (failure)
    return (
      <p role="alert" className="control-failure">
        Deployment comparison unavailable: {failure}
      </p>
    );
  if (!value)
    return (
      <p role="status" className="muted">
        Reading both variants at project revision {context.revision}…
      </p>
    );
  const provider = value.provider,
    show = (values: string[] | null) =>
      values === null ? "Unknown" : values.join(", ") || "None declared";
  return (
    <div>
      <VariantComparison
        key={key}
        left={value.left.resolution}
        right={value.right.resolution}
        leftName={leftName}
        rightName={rightName}
      />
      <section aria-label="Time, control and physical evidence">
        <h4>Time, control and physical evidence</h4>
        <p role="status">
          Captured project revision: {value.revision}. Both variants share
          System source {value.sharedSystem.ref}.
        </p>
        <p>
          System source-byte digest:{" "}
          <code>{value.sharedSystem.sourceDigest}</code>. This witnesses the
          captured source; platform semantic and executable identities remain
          separate.
        </p>
        <KeyValues
          values={{
            Provider: `${provider.providerId} ${provider.providerVersion}`,
            "Evidence scope": `${provider.maturity} / ${provider.evidenceScope}`,
            "Declared provider operations": show(provider.operations),
            "Declared provider clocks": show(provider.clockDomains),
            "Declared provider realizations": show(provider.realizationClasses),
            "Declared provider targets": show(provider.targetClasses),
            "Declared native OS": show(provider.supportedHostOS),
            "Declared architectures": show(provider.architectures),
            "Provider availability": provider.available
              ? "Reported available"
              : "Unavailable",
            "Host compatibility": provider.hostCompatible
              ? "Declared compatible"
              : "Unsupported",
            "Synchronization evidence":
              "Unmeasured; no precise latency available",
            "Physical state": "Unknown",
            Cleanup: "Unknown",
            Fidelity: "Unverified",
            "Runtime admission": "Fresh preflight required",
          }}
        />
        <p>
          Target capability strings and mapping tolerances are authored
          declarations. They do not grant provider permission, pause, rewind,
          determinism or measured clock accuracy.
        </p>
        {(provider.limitations || []).map((text: string, i: number) => (
          <p key={i}>Provider limit: {text}</p>
        ))}
        {[
          ["left", leftName],
          ["right", rightName],
        ].map(([side, name]) => (
          <div key={side}>
            <p>
              {name} static findings:{" "}
              {value[side].resolution.diagnostics
                .map((d: Data) => d.code)
                .join(", ") || "None reported; preflight remains required"}
              .
            </p>
            <DeclarationTable
              key={key + side + "targets"}
              name={name}
              kind="targets"
              rows={value[side].declaredTargets}
            />
            <DeclarationTable
              key={key + side + "mappings"}
              name={name}
              kind="mappings"
              rows={value[side].declaredMappings}
            />
          </div>
        ))}
        {value.limitations.map((text: string, i: number) => (
          <p key={i}>{text}</p>
        ))}
      </section>
    </div>
  );
}
