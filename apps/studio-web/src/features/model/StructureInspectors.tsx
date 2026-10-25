import type { Data } from "../../api/types";
import { Badge, KeyValues } from "../../app/ui";
import type { ElementGroup, ElementProjection } from "./projection";
import type { SourceTarget } from "./Views";
import { groupLabel } from "./tree/ModelTree";

const qualified = (resource: Data) =>
  `xdl://${resource.metadata?.namespace}/${String(resource.kind).toLowerCase()}/${resource.metadata?.name}`;

/** System › node › element › definition; each level is a keyboard-reachable button. */
export function ModelBreadcrumb({
  systemName,
  group,
  element,
  definition,
  onSystem,
  onGroup,
  onElement,
}: {
  systemName: string;
  group?: ElementGroup;
  element?: ElementProjection;
  definition?: Data;
  onSystem: () => void;
  onGroup: (key: string) => void;
  onElement: (ref: string) => void;
}) {
  // A node-kind element is the node itself; it is not repeated as a child step.
  const step = element && element.kind !== "node" ? element : undefined;
  return (
    <nav className="model-breadcrumb" aria-label="Model location">
      <button className="text-button" onClick={onSystem}>
        {systemName}
      </button>
      {group && (
        <>
          <span aria-hidden="true">›</span>
          <button className="text-button" onClick={() => onGroup(group.key)}>
            {groupLabel(group)}
          </button>
        </>
      )}
      {step && (
        <>
          <span aria-hidden="true">›</span>
          {/* The current location is text; it becomes a link back only below a definition. */}
          {definition ? (
            <button className="text-button" onClick={() => onElement(step.ref)}>
              {step.name}
            </button>
          ) : (
            <span aria-current="location">{step.name}</span>
          )}
        </>
      )}
      {definition && (
        <>
          <span aria-hidden="true">›</span>
          <span aria-current="location">{definition.metadata?.name}</span>
        </>
      )}
    </nav>
  );
}

export function NodeInspector({
  group,
  onSelectElement,
  onSource,
}: {
  group: ElementGroup;
  onSelectElement: (ref: string) => void;
  onSource: (target: SourceTarget) => void;
}) {
  const declaring =
    group.placement === "declared" && group.nodeId
      ? group.members.find((m) => m.kind === "node") || group.members[0]
      : undefined;
  return (
    <>
      <KeyValues
        values={{
          Node: groupLabel(group),
          System: group.systemRef,
          Roles: group.roles.length ? group.roles.join(", ") : "Not declared",
          Placement:
            group.placement === "declared"
              ? "Declared by the System"
              : group.placement === "undeclared"
                ? "Referenced by nodeId but not declared"
                : "These elements are not placed on any node",
          Members: group.members.length,
        }}
      />
      <p className="field-hint">
        Node placement groups logical elements; it is not a deployment target or
        a physical location.
      </p>
      <h4>Members</h4>
      <ul className="node-members">
        {group.members.map((member) => (
          <li key={member.ref}>
            <button
              className="text-button"
              onClick={() => onSelectElement(member.ref)}
            >
              {member.name}
            </button>{" "}
            <Badge>{member.kind}</Badge>
            {group.listedOnly.includes(member.ref) && (
              <small>
                {" "}
                listed in memberIds; placed {member.raw?.nodeId ?? "nowhere"}
              </small>
            )}
          </li>
        ))}
      </ul>
      {declaring && (
        <div className="inspector-actions">
          <button
            className="button"
            onClick={() =>
              onSource({
                documentId: declaring.documentId,
                ref: group.key,
                elementId: group.nodeId ?? undefined,
                collection: "nodes",
              })
            }
          >
            View node declaration
          </button>
        </div>
      )}
    </>
  );
}

export function DefinitionInspector({
  element,
  onBack,
  onSource,
}: {
  element: ElementProjection;
  onBack: () => void;
  onSource: (target: SourceTarget) => void;
}) {
  const definition = element.definition!,
    spec = definition.spec || {},
    list = (value: unknown): Data[] => (Array.isArray(value) ? value : []);
  return (
    <>
      <KeyValues
        values={{
          Definition: qualified(definition),
          Version: definition.metadata?.version || "Not declared",
          "Used by": element.ref,
          Capabilities: list(spec.capabilities).join(", ") || "Not declared",
        }}
      />
      <p className="field-hint">
        Read-only Component definition. Instance identity, placement and
        bindings stay on the System element.
      </p>
      <h4>Interfaces</h4>
      {list(spec.interfaces).map((item) => (
        <div className="port-row" key={item.id}>
          <code>{item.id}</code>
          <Badge>{item.direction}</Badge>
          <small>
            {item.payloadSchema} · unit {String(item.unitSemantics ?? "–")}
          </small>
        </div>
      ))}
      <h4>Named ports</h4>
      {list(spec.endpoints).map((item) => (
        <div className="port-row" key={item.id}>
          <span className="port-dot" />
          <code>{item.id}</code>
          <Badge>{item.direction}</Badge>
          <small>{item.interfaceId}</small>
        </div>
      ))}
      {list(spec.parameters).length > 0 && (
        <>
          <h4>Parameters</h4>
          {list(spec.parameters).map((item) => (
            <div className="port-row" key={item.id}>
              <code>{item.id}</code>
              <small>
                {item.valueType ?? ""} {item.unitSemantics ?? ""}
              </small>
            </div>
          ))}
        </>
      )}
      {list(spec.models).length > 0 && (
        <>
          <h4>Models</h4>
          {list(spec.models).map((item) => (
            <div className="port-row" key={item.id}>
              <code>{item.id}</code>
              <Badge>{item.modelKind}</Badge>
              <small>{item.externalRef}</small>
            </div>
          ))}
        </>
      )}
      <div className="inspector-actions">
        <button className="button" onClick={onBack}>
          Back to element
        </button>
        <button
          className="button"
          onClick={() =>
            onSource({
              documentId: definition.documentId,
              ref: qualified(definition),
            })
          }
        >
          View definition source
        </button>
      </div>
    </>
  );
}
