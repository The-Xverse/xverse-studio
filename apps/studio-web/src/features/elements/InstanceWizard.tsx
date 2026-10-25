import { useMemo, useState } from "react";
import type { CatalogEntry, Data } from "../../api/types";
import type { DoAction } from "../../app/App";
import { Badge } from "../../app/ui";
import type { Projection } from "../model/projection";

const IDENTIFIER = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const REALIZATIONS = ["simulated", "virtual", "physical", "hybrid"];
const list = (value: unknown): Data[] => (Array.isArray(value) ? value : []);
const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((v) => typeof v === "string") : [];
const validId = (value: string) => IDENTIFIER.test(value) && value.length <= 63;

interface Definition {
  /** Qualified identity: xdl://namespace/component/name. */
  key: string;
  name: string;
  namespace: string;
  version?: string;
  maturity?: string;
  roles: string[];
  capabilities: string[];
  interfaces: Data[];
  parameters: Data[];
  models: Data[];
  realizationClasses: string[];
  description?: string;
  limitations: string[];
  digest?: string;
  availability?: string;
  source: "project" | "catalog";
}

const resourceDefinition = (
  resource: Data,
  source: Definition["source"],
  entry?: CatalogEntry,
): Definition => ({
  key: `xdl://${resource.metadata?.namespace}/component/${resource.metadata?.name}`,
  name: resource.metadata?.name,
  namespace: resource.metadata?.namespace,
  version: entry?.version || resource.metadata?.version,
  maturity: entry?.maturity || resource.metadata?.provenance?.maturity,
  roles: strings(entry?.roles),
  capabilities: strings(resource.spec?.capabilities),
  interfaces: list(resource.spec?.interfaces),
  parameters: list(resource.spec?.parameters),
  models: list(resource.spec?.models),
  realizationClasses: strings(entry?.realizationClasses),
  description: entry?.description || resource.metadata?.description,
  limitations: [
    ...strings(resource.metadata?.provenance?.limitations),
    ...strings(entry?.limitations),
  ],
  digest: entry?.digest,
  availability: entry?.availability,
  source,
});

function parse(parameter: Data, raw: string | boolean) {
  if (parameter.valueType === "boolean") return Boolean(raw);
  if (parameter.valueType === "integer" || parameter.valueType === "number") {
    const value = Number(raw);
    return raw === "" || !Number.isFinite(value) ? undefined : value;
  }
  return raw;
}

/**
 * Instantiate a reusable Component definition with role/placement, configuration and
 * realization chosen separately. It writes existing XDL kinds only and never builds or runs.
 */
