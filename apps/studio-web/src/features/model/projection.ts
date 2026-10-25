import { parse } from "yaml";
import type { Project, Data, Parameter } from "../../api/types";
export interface ElementProjection {
  id: string;
  ref: string;
  systemRef: string;
  kind: string;
  name: string;
  role: string;
  nodeId: string;
  componentRef?: Data;
  documentId: string;
  raw: Data;
  definition?: Data;
  parameters: Parameter[];
}
export interface Projection {
  resources: Data[];
  elements: ElementProjection[];
  connections: Data[];
  deployments: Data[];
  scenarios: Data[];
  parameters: Parameter[];
  parseErrors: string[];
}
const records = (value: unknown): Data[] =>
  Array.isArray(value)
    ? value.filter((v) => v && typeof v === "object" && !Array.isArray(v))
    : [];
const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((v) => typeof v === "string") : [];
const text = (value: unknown, fallback = "Unresolved") =>
  typeof value === "string"
    ? value
    : typeof value === "number"
      ? String(value)
      : fallback;
/** Safe display projection only. This function neither validates XDL nor creates executable inputs. */
export function projectDisplay(project: Project | null): Projection {
  const result: Projection = {
    resources: [],
    elements: [],
    connections: [],
    deployments: [],
    scenarios: [],
    parameters: [],
    parseErrors: [],
  };
  if (!project) return result;
  for (const [documentId, document] of Object.entries(
    project.documents || {},
  )) {
    try {
      const content =
        typeof document === "string" ? document : document.content;
      const parsed = parse(content, { maxAliasCount: 50 });
      for (const raw of Array.isArray(parsed) ? parsed : [parsed]) {
        if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
          result.parseErrors.push(documentId);
          continue;
        }
        const spec =
          raw.spec && typeof raw.spec === "object" && !Array.isArray(raw.spec)
            ? raw.spec
            : {};
        result.resources.push({
          ...raw,
          documentId,
          kind: text(raw.kind),
          apiVersion: text(raw.apiVersion),
          metadata: {
            ...raw.metadata,
            name: text(raw.metadata?.name, documentId),
            namespace: text(raw.metadata?.namespace),
            version: text(raw.metadata?.version),
            description: text(raw.metadata?.description, ""),
          },
          spec,
        });
      }
    } catch {
      result.parseErrors.push(documentId);
    }
  }
  for (const resource of result.resources) {
    const spec = resource.spec;
    if (resource.kind === "System") {
      const systemRef = `xdl://${resource.metadata.namespace}/system/${resource.metadata.name}`;
      const instances = records(spec.componentInstances),
        nodes = records(spec.nodes),
        endpoints = records(spec.endpoints).filter(
          (e) => typeof e.id === "string" && typeof e.ownerId === "string",
        );
      spec.endpoints = endpoints.map((e) => ({
        ...e,
        interfaceId: text(e.interfaceId),
        direction: text(e.direction),
      }));
      for (const instance of instances) {
        if (typeof instance.id !== "string") {
          result.parseErrors.push(resource.documentId);
          continue;
        }
        const definition = result.resources.find(
          (r) =>
            r.kind === "Component" &&
            r.metadata?.name === instance.componentRef?.name &&
            r.metadata?.namespace === instance.componentRef?.namespace,
        );
        const node = nodes.find((n) => n.id === instance.nodeId);
        result.elements.push({
          id: instance.id,
          ref: `${systemRef}#${instance.id}`,
          systemRef,
          kind: "componentInstance",
          name: text(instance.displayName, instance.id),
          role: strings(node?.roles).join(", ") || "component",
          nodeId: text(instance.nodeId, "Unplaced"),
          componentRef: instance.componentRef,
          documentId: resource.documentId,
          raw: instance,
          definition,
          parameters: [],
        });
      }
      for (const node of nodes) {
        if (
          typeof node.id === "string" &&
          !instances.some((instance) => instance.nodeId === node.id)
        )
          result.elements.push({
            id: node.id,
            ref: `${systemRef}#${node.id}`,
            systemRef,
            kind: "node",
            name: node.id,
            role: strings(node.roles).join(", ") || "node",
            nodeId: node.id,
            documentId: resource.documentId,
            raw: node,
            parameters: [],
          });
      }
      for (const [collection, kind] of [
        ["devices", "device"],
        ["sensors", "sensor"],
        ["actuators", "actuator"],
        ["models", "model"],
      ]) {
        for (const asset of records(spec[collection])) {
          if (typeof asset.id !== "string") {
            result.parseErrors.push(resource.documentId);
            continue;
          }
          result.elements.push({
            id: asset.id,
            ref: `${systemRef}#${asset.id}`,
            systemRef,
            kind,
            name: text(asset.displayName, asset.id),
            role: kind,
            nodeId: text(asset.nodeId, "Unplaced"),
            documentId: resource.documentId,
            raw: asset,
            parameters: [],
          });
        }
        if (spec[collection] && !Array.isArray(spec[collection]))
          result.parseErrors.push(resource.documentId);
      }
      for (const flow of records(spec.flows)) {
        if (typeof flow.id !== "string") {
          result.parseErrors.push(resource.documentId);
          continue;
        }
        result.connections.push({
          ...flow,
          systemRef,
          id: flow.id,
          sourceEndpointId: text(flow.sourceEndpointId),
          destinationEndpointIds: strings(flow.destinationEndpointIds),
          interfaceId: text(flow.interfaceId),
          timeDomainId: text(flow.timeDomainId),
          documentId: resource.documentId,
        });
      }
      if (
        (spec.componentInstances && !Array.isArray(spec.componentInstances)) ||
        (spec.nodes && !Array.isArray(spec.nodes)) ||
        (spec.flows && !Array.isArray(spec.flows))
      )
        result.parseErrors.push(resource.documentId);
    }
    if (resource.kind === "Deployment") {
      const bindings = records(spec.bindings).map((b) => ({
        ...b,
        id: text(b.id),
        realizationClass: text(b.realizationClass),
        targetId: text(b.targetId),
        artifactIds: strings(b.artifactIds),
        logicalRef:
          typeof b.logicalRef === "object"
            ? b.logicalRef
            : { name: text(b.logicalRef) },
      }));
      const targets = records(spec.targets).map((t) => ({
        ...t,
        id: text(t.id),
        targetClass: text(t.targetClass),
      }));
      const artifacts = records(spec.artifacts).map((a) => ({
        ...a,
        id: text(a.id),
        artifactKind: text(a.artifactKind),
        version: text(a.version),
        digest: text(a.digest),
        sourceRef: text(a.sourceRef),
        maturity: text(a.maturity),
        limitations: strings(a.limitations),
      }));
      result.deployments.push({
        ...resource,
        spec: { ...spec, bindings, targets, artifacts },
      });
    }
    if (resource.kind === "Scenario") {
      const steps = records(spec.steps).map((s) => ({
        ...s,
        id: text(s.id),
        actionKind: text(s.actionKind),
        timeDomainId: text(s.timeDomainId),
        schedule: {
          at: text(s.schedule?.at, "?"),
          unit: text(s.schedule?.unit, "ticks"),
        },
      }));
      const observers = records(spec.observers).map((o) => ({
        ...o,
        id: text(o.id),
        samplingIntent: text(o.samplingIntent),
        timeDomainId: text(o.timeDomainId),
        unitSemantics: text(o.unitSemantics),
      }));
      const metrics = records(spec.metrics).map((m) => ({
        ...m,
        id: text(m.id),
        acceptance: text(m.acceptance),
        calculationRef: text(m.calculationRef),
      }));
      result.scenarios.push({
        ...resource,
        spec: {
          ...spec,
          steps,
          observers,
          metrics,
          acceptanceIntent: text(spec.acceptanceIntent, ""),
        },
      });
      const parameters = (resource.extensions || spec.extensions)?.[
        "io.xverse.experiment"
      ]?.parameters;
      for (const p of records(parameters)) {
        if (typeof p.id === "string")
          result.parameters.push({
            ...p,
            id: p.id,
            unit: text(p.unitSemantics),
            source: "Scenario XDL extension",
            documentId: resource.documentId,
            scenarioRef: `xdl://${resource.metadata.namespace}/scenario/${resource.metadata.name}`,
          });
      }
    }
  }
  return result;
}
export function textRef(value: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const v = value as Data;
    return [v.namespace, v.name, v.element || v.endpoint || v.id]
      .filter(Boolean)
      .map((v) => text(v))
      .join("/");
  }
  return "Not declared";
}
export function documentContent(document: Project["documents"][string]) {
  return typeof document === "string" ? document : document.content;
}

