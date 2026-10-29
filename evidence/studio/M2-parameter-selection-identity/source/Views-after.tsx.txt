import { parseDocument, isMap, isSeq } from "yaml";
import { LogicalAssetForm } from "./LogicalAssetForm";
import { Modal } from "../../app/ui";
import {
  useContext,
  useState,
  useEffect,
  useMemo,
  useRef,
  useId,
  useLayoutEffect,
} from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  MarkerType,
  ViewportPortal,
} from "@xyflow/react";
import type { NodeProps, Node } from "@xyflow/react";
import type { Data, Project, Parameter } from "../../api/types";
import { api, ApiError } from "../../api/client";
import type { DoAction } from "../../app/App";
import { Icon, Badge, Empty, Json, KeyValues } from "../../app/ui";
import type { Projection, ElementProjection } from "./projection";
import { documentContent, groupByNode, textRef } from "./projection";
import { groupLabel, ModelTree, placementLabel } from "./tree/ModelTree";
import {
  AdmissionCell,
  AdmissionSummary,
  targetGuidance,
  useConnectionAdmission,
} from "../connections/ConnectionAdmission";
import { FlowContractForm, RelationKinds } from "../connections/Relations";
import { CommunicationProjections } from "../connections/projections";
import { PresentationContext, useTerm } from "../profiles/presentation";
import {
  DefinitionInspector,
  ModelBreadcrumb,
  NodeInspector,
} from "./StructureInspectors";
export type SourceTarget = {
  documentId: string;
  ref?: string;
  elementId?: string;
  collection?: string;
};
export function sourceTarget(element: ElementProjection): SourceTarget {
  return {
    documentId: element.documentId,
    ref: element.ref,
    elementId: element.id,
    collection: (
      {
        device: "devices",
        sensor: "sensors",
        actuator: "actuators",
        model: "models",
        node: "nodes",
        componentInstance: "componentInstances",
      } as Record<string, string>
    )[element.kind],
  };
}
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
      {data.runChange && (
        <span className={`run-change ${data.runChange}`}>
          {data.runChange === "added" ? "new in draft" : "changed since run"}
        </span>
      )}
      {data.portList?.length > 0 && (
        <ul className="node-ports" aria-label="Named ports">
          {data.portList.slice(0, 4).map((port: Data) => (
            <li key={port.id}>
              <span aria-hidden="true">
                {port.direction === "input"
                  ? "→"
                  : port.direction === "output"
                    ? "←"
                    : "↔"}
              </span>
              <code>{port.id}</code>
              <small>{port.direction}</small>
            </li>
          ))}
          {data.portList.length > 4 && (
            <li>+{data.portList.length - 4} more</li>
          )}
        </ul>
      )}
      <div className="node-bottom">
        <span>{data.realization || "Logical element"}</span>
        <span>{data.ports || 0} ports</span>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { element: ElementNode };
