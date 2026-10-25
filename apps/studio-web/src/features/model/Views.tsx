import { useState, useEffect, useMemo, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  MarkerType,
} from "@xyflow/react";
import type { NodeProps, Node } from "@xyflow/react";
import type { Data, Project, Parameter } from "../../api/types";
import { api } from "../../api/client";
import type { DoAction } from "../../app/App";
import { Icon, Badge, Empty, Json, KeyValues } from "../../app/ui";
import type { Projection, ElementProjection } from "./projection";
import { documentContent, textRef } from "./projection";
function ElementNode({ data, selected }: NodeProps<Node<Data>>) {
  return (
    <div className={`element-node ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-top">
        <span className="node-symbol">
          <Icon
            name={
              data.role?.includes("observer")
                ? "results"
                : data.role?.includes("control")
                  ? "settings"
                  : "model"
            }
            size={18}
          />
        </span>
        <span className="node-type">{data.role || "Component"}</span>
        <span className="node-indicator" />
      </div>
      <strong>{data.name}</strong>
      <code>{data.id}</code>
      <div className="node-bottom">
        <span>{data.realization || "Logical element"}</span>
        <span>{data.ports || 0} ports</span>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { element: ElementNode };
export function ModelView({
  project,
  projection,
  parameters,
  selected,
  setSelected,
  edit,
  saveLayout,
  onSource,
  onCatalog,
}: {
  project: Project;
  projection: Projection;
  parameters: Parameter[];
  selected: string;
  setSelected: (id: string) => void;
  edit: (edits: Data[]) => Promise<unknown>;
  saveLayout: (layout: Data) => Promise<unknown>;
  onSource: () => void;
  onCatalog: () => void;
}) {
  const [search, setSearch] = useState(""),
    [structured, setStructured] = useState(false),
    [inspectorTab, setInspectorTab] = useState("Properties");
  const system = projection.resources.find((r) => r.kind === "System"),
    endpoints: Data[] = system?.spec?.endpoints || [];
  const initialNodes = useMemo(
    () =>
      projection.elements.map((e, i) => ({
        id: e.id,
        type: "element",
        position: project.layout?.positions?.[e.id] ||
          project.layout?.layout?.positions?.[e.id] || {
            x:
              75 +
              (i %
                (projection.elements.length > 12
                  ? Math.ceil(Math.sqrt(projection.elements.length * 1.5))
                  : 3)) *
                270,
            y:
              105 +
              Math.floor(
                i /
                  (projection.elements.length > 12
                    ? Math.ceil(Math.sqrt(projection.elements.length * 1.5))
                    : 3),
              ) *
                210,
          },
        data: {
          ...e,
          ports: endpoints.filter((p) => p.ownerId === e.id).length,
        },
        selected: e.id === selected,
      })),
    [project.revision, project.presentationRevision, projection.elements],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  useEffect(() => setNodes(initialNodes), [initialNodes]);
  useEffect(
    () =>
      setNodes((old) =>
        old.map((n) => ({ ...n, selected: n.id === selected })),
      ),
    [selected],
  );
  const edges = useMemo(
    () =>
      projection.connections.flatMap((flow) =>
        (flow.destinationEndpointIds || []).map(
          (target: string, index: number) => ({
            id: `${flow.id}-${index}`,
            source:
              endpoints.find((e) => e.id === flow.sourceEndpointId)?.ownerId ||
              "",
            target: endpoints.find((e) => e.id === target)?.ownerId || "",
            label: flow.id,
            type: "smoothstep",
            markerEnd: { type: MarkerType.ArrowClosed, color: "#8b9aaf" },
            style: { stroke: "#8b9aaf", strokeWidth: 1.7 },
            labelStyle: { fill: "#687b93", fontSize: 11 },
            labelBgStyle: { fill: "#f4f7fb" },
            labelBgPadding: [7, 4] as [number, number],
          }),
        ),
      ),
    [projection.connections, endpoints],
  );
  const element = projection.elements.find((e) => e.id === selected);
  async function persistLayout() {
    await saveLayout({
      formatVersion: "1.0",
      viewId: "model",
      systemRef: system
        ? {
            kind: "System",
            namespace: system.metadata?.namespace,
            name: system.metadata?.name,
          }
        : null,
      positions: Object.fromEntries(nodes.map((n) => [n.id, n.position])),
    });
  }
  return (
    <div className="model-workspace">
      <aside className="model-tree" aria-label="Structured model navigation">
        <div className="pane-title">
          <h2>System explorer</h2>
          <button
            className="icon-button"
            aria-label="View XDL source"
            onClick={onSource}
          >
            <Icon name="code" size={16} />
          </button>
        </div>
        <div className="tree-search">
          <Icon name="search" size={14} />
          <input
            aria-label="Search elements"
            placeholder="Find an element…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="tree-root">
          <Icon name="model" size={16} />
          <strong>{system?.metadata?.name || "System"}</strong>
          <span>{projection.elements.length}</span>
        </div>
        <div className="tree-list">
          {projection.elements
            .filter((e) =>
              `${e.name} ${e.id} ${e.role}`
                .toLowerCase()
                .includes(search.toLowerCase()),
            )
            .map((e) => (
              <button
                key={e.id}
                className={selected === e.id ? "selected" : ""}
                onClick={() => setSelected(e.id)}
              >
                <Icon
                  name={e.role.includes("observer") ? "results" : "model"}
                  size={15}
                />
                <span>{e.name}</span>
                <small>{e.role}</small>
              </button>
            ))}
        </div>
        <div className="tree-section">
          <span>RESOURCES</span>
          {projection.resources.map((r) => (
            <button key={r.documentId} onClick={onSource}>
              <Icon name="code" size={14} />
              <span>{r.metadata?.name || r.documentId}</span>
              <small>{r.kind}</small>
            </button>
          ))}
        </div>
        <div className="tree-bottom">
          <button className="button" onClick={onCatalog}>
            <Icon name="plus" />
            Add element
          </button>
        </div>
      </aside>
      <section className="canvas-pane" aria-label="Model canvas">
        {projection.parseErrors.length > 0 && (
          <div className="projection-warning">
            Some source structures cannot be projected safely. Inspect the XDL
            source and authoritative diagnostics.
          </div>
        )}
        <div className="canvas-toolbar">
          <div>
            <span className="canvas-label">LOGICAL MODEL</span>
            <Badge>{system?.metadata?.version || "Draft"}</Badge>
          </div>
          <div className="toolbar-actions">
            <button
              className="small-button"
              onClick={() => setStructured(!structured)}
            >
              {structured ? "Graph view" : "Table view"}
            </button>
            <button
              className="small-button"
              onClick={() =>
                setNodes((old) =>
                  old.map((n, i) => ({
                    ...n,
                    position: {
                      x:
                        75 +
                        (i %
                          (projection.elements.length > 12
                            ? Math.ceil(
                                Math.sqrt(projection.elements.length * 1.5),
                              )
                            : 3)) *
                          270,
                      y:
                        105 +
                        Math.floor(
                          i /
                            (projection.elements.length > 12
                              ? Math.ceil(
                                  Math.sqrt(projection.elements.length * 1.5),
                                )
                              : 3),
                        ) *
                          210,
                    },
                  })),
                )
              }
            >
              Auto layout
            </button>
            <button
              className="small-button"
              onClick={() => void persistLayout()}
            >
              Save layout
            </button>
          </div>
        </div>
        {structured ? (
          <div className="canvas-table">
            <table>
              <thead>
                <tr>
                  <th>Element</th>
                  <th>Role</th>
                  <th>Placement</th>
                  <th>Definition</th>
                </tr>
              </thead>
              <tbody>
                {projection.elements.map((e) => (
                  <tr key={e.id}>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => setSelected(e.id)}
                      >
                        {e.name}
                      </button>
                    </td>
                    <td>{e.role}</td>
                    <td>{e.nodeId}</td>
                    <td>{e.componentRef?.name || "System node"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onNodeClick={(_, node) => setSelected(node.id)}
            onPaneClick={() => setSelected("")}
            nodesConnectable={false}
            fitView
            fitViewOptions={{ padding: 0.15, minZoom: 0.01, maxZoom: 1.2 }}
            minZoom={0.01}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
            aria-label="Logical System graph. Use the System explorer for keyboard selection."
          >
            <Background color="#dbe3ee" gap={20} size={1.1} />
            <Controls showInteractive={false} />
            <MiniMap nodeColor="#c8d7e9" maskColor="rgba(244,247,251,.75)" />
          </ReactFlow>
        )}
        <div className="canvas-legend">
          <span>
            <i className="legend-line" />
            Declared communication
          </span>
          <span>
            <i className="legend-node" />
            Logical element
          </span>
          <span>Graph positions are presentation only</span>
        </div>
      </section>
      <aside className="inspector" aria-label="Element inspector">
        <div className="pane-title">
          <h2>{element ? "Element inspector" : "System inspector"}</h2>
          <Icon name="settings" size={16} />
        </div>
        <div className="inspector-summary">
          <span className="inspector-symbol">
            <Icon name={element ? "model" : "deployment"} size={23} />
          </span>
          <h3>{element?.name || system?.metadata?.name || project.name}</h3>
          <p>{element?.role || "Authoritative XDL System"}</p>
          <Badge tone="info">
            {element ? "Logical identity" : "Draft model"}
          </Badge>
        </div>
        <div className="inspector-tabs">
          {["Properties", "Parameters"].map((t) => (
            <button
              key={t}
              className={inspectorTab === t ? "active" : ""}
              onClick={() => setInspectorTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="inspector-body">
          {inspectorTab === "Parameters" ? (
            <ParameterForm
              parameters={parameters}
              onSave={async (parameterId, value) => {
                await edit([{ kind: "set_parameter", parameterId, value }]);
              }}
            />
          ) : element ? (
            <>
              <KeyValues
                values={{
                  "Element ID": element.id,
                  Role: element.role,
                  Realization:
                    projection.deployments
                      .flatMap((d) => d.spec?.bindings || [])
                      .find((b: Data) => b.logicalRef?.element === element.id)
                      ?.realizationClass || "Unbound",
                  Placement: element.nodeId,
                  Definition: textRef(element.componentRef),
                }}
              />
              <h4>Named ports</h4>
              {endpoints
                .filter((p) => p.ownerId === element.id)
                .map((p) => (
                  <div className="port-row" key={p.id}>
                    <span className="port-dot" />
                    <code>{p.id}</code>
                    <Badge>{p.direction}</Badge>
                  </div>
                ))}
              <h4>Provenance</h4>
              <p className="field-hint">
                {element.definition?.metadata?.description ||
                  "System node from the current XDL revision."}
              </p>
              <Json value={element.raw} />
            </>
          ) : (
            <>
              <p className="field-hint">
                Select an element in the graph or explorer to inspect its stable
                identity, role, realization, and placement.
              </p>
              <KeyValues
                values={{
                  Namespace: system?.metadata?.namespace || "Not declared",
                  "XDL version": system?.apiVersion || "Unknown",
                  Resources: projection.resources.length,
                  "Evidence scope": "Owned reference only",
                }}
              />
              <h4>Reference parameters</h4>
              <ParameterForm
                parameters={parameters}
                onSave={async (parameterId, value) => {
                  await edit([{ kind: "set_parameter", parameterId, value }]);
                }}
              />
            </>
          )}
        </div>
        <div className="inspector-note">
          <Icon name="info" size={15} />
          <span>
            Backend validation determines semantic compatibility and execution
            readiness.
          </span>
        </div>
      </aside>
    </div>
  );
}
function ParameterForm({
  parameters,
  onSave,
}: {
  parameters: Parameter[];
  onSave: (id: string, value: unknown) => Promise<void>;
}) {
  const [draft, setDraft] = useState<Record<string, string>>({});
  useEffect(
    () =>
      setDraft(
        Object.fromEntries(
          parameters.map((p) => [p.id, String(p.value ?? p.default ?? "")]),
        ),
      ),
    [parameters],
  );
  if (!parameters.length)
    return (
      <p className="field-hint">
        No admitted editable parameters are declared. Inspect the authored
        source.
      </p>
    );
  return (
    <div className="parameter-form">
      {parameters.map((p) => (
        <form
          key={p.id}
          onSubmit={async (e) => {
            e.preventDefault();
            await onSave(
              p.id,
              (p.valueType || p.type) === "number"
                ? Number(draft[p.id])
                : draft[p.id],
            );
          }}
        >
          <label>
            {p.label || p.id}
            <span className="unit-label">{p.unit || "unit not declared"}</span>
            {p.enum ? (
              <select
                value={draft[p.id] || ""}
                onChange={(e) => setDraft({ ...draft, [p.id]: e.target.value })}
              >
                {p.enum.map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            ) : (
              <input
                type={(p.valueType || p.type) === "number" ? "number" : "text"}
                step="any"
                min={p.minimum}
                max={p.maximum}
                value={draft[p.id] ?? ""}
                onChange={(e) => setDraft({ ...draft, [p.id]: e.target.value })}
                required
              />
            )}
          </label>
          <p className="field-hint">
            {p.description || "Value from authored Scenario configuration."}
          </p>
          <div className="parameter-source">
            <span>
              {p.source || "Scenario XDL"}
              {p.default !== undefined ? ` · default ${p.default}` : ""}
            </span>
            <button
              className="small-button"
              disabled={draft[p.id] === String(p.value ?? p.default ?? "")}
            >
              Apply
            </button>
          </div>
        </form>
      ))}
    </div>
  );
}
export function ConnectionsView({
  projection,
  edit,
}: {
  projection: Projection;
  edit: (edits: Data[]) => Promise<unknown>;
}) {
  const [source, setSource] = useState(""),
    [target, setTarget] = useState(""),
    [id, setId] = useState("");
  const system = projection.resources.find((r) => r.kind === "System"),
    endpoints: Data[] = system?.spec?.endpoints || [];
  return (
    <div className="view-page">
      <div className="section-heading">
        <div>
          <h2>Connections</h2>
          <p>
            Inspect declared data flows and their explicit endpoint contracts.
          </p>
        </div>
        <Badge>Communication projection</Badge>
      </div>
      <div className="connection-layout">
        <section className="panel">
          <h3>Declared topology</h3>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Flow</th>
                  <th>Source → destination</th>
                  <th>Interface</th>
                  <th>Clock</th>
                  <th>Observed</th>
                </tr>
              </thead>
              <tbody>
                {projection.connections.map((flow) => (
                  <tr key={flow.id}>
                    <td>
                      <strong>{flow.id}</strong>
                    </td>
                    <td>
                      <code>{flow.sourceEndpointId}</code>
                      <span className="flow-arrow">→</span>
                      <code>
                        {(flow.destinationEndpointIds || []).join(", ")}
                      </code>
                    </td>
                    <td>{flow.interfaceId}</td>
                    <td>{flow.timeDomainId || "Unknown"}</td>
                    <td>
                      <Badge>Not observed</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="scope-note">
            <Icon name="info" />
            <span>
              A declaration does not prove resolved routing or observed traffic.
              Reference runs do not activate native X-COM or a physical coupling
              solver.
            </span>
          </div>
          <h3>Endpoint contracts</h3>
          {endpoints.map((p) => (
            <div className="endpoint-card" key={p.id}>
              <div>
                <code>{p.id}</code>
                <small>Owner: {p.ownerId}</small>
              </div>
              <Badge>{p.direction}</Badge>
              <span>{p.interfaceId}</span>
            </div>
          ))}
        </section>
        <aside className="panel">
          <h3>Connect endpoints</h3>
          <p className="field-hint">
            The backend checks direction, schema, unit, multiplicity, clock, and
            provider compatibility. Conversions require an explicit admitted
            mapping.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void edit([
                {
                  kind: "connect_endpoints",
                  flowId: id,
                  sourceEndpointId: source,
                  destinationEndpointIds: [target],
                  interfaceId: endpoints.find((p) => p.id === source)
                    ?.interfaceId,
                  timeDomainId: system?.spec?.defaultTimeDomainId,
                },
              ]);
            }}
          >
            <label>
              Flow identifier
              <input
                value={id}
                onChange={(e) => setId(e.target.value)}
                required
                pattern="[a-zA-Z0-9_-]+"
              />
            </label>
            <label>
              Source endpoint
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                required
              >
                <option value="">Choose an output</option>
                {endpoints
                  .filter(
                    (p) =>
                      p.direction === "output" ||
                      p.direction === "bidirectional",
                  )
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.id} · {p.interfaceId}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Destination endpoint
              <select
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                required
              >
                <option value="">Choose an input</option>
                {endpoints
                  .filter(
                    (p) =>
                      p.direction === "input" ||
                      p.direction === "bidirectional",
                  )
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.id} · {p.interfaceId}
                    </option>
                  ))}
              </select>
            </label>
            <button
              className="button primary"
              disabled={!source || !target || !id}
            >
              <Icon name="connection" />
              Validate & connect
            </button>
          </form>
          <hr />
          <h4>Relationship kinds</h4>
          <ul className="limits-list">
            <li>Communication transfers declared data.</li>
            <li>Physical coupling needs a dedicated solver contract.</li>
            <li>Deployment binds a logical element to a realization.</li>
            <li>Trace links record references without proving a result.</li>
          </ul>
        </aside>
      </div>
    </div>
  );
}
export function DeploymentView({
  projection,
  providers,
  edit,
  header = true,
}: {
  header?: boolean;
  projection: Projection;
  providers: Data[];
  edit: (edits: Data[]) => Promise<unknown>;
}) {
  const [chosen, setChosen] = useState(0);
  const d = projection.deployments[chosen];
  return (
    <div className={header ? "view-page" : "deployment-inspection"}>
      {header && (
        <div className="section-heading">
          <div>
            <h2>Deployment variants</h2>
            <p>
              Keep logical identity stable while selecting realization and
              placement.
            </p>
          </div>
          <select
            aria-label="Deployment variant"
            value={chosen}
            onChange={(e) => setChosen(Number(e.target.value))}
          >
            {projection.deployments.map((d, i) => (
              <option key={d.documentId} value={i}>
                {d.metadata?.name}
              </option>
            ))}
          </select>
        </div>
      )}
      {d ? (
        <>
          <div className="deployment-summary">
            <section className="panel">
              <span className="eyebrow">SELECTED VARIANT</span>
              <h3>{d.metadata?.name}</h3>
              <p>{d.metadata?.description}</p>
              <KeyValues
                values={{
                  System: textRef(d.spec?.systemRef),
                  Targets: d.spec?.targets?.length || 0,
                  Artifacts: d.spec?.artifacts?.length || 0,
                  Bindings: d.spec?.bindings?.length || 0,
                }}
              />
            </section>
            <section className="panel">
              <h3>Provider readiness</h3>
              {providers.map((p) => (
                <div className="provider-row" key={p.providerId || p.id}>
                  <span>
                    <strong>{p.name || p.providerId || p.id}</strong>
                    <small>
                      {p.evidenceScope ||
                        p.scope ||
                        p.maturity ||
                        "Scope unknown"}
                    </small>
                  </span>
                  <Badge tone={p.available ? "success" : "warning"}>
                    {p.available
                      ? "Available"
                      : p.availability || "Unavailable"}
                  </Badge>
                </div>
              ))}
              <p className="field-hint">
                OS-specific provider support is separate from native Studio
                support. Run preflight to verify the selected bindings.
              </p>
            </section>
          </div>
          <section className="panel">
            <h3>Logical element bindings</h3>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Logical identity</th>
                    <th>Realization</th>
                    <th>Placement / target</th>
                    <th>Artifacts</th>
                  </tr>
                </thead>
                <tbody>
                  {(d.spec?.bindings || []).map((b: Data) => (
                    <tr key={b.id}>
                      <td>
                        <strong>
                          {b.logicalRef?.element || textRef(b.logicalRef)}
                        </strong>
                        <small>{b.id}</small>
                      </td>
                      <td>
                        <Badge tone="info">{b.realizationClass}</Badge>
                      </td>
                      <td>{b.targetId}</td>
                      <td>{(b.artifactIds || []).join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <div className="catalog-grid">
            {(d.spec?.artifacts || []).map((a: Data) => (
              <section className="panel" key={a.id}>
                <h3>{a.id}</h3>
                <KeyValues
                  values={{
                    Kind: a.artifactKind,
                    Version: a.version,
                    Identity: a.digest,
                    Source: a.sourceRef,
                    Maturity: a.maturity || "Not declared",
                  }}
                />
                {a.limitations?.map((l: string, i: number) => (
                  <p className="field-hint" key={i}>
                    {l}
                  </p>
                ))}
              </section>
            ))}
          </div>
          <BindingForm deployment={d} onSave={edit} />
          <section className="panel">
            <h3>Effective configuration provenance</h3>
            <p>
              Scenario values remain in authored XDL. No unspecified override
              precedence or implicit environment substitution is applied.
            </p>
            <Json value={d.spec} />
          </section>
        </>
      ) : (
        <Empty title="No deployment declared" icon="deployment">
          Add a supported Deployment resource in XDL, then validate its
          compatibility.
        </Empty>
      )}
    </div>
  );
}
export function SourceEditor({
  project,
  doAction,
  onSaved,
}: {
  project: Project;
  doAction: DoAction;
  onSaved: () => Promise<void>;
}) {
  const ids = Object.keys(project.documents),
    [id, setId] = useState(ids[0] || ""),
    [content, setContent] = useState(""),
    [history, setHistory] = useState<string[]>([]),
    [future, setFuture] = useState<string[]>([]),
    [compare, setCompare] = useState(false),
    [recovered, setRecovered] = useState(false);
  const baseline = documentContent(project.documents[id] || "");
  const draftKey = `studio.draft.${project.projectId}.${id}`;
  useEffect(() => {
    const original = documentContent(project.documents[id] || ""),
      saved = sessionStorage.getItem(draftKey);
    setContent(saved || original);
    setRecovered(!!saved && saved !== original);
    setHistory([]);
    setFuture([]);
  }, [id, project.projectId]);
  const dirty = content !== baseline;
  useEffect(() => {
    const timer = setTimeout(() => {
      if (dirty && content.length <= 524288)
        sessionStorage.setItem(draftKey, content);
      else sessionStorage.removeItem(draftKey);
    }, 500);
    return () => clearTimeout(timer);
  }, [content, dirty, draftKey]);
  useEffect(() => {
    const handle = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handle);
    return () => window.removeEventListener("beforeunload", handle);
  }, [dirty]);
  function change(value: string) {
    setHistory((h) => [...h.slice(-49), content]);
    setFuture([]);
    setContent(value);
  }
  function undo() {
    if (!history.length) return;
    setFuture((f) => [content, ...f].slice(0, 50));
    setContent(history[history.length - 1]);
    setHistory((h) => h.slice(0, -1));
  }
  function redo() {
    if (!future.length) return;
    setHistory((h) => [...h.slice(-49), content]);
    setContent(future[0]);
    setFuture((f) => f.slice(1));
  }
  return (
    <div className="source-editor">
      <div className="source-toolbar">
        <label>
          Resource
          <select
            aria-label="Resource"
            value={id}
            onChange={(e) => setId(e.target.value)}
          >
            {ids.map((id) => (
              <option key={id} value={id}>
                {typeof project.documents[id] === "string"
                  ? id
                  : project.documents[id].path}
              </option>
            ))}
          </select>
        </label>
        <Badge tone={dirty ? "warning" : "success"}>
          {dirty ? "Unsaved draft" : "Saved revision"}
        </Badge>
        <div className="source-tools">
          <button
            className="small-button"
            disabled={!history.length}
            onClick={undo}
          >
            Undo
          </button>
          <button
            className="small-button"
            disabled={!future.length}
            onClick={redo}
          >
            Redo
          </button>
          <button className="small-button" onClick={() => setCompare(!compare)}>
            {compare ? "Editor only" : "Compare changes"}
          </button>
        </div>
      </div>
      {recovered && (
        <p className="notice">
          Recovered an uncommitted draft from this browser tab. Review it before
          saving.
        </p>
      )}
      <p className="field-hint">
        Exact authored content is retained. Unknown extensions stay intact;
        platform validation decides whether the revision is executable. Saving
        changes only the draft.
      </p>
      <div className={`source-panels ${compare ? "compare" : ""}`}>
        {compare && (
          <div>
            <span className="source-pane-label">Saved revision</span>
            <pre className="source-baseline">{baseline}</pre>
          </div>
        )}
        <div>
          <label className="source-pane-label" htmlFor="xdl-source">
            {compare ? "Edited draft" : "XDL source"}
          </label>
          <textarea
            id="xdl-source"
            className="source-textarea"
            spellCheck={false}
            value={content}
            onChange={(e) => change(e.target.value)}
            onKeyDown={(e) => {
              if ((e.ctrlKey || e.metaKey) && e.key === "s") {
                e.preventDefault();
                void save();
              }
              if ((e.ctrlKey || e.metaKey) && e.key === "z") {
                e.preventDefault();
                e.shiftKey ? redo() : undo();
              }
            }}
          />
        </div>
      </div>
      <div className="source-footer">
        <span>
          Draft revision <code>{String(project.revision).slice(0, 12)}</code> ·
          UTF-8 · {content.length.toLocaleString()} characters
        </span>
        <button
          className="button primary"
          disabled={!dirty}
          onClick={() => void save()}
        >
          <Icon name="check" />
          Save source revision
        </button>
      </div>
    </div>
  );
  async function save() {
    await doAction("Saving source revision", async () => {
      const document = project.documents[id];
      await api(
        `/projects/${project.projectId}/documents/${encodeURIComponent(id)}`,
        {
          method: "PUT",
          revision: project.revision,
          body: {
            content,
            format: typeof document === "string" ? "yaml" : document.format,
          },
        },
      );
      sessionStorage.removeItem(draftKey);
      setRecovered(false);
      await onSaved();
    });
  }
}

function BindingForm({
  deployment,
  onSave,
}: {
  deployment: Data;
  onSave: (edits: Data[]) => Promise<unknown>;
}) {
  const bindings: Data[] = deployment.spec?.bindings || [],
    targets: Data[] = deployment.spec?.targets || [];
  const [id, setId] = useState(bindings[0]?.id || ""),
    [targetId, setTargetId] = useState(bindings[0]?.targetId || ""),
    [realization, setRealization] = useState(
      bindings[0]?.realizationClass || "simulated",
    );
  useEffect(() => {
    const b = bindings.find((b) => b.id === id);
    if (b) {
      setTargetId(b.targetId);
      setRealization(b.realizationClass);
    }
  }, [id, deployment]);
  return (
    <section className="panel">
      <h3>Inspect and update a binding</h3>
      <p className="field-hint">
        Role stays in the logical System. Realization and target placement are
        selected independently here. Provider compatibility is revalidated
        before execution.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void onSave([
            {
              kind: "set_binding",
              bindingId: id,
              targetId,
              realizationClass: realization,
            },
          ]);
        }}
      >
        <div className="binding-fields">
          <label>
            Logical binding
            <select value={id} onChange={(e) => setId(e.target.value)}>
              {bindings.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.logicalRef?.element || b.id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Realization
            <select
              value={realization}
              onChange={(e) => setRealization(e.target.value)}
            >
              <option value="simulated">Simulated</option>
              <option value="software">Software</option>
              <option value="emulated">Emulated</option>
              <option value="physical">Physical</option>
            </select>
          </label>
          <label>
            Target placement
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
            >
              {targets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id} · {t.targetClass}
                </option>
              ))}
            </select>
          </label>
          <button className="button primary" disabled={!id || !targetId}>
            Save draft binding
          </button>
        </div>
      </form>
      <p className="field-hint">
        Selecting a realization does not install a provider or authorize
        hardware. Unsupported combinations remain blocked at backend admission.
      </p>
    </section>
  );
}
