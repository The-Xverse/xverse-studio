import { useState } from "react";
import { useTerm } from "../profiles/presentation";
import type { Data } from "../../api/types";
import type { Projection } from "../model/projection";
import type { SourceTarget } from "../model/Views";
import { Modal, Badge } from "../../app/ui";
type ItemKind = "step" | "fault" | "observer" | "metric";
const collections = {
  step: "steps",
  fault: "faults",
  observer: "observers",
  metric: "metrics",
};
const names = {
  step: "Stimulus step",
  fault: "Fault intent",
  observer: "Observer",
  metric: "Metric intent",
};
const maturityValues = [
  "observed",
  "inferred",
  "architectural-target",
  "prototype",
  "verified",
];
function object(value: string) {
  const parsed = JSON.parse(value);
  if (
    !parsed ||
    typeof parsed !== "object" ||
    Array.isArray(parsed) ||
    !Object.keys(parsed).length
  )
    throw new Error(
      "Supply a nonempty JSON object. Opaque fields are preserved as authored intent.",
    );
  return parsed;
}
function reference(resource: Data) {
  return `xdl://${resource.metadata.namespace}/${resource.kind.toLowerCase()}/${resource.metadata.name}`;
}
export function ScenarioAuthoring({
  scenario,
  projection,
  limits,
  edit,
  onSource,
}: {
  scenario: Data;
  projection: Projection;
  limits: Data;
  edit: (edits: Data[]) => Promise<unknown>;
  onSource: (target?: SourceTarget) => void;
}) {
  const term = useTerm();
  const [selection, setSelection] = useState<{
      kind: ItemKind;
      item?: Data;
    } | null>(null),
    [conditions, setConditions] = useState(false),
    [remove, setRemove] = useState<{ kind: ItemKind; item: Data } | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const spec = scenario.spec,
    ref = reference(scenario);
  const source = (kind?: ItemKind, item?: Data) =>
    onSource({
      documentId: scenario.documentId,
      ref: item ? ref + "#" + item.id : ref,
      ...(item && kind
        ? { elementId: item.id, collection: collections[kind] }
        : {}),
    });
  async function removeItem() {
    if (!remove) return;
    setBusy(true);
    setError("");
    try {
      await edit([
        {
          kind: "remove_scenario_item",
          documentId: scenario.documentId,
          elementRef: ref + "#" + remove.item.id,
          itemKind: remove.kind,
          itemId: remove.item.id,
        },
      ]);
      setRemove(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Removal failed.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      className="panel scenario-authoring"
      aria-label="Scenario authoring"
    >
      <div className="section-heading">
        <div>
          <h3>Author {term("Scenario").toLowerCase()} intent</h3>
          <p>
            Edits create a validated draft revision. Existing run inputs stay
            frozen.
          </p>
        </div>
        <button className="button" onClick={() => setConditions(true)}>
          Edit initial conditions
        </button>
      </div>
      <p className="notice">
        Actions, fault activation/recovery and metric acceptance are authored
        intent. They are not runtime permissions, observed effects or evaluated
        assertions. Unsupported schedules block preflight.
      </p>
      <div className="scenario-item-grid">
        {(Object.keys(collections) as ItemKind[]).map((kind) => {
          const rows: Data[] = spec[collections[kind]] || [],
            limit = limits[collections[kind]];
          return (
            <section
              key={kind}
              className="scenario-item-group"
              aria-label={names[kind] + " authoring"}
            >
              <div className="section-heading">
                <h4>
                  {names[kind]}s{" "}
                  <Badge>
                    {rows.length}
                    {limit ? ` / ${limit}` : ""}
                  </Badge>
                </h4>
                <button
                  className="small-button"
                  disabled={!!limit && rows.length >= limit}
                  onClick={() => setSelection({ kind })}
                >
                  Add {names[kind].toLowerCase()}
                </button>
              </div>
              {rows.map((item) => (
                <article key={item.id}>
                  <code>{item.id}</code>
                  <div className="scenario-row-actions">
                    <button
                      className="small-button"
                      aria-label={`Edit ${kind} ${item.id}`}
                      onClick={() => setSelection({ kind, item })}
                    >
                      Edit
                    </button>
                    <button
                      className="small-button"
                      aria-label={`View source for ${kind} ${item.id}`}
                      onClick={() => source(kind, item)}
                    >
                      Source
                    </button>
                    <button
                      className="small-button"
                      aria-label={`Remove ${kind} ${item.id}`}
                      disabled={kind !== "fault" && rows.length <= 1}
                      title={
                        kind !== "fault" && rows.length <= 1
                          ? "The public Scenario schema requires at least one item in this collection."
                          : undefined
                      }
                      onClick={() => {
                        setError("");
                        setRemove({ kind, item });
                      }}
                    >
                      Remove
                    </button>
                  </div>
                </article>
              ))}
              {!rows.length && (
                <p className="field-hint">
                  No {names[kind].toLowerCase()} declared.
                </p>
              )}
            </section>
          );
        })}
      </div>
      <p className="field-hint">
        Clock and target choices come from this Scenario’s selected resources.
        The public XDL validator decides reference validity; a provider must
        separately admit execution.
      </p>
      {selection && (
        <Modal
          title={`${selection.item ? "Edit" : "Add"} ${names[selection.kind].toLowerCase()}`}
          wide
          onClose={() => setSelection(null)}
        >
          <ScenarioItemForm
            key={selection.kind + ":" + (selection.item?.id || "new")}
            scenario={scenario}
            projection={projection}
            kind={selection.kind}
            item={selection.item}
            onSave={async (properties, itemId) => {
              await edit([
                {
                  kind: selection.item
                    ? "update_scenario_item"
                    : "add_scenario_item",
                  documentId: scenario.documentId,
                  elementRef: selection.item ? ref + "#" + itemId : ref,
                  itemKind: selection.kind,
                  itemId,
                  properties,
                },
              ]);
              setSelection(null);
            }}
          />
        </Modal>
      )}
      {conditions && (
        <Modal
          title="Edit scenario conditions"
          wide
          onClose={() => setConditions(false)}
        >
          <ConditionsForm
            spec={spec}
            onSave={async (properties) => {
              await edit([
                {
                  kind: "set_scenario_conditions",
                  documentId: scenario.documentId,
                  elementRef: ref,
                  properties,
                },
              ]);
              setConditions(false);
            }}
          />
        </Modal>
      )}
      {remove && (
        <Modal
          title="Remove authored scenario item"
          onClose={() => setRemove(null)}
        >
          <p>
            Remove{" "}
            <code>
              {ref}#{remove.item.id}
            </code>{" "}
            from the current draft? This does not alter historical snapshots or
            stop any run. References are revalidated before saving.
          </p>
          {error && (
            <p role="alert" className="error-banner">
              {error}
            </p>
          )}
          <div className="form-actions">
            <button className="button" onClick={() => setRemove(null)}>
              Keep item
            </button>
            <button
              className="button danger-button"
              disabled={busy}
              onClick={() => void removeItem()}
            >
              Remove draft item
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
function ConditionsForm({
  spec,
  onSave,
}: {
  spec: Data;
  onSave: (properties: Data) => Promise<void>;
}) {
  const [initial, setInitial] = useState(
      JSON.stringify(spec.initialConditions, null, 2),
    ),
    [acceptance, setAcceptance] = useState(spec.acceptanceIntent || ""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setError("");
        setBusy(true);
        void (async () => {
          try {
            await onSave({
              initialConditions: object(initial),
              ...(acceptance ? { acceptanceIntent: acceptance } : {}),
            });
          } catch (e) {
            setError(
              e instanceof Error ? e.message : "Saving conditions failed.",
            );
          } finally {
            setBusy(false);
          }
        })();
      }}
    >
      <label>
        Initial conditions (JSON object)
        <textarea
          required
          rows={8}
          maxLength={65536}
          aria-label="Initial conditions (JSON object)"
          value={initial}
          onChange={(e) => setInitial(e.target.value)}
          spellCheck={false}
        />
      </label>
      <label>
        Scenario acceptance intent
        <textarea
          required={!!spec.acceptanceIntent}
          rows={3}
          maxLength={16000}
          aria-label="Scenario acceptance intent"
          value={acceptance}
          onChange={(e) => setAcceptance(e.target.value)}
        />
      </label>
      <p className="field-hint">
        These values remain opaque XDL intent unless an admitted
        profile/provider defines their meaning. This does not create a passing
        assertion.
      </p>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="form-actions">
        <button className="button primary" disabled={busy}>
          Save scenario conditions
        </button>
      </div>
    </form>
  );
}
function ScenarioItemForm({
  scenario,
  projection,
  kind,
  item,
  onSave,
}: {
  scenario: Data;
  projection: Projection;
  kind: ItemKind;
  item?: Data;
  onSave: (properties: Data, itemId: string) => Promise<void>;
}) {
  const spec = scenario.spec,
    system = projection.resources.find(
      (r) =>
        r.kind === "System" &&
        r.metadata.namespace === spec.systemRef.namespace &&
        r.metadata.name === spec.systemRef.name,
    ),
    deployment = projection.resources.find(
      (r) =>
        r.kind === "Deployment" &&
        r.metadata.namespace === spec.deploymentRef?.namespace &&
        r.metadata.name === spec.deploymentRef?.name,
    );
  const targets = [system, deployment].filter(Boolean).flatMap((resource) =>
    [
      "nodes",
      "componentInstances",
      "devices",
      "sensors",
      "actuators",
      "models",
      "interfaces",
      "endpoints",
      "flows",
      "networks",
      "targets",
      "bindings",
      "artifacts",
    ].flatMap((collection) =>
      (resource!.spec[collection] || [])
        .filter((row: Data) => typeof row.id === "string")
        .map((row: Data) => ({
          key: reference(resource!) + "#" + row.id,
          label: `${resource!.kind} ${resource!.metadata.name} / ${row.id} (${collection})`,
          ref: {
            apiVersion: resource!.apiVersion,
            kind: resource!.kind,
            namespace: resource!.metadata.namespace,
            name: resource!.metadata.name,
            element: row.id,
          },
        })),
    ),
  );
  const originalTarget = item?.targetRef
    ? `xdl://${item.targetRef.namespace}/${item.targetRef.kind.toLowerCase()}/${item.targetRef.name}#${item.targetRef.element}`
    : "";
  const clocks: Data[] = system?.spec.timeDomains || [];
  const [id, setId] = useState(item?.id || ""),
    [target, setTarget] = useState(originalTarget),
    [clock, setClock] = useState(item?.timeDomainId || clocks[0]?.id || ""),
    [actionKind, setActionKind] = useState(item?.actionKind || "set_parameter"),
    [at, setAt] = useState(String(item?.schedule?.at ?? 0)),
    [scheduleUnit, setScheduleUnit] = useState(item?.schedule?.unit || "s"),
    [action, setAction] = useState(
      JSON.stringify(
        item?.action || { parameter: "target", value: 1 },
        null,
        2,
      ),
    ),
    [faultKind, setFaultKind] = useState(item?.faultKind || "provider-defined"),
    [activation, setActivation] = useState(item?.activation || ""),
    [recovery, setRecovery] = useState(item?.recovery || ""),
    [maturity, setMaturity] = useState(item?.maturity || "prototype"),
    [sampling, setSampling] = useState(item?.samplingIntent || ""),
    [payload, setPayload] = useState(
      item?.payloadSchema || "urn:xverse:studio:normalized-scalar:v1",
    ),
    [unit, setUnit] = useState(item?.unitSemantics || "1"),
    [sink, setSink] = useState(
      item?.evidenceSinkRef || "urn:xverse:studio:reference:evidence",
    ),
    [observers, setObservers] = useState<string[]>(item?.observerIds || []),
    [calculation, setCalculation] = useState(
      item?.calculationRef || "urn:example:metric:opaque",
    ),
    [acceptance, setAcceptance] = useState(item?.acceptance || ""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const targetRef = targets.find((t) => t.key === target)?.ref;
      if (kind !== "metric" && !targetRef)
        throw new Error(
          "Select a declared target from this Scenario's System or Deployment.",
        );
      const properties =
        kind === "step"
          ? {
              targetRef,
              timeDomainId: clock,
              actionKind,
              schedule: {
                ...item?.schedule,
                at: Number(at),
                unit: scheduleUnit,
              },
              action: object(action),
            }
          : kind === "fault"
            ? { targetRef, faultKind, activation, recovery, maturity }
            : kind === "observer"
              ? {
                  targetRef,
                  timeDomainId: clock,
                  samplingIntent: sampling,
                  payloadSchema: payload,
                  unitSemantics: unit,
                  evidenceSinkRef: sink,
                }
              : {
                  observerIds: observers,
                  calculationRef: calculation,
                  unitSemantics: unit,
                  acceptance,
                };
      await onSave(properties, id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The item could not be saved.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="scenario-item-form" onSubmit={(e) => void save(e)}>
      <label>
        Scenario item identifier
        <input
          required
          disabled={!!item}
          pattern="[a-z][a-z0-9]*(-[a-z0-9]+)*"
          maxLength={63}
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
      </label>
      {kind !== "metric" && (
        <label>
          Declared target
          <select
            aria-label="Declared target"
            required
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="">Choose a declared target</option>
            {targets.map((t) => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
      )}
      {(kind === "step" || kind === "observer") && (
        <label>
          Declared clock domain
          <select
            aria-label="Declared clock domain"
            required
            value={clock}
            onChange={(e) => setClock(e.target.value)}
          >
            {clocks.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id} · {c.clockClass}
              </option>
            ))}
          </select>
        </label>
      )}
      {kind === "step" ? (
        <>
          <div className="two-fields">
            <label>
              Scheduled at
              <input
                required
                min={0}
                step="any"
                type="number"
                value={at}
                onChange={(e) => setAt(e.target.value)}
              />
            </label>
            <label>
              Schedule unit
              <input
                required
                value={scheduleUnit}
                onChange={(e) => setScheduleUnit(e.target.value)}
              />
            </label>
          </div>
          <label>
            Action kind
            <input
              required
              maxLength={120}
              value={actionKind}
              onChange={(e) => setActionKind(e.target.value)}
            />
          </label>
          <label>
            Action payload (JSON object)
            <textarea
              required
              rows={6}
              maxLength={65536}
              spellCheck={false}
              aria-label="Action payload (JSON object)"
              value={action}
              onChange={(e) => setAction(e.target.value)}
            />
          </label>
          <p className="field-hint">
            An action kind and payload describe requested intent. Text is never
            executed as a shell command. Provider support and effective frozen
            inputs are checked at preflight.
          </p>
        </>
      ) : kind === "fault" ? (
        <>
          <label>
            Fault kind
            <input
              required
              maxLength={120}
              value={faultKind}
              onChange={(e) => setFaultKind(e.target.value)}
            />
          </label>
          <label>
            Activation intent
            <textarea
              required
              rows={3}
              maxLength={16000}
              aria-label="Activation intent"
              value={activation}
              onChange={(e) => setActivation(e.target.value)}
            />
          </label>
          <label>
            Recovery intent
            <textarea
              required
              rows={3}
              maxLength={16000}
              aria-label="Recovery intent"
              value={recovery}
              onChange={(e) => setRecovery(e.target.value)}
            />
          </label>
          <label>
            Fault maturity
            <select
              aria-label="Fault maturity"
              value={maturity}
              onChange={(e) => setMaturity(e.target.value)}
            >
              {maturityValues.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <p className="field-hint">
            The admitted schema stores activation and recovery as opaque
            strings. They are not parsed into a schedule or device instruction.
            Observed effect requires separate provider evidence.
          </p>
        </>
      ) : kind === "observer" ? (
        <>
          <label>
            Sampling intent
            <textarea
              required
              rows={3}
              maxLength={16000}
              aria-label="Sampling intent"
              value={sampling}
              onChange={(e) => setSampling(e.target.value)}
            />
          </label>
          <label>
            Payload schema reference
            <input
              required
              maxLength={512}
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
            />
          </label>
          <label>
            Evidence sink reference
            <input
              required
              maxLength={512}
              value={sink}
              onChange={(e) => setSink(e.target.value)}
            />
          </label>
          <label>
            Observer unit semantics
            <input
              required
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
            />
          </label>
        </>
      ) : (
        <>
          <fieldset>
            <legend>Declared observers</legend>
            {(spec.observers || []).map((o: Data) => (
              <label className="check-label" key={o.id}>
                <input
                  type="checkbox"
                  checked={observers.includes(o.id)}
                  onChange={(e) =>
                    setObservers(
                      e.target.checked
                        ? [...observers, o.id]
                        : observers.filter((v) => v !== o.id),
                    )
                  }
                />
                {o.id}
              </label>
            ))}
          </fieldset>
          <label>
            Calculation reference (inert)
            <input
              required
              maxLength={512}
              value={calculation}
              onChange={(e) => setCalculation(e.target.value)}
            />
          </label>
          <label>
            Metric unit semantics
            <input
              required
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
            />
          </label>
          <label>
            Metric acceptance intent
            <textarea
              required
              rows={3}
              maxLength={16000}
              aria-label="Metric acceptance intent"
              value={acceptance}
              onChange={(e) => setAcceptance(e.target.value)}
            />
          </label>
          <p className="field-hint">
            Metric intent is not an assertion verdict. Use a frozen admitted
            bounded evaluation definition to assess actual evidence.
          </p>
        </>
      )}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="form-actions">
        <button
          className="button primary"
          disabled={busy || (kind === "metric" && !observers.length)}
        >
          {busy
            ? "Validating intent…"
            : item
              ? "Save scenario item"
              : "Add scenario item"}
        </button>
      </div>
    </form>
  );
}
