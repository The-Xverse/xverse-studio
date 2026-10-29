import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import type { Data, Project, Run } from "../../api/types";
import { Badge } from "../../app/ui";
import { documentContent, projectDisplay, type Projection } from "./projection";

// Compares the editable draft with the selected run's verified, immutable snapshot.
// It reads only; neither side is changed, and the run keeps its exact inputs.

export type ElementChange = "added" | "removed" | "changed" | "definition";

export interface Divergence {
  runId: string;
  snapshotId: string;
  snapshotDigest?: string;
  snapshotRevision: number;
  draftRevision: number;
  /** Differences in the documents the run actually executed. */
  documents: { path: string; change: "removed" | "changed" }[];
  /** Draft documents the run did not use; informational only. */
  otherDocuments: string[];
  elements: { ref: string; name: string; change: ElementChange }[];
  nodes: { id: string; change: "added" | "removed" }[];
  parameters: {
    key: string;
    id: string;
    draft: unknown;
    run: unknown;
    change: "added" | "removed" | "changed";
  }[];
  profileLocksChanged: boolean;
  runInputChanges: number;
  /** Element ref → change, for canvas badges. */
  byElement: Record<string, ElementChange>;
}

const same = (a: unknown, b: unknown) =>
  JSON.stringify(a) === JSON.stringify(b);
const pseudoProject = (project: Project, documents: Record<string, string>) =>
  ({
    ...project,
    documents: Object.fromEntries(
      Object.entries(documents).map(([path, content]) => [
        path,
        { path, content, format: path.endsWith(".json") ? "json" : "yaml" },
      ]),
    ),
  }) as Project;
const nodeIds = (projection: Projection) =>
  new Set(
    projection.resources
      .filter((r) => r.kind === "System")
      .flatMap((r) =>
        (Array.isArray(r.spec?.nodes) ? r.spec.nodes : [])
          .filter((n: Data) => typeof n?.id === "string")
          .map(
            (n: Data) =>
              `xdl://${r.metadata?.namespace}/system/${r.metadata?.name}#${n.id}`,
          ),
      ),
  );

export function compareDraft(
  project: Project,
  projection: Projection,
  frozenProjection: Projection,
  runId: string,
  snapshot: Data,
): Divergence {
  // The run executed snapshot.documents (a campaign child may differ from the authored revision).
  const executed: Record<string, string> = snapshot.documents || {};
  const draft: Record<string, string> = Object.fromEntries(
    Object.values(project.documents).map((d: any) => [
      d.path,
      documentContent(d),
    ]),
  );
  const documents: Divergence["documents"] = [];
  for (const path of Object.keys(executed).sort())
    if (!(path in draft)) documents.push({ path, change: "removed" });
    else if (draft[path] !== executed[path])
      documents.push({ path, change: "changed" });
  const otherDocuments = Object.keys(draft)
    .filter((path) => !(path in executed))
    .sort();
  // Nodes are compared as declarations; an empty node's placeholder element is not an element change.
  const nodesBefore = nodeIds(frozenProjection),
    nodesAfter = nodeIds(projection);
  const nodes: Divergence["nodes"] = [
    ...[...nodesAfter]
      .filter((id) => !nodesBefore.has(id))
      .map((id) => ({ id, change: "added" as const })),
    ...[...nodesBefore]
      .filter((id) => !nodesAfter.has(id))
      .map((id) => ({ id, change: "removed" as const })),
  ];
  const members = (p: Projection) =>
    new Map(p.elements.filter((e) => e.kind !== "node").map((e) => [e.ref, e]));
  const before = members(frozenProjection),
    after = members(projection);
  const changedDefinitions = new Set(
    frozenProjection.resources
      .filter((r) => r.kind === "Component")
      .filter((r) => {
        const now = projection.resources.find(
          (n) =>
            n.kind === "Component" &&
            n.metadata?.namespace === r.metadata?.namespace &&
            n.metadata?.name === r.metadata?.name,
        );
        return !now || !same(now.spec, r.spec);
      })
      .map((r) => `${r.metadata?.namespace}/${r.metadata?.name}`),
  );
  const elements: Divergence["elements"] = [];
  for (const [ref, element] of after)
    if (!before.has(ref))
      elements.push({ ref, name: element.name, change: "added" });
    else if (!same(before.get(ref)!.raw, element.raw))
      elements.push({ ref, name: element.name, change: "changed" });
    else if (
      element.componentRef &&
      changedDefinitions.has(
        `${element.componentRef.namespace}/${element.componentRef.name}`,
      )
    )
      elements.push({ ref, name: element.name, change: "definition" });
  for (const [ref, element] of before)
    if (!after.has(ref))
      elements.push({ ref, name: element.name, change: "removed" });
  // Only the run's own Scenario parameters are run inputs.
  const scenario = snapshot.selection?.scenarioRef;
  const key = (p: { scenarioRef?: string; id: string }) =>
      `${p.scenarioRef}#${p.id}`,
    value = (p: { value?: unknown; default?: unknown }) => p.value ?? p.default,
    inScope = (p: { scenarioRef?: string }) =>
      !scenario || p.scenarioRef === scenario;
  const frozenParameters = new Map(
    frozenProjection.parameters.filter(inScope).map((p) => [key(p), p]),
  );
  const draftParameters = new Map(
    projection.parameters.filter(inScope).map((p) => [key(p), p]),
  );
  const parameters: Divergence["parameters"] = [];
  for (const [k, p] of draftParameters) {
    const old = frozenParameters.get(k);
    if (!old)
      parameters.push({
        key: k,
        id: p.id,
        draft: value(p),
        run: undefined,
        change: "added",
      });
    else if (!same(value(old), value(p)))
      parameters.push({
        key: k,
        id: p.id,
        draft: value(p),
        run: value(old),
        change: "changed",
      });
  }
  for (const [k, p] of frozenParameters)
    if (!draftParameters.has(k))
      parameters.push({
        key: k,
        id: p.id,
        draft: undefined,
        run: value(p),
        change: "removed",
      });
  const profileLocksChanged = !same(
    snapshot.profileLocks || [],
    project.manifest?.profiles || [],
  );
  return {
    runId,
    snapshotId: snapshot.snapshotId,
    snapshotDigest: snapshot.snapshotDigest,
    snapshotRevision: snapshot.revision,
    draftRevision: project.revision,
    documents,
    otherDocuments,
    elements,
    nodes,
    parameters,
    profileLocksChanged,
    runInputChanges:
      documents.length +
      elements.length +
      nodes.length +
      parameters.length +
      (profileLocksChanged ? 1 : 0),
    byElement: Object.fromEntries(elements.map((e) => [e.ref, e.change])),
  };
}

