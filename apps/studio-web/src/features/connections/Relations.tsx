import { useEffect, useState } from "react";
import type { Data } from "../../api/types";
import { Badge } from "../../app/ui";

// Communication, model coupling, deployment and traceability are different relations with different
// semantics and actions; none can be drawn or connected as another (FR-037).

const CONTRACTS = "io.xverse.studio.connections";

/** Declares or removes a flow's owned contract; admission and the provider decide the verdict. */
export function FlowContractForm({
  flows,
  interfaces,
  report,
  edit,
}: {
  flows: Data[];
  interfaces: Data[];
  report: Data | null;
  edit: (edits: Data[]) => Promise<unknown>;
}) {
  const [flowId, setFlowId] = useState(""),
    flow = flows.find((f) => f.id === flowId),
    current = flow?.extensions?.[CONTRACTS] || {},
    unit =
      interfaces.find((i) => i.id === flow?.interfaceId)?.unitSemantics || "",
    [delay, setDelay] = useState(false),
    [convert, setConvert] = useState(false),
    [toUnit, setToUnit] = useState(""),
    [scale, setScale] = useState("1"),
    [offset, setOffset] = useState("0");
  useEffect(() => {
    // Show the authored contract of the chosen flow, never a previous flow's draft.
    setDelay(current.causality?.kind === "unit-delay");
    setConvert(!!current.converter);
    setToUnit(current.converter?.toUnit || "");
    setScale(String(current.converter?.scale ?? 1));
    setOffset(String(current.converter?.offset ?? 0));
  }, [flowId, JSON.stringify(current)]);
  const verdict = report?.connections.find((c: Data) =>
      c.ref.endsWith(`#${flowId}`),
    ),
    supported = report?.admittedContracts || {};
  return (
    <form
      className="flow-contract-form"
      aria-label="Flow contract"
      onSubmit={(e) => {
        e.preventDefault();
        void edit([
          {
            kind: "set_flow_contract",
            flowId,
            ...(delay ? { causality: "unit-delay" } : {}),
            ...(convert
              ? {
                  converter: {
                    fromUnit: unit,
                    toUnit,
                    scale: Number(scale),
                    offset: Number(offset),
                  },
                }
              : {}),
          },
        ]);
      }}
    >
      <h4>Flow contract</h4>
      <p className="field-hint">
        Declares an owned contract on one flow. The selected provider{" "}
        {report?.providerId ? <code>{report.providerId}</code> : null} declares
        converters {supported.converter ? "yes" : "no"} and causality{" "}
        {supported.causality ? "yes" : "no"}; admission judges the declaration,
        and Studio never converts or delays anything itself.
      </p>
      <label>
        Flow
        <select value={flowId} onChange={(e) => setFlowId(e.target.value)}>
          <option value="">Choose a flow</option>
          {flows.map((f) => (
            <option key={f.id} value={f.id}>
              {f.id} · {f.interfaceId}
            </option>
          ))}
        </select>
      </label>
      <fieldset disabled={!flow}>
        <legend>Causality</legend>
        <label className="resource-choice">
          <input
            type="checkbox"
            checked={delay}
            onChange={(e) => setDelay(e.target.checked)}
          />
          Unit delay: the destination uses the value from the previous step
        </label>
      </fieldset>
      <fieldset disabled={!flow}>
        <legend>Linear converter y = scale·x + offset</legend>
        <label className="resource-choice">
          <input
            type="checkbox"
            checked={convert}
            disabled={!unit}
            onChange={(e) => setConvert(e.target.checked)}
          />
          {unit ? (
            <>
              Declare an explicit converter from <code>{unit}</code>
            </>
          ) : (
            "The flow's interface declares no unit, so no converter can map from it."
          )}
        </label>
        {current.converter && current.converter.fromUnit !== unit && (
          <p className="control-failure" role="note">
            The authored converter maps from{" "}
            <code>{String(current.converter.fromUnit)}</code>, not the interface
            unit; admission rejects it. Saving replaces it with a mapping from{" "}
            <code>{unit}</code>.
          </p>
        )}
        <label>
          Target unit
          <input
            value={toUnit}
            disabled={!convert}
            required={convert}
            maxLength={64}
            onChange={(e) => setToUnit(e.target.value)}
          />
        </label>
        <label>
          Scale
          <input
            type="number"
            step="any"
            value={scale}
            disabled={!convert}
            required={convert}
            onChange={(e) => setScale(e.target.value)}
          />
        </label>
        <label>
          Offset
          <input
            type="number"
            step="any"
            value={offset}
            disabled={!convert}
            required={convert}
            onChange={(e) => setOffset(e.target.value)}
          />
        </label>
      </fieldset>
      {verdict && (
        <p role="status">
          Current admission of {flowId}: <Badge>{verdict.admission}</Badge>
        </p>
      )}
      <button className="button" disabled={!flow}>
        Save flow contract
      </button>
    </form>
  );
}