export function InstanceWizard({
  catalog,
  projection,
  initialTemplate = "",
  onSubmit,
  doAction,
}: {
  catalog: CatalogEntry[];
  projection: Projection;
  initialTemplate?: string;
  onSubmit: (edits: Data[]) => Promise<void>;
  doAction: DoAction;
}) {
  const definitions = useMemo<Definition[]>(() => {
    const result = new Map<string, Definition>();
    const entries = catalog.filter((entry) => entry.kind === "component");
    for (const resource of projection.resources)
      if (resource.kind === "Component") {
        // A catalog entry describes a project definition only on exact identity.
        const entry = entries.find(
          (e) =>
            e.resource?.metadata?.namespace === resource.metadata?.namespace &&
            e.resource?.metadata?.name === resource.metadata?.name,
        );
        const definition = resourceDefinition(resource, "project", entry);
        result.set(definition.key, definition);
      }
    for (const entry of entries)
      if (entry.resource?.metadata) {
        const definition = resourceDefinition(entry.resource, "catalog", entry);
        if (!result.has(definition.key)) result.set(definition.key, definition);
      }
    return [...result.values()];
  }, [catalog, projection.resources]);
  const systems = projection.resources.filter((r) => r.kind === "System");
  const [systemDoc, setSystemDoc] = useState(systems[0]?.documentId || ""),
    [query, setQuery] = useState(""),
    [maturity, setMaturity] = useState(""),
    [chosen, setChosen] = useState(""),
    [identifier, setIdentifier] = useState(""),
    [roleFilter, setRoleFilter] = useState(""),
    [nodeId, setNodeId] = useState(""),
    [config, setConfig] = useState<Record<string, string | boolean>>({}),
    [deploymentId, setDeploymentId] = useState(""),
    [realization, setRealization] = useState(""),
    [targetId, setTargetId] = useState(""),
    [artifactIds, setArtifactIds] = useState<string[]>([]),
    [bindingId, setBindingId] = useState("");
  const system = systems.find((s) => s.documentId === systemDoc) || systems[0],
    systemRef = system
      ? `xdl://${system.metadata?.namespace}/system/${system.metadata?.name}`
      : "",
    nodes = list(system?.spec?.nodes).filter((n) => typeof n.id === "string"),
    deployments = projection.deployments.filter(
      (d) =>
        `xdl://${d.spec?.systemRef?.namespace}/system/${d.spec?.systemRef?.name}` ===
        systemRef,
    );
  const shown = definitions.filter(
    (d) =>
      `${d.name} ${d.namespace} ${d.roles.join(" ")} ${d.capabilities.join(" ")} ${d.interfaces.map((i) => i.id).join(" ")}`
        .toLowerCase()
        .includes(query.trim().toLowerCase()) &&
      (!maturity || d.maturity === maturity),
  );
  const initial = definitions.find(
    (d) =>
      d.source === "project" &&
      (d.name === initialTemplate || d.key === initialTemplate),
  );
  // Only a definition the filters still show can be the selection.
  const definition = shown.find((d) => d.key === (chosen || initial?.key)),
    roles = [
      ...new Set([
        ...nodes.flatMap((n) => strings(n.roles)),
        ...(definition?.roles || []),
      ]),
    ],
    role = roles.includes(roleFilter) ? roleFilter : "",
    placeable = nodes.filter((n) => !role || strings(n.roles).includes(role)),
    placement = placeable.some((n) => n.id === nodeId) ? nodeId : "",
    deployment = deployments.find((d) => d.documentId === deploymentId),
    targets = list(deployment?.spec?.targets),
    target = targets.find((t) => t.id === targetId),
    artifacts = list(deployment?.spec?.artifacts),
    effectiveBinding = bindingId || (identifier ? `${identifier}-binding` : "");
  const configurable = (definition?.parameters || []).filter(
      (p) =>
        p.mutability !== "constant" &&
        ["boolean", "integer", "number", "string"].includes(p.valueType),
    ),
    parameterValues: Record<string, unknown> = {},
    invalidParameters: string[] = [];
  for (const parameter of configurable)
    if (parameter.id in config) {
      const value = parse(parameter, config[parameter.id]);
      if (
        value === undefined ||
        (parameter.valueType === "integer" && !Number.isInteger(value))
      )
        invalidParameters.push(parameter.id);
      else if (value !== parameter.default)
        parameterValues[parameter.id] = value;
    }
  const blocked = !definition
    ? "Choose a reusable definition."
    : definition.source !== "project"
      ? "This catalog definition is not in the project; it can be inspected but not instantiated."
      : !validId(identifier)
        ? "Enter a lowercase, hyphenated instance identifier of at most 63 characters."
        : invalidParameters.length
          ? `Enter valid values for: ${invalidParameters.join(", ")}.`
          : deployment && !realization
            ? "Choose a realization class, or choose no realization yet."
            : deployment && !target
              ? "Choose a deployment target, or choose no realization yet."
              : deployment && !validId(effectiveBinding)
                ? "Enter a lowercase, hyphenated binding identifier of at most 63 characters."
                : "";
  const edits: Data[] = blocked
    ? []
    : [
        {
          kind: "add_element",
          documentId: system?.documentId,
          templateId: definition!.key,
          elementId: identifier,
          ...(placement ? { nodeId: placement } : {}),
          ...(Object.keys(parameterValues).length ? { parameterValues } : {}),
        },
        ...(deployment
          ? [
              {
                kind: "add_binding",
                documentId: deployment.documentId,
                bindingId: effectiveBinding,
                elementId: identifier,
                targetId,
                realizationClass: realization,
                ...(artifactIds.length ? { artifactIds } : {}),
              },
            ]
          : []),
      ];
  return (
    <form
      className="instance-wizard"
      onSubmit={(event) => {
        event.preventDefault();
        if (!blocked)
          void doAction("Adding element instance", () => onSubmit(edits));
      }}
    >
      {systems.length > 1 && (
        <label>
          System
          <select
            value={system?.documentId}
            onChange={(e) => {
              setSystemDoc(e.target.value);
              setNodeId("");
              setDeploymentId("");
            }}
          >
            {systems.map((s) => (
              <option key={s.documentId} value={s.documentId}>
                {s.metadata?.namespace}/{s.metadata?.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <fieldset>
        <legend>1. Reusable definition</legend>
        <div className="wizard-filters">
          <label>
            Search definitions
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Name, namespace, role, capability or interface"
            />
          </label>
          <label>
            Maturity
            <select
              value={maturity}
              onChange={(e) => setMaturity(e.target.value)}
            >
              <option value="">Any maturity</option>
              {[
                ...new Set(definitions.map((d) => d.maturity).filter(Boolean)),
              ].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div
          role="radiogroup"
          aria-label="Definitions"
          className="wizard-options"
        >
          {shown.length === 0 && (
            <p className="field-hint">No definitions match these filters.</p>
          )}
          {shown.map((d) => (
            <label key={d.key} className="wizard-option">
              <input
                type="radio"
                name="definition"
                value={d.key}
                checked={definition?.key === d.key}
                onChange={() => {
                  setChosen(d.key);
                  setConfig({});
                }}
              />
              <span>
                <strong>{d.name}</strong> <code>{d.namespace}</code>{" "}
                {d.version && <code>{d.version}</code>}{" "}
                {d.maturity && <Badge>{d.maturity}</Badge>}{" "}
                <Badge tone={d.source === "project" ? "info" : "warning"}>
                  {d.source === "project" ? "in project" : "catalog only"}
                </Badge>
                <small>
                  {d.roles.length
                    ? `Suggested role: ${d.roles.join(", ")}`
                    : "No suggested role"}
                  {d.capabilities.length
                    ? ` · capabilities: ${d.capabilities.join(", ")}`
                    : ""}
                </small>
              </span>
            </label>
          ))}
        </div>
        {definition && (
          <div className="wizard-details" aria-label="Definition details">
            <p>{definition.description || "No description declared."}</p>
            <p>
              Interfaces:{" "}
              {definition.interfaces.length
                ? definition.interfaces
                    .map(
                      (i) =>
                        `${i.id} (${i.direction}, unit ${i.unitSemantics ?? "–"})`,
                    )
                    .join("; ")
                : "none declared"}
            </p>
            <p>
              Requirements:{" "}
              {definition.models.length
                ? definition.models
                    .map((m) => `model ${m.id} → ${m.externalRef}`)
                    .join("; ")
                : "no model artifacts required"}
            </p>
            <p>
              Declared realization support:{" "}
              {definition.realizationClasses.join(", ") || "not declared"}
              {definition.availability
                ? ` · catalog availability: ${definition.availability}`
                : ""}
            </p>
            {definition.digest && (
              <p>
                Catalog digest <code>{definition.digest}</code>
              </p>
            )}
            {definition.limitations.length > 0 && (
              <ul>
                {definition.limitations.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </fieldset>
      <fieldset>
        <legend>2. Instance identity</legend>
        <label>
          Instance identifier
          <input
            required
            value={identifier}
            maxLength={63}
            pattern="[a-z][a-z0-9]*(-[a-z0-9]+)*"
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="new-instance"
          />
        </label>
        <p className="field-hint">
          A new, distinct System element. The reusable definition is referenced,
          not copied or changed.
        </p>
      </fieldset>
      <fieldset>
        <legend>3. Role and placement</legend>
        <label>
          Role filter
          <select value={role} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">Any role</option>
            {roles.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Placement node
          <select value={placement} onChange={(e) => setNodeId(e.target.value)}>
            <option value="">Not placed on a node</option>
            {placeable.map((n) => (
              <option key={n.id} value={n.id}>
                {n.id} ({strings(n.roles).join(", ") || "no role"})
              </option>
            ))}
          </select>
        </label>
        <p className="field-hint">
          In XDL a role belongs to the node; choosing the node places the
          instance. Suggested roles are guidance, not inference.
        </p>
      </fieldset>
      <fieldset>
        <legend>4. Configuration</legend>
        {!definition || definition.parameters.length === 0 ? (
          <p className="field-hint">
            The definition declares no configuration parameters.
          </p>
        ) : (
          definition.parameters.map((p) => {
            const editable = configurable.includes(p),
              label = `${p.id} (${p.valueType}, unit ${p.unitSemantics})`;
            return (
              <label key={p.id}>
                {label}
                {p.valueType === "boolean" ? (
                  <input
                    type="checkbox"
                    disabled={!editable}
                    checked={Boolean(config[p.id] ?? p.default)}
                    onChange={(e) =>
                      setConfig((old) => ({ ...old, [p.id]: e.target.checked }))
                    }
                  />
                ) : (
                  <input
                    type={
                      p.valueType === "number" || p.valueType === "integer"
                        ? "number"
                        : "text"
                    }
                    step={p.valueType === "integer" ? 1 : "any"}
                    disabled={!editable}
                    value={String(config[p.id] ?? p.default ?? "")}
                    onChange={(e) =>
                      setConfig((old) => ({ ...old, [p.id]: e.target.value }))
                    }
                  />
                )}
                <small>
                  {p.description || "No description declared."}
                  {p.default !== undefined
                    ? ` Default ${JSON.stringify(p.default)}.`
                    : ""}
                  {p.constraints
                    ? ` Constraints ${JSON.stringify(p.constraints)}.`
                    : ""}
                  {!editable
                    ? p.mutability === "constant"
                      ? " Constant."
                      : " Edit this value in source."
                    : ""}
                </small>
              </label>
            );
          })
        )}
      </fieldset>
      <fieldset>
        <legend>5. Realization (optional)</legend>
        <label>
          Deployment variant
          <select
            value={deployment?.documentId || ""}
            onChange={(e) => {
              setDeploymentId(e.target.value);
              setRealization("");
              setTargetId("");
              setArtifactIds([]);
            }}
          >
            <option value="">No realization yet</option>
            {deployments.map((d) => (
              <option key={d.documentId} value={d.documentId}>
                {d.metadata?.name}
              </option>
            ))}
          </select>
        </label>
        {deployment && (
          <>
            <div
              role="radiogroup"
              aria-label="Realization class"
              className="wizard-inline"
            >
              {REALIZATIONS.map((value) => (
                <label key={value}>
                  <input
                    type="radio"
                    name="realization"
                    value={value}
                    checked={realization === value}
                    onChange={() => setRealization(value)}
                  />
                  {value}
                  {definition?.realizationClasses.length &&
                  !definition.realizationClasses.includes(value) ? (
                    <small> (not declared by the definition)</small>
                  ) : null}
                </label>
              ))}
            </div>
            <label>
              Deployment target
              <select
                value={target?.id || ""}
                onChange={(e) => setTargetId(e.target.value)}
              >
                <option value="">Select a target</option>
                {targets.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.id} ({t.targetClass}
                    {strings(t.capabilities).length
                      ? `: ${strings(t.capabilities).join(", ")}`
                      : ""}
                    )
                  </option>
                ))}
              </select>
            </label>
            <fieldset className="wizard-artifacts">
              <legend>Chosen artifacts</legend>
              {artifacts.length === 0 && (
                <p className="field-hint">
                  This deployment declares no artifacts.
                </p>
              )}
              {artifacts.map((a) => (
                <label key={a.id}>
                  <input
                    type="checkbox"
                    checked={artifactIds.includes(a.id)}
                    onChange={(e) =>
                      setArtifactIds((old) =>
                        e.target.checked
                          ? [...old, a.id]
                          : old.filter((id) => id !== a.id),
                      )
                    }
                  />
                  {a.id}{" "}
                  <small>
                    {a.artifactKind} {a.version}
                  </small>
                </label>
              ))}
            </fieldset>
            <label>
              Binding identifier
              <input
                value={bindingId}
                maxLength={63}
                pattern="[a-z][a-z0-9]*(-[a-z0-9]+)*"
                placeholder={effectiveBinding || "instance-binding"}
                onChange={(e) => setBindingId(e.target.value)}
              />
            </label>
            <p className="field-hint">
              Realization is a deployment binding; the authoritative validator
              decides whether a class fits the target. Choosing an artifact
              records a choice; it does not satisfy or build a requirement.
            </p>
          </>
        )}
      </fieldset>
      <section className="wizard-review" aria-label="Review">
        <h4>Review</h4>
        {blocked ? (
          <p role="status" id="wizard-blocked">
            {blocked}
          </p>
        ) : (
          <ol>
            {edits.map((edit, index) => (
              <li key={index}>
                {edit.kind === "add_element"
                  ? `Add instance ${edit.elementId} of ${definition!.name}${edit.nodeId ? ` on node ${edit.nodeId}` : ", not placed"}${edit.parameterValues ? ` with ${Object.keys(edit.parameterValues).join(", ")} configured` : ""}`
                  : `Bind ${edit.elementId} as ${edit.realizationClass} to target ${edit.targetId} (${edit.bindingId}) with lifecycle ${Object.keys(target?.lifecycle || {}).join(", ") || "as declared"}`}
              </li>
            ))}
          </ol>
        )}
        <p className="field-hint">
          One authoritative transaction. Nothing is built, flashed or executed,
          and adding an instance grants no provider support.
        </p>
      </section>
      <div className="form-actions">
        <button
          className="button primary"
          disabled={Boolean(blocked)}
          aria-describedby={blocked ? "wizard-blocked" : undefined}
        >
          Add instance
        </button>
      </div>
    </form>
  );
}