export interface SnapshotState {
  status: "loading" | "verified" | "invalid" | "unavailable";
  message?: string;
}

/** Loads the verified snapshot for the selected run of this project, once per run. */
export function useRunDivergence(
  project: Project | null,
  projection: Projection,
  run: Run | null,
) {
  const [snapshot, setSnapshot] = useState<{
      runId: string;
      value?: Data;
      state: SnapshotState;
    } | null>(null),
    [attempt, setAttempt] = useState(0);
  const runId =
    run && project && run.projectId === project.projectId ? run.runId : "";
  useEffect(() => {
    if (!runId) return;
    const controller = new AbortController();
    setSnapshot({ runId, state: { status: "loading" } });
    api(`/runs/${encodeURIComponent(runId)}/snapshot`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (controller.signal.aborted) return;
        if (response.integrity !== "valid" || response.readOnly !== true)
          setSnapshot({
            runId,
            state: {
              status: "invalid",
              message: "The backend could not verify the snapshot's integrity.",
            },
          });
        else
          setSnapshot({
            runId,
            value: response.snapshot,
            state: { status: "verified" },
          });
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        // A failed read is not an integrity verdict.
        setSnapshot({
          runId,
          state: {
            status:
              error?.code === "SNAPSHOT_INTEGRITY" ? "invalid" : "unavailable",
            message:
              error instanceof Error
                ? error.message
                : "Run snapshot unavailable.",
          },
        });
      });
    return () => controller.abort();
  }, [runId, attempt]);
  const current = snapshot?.runId === runId ? snapshot : null,
    frozen = current?.value;
  // The frozen projection depends only on the snapshot, not on draft edits.
  const frozenProjection = useMemo(
    () =>
      project && frozen
        ? projectDisplay(pseudoProject(project, frozen.documents || {}))
        : null,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [frozen],
  );
  const divergence = useMemo(
    () =>
      project && runId && frozen && frozenProjection
        ? compareDraft(project, projection, frozenProjection, runId, frozen)
        : null,
    [project, projection, frozenProjection, frozen, runId],
  );
  return {
    divergence,
    snapshot: frozen || null,
    state: runId ? current?.state || { status: "loading" as const } : null,
    retry: () => setAttempt((value) => value + 1),
  };
}

const plural = (count: number, word: string) =>
  `${count} ${word}${count === 1 ? "" : "s"}`;