export interface ElementGroup {
  key: string;
  systemRef: string;
  /** Null for elements the System does not place on any node. */
  nodeId: string | null;
  roles: string[];
  /** declared: the System declares the node; undeclared: referenced only; unplaced: no node. */
  placement: "declared" | "undeclared" | "unplaced";
  members: ElementProjection[];
  /** Members listed by the node's memberIds but placed elsewhere or not placed. */
  listedOnly: string[];
}

const placementOf = (element: ElementProjection) =>
  element.kind === "node"
    ? element.id
    : typeof element.raw?.nodeId === "string"
      ? element.raw.nodeId
      : null;

/** Presentation grouping by XDL node placement (nodeId and memberIds); it adds no semantics. */
export function groupByNode(projection: Projection): ElementGroup[] {
  const declared = new Map<string, ElementGroup>(),
    listed = new Map<string, string[]>();
  for (const resource of projection.resources) {
    if (resource.kind !== "System") continue;
    const systemRef = `xdl://${resource.metadata?.namespace}/system/${resource.metadata?.name}`;
    for (const node of records(resource.spec?.nodes)) {
      if (typeof node.id !== "string") continue;
      const key = `${systemRef}#${node.id}`;
      declared.set(key, {
        key,
        systemRef,
        nodeId: node.id,
        roles: strings(node.roles),
        placement: "declared",
        members: [],
        listedOnly: [],
      });
      listed.set(key, strings(node.memberIds));
    }
  }
  const undeclared = new Map<string, ElementGroup>(),
    unplaced = new Map<string, ElementGroup>();
  for (const element of projection.elements) {
    const nodeId = placementOf(element);
    if (nodeId === null) {
      const key = `${element.systemRef}#unplaced`;
      if (!unplaced.has(key))
        unplaced.set(key, {
          key,
          systemRef: element.systemRef,
          nodeId: null,
          roles: [],
          placement: "unplaced",
          members: [],
          listedOnly: [],
        });
      unplaced.get(key)!.members.push(element);
      continue;
    }
    const key = `${element.systemRef}#${nodeId}`;
    const group =
      declared.get(key) ||
      undeclared.get(key) ||
      undeclared
        .set(key, {
          key,
          systemRef: element.systemRef,
          nodeId,
          roles: [],
          placement: "undeclared",
          members: [],
          listedOnly: [],
        })
        .get(key)!;
    group.members.push(element);
  }
  for (const [key, ids] of listed) {
    const group = declared.get(key)!;
    for (const id of ids) {
      const element = projection.elements.find(
        (e) => e.systemRef === group.systemRef && e.id === id,
      );
      if (element && !group.members.includes(element)) {
        group.members.push(element);
        group.listedOnly.push(element.ref);
      }
    }
  }
  return [...declared.values(), ...undeclared.values(), ...unplaced.values()];
}
