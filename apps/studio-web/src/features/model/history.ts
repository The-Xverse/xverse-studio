import { api } from "../../api/client";
import type { Project } from "../../api/types";

// Graph undo/redo as backend transactions. Each step names the revision to restore
// and the revision at which the step is still valid; restoring always creates a new
// forward revision from verified history, so history is never rewritten. A step is
// refused when the project moved on elsewhere, instead of overwriting that change.

export interface HistoryStep {
  target: number;
  at: number;
  label: string;
}
export interface EditHistory {
  undo: HistoryStep[];
  redo: HistoryStep[];
}

const LIMIT = 50,
  name = (projectId: string) => "studio.graphHistory." + projectId;

const validStep = (step: any): step is HistoryStep =>
  step &&
  Number.isInteger(step.target) &&
  Number.isInteger(step.at) &&
  typeof step.label === "string";

export function readHistory(projectId: string): EditHistory {
  try {
    const value = JSON.parse(sessionStorage.getItem(name(projectId)) || "null");
    if (Array.isArray(value?.undo) && Array.isArray(value?.redo))
      return {
        undo: value.undo.filter(validStep).slice(-LIMIT),
        redo: value.redo.filter(validStep).slice(-LIMIT),
      };
  } catch {
    /* A lost tab history only removes undo; committed revisions remain. */
  }
  return { undo: [], redo: [] };
}

export function writeHistory(projectId: string, history: EditHistory) {
  try {
    sessionStorage.setItem(
      name(projectId),
      JSON.stringify({
        undo: history.undo.slice(-LIMIT),
        redo: history.redo.slice(-LIMIT),
      }),
    );
  } catch {
    /* Storage loss only removes undo; committed revisions remain. */
  }
}

export function recordEdit(
  history: EditHistory,
  before: number,
  after: number,
  label: string,
): EditHistory {
  // Steps chain only through revisions this tab produced; anything else starts afresh.
  const top = history.undo[history.undo.length - 1],
    undo = top && top.at !== before ? [] : history.undo;
  return {
    undo: [...undo, { target: before, at: after, label }].slice(-LIMIT),
    redo: [],
  };
}

/** Keep history only while its top steps still describe the loaded revision. */
export function reconcileHistory(
  history: EditHistory,
  revision: number,
): EditHistory {
  const fits = (stack: HistoryStep[]) =>
    !stack.length || stack[stack.length - 1].at === revision;
  return fits(history.undo) && fits(history.redo)
    ? history
    : { undo: [], redo: [] };
}

export class HistoryStale extends Error {
  constructor() {
    super(
      "The project changed since this step was recorded. Undo/redo history was cleared; earlier revisions remain in the revision history.",
    );
  }
}

/** Apply the top undo (or redo) step; the opposite stack gains its inverse. */
export async function applyStep(
  project: Project,
  history: EditHistory,
  direction: "undo" | "redo",
): Promise<{ project: Project; history: EditHistory } | null> {
  const from = direction === "undo" ? history.undo : history.redo,
    step = from[from.length - 1];
  if (!step) return null;
  if (step.at !== project.revision) throw new HistoryStale();
  const restored = await api<Project>(
    `/projects/${encodeURIComponent(project.projectId)}/revisions/${step.target}/restore`,
    { method: "POST", revision: project.revision, body: {} },
  );
  const inverse = {
      target: step.at,
      at: restored.revision,
      label: step.label,
    },
    rest = from.slice(0, -1);
  // The restored revision has the bytes of step.target. The next step stays valid
  // only if it was recorded at that revision; otherwise the chain is broken.
  const next = rest[rest.length - 1];
  if (next && next.at === step.target)
    rest[rest.length - 1] = { ...next, at: restored.revision };
  else rest.length = 0;
  return {
    project: restored,
    history:
      direction === "undo"
        ? { undo: rest, redo: [...history.redo, inverse] }
        : { undo: [...history.undo, inverse], redo: rest },
  };
}