/** The four relation kinds, each with its own style, meaning and permitted action. */
export function RelationKinds({
  projection,
  report,
  onOpenView,
}: {
  projection: Data;
  report: Data | null;
  onOpenView?: (view: string) => void;
}) {
  const bindings: Data[] = (projection.deployments || []).flatMap(
      (deployment: Data) =>
        (deployment.spec?.bindings || []).map((binding: Data) => ({
          deployment: deployment.metadata?.name,
          ...binding,
        })),
    ),
    traces: Data[] = (projection.resources || []).flatMap((resource: Data) =>
      (resource.metadata?.traceability || []).map((link: Data) => ({
        owner: `${resource.kind} ${resource.metadata?.name}`,
        ...link,
      })),
    ),
    couplings: Data[] = report?.couplings || [];
  return (
    <section
      className="relation-kinds"
      aria-labelledby="relation-kinds-heading"
    >
      <h3 id="relation-kinds-heading">Relations by kind</h3>
      <div className="relation-kind relation-communication">
        <h4>
          Communication{" "}
          <Badge tone="info">{projection.connections.length}</Badge>
        </h4>
        <p>
          Declared data flows between endpoints. Action: connect compatible
          endpoints in this view. Communication is never a physical solver.
        </p>
      </div>
      <div className="relation-kind relation-coupling">
        <h4>
          Model coupling{" "}
          <Badge tone={couplings.length ? "danger" : "neutral"}>
            {couplings.length}
          </Badge>
        </h4>
        {couplings.length ? (
          <ul>
            {couplings.map((c: Data) => (
              <li key={c.ref}>
                <code>{c.ref.split("#")[1]}</code> {c.status}: {c.message}
              </li>
            ))}
          </ul>
        ) : (
          <p>
            No model couplings are declared. No coupling solver is admitted, so
            a declared coupling would block execution; it cannot be created by
            connecting endpoints.
          </p>
        )}
      </div>
      <div className="relation-kind relation-deployment">
        <h4>
          Deployment <Badge tone="info">{bindings.length}</Badge>
        </h4>
        <ul>
          {bindings.map((b) => (
            <li key={`${b.deployment}:${b.id}`}>
              {b.logicalRef?.element} → {b.targetId} ({b.realizationClass}) in{" "}
              {b.deployment}
            </li>
          ))}
        </ul>
        {onOpenView && (
          <button
            type="button"
            className="small-button"
            onClick={() => onOpenView("Deployment")}
          >
            Edit placement in Deployment
          </button>
        )}
      </div>
      <div className="relation-kind relation-traceability">
        <h4>
          Traceability <Badge tone="neutral">{traces.length}</Badge>
        </h4>
        {traces.length ? (
          <ul>
            {traces.map((t, index) => (
              <li key={index}>
                {t.owner}
                {t.elementId ? `#${t.elementId}` : ""} {t.relation}{" "}
                <code>{t.ref}</code> ({t.revision})
              </li>
            ))}
          </ul>
        ) : (
          <p>No traceability links are authored.</p>
        )}
        <p className="field-hint">
          A trace link records a reference; it is never fetched and never proves
          a result.
        </p>
      </div>
    </section>
  );
}