export function RunDivergenceBadge({
  divergence,
  state,
  open,
  onToggle,
  onRetry,
}: {
  divergence: Divergence | null;
  state: SnapshotState | null;
  open: boolean;
  onToggle: () => void;
  onRetry: () => void;
}) {
  if (!state || state.status === "loading") return null;
  if (state.status !== "verified")
    return (
      <span className="divergence-unavailable" role="status">
        <Badge tone="warning">
          {state.status === "invalid"
            ? "Snapshot integrity not verified"
            : "Snapshot unavailable"}
        </Badge>{" "}
        <small>{state.message}</small>{" "}
        {state.status === "unavailable" && (
          <button className="small-button" onClick={onRetry}>
            Retry
          </button>
        )}
      </span>
    );
  if (!divergence) return null;
  const parts = [
    plural(divergence.documents.length, "document"),
    plural(divergence.elements.length + divergence.nodes.length, "element"),
    plural(divergence.parameters.length, "parameter"),
    ...(divergence.profileLocksChanged ? ["profile locks"] : []),
  ];
  return (
    <button
      className={`divergence-badge ${divergence.runInputChanges ? "diverged" : "matching"}`}
      aria-expanded={open}
      aria-controls={open ? "run-divergence" : undefined}
      onClick={onToggle}
    >
      {divergence.runInputChanges
        ? `Draft differs from run inputs (${parts.join(", ")})`
        : "Draft matches run inputs"}
    </button>
  );
}

export function RunDivergencePanel({
  divergence,
  onSelectElement,
  onOpenDocument,
  onFrozenInputs,
}: {
  divergence: Divergence;
  onSelectElement: (ref: string) => void;
  onOpenDocument: (path: string) => void;
  onFrozenInputs: () => void;
}) {
  return (
    <section
      id="run-divergence"
      className="run-divergence panel"
      aria-label="Draft and run snapshot"
    >
      <p>
        Run <code>{divergence.runId}</code> executed immutable snapshot{" "}
        <code>{divergence.snapshotId}</code>
        {divergence.snapshotDigest && (
          <>
            {" "}
            (<code>{divergence.snapshotDigest}</code>)
          </>
        )}
        , frozen from revision {divergence.snapshotRevision}. The editable draft
        is revision {divergence.draftRevision}. Draft edits never change this
        run.
      </p>
      {divergence.snapshotRevision !== divergence.draftRevision &&
        !divergence.runInputChanges && (
          <p className="field-hint">
            The revision numbers differ, but every run input matches the
            snapshot byte for byte.
          </p>
        )}
      <div className="button-row">
        <button
          className="button"
          data-frozen-inputs-trigger=""
          onClick={onFrozenInputs}
        >
          Inspect frozen run inputs
        </button>
      </div>
      {divergence.profileLocksChanged && (
        <p>
          <Badge tone="warning">profile locks</Badge> The draft's profile locks
          differ from those frozen in the snapshot.
        </p>
      )}
      {(divergence.elements.length > 0 || divergence.nodes.length > 0) && (
        <>
          <h4>Elements</h4>
          <ul>
            {divergence.nodes.map((n) => (
              <li key={n.id}>
                <Badge tone="info">
                  {n.change === "added"
                    ? "node new in draft"
                    : "node only in run"}
                </Badge>{" "}
                <code>{n.id}</code>
              </li>
            ))}
            {divergence.elements.map((e) => (
              <li key={e.ref}>
                <Badge tone={e.change === "removed" ? "warning" : "info"}>
                  {e.change === "added"
                    ? "new in draft"
                    : e.change === "removed"
                      ? "only in run"
                      : e.change === "definition"
                        ? "definition changed"
                        : "changed since run"}
                </Badge>{" "}
                {e.change === "removed" ? (
                  <code>{e.ref}</code>
                ) : (
                  <button
                    className="text-button"
                    onClick={() => onSelectElement(e.ref)}
                  >
                    {e.name}
                  </button>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      {divergence.parameters.length > 0 && (
        <>
          <h4>Run scenario parameters</h4>
          <ul>
            {divergence.parameters.map((p) => (
              <li key={p.key}>
                <code>{p.id}</code>:{" "}
                {p.change === "added"
                  ? `new in draft (${JSON.stringify(p.draft)})`
                  : p.change === "removed"
                    ? `only in run (${JSON.stringify(p.run)})`
                    : `run ${JSON.stringify(p.run)} → draft ${JSON.stringify(p.draft)}`}
              </li>
            ))}
          </ul>
        </>
      )}
      {divergence.documents.length > 0 && (
        <>
          <h4>Run input documents</h4>
          <ul>
            {divergence.documents.map((d) => (
              <li key={d.path}>
                <Badge>
                  {d.change === "removed" ? "missing in draft" : "changed"}
                </Badge>{" "}
                {d.change === "removed" ? (
                  <code>{d.path}</code>
                ) : (
                  <button
                    className="text-button"
                    onClick={() => onOpenDocument(d.path)}
                  >
                    {d.path} (draft)
                  </button>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      {divergence.otherDocuments.length > 0 && (
        <p className="field-hint">
          Not used by this run: {divergence.otherDocuments.join(", ")}.
        </p>
      )}
    </section>
  );
}
