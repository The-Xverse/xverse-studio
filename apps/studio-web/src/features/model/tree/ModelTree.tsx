import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { Icon } from "../../../app/ui";
import type { ElementGroup, ElementProjection } from "../projection";

interface Item {
  id: string;
  kind: "group" | "member";
  group: ElementGroup;
  element?: ElementProjection;
}

export const groupLabel = (group: ElementGroup) =>
  group.nodeId ?? "Not placed on a node";
export const placementLabel = (group: ElementGroup) =>
  group.placement === "declared"
    ? ""
    : group.placement === "undeclared"
      ? "undeclared"
      : "unplaced";

/** Keyboard tree of XDL node placement: arrows move, Right/Left expand/collapse, Enter selects. */
export function ModelTree({
  groups,
  search,
  selected,
  selectedGroup,
  onSelectElement,
  onSelectGroup,
}: {
  groups: ElementGroup[];
  search: string;
  selected: string;
  selectedGroup: string;
  onSelectElement: (ref: string) => void;
  onSelectGroup: (key: string) => void;
}) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set()),
    [focused, setFocused] = useState(""),
    refs = useRef(new Map<string, HTMLElement>());
  const query = search.trim().toLowerCase();
  // One rule for rendering and keys: a search shows every group it matches expanded.
  const isExpanded = (group: ElementGroup) =>
    Boolean(query) || !collapsed.has(group.key);
  const rows = useMemo(() => {
    const result: { group: ElementGroup; items: Item[] }[] = [];
    for (const group of groups) {
      const groupMatches = `${groupLabel(group)} ${group.roles.join(" ")}`
        .toLowerCase()
        .includes(query);
      const members =
        !query || groupMatches
          ? group.members
          : group.members.filter((e) =>
              `${e.name} ${e.id} ${e.role}`.toLowerCase().includes(query),
            );
      if (query && !members.length && !groupMatches) continue;
      result.push({
        group,
        items: (Boolean(query) || !collapsed.has(group.key) ? members : []).map(
          (element) => ({
            id: "m:" + group.key + ":" + element.ref,
            kind: "member" as const,
            group,
            element,
          }),
        ),
      });
    }
    return result;
  }, [groups, query, collapsed]);
  const visible = useMemo(
    () =>
      rows.flatMap(({ group, items }) => [
        { id: group.key, kind: "group" as const, group } as Item,
        ...items,
      ]),
    [rows],
  );
  const active =
    visible.find((item) => item.id === focused) ||
    visible.find(
      (item) =>
        (item.kind === "member" && item.element?.ref === selected) ||
        (item.kind === "group" && item.id === selectedGroup),
    ) ||
    visible[0];
  useEffect(() => {
    if (focused && !visible.some((item) => item.id === focused)) setFocused("");
  }, [visible, focused]);
  function move(item: Item | undefined) {
    if (!item) return;
    setFocused(item.id);
    refs.current.get(item.id)?.focus();
  }
  function setExpanded(key: string, open: boolean) {
    setCollapsed((old) => {
      const next = new Set(old);
      if (open) next.delete(key);
      else next.add(key);
      return next;
    });
  }
  function onKeyDown(event: KeyboardEvent) {
    if (!active || event.altKey || event.ctrlKey || event.metaKey) return;
    const index = visible.indexOf(active);
    switch (event.key) {
      case "ArrowDown":
        move(visible[index + 1]);
        break;
      case "ArrowUp":
        move(visible[index - 1]);
        break;
      case "Home":
        move(visible[0]);
        break;
      case "End":
        move(visible[visible.length - 1]);
        break;
      case "ArrowRight":
        if (active.kind === "group") {
          if (!isExpanded(active.group)) setExpanded(active.group.key, true);
          else if (visible[index + 1]?.kind === "member")
            move(visible[index + 1]);
        }
        break;
      case "ArrowLeft":
        if (active.kind === "member")
          move(visible.find((item) => item.id === active.group.key));
        else if (!query && isExpanded(active.group))
          setExpanded(active.group.key, false);
        break;
      case "Enter":
      case " ":
        if (active.kind === "group") onSelectGroup(active.group.key);
        else if (active.element) onSelectElement(active.element.ref);
        break;
      default:
        return;
    }
    event.preventDefault();
  }
  const register = (id: string) => (node: HTMLElement | null) => {
    if (node) refs.current.set(id, node);
    else refs.current.delete(id);
  };
  return (
    <ul
      className="model-tree-nodes"
      role="tree"
      aria-label="System structure by node"
      onKeyDown={onKeyDown}
    >
      {rows.length === 0 && (
        <li role="none" className="tree-empty">
          {query ? "No elements or nodes match this search." : "No elements."}
        </li>
      )}
      {rows.map(({ group, items }) => {
        const expanded = isExpanded(group),
          marker = placementLabel(group);
        return (
          <li
            key={group.key}
            role="treeitem"
            aria-expanded={expanded}
            aria-selected={selectedGroup === group.key}
            aria-label={`${groupLabel(group)}${group.nodeId ? " node" : ""}${group.roles.length ? ", " + group.roles.join(", ") : ""}${marker ? ", " + marker : ""}, ${group.members.length} members`}
            tabIndex={active?.id === group.key ? 0 : -1}
            ref={register(group.key)}
            onFocus={(event) => {
              if (event.target === event.currentTarget) setFocused(group.key);
            }}
            className="tree-group"
          >
            <div
              className={`tree-group-label ${selectedGroup === group.key ? "selected" : ""}`}
              onClick={() => {
                setFocused(group.key);
                onSelectGroup(group.key);
              }}
            >
              <span
                className="tree-twisty"
                aria-hidden="true"
                onClick={(event) => {
                  event.stopPropagation();
                  if (!query) setExpanded(group.key, !expanded);
                }}
              >
                <Icon name="chevron" size={12} />
              </span>
              <Icon name="folder" size={14} />
              <span>{groupLabel(group)}</span>
              {marker && <em className="tree-marker">({marker})</em>}
              <small className="tree-count">{group.members.length}</small>
            </div>
            {items.length > 0 && (
              <ul role="group">
                {items.map((item) => {
                  const element = item.element!;
                  return (
                    <li
                      key={item.id}
                      role="treeitem"
                      aria-selected={selected === element.ref}
                      aria-label={`${element.name} ${element.role}`}
                      tabIndex={active?.id === item.id ? 0 : -1}
                      ref={register(item.id)}
                      onFocus={() => setFocused(item.id)}
                      className={`tree-member ${selected === element.ref ? "selected" : ""}`}
                      onClick={(event) => {
                        event.stopPropagation();
                        setFocused(item.id);
                        onSelectElement(element.ref);
                      }}
                    >
                      <Icon
                        name={
                          element.role.includes("observer")
                            ? "results"
                            : "model"
                        }
                        size={14}
                      />
                      <span>{element.name}</span>
                      {group.listedOnly.includes(element.ref) && (
                        <em className="tree-marker">(listed)</em>
                      )}
                      <small>{element.role}</small>
                    </li>
                  );
                })}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