// Stable identity: a fresh default object per render would reset node positions.
const NO_RUN_CHANGES: Record<string, string> = {};
// Deterministic presentation layouts; positions never enter executable identity.
function gridPosition(index: number, count: number) {
  const columns = count > 12 ? Math.ceil(Math.sqrt(count * 1.5)) : 3;
  return {
    x: 75 + (index % columns) * 270,
    y: 105 + Math.floor(index / columns) * 210,
  };
}
// Each node's members tile a near-square block; blocks wrap into rows of groups.
function groupedPositions(groups: ReturnType<typeof groupByNode>) {
  const positions: Record<string, { x: number; y: number }> = {},
    perRow = Math.max(1, Math.ceil(Math.sqrt(groups.length)));
  let x = 75,
    y = 125,
    rowHeight = 0;
  groups.forEach((group, index) => {
    if (index && index % perRow === 0) {
      x = 75;
      y += rowHeight + 90;
      rowHeight = 0;
    }
    const columns = Math.max(1, Math.ceil(Math.sqrt(group.members.length)));
    group.members.forEach((member, i) => {
      // An element listed by several nodes keeps its first position.
      positions[member.ref] ??= {
        x: x + (i % columns) * 230,
        y: y + Math.floor(i / columns) * 210,
      };
    });
    x += columns * 230 + 70;
    rowHeight = Math.max(
      rowHeight,
      Math.ceil(group.members.length / columns) * 210,
    );
  });
  return positions;
}
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
  runChanges = NO_RUN_CHANGES,
}: {
  /** Element ref → change since the selected run's snapshot (presentation only). */
  runChanges?: Record<string, string>;
  project: Project;
  projection: Projection;
  parameters: Parameter[];
  selected: string;
  setSelected: (id: string) => void;
  edit: (edits: Data[]) => Promise<Project | undefined>;
  saveLayout: (layout: Data) => Promise<unknown>;
  onSource: (target?: SourceTarget) => void;
  onCatalog: () => void;
}) {
  const term = useTerm();
  const [search, setSearch] = useState(""),
    [structured, setStructured] = useState(false),
    [inspectorTab, setInspectorTab] = useState("Properties"),
    [editingAsset, setEditingAsset] = useState(false),
    [grouped, setGrouped] = useState(() => {
      try {
        return localStorage.getItem("studio.model.groupByNode") === "1";
      } catch {
        return false;
      }
    }),
    [selectedGroup, setSelectedGroup] = useState(""),
    [definitionOf, setDefinitionOf] = useState("");
  const groups = useMemo(() => groupByNode(projection), [projection]);
  function chooseGrouping(value: boolean) {
    setGrouped(value);
    // Arrange by node so frames describe placement; the layout is saved only on request.
    if (value) {
      const byNode = groupedPositions(groups);
      setNodes((old) =>
        old.map((n) => (byNode[n.id] ? { ...n, position: byNode[n.id] } : n)),
      );
    }
    try {
      localStorage.setItem("studio.model.groupByNode", value ? "1" : "0");
    } catch {
      /* The preference only affects this browser's presentation. */
    }
  }
  function selectElement(ref: string) {
    setSelectedGroup("");
    setDefinitionOf("");
    setSelected(ref);
  }
  function selectGroup(key: string) {
    setSelected("");
    setDefinitionOf("");
    setSelectedGroup(key);
  }
  const system = projection.resources.find((r) => r.kind === "System"),
    endpoints: Data[] = system?.spec?.endpoints || [];
  const runChangesKey = JSON.stringify(runChanges);
  const initialNodes = useMemo<Node<Data>[]>(
    () =>
      projection.elements.map((e, i) => ({
        id: e.ref,
        type: "element",
        position: project.layout?.positions?.[e.ref] ||
          project.layout?.positions?.[e.id] ||
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
          ...(() => {
            const portList = (
              projection.resources.find((r) => r.documentId === e.documentId)
                ?.spec.endpoints || []
            ).filter((p: Data) => p.ownerId === e.id);
            return { ports: portList.length, portList };
          })(),
          runChange: runChanges[e.ref],
        },
        selected: e.ref === selected || e.id === selected,
      })),
    [
      project.revision,
      project.presentationRevision,
      projection.elements,
      runChangesKey,
    ],
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
            id: `${flow.systemRef}#${flow.id}-${index}`,
            source: `${flow.systemRef}#${(projection.resources.find((r) => r.documentId === flow.documentId)?.spec.endpoints || []).find((e: Data) => e.id === flow.sourceEndpointId)?.ownerId || ""}`,
            target: `${flow.systemRef}#${(projection.resources.find((r) => r.documentId === flow.documentId)?.spec.endpoints || []).find((e: Data) => e.id === target)?.ownerId || ""}`,
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
  // Frames follow their members' current positions; they are never saved.
  const frames = useMemo(() => {
    if (!grouped) return [];
    const membership = new Map<string, string[]>();
    for (const group of groups)
      for (const member of group.members)
        membership.set(member.ref, [
          ...(membership.get(member.ref) || []),
          group.key,
        ]);
    const boxes = new Map<
      string,
      { left: number; top: number; right: number; bottom: number }
    >();
    for (const n of nodes)
      for (const key of membership.get(n.id) || []) {
        const box = boxes.get(key),
          right = n.position.x + (n.measured?.width ?? 194),
          bottom = n.position.y + (n.measured?.height ?? 150);
        boxes.set(
          key,
          box
            ? {
                left: Math.min(box.left, n.position.x),
                top: Math.min(box.top, n.position.y),
                right: Math.max(box.right, right),
                bottom: Math.max(box.bottom, bottom),
              }
            : { left: n.position.x, top: n.position.y, right, bottom },
        );
      }
    return groups.flatMap((group) => {
      const box = boxes.get(group.key);
      if (!box) return [];
      const left = box.left - 22,
        top = box.top - 42;
      return [
        {
          group,
          left,
          top,
          width: box.right - left + 22,
          height: box.bottom - top + 22,
          // A frame that also covers other elements misdescribes placement.
          overlaps: nodes.some(
            (n) =>
              !(membership.get(n.id) || []).includes(group.key) &&
              n.position.x + 97 > left &&
              n.position.x + 97 < left + box.right - left + 22 &&
              n.position.y + 60 > top &&
              n.position.y + 60 < top + box.bottom - top + 22,
          ),
        },
      ];
    });
  }, [grouped, groups, nodes]);
  const element = projection.elements.find(
    (e) => e.ref === selected || e.id === selected,
  );
  const group = groups.find((g) => g.key === selectedGroup);
  const definitionElement = projection.elements.find(
    (e) => e.ref === definitionOf,
  );
  const selectedEndpoints: Data[] =
    projection.resources.find((r) => r.documentId === element?.documentId)?.spec
      .endpoints || endpoints;
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
          <h2>{term("System")} explorer</h2>
          <button
            className="icon-button"
            aria-label="View XDL source"
            onClick={() =>
              onSource(
                element
                  ? sourceTarget(element)
                  : system
                    ? { documentId: system.documentId }
                    : undefined,
              )
            }
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
          <button
            className="small-button"
            aria-pressed={grouped}
            onClick={() => chooseGrouping(!grouped)}
          >
            Group by node
          </button>
        </div>
        {grouped ? (
          <ModelTree
            groups={groups}
            search={search}
            selected={element?.ref || ""}
            selectedGroup={selectedGroup}
            onSelectElement={selectElement}
            onSelectGroup={selectGroup}
          />
        ) : (
          <div className="tree-list">
            {projection.elements
              .filter((e) =>
                `${e.name} ${e.id} ${e.role}`
                  .toLowerCase()
                  .includes(search.toLowerCase()),
              )
              .map((e) => (
                <button
                  key={e.ref}
                  className={
                    selected === e.ref || selected === e.id ? "selected" : ""
                  }
                  onClick={() => selectElement(e.ref)}
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
        )}
        <div className="tree-section">
          <span>RESOURCES</span>
          {projection.resources.map((r) => (
            <button
              key={r.documentId + r.kind + r.metadata.name}
              onClick={() =>
                onSource({
                  documentId: r.documentId,
                  ref: `xdl://${r.metadata.namespace}/${r.kind.toLowerCase()}/${r.metadata.name}`,
                })
              }
            >
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
              onClick={() => {
                const byNode = groupedPositions(groups);
                setNodes((old) =>
                  old.map((n, i) => ({
                    ...n,
                    position:
                      grouped && byNode[n.id]
                        ? byNode[n.id]
                        : gridPosition(i, projection.elements.length),
                  })),
                );
              }}
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
                  <th>Logical containing node</th>
                  <th>Definition</th>
                </tr>
              </thead>
              <tbody>
                {projection.elements.map((e) => (
                  <tr key={e.ref}>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => setSelected(e.ref)}
                      >
                        {e.name}
                      </button>
                    </td>
                    <td>{e.role}</td>
                    <td>{e.nodeId}</td>
                    <td>{e.componentRef?.name || e.kind}</td>
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
            onNodeClick={(_, node) => {
              if (node.type === "element") selectElement(node.id);
            }}
            onPaneClick={() => selectElement("")}
            nodesConnectable={false}
            fitView
            fitViewOptions={{ padding: 0.15, minZoom: 0.01, maxZoom: 1.2 }}
            minZoom={0.01}
            maxZoom={2}
            proOptions={{ hideAttribution: true }}
            aria-label="Logical System graph. Use the System explorer for keyboard selection."
          >
            <Background color="#dbe3ee" gap={20} size={1.1} />
            <ViewportPortal>
              {frames.map(({ group, left, top, width, height }) => (
                <div
                  key={group.key}
                  className={`node-group-frame ${group.placement}`}
                  style={{
                    position: "absolute",
                    transform: `translate(${left}px, ${top}px)`,
                    width,
                    height,
                  }}
                  aria-hidden="true"
                >
                  <span>
                    {groupLabel(group)}
                    <small>
                      {placementLabel(group) ||
                        group.roles.join(", ") ||
                        "node"}
                    </small>
                  </span>
                </div>
              ))}
            </ViewportPortal>
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
          {frames.some((frame) => frame.overlaps) && (
            <span role="status" className="frame-overlap">
              Some node frames also cover other elements; use Auto layout to
              arrange by node.
            </span>
          )}
        </div>
      </section>
      <aside className="inspector" aria-label="Element inspector">
        <div className="pane-title">
          <h2>
            {definitionElement
              ? "Definition inspector"
              : group
                ? "Node inspector"
                : element
                  ? "Element inspector"
                  : "System inspector"}
          </h2>
          <Icon name="settings" size={16} />
        </div>
        <div className="inspector-summary">
          <span className="inspector-symbol">
            <Icon
              name={
                definitionElement || element
                  ? "model"
                  : group
                    ? "folder"
                    : "deployment"
              }
              size={23}
            />
          </span>
          <h3>
            {definitionElement?.definition?.metadata?.name ||
              (group && groupLabel(group)) ||
              element?.name ||
              system?.metadata?.name ||
              project.name}
          </h3>
          <p>
            {definitionElement
              ? "Component definition"
              : group
                ? group.roles.join(", ") || "Node"
                : element?.role || "Authoritative XDL System"}
          </p>
          <Badge tone="info">
            {definitionElement
              ? "Read-only definition"
              : group
                ? "XDL node placement"
                : element
                  ? "Logical identity"
                  : "Draft model"}
          </Badge>
        </div>
        <ModelBreadcrumb
          systemName={system?.metadata?.name || project.name}
          group={
            group ||
            groups.find((g) =>
              g.members.some(
                (m) => m.ref === (definitionElement || element)?.ref,
              ),
            )
          }
          element={definitionElement || element}
          definition={definitionElement?.definition}
          onSystem={() => selectElement("")}
          onGroup={selectGroup}
          onElement={selectElement}
        />
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
              projectId={project.projectId}
              parameters={parameters}
              onSave={async (parameterId, value) => {
                return Boolean(
                  await edit([{ kind: "set_parameter", parameterId, value }]),
                );
              }}
            />
          ) : definitionElement?.definition ? (
            <DefinitionInspector
              element={definitionElement}
              onBack={() => selectElement(definitionElement.ref)}
              onSource={onSource}
            />
          ) : group ? (
            <NodeInspector
              group={group}
              onSelectElement={selectElement}
              onSource={onSource}
            />
          ) : element ? (
            <>
              <KeyValues
                values={{
                  "Element ID": element.id,
                  "Qualified identity": element.ref,
                  Kind: element.kind,
                  Role: element.role,
                  Capabilities:
                    element.definition?.spec.capabilities ||
                    element.raw.capabilities ||
                    "Not declared",
                  "Supported realization capabilities":
                    element.raw.supportedRealizationClasses || "Not declared",
                  "Deployment bindings": projection.deployments.flatMap(
                    (deployment) =>
                      (deployment.spec.bindings || [])
                        .filter(
                          (binding: Data) =>
                            binding.logicalRef?.kind === "System" &&
                            binding.logicalRef?.element === element.id &&
                            element.systemRef ===
                              `xdl://${binding.logicalRef.namespace}/system/${binding.logicalRef.name}`,
                        )
                        .map((binding: Data) => ({
                          variant: deployment.metadata.name,
                          bindingId: binding.id,
                          realization: binding.realizationClass,
                          target: binding.targetId || "Unplaced",
                        })),
                  ),
                  "Logical containing node": element.nodeId,
                  Definition: textRef(element.componentRef),
                }}
              />
              <div className="inspector-actions">
                <button
                  className="button"
                  onClick={() => onSource(sourceTarget(element))}
                >
                  View selected declaration
                </button>
                {element.definition && (
                  <button
                    className="button"
                    onClick={() => {
                      setSelectedGroup("");
                      setDefinitionOf(element.ref);
                    }}
                  >
                    Open component definition
                  </button>
                )}
                {["device", "sensor", "actuator", "model"].includes(
                  element.kind,
                ) && (
                  <button
                    className="button"
                    onClick={() => setEditingAsset(true)}
                  >
                    Edit logical asset
                  </button>
                )}
              </div>
              <h4>Named ports</h4>
              {selectedEndpoints
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
                  "Logical System member from the current XDL revision."}
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
                projectId={project.projectId}
                parameters={parameters}
                onSave={async (parameterId, value) => {
                  return Boolean(
                    await edit([{ kind: "set_parameter", parameterId, value }]),
                  );
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
      {editingAsset && element && (
        <Modal
          title="Edit a logical asset"
          onClose={() => setEditingAsset(false)}
        >
          <LogicalAssetForm
            projection={projection}
            element={element}
            onSave={async (edits) => {
              await edit(edits);
              setEditingAsset(false);
            }}
          />
        </Modal>
      )}
    </div>
  );
}
function ParameterForm({
  projectId,
  parameters,
  onSave,
}: {
  projectId: string;
  parameters: Parameter[];
  onSave: (id: string, value: unknown) => Promise<boolean>;
}) {
  type FieldDraft = {
    text: string;
    authored: string;
    version: number;
    edited: boolean;
    submitted?: { version: number; value: unknown };
  };
  const keyOf = (p: Parameter) =>
    JSON.stringify([projectId, p.documentId, p.scenarioRef, p.id]);
  const authoredValue = (p: Parameter) => p.value ?? p.default ?? "";
  const [draft, setDraft] = useState<Record<string, FieldDraft>>({});
  const guidancePrefix = useId(),
    controls = useRef<Record<string, HTMLInputElement | HTMLSelectElement>>({}),
    submitControls = useRef<Record<string, HTMLButtonElement>>({}),
    mounted = useRef(false),
    currentKeys = useRef(new Set<string>());
  const focusedControl = useRef<{
    key: string;
    kind: "value" | "submit";
    node: HTMLInputElement | HTMLSelectElement | HTMLButtonElement;
  } | null>(null);
  currentKeys.current = new Set(parameters.map(keyOf));
  const [focusRequest, setFocusRequest] = useState<{
    key: string;
    version: number;
    origin: Element;
  } | null>(null);
  const presentation = useContext(PresentationContext);
  const groupHost = useRef<HTMLDivElement>(null),
    groupProject = useRef(projectId);
  const [groupPresentation, setGroupPresentation] = useState(presentation);
  // Inert metadata may arrive between native Select All and typing. Reparenting a
  // focused input would replace its DOM node and discard the browser selection.
  // Apply group membership after focus leaves this form; source values stay live.
  useLayoutEffect(() => {
    const changedProject = groupProject.current !== projectId;
    groupProject.current = projectId;
    if (changedProject || !groupHost.current?.contains(document.activeElement))
      setGroupPresentation(presentation);
  }, [presentation, projectId]);
  useLayoutEffect(() => {
    const previous = focusedControl.current;
    if (!previous || previous.node.isConnected) return;
    focusedControl.current = null;
    const replacement =
      previous.kind === "submit"
        ? submitControls.current[previous.key]
        : controls.current[previous.key];
    if (
      replacement &&
      !replacement.disabled &&
      currentKeys.current.has(previous.key) &&
      document.activeElement === document.body &&
      !document.querySelector('[role="dialog"][aria-modal="true"]')
    )
      replacement.focus();
  });
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    setDraft((previous) =>
      Object.fromEntries(
        parameters.map((p) => {
          const key = keyOf(p),
            authored = String(authoredValue(p)),
            old = previous[key];
          if (!old)
            return [
              key,
              { text: authored, authored, version: 0, edited: false },
            ];
          if (old.authored === authored) return [key, old];
          const acknowledged =
            old.submitted && Object.is(old.submitted.value, authoredValue(p));
          const newerInput =
            old.submitted && old.version !== old.submitted.version;
          // An edit generation is intent, including retyping the old authored value.
          // Only the exact submitted generation may be normalized by its acknowledgement.
          if (!old.edited || (acknowledged && !newerInput))
            return [
              key,
              {
                ...old,
                text: authored,
                authored,
                edited: false,
                submitted: undefined,
              },
            ];
          return [
            key,
            {
              ...old,
              authored,
              submitted: acknowledged ? undefined : old.submitted,
            },
          ];
        }),
      ),
    );
  }, [parameters, projectId]);
  useEffect(() => {
    if (!focusRequest) return;
    const field = draft[focusRequest.key],
      control = controls.current[focusRequest.key],
      parameter = parameters.find((p) => keyOf(p) === focusRequest.key);
    // Wait for the field merge when props and the completion arrive together.
    if (
      parameter &&
      field &&
      field.authored !== String(authoredValue(parameter))
    )
      return;
    setFocusRequest(null);
    if (
      !mounted.current ||
      !currentKeys.current.has(focusRequest.key) ||
      !field ||
      !control ||
      field.version !== focusRequest.version ||
      field.text !== field.authored ||
      document.querySelector('[role="dialog"][aria-modal="true"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== focusRequest.origin)
    )
      return;
    control.focus();
  }, [focusRequest, draft, parameters]);
  function change(p: Parameter, text: string) {
    const key = keyOf(p);
    setDraft((previous) => {
      const old = previous[key] || {
        text: String(authoredValue(p)),
        authored: String(authoredValue(p)),
        version: 0,
        edited: false,
      };
      return {
        ...previous,
        [key]: { ...old, text, version: old.version + 1, edited: true },
      };
    });
  }
  if (!parameters.length)
    return (
      <p className="field-hint">
        No admitted editable parameters are declared. Inspect the authored
        source.
      </p>
    );
  // Domain form groups only arrange the same parameters; ungrouped ones stay listed.
  const groups: { id: string; label: string; items: Parameter[] }[] = [];
  const placed = new Set<string>();
  for (const group of groupPresentation.formGroups || []) {
    const items = parameters.filter(
      (p) => group.parameters.includes(p.id) && !placed.has(p.id),
    );
    items.forEach((p) => placed.add(p.id));
    if (items.length) groups.push({ id: group.id, label: group.label, items });
  }
  const rest = parameters.filter((p) => !placed.has(p.id));
  if (rest.length)
    groups.push({
      id: "__ungrouped",
      label: groups.length ? "Other parameters" : "",
      items: rest,
    });
  return (
    <div
      className="parameter-form"
      ref={groupHost}
      onBlurCapture={(event) => {
        const next = event.relatedTarget;
        if (!(next instanceof Node) || !event.currentTarget.contains(next))
          setGroupPresentation(presentation);
      }}
    >
      {groups.map((group) => (
        <fieldset className="parameter-group" key={group.id}>
          {group.label && <legend>{group.label}</legend>}
          {group.items.map((p) => {
            const key = keyOf(p),
              field = draft[key],
              text = field?.text ?? String(authoredValue(p)),
              guidanceId = `${guidancePrefix}-${encodeURIComponent(p.id)}`,
              dirty = text !== String(authoredValue(p)),
              describedBy = `${guidanceId}${dirty ? ` ${guidanceId}-draft` : ""}`;
            return (
              <form
                key={key}
                onSubmit={async (e) => {
                  e.preventDefault();
                  const version = field?.version ?? 0,
                    value =
                      (p.valueType || p.type) === "number"
                        ? Number(text)
                        : text,
                    origin = document.activeElement;
                  setDraft((previous) => ({
                    ...previous,
                    [key]: {
                      ...(previous[key] || {
                        text,
                        authored: String(authoredValue(p)),
                        version,
                        edited: true,
                      }),
                      submitted: { version, value },
                    },
                  }));
                  const acknowledged = await onSave(p.id, value);
                  if (
                    acknowledged &&
                    mounted.current &&
                    currentKeys.current.has(key) &&
                    origin
                  ) {
                    // A successful same-value numeric edit need not change props
                    // (for example 5.0 -> typed 5). Normalize only its own generation.
                    setDraft((previous) => {
                      const old = previous[key];
                      if (
                        !old ||
                        old.version !== version ||
                        old.authored !== String(value)
                      )
                        return previous;
                      return {
                        ...previous,
                        [key]: {
                          ...old,
                          text: old.authored,
                          edited: false,
                          submitted: undefined,
                        },
                      };
                    });
                    setFocusRequest({ key, version, origin });
                  }
                }}
              >
                <label>
                  {p.label || p.id}
                  <span className="unit-label">
                    {p.unit || "unit not declared"}
                  </span>
                  {p.enum ? (
                    <select
                      ref={(node) => {
                        if (node) controls.current[key] = node;
                        else delete controls.current[key];
                      }}
                      value={text}
                      onChange={(e) => change(p, e.target.value)}
                      onFocus={(e) => {
                        focusedControl.current = {
                          key,
                          kind: "value",
                          node: e.currentTarget,
                        };
                      }}
                      onBlur={(e) => {
                        if (
                          focusedControl.current?.node === e.currentTarget &&
                          e.currentTarget.isConnected
                        )
                          focusedControl.current = null;
                      }}
                      aria-describedby={describedBy}
                    >
                      {p.enum.map((value) => (
                        <option key={value}>{value}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      ref={(node) => {
                        if (node) controls.current[key] = node;
                        else delete controls.current[key];
                      }}
                      type={
                        (p.valueType || p.type) === "number" ? "number" : "text"
                      }
                      step="any"
                      min={p.minimum}
                      max={p.maximum}
                      value={text}
                      onChange={(e) => change(p, e.target.value)}
                      onFocus={(e) => {
                        focusedControl.current = {
                          key,
                          kind: "value",
                          node: e.currentTarget,
                        };
                      }}
                      onBlur={(e) => {
                        if (
                          focusedControl.current?.node === e.currentTarget &&
                          e.currentTarget.isConnected
                        )
                          focusedControl.current = null;
                      }}
                      aria-describedby={describedBy}
                      required
                    />
                  )}
                </label>
                <p className="field-hint" id={guidanceId}>
                  {p.description ||
                    "Value from authored Scenario configuration."}
                </p>
                {dirty && (
                  <p
                    className="field-hint"
                    id={`${guidanceId}-draft`}
                    role="status"
                  >
                    Unsaved value. Current saved value:{" "}
                    {String(authoredValue(p))}.
                  </p>
                )}
                <div className="parameter-source">
                  <span>
                    {p.source || "Scenario XDL"}
                    {p.default !== undefined ? ` · default ${p.default}` : ""}
                  </span>
                  <button
                    ref={(node) => {
                      if (node) submitControls.current[key] = node;
                      else delete submitControls.current[key];
                    }}
                    className="small-button"
                    disabled={text === String(authoredValue(p))}
                    onFocus={(e) => {
                      focusedControl.current = {
                        key,
                        kind: "submit",
                        node: e.currentTarget,
                      };
                    }}
                    onBlur={(e) => {
                      if (
                        focusedControl.current?.node === e.currentTarget &&
                        e.currentTarget.isConnected
                      )
                        focusedControl.current = null;
                    }}
                  >
                    Apply
                  </button>
                </div>
              </form>
            );
          })}
        </fieldset>
      ))}
    </div>
  );
}
export function ConnectionsView({
  projection,
  edit,
  projectId,
  revision,
  onOpenView,
  runId,
  runState,
}: {
  projection: Projection;
  edit: (edits: Data[]) => Promise<unknown>;
  projectId: string;
  revision: number;
  onOpenView?: (view: string) => void;
  runId?: string;
  runState?: string;
}) {
  const [source, setSource] = useState(""),
    [target, setTarget] = useState(""),
    [id, setId] = useState("");
  const system = projection.resources.find((r) => r.kind === "System"),
    endpoints: Data[] = system?.spec?.endpoints || [],
    interfaces: Data[] = system?.spec?.interfaces || [];
  const term = useTerm();
  const { report, failure } = useConnectionAdmission(projectId, revision),
    guidance = targetGuidance(endpoints, interfaces, source),
    chosen = guidance.find((g) => g.endpoint.id === target);
  return (
    <div className="view-page">
      <div className="section-heading">
        <div>
          <h2>Connections</h2>
          <p>
            Inspect declared {term("Flow").toLowerCase()} flows and their
            explicit endpoint contracts.
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
                  <th>Admission</th>
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
                    <td>
                      {flow.timeDomainId ||
                        (report?.connections
                          .find(
                            (c: Data) =>
                              c.ref === `${flow.systemRef}#${flow.id}`,
                          )
                          ?.checks.some(
                            (check: Data) => check.code === "CLOCK_AMBIGUOUS",
                          )
                          ? "Ambiguous"
                          : "System default")}
                    </td>
                    <td>
                      <AdmissionCell
                        connection={report?.connections.find(
                          (c: Data) => c.ref === `${flow.systemRef}#${flow.id}`,
                        )}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <AdmissionSummary report={report} failure={failure} />
          <CommunicationProjections
            projectId={projectId}
            revision={revision}
            runId={runId}
            runState={runState}
          />
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
            The authoritative validator checks direction and interface identity;
            admission then reports multiplicity, clock, compatibility and
            feedback. Studio never converts: a conversion needs an explicit
            converter declaration that the selected provider admits.
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
                pattern="[a-z][a-z0-9]*(-[a-z0-9]+)*"
                aria-describedby="flow-id-guidance"
                aria-invalid={
                  id.length > 0 && !/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(id)
                }
              />
            </label>
            <p className="field-hint" id="flow-id-guidance">
              Start with a lowercase letter; use lowercase letters and digits
              separated by single hyphens.
            </p>
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
                aria-describedby="target-guidance"
              >
                <option value="">Choose an input</option>
                {guidance.map(({ endpoint, compatible, reason }) => (
                  <option
                    key={endpoint.id}
                    value={endpoint.id}
                    disabled={!compatible}
                  >
                    {endpoint.id} · {endpoint.interfaceId}
                    {compatible ? "" : ` — ${reason}`}
                  </option>
                ))}
              </select>
            </label>
            <p className="field-hint" id="target-guidance" role="status">
              {!source
                ? "Choose a source to see compatible destinations first."
                : chosen?.reason ||
                  `${guidance.filter((g) => g.compatible).length} compatible destination(s); incompatible ones are listed with their reason.`}
            </p>
            <button
              className="button primary"
              disabled={!source || !target || !id || !chosen?.compatible}
            >
              <Icon name="connection" />
              Validate & connect
            </button>
          </form>
          <hr />
          <FlowContractForm
            flows={projection.connections}
            interfaces={interfaces}
            report={report}
            edit={edit}
          />
          <hr />
          <RelationKinds
            projection={projection}
            report={report}
            onOpenView={onOpenView}
          />
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
  providerId = "studio.reference",
}: {
  header?: boolean;
  projection: Projection;
  providers: Data[];
  edit: (edits: Data[]) => Promise<unknown>;
  providerId?: string;
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
          <BindingForm
            deployment={d}
            onSave={edit}
            provider={providers.find((p) => p.providerId === providerId)}
          />
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
  target,
}: {
  target?: SourceTarget;
  project: Project;
  doAction: DoAction;
  onSaved: (saved: Project) => boolean;
}) {
  type Draft = {
    projectId: string;
    id: string;
    content: string;
    history: string[];
    future: string[];
    recovered: boolean;
    recoveryUnavailable: boolean;
  };
  const ids = Object.keys(project.documents);
  function loadDraft(id: string): Draft {
    const original = documentContent(project.documents[id] ?? "");
    let saved: string | null = null,
      recoveryUnavailable = false;
    try {
      saved = sessionStorage.getItem(`studio.draft.${project.projectId}.${id}`);
    } catch {
      recoveryUnavailable = true;
    }
    return {
      projectId: project.projectId,
      id,
      content: saved ?? original,
      history: [],
      future: [],
      recovered: saved !== null && saved !== original,
      recoveryUnavailable,
    };
  }
  const [draft, setDraft] = useState<Draft>(() =>
    loadDraft(
      target?.documentId && ids.includes(target.documentId)
        ? target.documentId
        : ids[0] || "",
    ),
  );
  const activeDraft = useRef(draft),
    latestSourceProject = useRef(project),
    mounted = useRef(true),
    sending = useRef(false),
    guidanceId = useId();
  latestSourceProject.current = project;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const { id, content, history, future, recovered } = draft;
  const contentBytes = useMemo(
    () => new TextEncoder().encode(content).byteLength,
    [content],
  );
  const [compare, setCompare] = useState(false),
    [saving, setSaving] = useState(false),
    [recoveryError, setRecoveryError] = useState(""),
    [saveError, setSaveError] = useState<Error | null>(null),
    [saveFocus, setSaveFocus] = useState<{
      id: string;
      content: string;
      origin: Element | null;
    } | null>(null);
  function replaceDraft(next: Draft) {
    activeDraft.current = next;
    setDraft(next);
  }
  function persistDraft(value: Draft) {
    // Do not replace an unread cached draft with the canonical fallback or new text.
    if (value.recoveryUnavailable) return;
    const currentProject = latestSourceProject.current,
      original = documentContent(currentProject.documents[value.id] ?? ""),
      key = `studio.draft.${value.projectId}.${value.id}`;
    if (
      value.projectId !== currentProject.projectId ||
      !Object.hasOwn(currentProject.documents, value.id)
    )
      return;
    if (value.content === original) sessionStorage.removeItem(key);
    else if (new TextEncoder().encode(value.content).byteLength <= 524288)
      sessionStorage.setItem(key, value.content);
  }
  function switchDocument(nextId: string) {
    if (saving || !Object.hasOwn(project.documents, nextId)) return;
    try {
      persistDraft(activeDraft.current);
    } catch {
      setRecoveryError(
        "Browser draft recovery is unavailable. Keep a local copy before closing this editor.",
      );
    }
    replaceDraft(loadDraft(nextId));
    setSaveError(null);
    anchored.current = false;
    setAnchorNotice("");
  }
  const textarea = useRef<HTMLTextAreaElement>(null),
    anchored = useRef(false);
  const [anchorNotice, setAnchorNotice] = useState("");
  function goToDeclaration() {
    if (id !== target?.documentId || (!target.ref && !target.elementId)) return;
    try {
      const doc = parseDocument(content),
        roots = isSeq(doc.contents) ? doc.contents.items : [doc.contents];
      for (const root of roots) {
        if (!isMap(root)) continue;
        const metadata = root.get("metadata", true),
          resourceKind = root.get("kind");
        if (target.ref && isMap(metadata)) {
          const resourceRef = `xdl://${metadata.get("namespace")}/${String(resourceKind).toLowerCase()}/${metadata.get("name")}`;
          if (target.ref.split("#")[0] !== resourceRef) continue;
        }
        let entry: unknown = root;
        if (target.elementId && target.collection) {
          const spec = root.get("spec", true);
          if (!isMap(spec)) continue;
          const entries = spec.get(target.collection, true);
          if (!isSeq(entries)) continue;
          entry = entries.items.find(
            (item) => isMap(item) && item.get("id") === target.elementId,
          );
        }
        if (isMap(entry) && entry.range && textarea.current) {
          textarea.current.focus();
          textarea.current.setSelectionRange(entry.range[0], entry.range[1]);
          const line = content.slice(0, entry.range[0]).split("\n").length - 1;
          textarea.current.scrollTop = Math.max(
            0,
            line * parseFloat(getComputedStyle(textarea.current).lineHeight) -
              40,
          );
          setAnchorNotice("Selected declaration highlighted in this draft.");
          return;
        }
      }
    } catch {
      /* Invalid drafts remain editable; never infer an approximate semantic anchor. */
    }
    setAnchorNotice(
      "The selected declaration could not be located in this draft. Inspect the source or compare it with the saved revision.",
    );
  }
  useEffect(() => {
    if (!anchored.current && content && (target?.elementId || target?.ref)) {
      anchored.current = true;
      goToDeclaration();
    }
  }, [content, id]);
  const externalSource = project.sourceIntegrity === "modified";
  const identityMatches =
    draft.projectId === project.projectId &&
    Object.hasOwn(project.documents, id);
  const baseline = documentContent(project.documents[id] ?? "");
  const dirty = identityMatches && content !== baseline;
  const recoveryMessage =
    contentBytes > 524288 && dirty
      ? "This draft exceeds the 512 KiB browser recovery limit. Keep a local copy before closing."
      : recoveryError;
  useEffect(() => {
    if (saving || !saveFocus) return;
    setSaveFocus(null);
    if (
      saveFocus.id === id &&
      saveFocus.content === content &&
      identityMatches &&
      textarea.current &&
      !textarea.current.disabled &&
      document.querySelector('[role="dialog"]') ===
        textarea.current.closest('[role="dialog"]') &&
      (document.activeElement === document.body ||
        document.activeElement === saveFocus.origin)
    )
      textarea.current.focus();
  }, [saving, saveFocus, id, content, identityMatches]);
  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        persistDraft(draft);
        setRecoveryError("");
      } catch {
        setRecoveryError(
          "Browser draft recovery is unavailable. Keep a local copy before closing this editor.",
        );
      }
    }, 500);
    return () => {
      clearTimeout(timer);
      try {
        persistDraft(activeDraft.current);
      } catch {
        /* Storage quota cannot make source text executable or target another document. */
      }
    };
  }, [draft, baseline, contentBytes]);
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
    const current = activeDraft.current;
    setSaveError(null);
    replaceDraft({
      ...current,
      history: [...current.history.slice(-49), current.content],
      future: [],
      content: value,
    });
  }
  function undo() {
    const current = activeDraft.current;
    if (!current.history.length || saving) return;
    replaceDraft({
      ...current,
      future: [current.content, ...current.future].slice(0, 50),
      content: current.history[current.history.length - 1],
      history: current.history.slice(0, -1),
    });
  }
  function redo() {
    const current = activeDraft.current;
    if (!current.future.length || saving) return;
    replaceDraft({
      ...current,
      history: [...current.history.slice(-49), current.content],
      content: current.future[0],
      future: current.future.slice(1),
    });
  }
  return (
    <div className="source-editor">
      <div className="source-toolbar">
        <label>
          Resource
          <select
            aria-label="Resource"
            value={id}
            disabled={saving || !identityMatches}
            onChange={(e) => switchDocument(e.target.value)}
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
        <Badge tone={externalSource || dirty ? "warning" : "success"}>
          {externalSource
            ? "Inspected external bytes"
            : dirty
              ? "Unsaved draft"
              : "Saved revision"}
        </Badge>
        <div className="source-tools">
          <button
            className="small-button"
            disabled={saving || !history.length}
            onClick={undo}
          >
            Undo
          </button>
          <button
            className="small-button"
            disabled={saving || !future.length}
            onClick={redo}
          >
            Redo
          </button>
          <button className="small-button" onClick={() => setCompare(!compare)}>
            {compare ? "Editor only" : "Compare changes"}
          </button>
        </div>
      </div>
      {target && id === target.documentId && (
        <div className="source-context">
          <code>{target.ref || target.documentId}</code>
          {target.elementId && (
            <>
              <span>
                spec.{target.collection}[id={target.elementId}]
              </span>
            </>
          )}
          {(target.ref || target.elementId) && (
            <button className="small-button" onClick={goToDeclaration}>
              Go to selected declaration
            </button>
          )}
          <span role="status">{anchorNotice}</span>
        </div>
      )}
      {externalSource && (
        <div className="notice" role="alert">
          Source files changed outside Studio. These are inspected external
          bytes, not an admitted saved revision. Keep a local copy before
          recovery. Local drafts remain editable; saving and execution are
          blocked.
          <Json value={project.sourceDiagnostics || []} />
        </div>
      )}
      {(recoveryMessage || draft.recoveryUnavailable) && (
        <p role="alert" className="notice">
          {draft.recoveryUnavailable &&
            "Browser draft recovery could not be read. The unread cache is preserved. Keep a local copy before closing this editor. "}
          {recoveryMessage}
        </p>
      )}
      {saveError && (
        <p role="alert" className="error-banner">
          {saveError instanceof ApiError ? `${saveError.code}: ` : ""}
          {saveError.message}{" "}
          {saveError instanceof ApiError &&
          saveError.code === "REVISION_CONFLICT"
            ? "Your draft is retained. Close this editor to load the current revision, then compare it before saving again."
            : "Your draft remains in this editor. Review the error and keep a local copy. Correct the source or retry when the service is available."}
        </p>
      )}
      {!identityMatches && (
        <p role="alert" className="error-banner">
          The selected document belongs to a different project revision. Reopen
          the editor before saving.
        </p>
      )}
      {recovered && (
        <p className="notice">
          <span>
            Recovered an uncommitted draft from this browser tab. Review it
            before saving.
          </span>{" "}
          This is the last cached text; newer uncached edits may be missing.
        </p>
      )}
      <p className="field-hint" id={guidanceId}>
        Exact authored content is retained. Unknown extensions stay intact;
        platform validation decides whether the revision is executable. Saving
        changes only the draft.
      </p>
      <div className={`source-panels ${compare ? "compare" : ""}`}>
        {compare && (
          <div>
            <span className="source-pane-label">
              {externalSource ? "Inspected external bytes" : "Saved revision"}
            </span>
            <pre className="source-baseline">{baseline}</pre>
          </div>
        )}
        <div>
          <label className="source-pane-label" htmlFor="xdl-source">
            {compare ? "Edited draft" : "XDL source"}
          </label>
          <textarea
            ref={textarea}
            id="xdl-source"
            className="source-textarea"
            aria-describedby={guidanceId}
            disabled={saving || !identityMatches}
            spellCheck={false}
            value={content}
            onChange={(e) => change(e.target.value)}
            onKeyDown={(e) => {
              if (e.altKey || e.nativeEvent.isComposing) return;
              const key = e.key.toLowerCase();
              if ((e.ctrlKey || e.metaKey) && key === "s") {
                e.preventDefault();
                void save();
              }
              if ((e.ctrlKey || e.metaKey) && key === "z") {
                e.preventDefault();
                e.shiftKey ? redo() : undo();
              }
            }}
          />
        </div>
      </div>
      <div className="source-footer">
        <span>
          {externalSource
            ? "Recorded revision (externally modified source)"
            : "Draft revision"}{" "}
          <code>{String(project.revision).slice(0, 12)}</code> · UTF-8 ·{" "}
          {contentBytes.toLocaleString()} bytes
        </span>
        <button
          className="button primary"
          disabled={saving || externalSource || !dirty || !identityMatches}
          onClick={() => void save()}
        >
          <Icon name="check" />
          Save source revision
        </button>
      </div>
    </div>
  );
  async function save() {
    const submitted = activeDraft.current,
      document = project.documents[submitted.id];
    if (
      sending.current ||
      externalSource ||
      submitted.projectId !== project.projectId ||
      !Object.hasOwn(project.documents, submitted.id) ||
      submitted.content === documentContent(document)
    )
      return;
    sending.current = true;
    setSaving(true);
    setSaveError(null);
    const origin = window.document.activeElement;
    try {
      await doAction("Saving source revision", async () => {
        let saved: Project;
        try {
          saved = await api<Project>(
            `/projects/${submitted.projectId}/documents/${encodeURIComponent(submitted.id)}`,
            {
              method: "PUT",
              revision: project.revision,
              body: {
                content: submitted.content,
                format: typeof document === "string" ? "yaml" : document.format,
              },
            },
          );
        } catch (error) {
          if (
            mounted.current &&
            activeDraft.current.id === submitted.id &&
            activeDraft.current.content === submitted.content
          )
            setSaveError(
              error instanceof Error ? error : new Error("Source save failed."),
            );
          throw error;
        }
        const current = onSaved(saved);
        if (!mounted.current || !current) return;
        if (saved.revision > latestSourceProject.current.revision)
          latestSourceProject.current = saved;
        const key = `studio.draft.${submitted.projectId}.${submitted.id}`;
        try {
          if (sessionStorage.getItem(key) === submitted.content)
            sessionStorage.removeItem(key);
        } catch {
          setRecoveryError(
            "The revision was saved, but browser draft recovery is unavailable. Keep a local copy before closing this editor.",
          );
        }
        if (
          activeDraft.current.id === submitted.id &&
          activeDraft.current.content === submitted.content
        )
          replaceDraft({ ...activeDraft.current, recovered: false });
      });
    } finally {
      sending.current = false;
      if (mounted.current) {
        setSaving(false);
        setSaveFocus({ id: submitted.id, content: submitted.content, origin });
      }
    }
  }
}

// The XDL realization classes; the selected provider may execute only some of them.
const REALIZATION_CLASSES = ["simulated", "virtual", "physical", "hybrid"];

function BindingForm({
  deployment,
  onSave,
  provider,
}: {
  deployment: Data;
  onSave: (edits: Data[]) => Promise<unknown>;
  provider?: Data;
}) {
  const supported: string[] | undefined = provider?.realizationClasses;
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
              {REALIZATION_CLASSES.map((value) => (
                <option key={value} value={value}>
                  {value[0].toUpperCase() + value.slice(1)}
                  {supported && !supported.includes(value)
                    ? ` (not executable by ${provider?.providerId})`
                    : ""}
                </option>
              ))}
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
