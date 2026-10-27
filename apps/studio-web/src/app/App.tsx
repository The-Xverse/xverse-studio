import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import type { NewProject, Selection } from "../../../../packages/contracts/api";
import {
  api,
  ApiError,
  setCsrfToken,
  items,
  mutationKey,
  subscribe,
  mergeRun,
} from "../api/client";
import type {
  Project,
  Data,
  CatalogEntry,
  Run,
  RunEvent,
  Preflight,
  Diagnostic,
  Parameter,
} from "../api/types";
import {
  projectDisplay,
  documentContent,
  textRef,
} from "../features/model/projection";
import {
  ModelView,
  ConnectionsView,
  DeploymentView,
  SourceEditor,
  type SourceTarget,
} from "../features/model/Views";
import {
  DeploymentComposer,
  type ExecutionSelection,
} from "../features/deployments/DeploymentComposer";
import {
  ProfileBindingsPanel,
  type ProfileBindingCommit,
  type ProfileBindingRefusal,
} from "../features/profiles/ProfileBindingsPanel";
import {
  DomainBadge,
  PresentationContext,
  usePresentationData,
} from "../features/profiles/presentation";
import { ArtifactRegistrationForm } from "../features/catalog/ArtifactRegistrationForm";
import { LogicalAssetForm } from "../features/model/LogicalAssetForm";
import {
  RetentionDialog,
  type RetentionTarget,
} from "../features/retention/RetentionDialog";
import { PreflightReview } from "../features/preflight/PreflightReview";
import { ResultsView } from "../features/results/ResultsView";
import { PendingStartNotice } from "../features/runs/PendingStartNotice";
import { RecoveryPanel, type RecoveryResult } from "../features/model/RecoveryPanel";
import { FrozenInputs } from "../features/results/FrozenInputs";
import {
  RunDivergenceBadge,
  RunDivergencePanel,
  useRunDivergence,
} from "../features/model/run-overlay";
import { InstanceWizard } from "../features/elements/InstanceWizard";
import {
  InspectionButton,
  ProjectInspection,
  useProjectInspection,
} from "../features/projects/ProjectInspection";
import {
  applyStep,
  HistoryStale,
  readHistory,
  reconcileHistory,
  recordEdit,
  writeHistory,
  type EditHistory,
} from "../features/model/history";
import {
  clearPendingStart,
  isDefinitiveRejection,
  readPendingStart,
  startRequest,
  writePendingStart,
  type PendingStart,
} from "../features/runs/control";
import { ExperimentsView, LabView } from "./OperationsViews";
import {
  Icon,
  Badge,
  Diagnostics,
  Empty,
  Json,
  Modal,
  statusTone,
  KeyValues,
} from "./ui";
type View = "Model" | "Connections" | "Deployment" | "Experiments" | "Results";
// The core term whose domain icon, when a profile supplies one, marks each workflow tab.
const viewTerms: Record<View, string> = {
  Model: "System",
  Connections: "Flow",
  Deployment: "Deployment",
  Experiments: "Scenario",
  Results: "Results",
};
const viewIcons: Record<View, string> = {
  Model: "model",
  Connections: "connection",
  Deployment: "deployment",
  Experiments: "experiment",
  Results: "results",
};
export type DoAction = (
  label: string,
  action: () => Promise<unknown>,
) => Promise<any>;
type ProjectIntent = {
  projectId: string;
  loadSequence: number;
  intentSequence: number;
  workspaceSequence: number;
};
type ProjectRequestError = Error & { requestedProjectId?: string };
export default function App() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null),
    [csrf, setCsrf] = useState("");
  const [projects, setProjects] = useState<Project[]>([]),
    [catalog, setCatalog] = useState<CatalogEntry[]>([]),
    [providers, setProviders] = useState<Data[]>([]),
    [capabilities, setCapabilities] = useState<Data>({}),
    [executionSelection, setExecutionSelection] = useState<ExecutionSelection>(
      {},
    ),
    [addTemplate, setAddTemplate] = useState(""),
    [executionProvider, setExecutionProvider] = useState("studio.reference");
  const [sourceContext, setSourceContext] = useState<
      SourceTarget | undefined
    >(),
    [addKind, setAddKind] = useState("component");
  const openSource = (target?: SourceTarget) => {
    setSourceContext(target);
    setModal("source");
  };
  const [retentionTarget, setRetentionTarget] =
    useState<RetentionTarget | null>(null);
  const [project, storeProject] = useState<Project | null>(null),
    [view, setView] = useState<View>("Model"),
    [section, setSection] = useState<
      "workspace" | "catalog" | "lab" | "settings"
    >("workspace");
  const [error, setError] = useState<ApiError | Error | null>(null),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(""),
    [modal, storeModal] = useState(""),
    [name, setName] = useState(""),
    [selected, setSelected] = useState(""),
    [preflight, setPreflight] = useState<Preflight | null>(null);
  const [run, setRun] = useState<Run | null>(null),
    [events, setEvents] = useState<RunEvent[]>([]),
    [omitted, setOmitted] = useState(0),
    [streamState, setStreamState] = useState("Disconnected"),
    [evidenceImport, setEvidenceImport] = useState<Data | null>(null),
    [pendingStart, setPendingStart] = useState<PendingStart | null>(null),
    [editHistory, setEditHistory] = useState<EditHistory>({
      undo: [],
      redo: [],
    }),
    [startSending, setStartSending] = useState(false);
  const startKey = useRef(mutationKey()),
    preflightRequestSequence = useRef(0),
    lastRun = useRef(localStorage.getItem("studio.lastRun") || ""),
    selectedProjectRef = useRef(""),
    projectLoadSequence = useRef(0),
    workspaceInteractionSequence = useRef(0),
    streamIdentity = useRef("");
  const latestProject = useRef(project);
  function setProject(value: Project | null) {
    latestProject.current = value;
    storeProject(value);
  }
  const renderedLoadSequence = projectLoadSequence.current,
    renderedIntentSequence = preflightRequestSequence.current;
  function projectIntent(): ProjectIntent {
    return {
      projectId: selectedProjectRef.current,
      loadSequence: projectLoadSequence.current,
      intentSequence: preflightRequestSequence.current,
      workspaceSequence: workspaceInteractionSequence.current,
    };
  }
  function sameProjectIntent(
    context: ProjectIntent,
    includeInteraction = true,
  ) {
    return (
      selectedProjectRef.current === context.projectId &&
      projectLoadSequence.current === context.loadSequence &&
      (!includeInteraction ||
        (preflightRequestSequence.current === context.intentSequence &&
          workspaceInteractionSequence.current === context.workspaceSequence))
    );
  }
  function projectRequestError(error: unknown, projectId: string) {
    return Object.assign(
      error instanceof Error ? error : new Error("The project request failed."),
      { requestedProjectId: projectId },
    );
  }
  function workspaceInteraction(event: { target: EventTarget | null }) {
    // Authoring can resume without a modal or a committed edit, for example by
    // typing a parameter. Keep that intent separate from revision acknowledgements.
    if (
      project &&
      section === "workspace" &&
      event.target instanceof Element &&
      !event.target.closest(".alerts")
    )
      workspaceInteractionSequence.current++;
  }
  function commitProjectRevision(saved: Project) {
    const current = latestProject.current;
    if (
      !project ||
      !current ||
      selectedProjectRef.current !== project.projectId ||
      projectLoadSequence.current !== renderedLoadSequence ||
      current.projectId !== saved.projectId ||
      project.projectId !== saved.projectId ||
      saved.revision <= current.revision
    )
      return false;
    const visible = renderedIntentSequence === preflightRequestSequence.current;
    preflightRequestSequence.current++;
    setProject(saved);
    const history = reconcileHistory(readHistory(saved.projectId), saved.revision);
    writeHistory(saved.projectId, history);
    setEditHistory(history);
    setPreflight(null);
    return visible;
  }
  const sourceControl = useRef<HTMLButtonElement>(null),
    operationError = useRef<HTMLDivElement>(null);
  const [projectActionFocus, setProjectActionFocus] = useState<{
    projectId: string;
    loadSequence: number;
    intentSequence: number;
    origin: Element | null;
    target: "source" | "error";
  } | null>(null);
  useEffect(() => {
    if (busy || !projectActionFocus) return;
    setProjectActionFocus(null);
    if (
      selectedProjectRef.current !== projectActionFocus.projectId ||
      projectLoadSequence.current !== projectActionFocus.loadSequence ||
      preflightRequestSequence.current !== projectActionFocus.intentSequence ||
      modal ||
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== projectActionFocus.origin)
    )
      return;
    if (projectActionFocus.target === "error") operationError.current?.focus();
    else if (
      project?.projectId === projectActionFocus.projectId &&
      section === "workspace"
    )
      sourceControl.current?.focus();
  }, [busy, projectActionFocus, project?.projectId, section, modal]);
  function recoveryHandlers(projectId: string) {
    let context: ProjectIntent | undefined;
    return {
      doAction: (label: string, action: () => Promise<unknown>) => {
        projectLoadSequence.current++;
        preflightRequestSequence.current++;
        const initiating = projectIntent(),
          origin = document.activeElement;
        context = initiating;
        return doAction(label, async () => {
          try {
            return await action();
          } catch (error) {
            if (sameProjectIntent(initiating)) {
              setProjectActionFocus({ ...initiating, origin, target: "error" });
              throw projectRequestError(error, projectId);
            }
          }
        });
      },
      onRecovered: (result: RecoveryResult, origin: HTMLButtonElement) => {
        if (context) completeRecovery(projectId, result, origin, context);
      },
    };
  }
  function completeRecovery(
    projectId: string,
    result: RecoveryResult,
    origin: HTMLButtonElement,
    context: ProjectIntent,
  ) {
    const saved = result.project,
      known = latestProject.current;
    if (
      saved.projectId !== projectId ||
      !sameProjectIntent(context, false) ||
      (known?.projectId === projectId && saved.revision <= known.revision)
    )
      return;
    const visible = sameProjectIntent(context),
      changed = known?.projectId !== projectId;
    if (changed && !visible) return;
    preflightRequestSequence.current++;
    selectedProjectRef.current = projectId;
    setProject(saved);
    const history = reconcileHistory(readHistory(projectId), saved.revision);
    writeHistory(projectId, history);
    setEditHistory(history);
    setPreflight(null);
    localStorage.setItem("studio.projectId", projectId);
    setProjects((values) =>
      values.map((value) =>
        value.projectId === projectId
          ? { ...value, name: saved.name, revision: saved.revision }
          : value,
      ),
    );
    if (changed) {
      setExecutionProvider("studio.reference");
      setSelected("");
      setView("Model");
      try {
        const cached = JSON.parse(
          localStorage.getItem("studio.selection." + projectId) || "{}",
        );
        setExecutionSelection({
          ...(typeof cached?.deploymentRef === "string"
            ? { deploymentRef: cached.deploymentRef }
            : {}),
          ...(typeof cached?.scenarioRef === "string"
            ? { scenarioRef: cached.scenarioRef }
            : {}),
        });
      } catch {
        setExecutionSelection({});
      }
      setPendingStart(readPendingStart(projectId));
      setRun(null);
      localStorage.removeItem("studio.lastRun");
      const storedRun = localStorage.getItem("studio.lastRun." + projectId);
      if (storedRun)
        void api<Run>(`/runs/${storedRun}`)
          .then((value) => {
            if (
              selectedProjectRef.current !== projectId ||
              projectLoadSequence.current !== context.loadSequence ||
              localStorage.getItem("studio.lastRun." + projectId) !== storedRun
            )
              return;
            setRun(value.projectId === projectId ? value : null);
            if (value.projectId === projectId)
              localStorage.setItem("studio.lastRun", storedRun);
          })
          .catch(() => {
            /* Missing retained run metadata does not start or replay a run. */
          });
    }
    if (visible) {
      setSection("workspace");
      setNotice(
        `Recovered as revision ${saved.revision}. The observed external bytes are preserved in backup ${result.recovery.recoveryId}.`,
      );
      setProjectActionFocus({
        projectId,
        loadSequence: context.loadSequence,
        intentSequence: preflightRequestSequence.current,
        origin,
        target: "source",
      });
    }
  }
  const undoControl = useRef<HTMLButtonElement | null>(null),
    redoControl = useRef<HTMLButtonElement | null>(null);
  const [historyFocus, setHistoryFocus] = useState<{
    projectId: string;
    loadSequence: number;
    intentSequence: number;
    direction: "undo" | "redo";
    origin: HTMLButtonElement;
  } | null>(null);
  useEffect(() => {
    if (busy || !historyFocus) return;
    setHistoryFocus(null);
    if (
      project?.projectId !== historyFocus.projectId ||
      selectedProjectRef.current !== historyFocus.projectId ||
      projectLoadSequence.current !== historyFocus.loadSequence ||
      preflightRequestSequence.current !== historyFocus.intentSequence ||
      section !== "workspace" || modal ||
      (document.activeElement !== document.body && document.activeElement !== historyFocus.origin)
    ) return;
    const same = historyFocus.direction === "undo" ? undoControl.current : redoControl.current,
      opposite = historyFocus.direction === "undo" ? redoControl.current : undoControl.current;
    (same && !same.disabled ? same : opposite && !opposite.disabled ? opposite : null)?.focus();
  }, [busy, historyFocus, project?.projectId, section, modal]);
  function setModal(value: string) {
    preflightRequestSequence.current++;
    storeModal(value);
  }
  function showHome(removeLastProject = false) {
    projectLoadSequence.current++;
    selectedProjectRef.current = "";
    setPreflight(null);
    setModal("");
    setProject(null);
    setSection("workspace");
    if (removeLastProject) localStorage.removeItem("studio.projectId");
  }
  function changeSection(value: typeof section) {
    projectLoadSequence.current++;
    selectedProjectRef.current = project?.projectId || "";
    setPreflight(null);
    setModal("");
    setSection(value);
  }
  const doAction: DoAction = useCallback(async (label, action) => {
    setBusy(label);
    setError(null);
    setNotice("");
    try {
      return await action();
    } catch (e) {
      setError(e instanceof Error ? e : new Error("The operation failed."));
      return undefined;
    } finally {
      setBusy("");
    }
  }, []);
  const runUpdated = useCallback(
    (updated: Run) =>
      setRun((old) => (old?.runId === updated.runId ? updated : old)),
    [],
  );
  async function refreshProjects() {
    setProjects(items<Project>(await api("/projects")));
  }
  async function loadProject(projectId: string) {
    projectLoadSequence.current++;
    const context = projectIntent();
    let value: Project;
    try {
      value = await api<Project>(`/projects/${encodeURIComponent(projectId)}`);
    } catch (error) {
      if (sameProjectIntent(context))
        throw projectRequestError(error, projectId);
      return;
    }
    const known = latestProject.current;
    if (
      !sameProjectIntent(context) ||
      (known?.projectId === projectId && known.revision > value.revision)
    )
      return;
    const changed = selectedProjectRef.current !== projectId;
    selectedProjectRef.current = projectId;
    setProject(value);
    {
      const history = reconcileHistory(readHistory(projectId), value.revision);
      writeHistory(projectId, history);
      setEditHistory(history);
    }
    localStorage.setItem("studio.projectId", projectId);
    setSection("workspace");
    setPreflight(null);
    if (changed) {
      setExecutionProvider("studio.reference");
      setSelected("");
      setView("Model");
      try {
        const cached = JSON.parse(
          localStorage.getItem("studio.selection." + projectId) || "{}",
        );
        setExecutionSelection({
          ...(typeof cached?.deploymentRef === "string"
            ? { deploymentRef: cached.deploymentRef }
            : {}),
          ...(typeof cached?.scenarioRef === "string"
            ? { scenarioRef: cached.scenarioRef }
            : {}),
        });
      } catch {
        setExecutionSelection({});
      }
    }
    setPendingStart(readPendingStart(projectId));
    const accepted = projectIntent();
    const storedRun = localStorage.getItem("studio.lastRun." + projectId);
    const retainedRunCurrent = () =>
      sameProjectIntent(accepted, false) &&
      localStorage.getItem("studio.lastRun." + projectId) === storedRun;
    if (storedRun) {
      if (changed) {
        setRun(null);
        localStorage.removeItem("studio.lastRun");
      }
      try {
        const selectedRun = await api<Run>(`/runs/${storedRun}`);
        if (!retainedRunCurrent()) return;
        setRun(selectedRun.projectId === projectId ? selectedRun : null);
        if (selectedRun.projectId === projectId)
          localStorage.setItem("studio.lastRun", storedRun);
        else localStorage.removeItem("studio.lastRun");
      } catch {
        if (!retainedRunCurrent()) return;
        setRun(null);
        localStorage.removeItem("studio.lastRun");
      }
    } else {
      setRun(null);
      localStorage.removeItem("studio.lastRun");
    }
    // Hydrating the same project's run is still useful after opening Results or
    // Source. Navigation continuations must not close a newer modal or recapture it.
    return sameProjectIntent(accepted) ? value : undefined;
  }
  async function loadBoot() {
    const context = projectIntent();
    const metadata = await Promise.all([
      api("/projects"),
      api("/catalog"),
      api("/providers"),
      api("/capabilities"),
    ]).catch((error) => {
      if (sameProjectIntent(context)) throw error;
      return undefined;
    });
    if (!metadata) return;
    const [p, c, d, cap] = metadata;
    setProjects(items<Project>(p));
    setCatalog(items<CatalogEntry>(c));
    setProviders(items<Data>(d));
    setCapabilities(cap);
    if (!sameProjectIntent(context)) return;
    const saved = localStorage.getItem("studio.projectId");
    if (saved && items<Project>(p).some((p) => p.projectId === saved))
      await loadProject(saved);
  }
  useEffect(() => {
    let active = true;
    api("/session")
      .then((s) => {
        if (!active) return;
        setCsrfToken(s.csrfToken);
        setCsrf(s.csrfToken);
        setAuthenticated(true);
        void doAction("Opening workspace", loadBoot);
      })
      .catch(() => {
        if (active) setAuthenticated(false);
      });
    return () => {
      active = false;
    };
  }, []);
  const refreshProject = async () =>
    project &&
    selectedProjectRef.current === project.projectId &&
    projectLoadSequence.current === renderedLoadSequence &&
    preflightRequestSequence.current === renderedIntentSequence
      ? loadProject(project.projectId)
      : undefined;
  const historyShortcut = useRef<(direction: "undo" | "redo") => void>(
    () => undefined,
  );
  historyShortcut.current = (direction) => {
    if (
      !project ||
      busy ||
      modal ||
      section !== "workspace" ||
      !editHistory[direction].length
    )
      return;
    const active = document.activeElement;
    if (active === undoControl.current || active === redoControl.current) {
      historyFromControl(direction, active as HTMLButtonElement);
      return;
    }
    void doAction(
      direction === "undo" ? "Undoing graph edit" : "Redoing graph edit",
      () => stepHistory(direction),
    );
  };
  useEffect(() => {
    // Text fields keep their own undo; graph history applies elsewhere.
    const handle = (event: KeyboardEvent) => {
      if (
        !(event.ctrlKey || event.metaKey) ||
        event.altKey ||
        event.isComposing ||
        event.key.toLowerCase() !== "z"
      )
        return;
      const target = event.target as HTMLElement | null;
      if (
        target?.closest(
          "input, textarea, select, [contenteditable='true'], [role='dialog']",
        )
      )
        return;
      event.preventDefault();
      historyShortcut.current(event.shiftKey ? "redo" : "undo");
    };
    window.addEventListener("keydown", handle);
    return () => window.removeEventListener("keydown", handle);
  }, []);
  const projection = useMemo(() => projectDisplay(project), [project]);
  const {
      divergence,
      snapshot: runSnapshot,
      state: snapshotState,
      retry: retrySnapshot,
    } = useRunDivergence(project, projection, run),
    [divergenceOpen, setDivergenceOpen] = useState(false),
    [frozenOpen, setFrozenOpen] = useState(false);
  // The comparison panel belongs to one run; a different run starts closed.
  useEffect(() => {
    setDivergenceOpen(false);
    setFrozenOpen(false);
  }, [run?.runId]);
  const entry =
    catalog.find(
      (c) =>
        (c.id || c.entryId) === project?.manifest?.provenance?.blueprintRef,
    ) || catalog.find((c) => project?.name?.includes(c.name));
  function chooseExecution(selection: ExecutionSelection) {
    preflightRequestSequence.current++;
    setExecutionSelection(selection);
    setPreflight(null);
    if (project)
      localStorage.setItem(
        "studio.selection." + project.projectId,
        JSON.stringify(selection),
      );
  }
  const parameters = useMemo(() => {
    const defined = entry?.parameters || catalog[0]?.parameters || [];
    return projection.parameters
      .filter((p) =>
        executionSelection.scenarioRef
          ? p.scenarioRef === executionSelection.scenarioRef
          : projection.scenarios.length <= 1,
      )
      .map((p) => ({
        ...defined.find((d) => d.id === p.id),
        ...p,
      }));
  }, [
    projection.parameters,
    projection.scenarios.length,
    executionSelection.scenarioRef,
    entry,
    catalog,
  ]);
  const terminalStream =
    !!run && ["stopped", "failed"].includes(String(run.status || run.state));
  useEffect(() => {
    if (!run?.runId) return;
    const runId = run.runId,
      snapshotId = run.snapshotId;
    if (streamIdentity.current !== runId) {
      streamIdentity.current = runId;
      setEvents([]);
      setOmitted(0);
    }
    if (terminalStream) {
      setStreamState("Retained history available");
      return;
    }
    let active = true,
      readGeneration = 0,
      displayed = 0,
      dropped = 0,
      lossNotice = "";
    let pending: RunEvent[] = [],
      flushTimer: number | undefined;
    let stateRequest: AbortController | undefined;
    const flush = () => {
      flushTimer = undefined;
      if (!active || (!pending.length && !dropped)) return;
      const batch = pending;
      pending = [];
      const overflow = Math.max(0, displayed + batch.length - 200) + dropped;
      displayed = Math.min(200, displayed + batch.length);
      dropped = 0;
      if (overflow) setOmitted((value) => value + overflow);
      setEvents((old) => [...old, ...batch].slice(-200));
    };
    const refreshState = async () => {
      const generation = ++readGeneration;
      stateRequest?.abort();
      stateRequest = new AbortController();
      try {
        const value = await api<Run>(`/runs/${runId}`, {
          signal: stateRequest.signal,
        });
        if (
          active &&
          generation === readGeneration &&
          value.snapshotId === snapshotId
        )
          setRun((old) => mergeRun(old, value));
      } catch {
        /* Reconnection never infers a new lifecycle outcome from a failed read. */
      }
    };
    const pollTimer = window.setInterval(() => void refreshState(), 2000);
    const stop = subscribe(
      runId,
      (event) => {
        if (!active) throw Error("Obsolete run session");
        if (pending.length >= 200) {
          pending.shift();
          dropped++;
        }
        pending.push(event);
        if (flushTimer === undefined) flushTimer = window.setTimeout(flush, 16);
        if (
          [
            "run.state_changed",
            "cleanup.updated",
            "evidence.updated",
            "run.reconciling",
            "run.ownership_unknown",
          ].includes(event.type)
        )
          void refreshState();
      },
      (state) => {
        if (active) setStreamState(state);
      },
      async (recovery) => {
        if (!active) throw Error("Obsolete recovery");
        ++readGeneration;
        stateRequest?.abort();
        if (flushTimer !== undefined) clearTimeout(flushTimer);
        flushTimer = undefined;
        pending = [];
        dropped = 0;
        displayed = recovery.history.items.length;
        setRun((old) => mergeRun(old, recovery.run));
        setEvents(recovery.history.items.slice(-200));
        setOmitted(recovery.history.omittedRecords);
        setNotice(
          `${lossNotice} Current run state and a bounded history tail were resynchronized. Reader integrity: ${recovery.history.integrity}. Display omissions remain inspectable through retained history; this does not restore missing canonical evidence.`,
        );
      },
      {
        snapshotId,
        onControl: (control) => {
          if (!active) return;
          if (control.type === "stream.end") {
            flush();
            clearInterval(pollTimer);
            void refreshState();
            return;
          }
          if (
            control.type === "stream.gap" ||
            control.type === "stream.resync_required"
          ) {
            lossNotice =
              control.missingCount === null
                ? "The presentation loss count is unknown."
                : `${control.missingCount} presentation record(s) are unavailable in this delivery interval.`;
            setNotice(
              `${lossNotice} State and retained history resynchronization is pending. ${control.reason}`,
            );
          }
        },
      },
    );
    return () => {
      active = false;
      ++readGeneration;
      stateRequest?.abort();
      stop();
      clearInterval(pollTimer);
      if (flushTimer !== undefined) clearTimeout(flushTimer);
      pending = [];
    };
  }, [run?.runId, run?.snapshotId, terminalStream]);
  async function createProject(blueprintRef?: string) {
    projectLoadSequence.current++;
    const context = projectIntent();
    const value = await (async () => {
      const created = await api<Project>("/projects", {
        method: "POST",
        body: {
          name:
            name.trim() ||
            (blueprintRef
              ? catalog.find((c) => (c.id || c.entryId) === blueprintRef)?.name
              : "Untitled System") ||
            "New System",
          ...(blueprintRef ? { blueprintRef } : {}),
        } satisfies NewProject,
      });
      await refreshProjects();
      return created;
    })().catch((error) => {
      if (sameProjectIntent(context)) throw error;
      return undefined;
    });
    if (!value || !sameProjectIntent(context)) return;
    if (!(await loadProject(value.projectId))) return;
    setModal("");
    setName("");
    setNotice(
      "Project created. Review its scope and validate the XDL before running.",
    );
  }
  async function checkPreflight(providerId = executionProvider) {
    if (!project) return;
    const sequence = ++preflightRequestSequence.current,
      loadSequence = projectLoadSequence.current;
    const current = await api<Project>(
      `/projects/${encodeURIComponent(project.projectId)}`,
    );
    if (
      sequence !== preflightRequestSequence.current ||
      loadSequence !== projectLoadSequence.current ||
      selectedProjectRef.current !== project.projectId
    )
      return;
    const value = await api<Preflight>(
      `/projects/${project.projectId}/preflights`,
      {
        method: "POST",
        body: {
          revision: current.revision,
          providerId,
          ...executionSelection,
        } satisfies Selection,
        key: mutationKey(),
      },
    );
    if (
      sequence !== preflightRequestSequence.current ||
      loadSequence !== projectLoadSequence.current ||
      selectedProjectRef.current !== project.projectId
    )
      return;
    if (current.revision !== project.revision) {
      setProject(current);
      const history = reconcileHistory(
        readHistory(current.projectId),
        current.revision,
      );
      writeHistory(current.projectId, history);
      setEditHistory(history);
    }
    setExecutionProvider(providerId);
    setPreflight(value);
    startKey.current = mutationKey();
    setModal("preflight");
  }
  // A Start with a fresh request identity is withheld while an earlier Start's
  // acknowledgement is unresolved: it could otherwise admit a second run.
  const unresolvedStartReason =
    "An earlier Start acknowledgement is unresolved. Retry that same Start or dismiss its receipt before starting a new snapshot.";
  function startBlocked(projectId: string) {
    const existing = readPendingStart(projectId);
    return Boolean(existing && existing.key !== startKey.current);
  }
  async function start() {
    if (!preflight || preflight.status !== "ready" || !project) return;
    if (startBlocked(project.projectId)) throw new Error(unresolvedStartReason);
    const pending: PendingStart = {
      key: startKey.current,
      projectId: project.projectId,
      snapshotId: preflight.snapshotId,
      preflightId: preflight.preflightId,
      sentAt: Date.now(),
    };
    // Persist the request identity first: a lost acknowledgement stays retryable after refresh.
    writePendingStart(pending);
    setPendingStart(pending);
    await deliverStart(pending);
  }
  async function deliverStart(pending: PendingStart) {
    const settle = () => {
      clearPendingStart(pending.projectId);
      setPendingStart((current) =>
        current?.key === pending.key ? null : current,
      );
    };
    setStartSending(true);
    let value: Run;
    try {
      value = await startRequest(pending);
    } catch (error) {
      if (isDefinitiveRejection(error)) settle();
      throw error;
    } finally {
      setStartSending(false);
    }
    if (value.runId) {
      // Keep a pointer to the accepted run before the receipt is released.
      localStorage.setItem("studio.lastRun." + pending.projectId, value.runId);
      if (selectedProjectRef.current === pending.projectId)
        localStorage.setItem("studio.lastRun", value.runId);
    }
    settle();
    const current = value.runId
      ? await api<Run>(`/runs/${encodeURIComponent(value.runId)}`)
      : value;
    if (selectedProjectRef.current === current.projectId) setRun(current);
    lastRun.current = current.runId;
    localStorage.setItem("studio.lastRun", current.runId);
    if (current.projectId)
      localStorage.setItem(
        "studio.lastRun." + current.projectId,
        current.runId,
      );
    setModal("");
    if (selectedProjectRef.current === current.projectId) setView("Results");
    setNotice(
      "Run accepted by the backend. Browser disconnection will not duplicate or terminate it.",
    );
  }
  async function edit(edits: Data[]): Promise<Project | undefined> {
    const selectedScenario = projection.scenarios.find(
      (resource) =>
        `xdl://${resource.metadata.namespace}/scenario/${resource.metadata.name}` ===
        executionSelection.scenarioRef,
    );
    edits = edits.map((edit) =>
      edit.kind === "set_parameter" && !edit.documentId && selectedScenario
        ? { ...edit, documentId: selectedScenario.documentId }
        : edit,
    );
    if (!project) return;
    const projectId = project.projectId,
      sequence = projectLoadSequence.current,
      intent = preflightRequestSequence.current,
      initialHistory = readHistory(projectId),
      current = () => selectedProjectRef.current === projectId && projectLoadSequence.current === sequence;
    try {
      const saved = await api<Project>(`/projects/${projectId}/edits`, {
        method: "POST",
        revision: project.revision,
        body: { baseRevision: project.revision, edits },
      });
      const known = latestProject.current;
      if (known?.projectId === projectId && known.revision > saved.revision) return undefined;
      const history = recordEdit(initialHistory, project.revision, saved.revision,
        edits.map((edit) => String(edit.kind).replace(/_/g, " ")).join(", ")),
        persisted = JSON.stringify(readHistory(projectId)) === JSON.stringify(initialHistory);
      // A completed edit belongs to its original tab head, even after departure.
      // A newer load/edit must never have its history replaced by an older reply.
      if (persisted) writeHistory(projectId, history);
      if (!current()) return undefined;
      const visible = intent === preflightRequestSequence.current;
      if (persisted) setEditHistory(history);
      if (!known || saved.revision > known.revision) {
        // The response is already the full authoritative committed Project.
        setProject(saved);
        if (!persisted) setEditHistory(reconcileHistory(readHistory(projectId), saved.revision));
        preflightRequestSequence.current++;
        setPreflight(null);
        if (visible)
          setNotice("Draft saved. Existing run snapshots remain unchanged.");
      }
      // Callers may complete local form/focus work only for the current intent.
      return visible ? saved : undefined;
    } catch (error) {
      if (current() && intent === preflightRequestSequence.current) throw error;
      return undefined;
    }
  }
  async function stepHistory(direction: "undo" | "redo") {
    if (!project) return;
    const projectId = project.projectId,
      sequence = projectLoadSequence.current,
      history = readHistory(projectId),
      current = () => selectedProjectRef.current === projectId && projectLoadSequence.current === sequence,
      persist = (next: EditHistory) => {
        // A newer load/edit may already have reconciled this tab's head.
        if (JSON.stringify(readHistory(projectId)) !== JSON.stringify(history)) return false;
        writeHistory(projectId, next);
        return true;
      };
    try {
      const result = await applyStep(project, history, direction);
      if (!result) return;
      const persisted = persist(result.history);
      if (!current()) return;
      // Restore already returns the full committed Project. Starting another load here
      // would recapture an obsolete navigation intent after the user had left.
      setProject(result.project);
      setEditHistory(persisted ? result.history : reconcileHistory(readHistory(projectId), result.project.revision));
      setPreflight(null);
      setNotice(
        `${direction === "undo" ? "Undid" : "Redid"} a graph edit as new revision ${result.project.revision}. Earlier revisions and run snapshots are unchanged.`,
      );
    } catch (error) {
      if (error instanceof HistoryStale) {
        persist({ undo: [], redo: [] });
        if (current()) setEditHistory({ undo: [], redo: [] });
      }
      if (!current()) return;
      throw error;
    }
  }
  function historyFromControl(direction: "undo" | "redo", origin: HTMLButtonElement) {
    const request = project && document.activeElement === origin ? {
      projectId: project.projectId,
      loadSequence: projectLoadSequence.current,
      intentSequence: preflightRequestSequence.current,
      direction: origin === undoControl.current ? "undo" as const : "redo" as const, origin,
    } : null;
    void doAction(direction === "undo" ? "Undoing graph edit" : "Redoing graph edit", async () => {
      try { await stepHistory(direction); }
      finally { if (request) setHistoryFocus(request); }
    });
  }
  async function validate() {
    if (!project) return;
    const result = await api(`/projects/${project.projectId}/validations`, {
      method: "POST",
      body: { revision: project.revision },
    });
    setNotice(
      result.valid
        ? "Authoritative platform validation passed. Execution readiness is checked separately."
        : "Validation found issues. The source remains available for correction.",
    );
    if (result.diagnostics?.length)
      setError(
        Object.assign(new Error("Validation diagnostics"), {
          details: { diagnostics: result.diagnostics },
          code: "VALIDATION_DIAGNOSTICS",
        }),
      );
  }
  async function exportProject() {
    if (!project) return;
    const response = await fetch(
      `/api/v1/projects/${project.projectId}/exports`,
      {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrf,
          "If-Match": `"${project.revision}"`,
          "Idempotency-Key": mutationKey(),
        },
        body: JSON.stringify({ revision: project.revision }),
      },
    );
    if (!response.ok)
      throw new ApiError(response.status, await response.json());
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const result = await response.json();
      const downloadUrl = result.downloadUrl || result.result?.downloadUrl;
      if (downloadUrl) {
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "project.studio.zip";
        a.click();
      } else
        setNotice(
          `Export accepted: ${result.operationId || JSON.stringify(result)}`,
        );
    } else {
      const url = URL.createObjectURL(await response.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "project.studio.zip";
      a.click();
      URL.revokeObjectURL(url);
    }
  }
  async function importFile(file: File) {
    projectLoadSequence.current++;
    const context = projectIntent();
    const uploadLimit =
      Math.floor(
        (capabilities.limits?.requestBytes || 8 * 1024 * 1024) * 0.75,
      ) - 1024;
    if (file.size > uploadLimit)
      throw new Error(
        `Select an archive smaller than ${(uploadLimit / 1024 / 1024).toFixed(1)} MiB for the advertised request limit.`,
      );
    const result = await (async () => {
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (let i = 0; i < bytes.length; i += 8192)
        binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      const imported = await api<Project>("/projects/imports", {
        method: "POST",
        body: { archiveBase64: btoa(binary) },
        key: mutationKey(),
      });
      await refreshProjects();
      return imported;
    })().catch((error) => {
      if (sameProjectIntent(context)) throw error;
      return undefined;
    });
    if (!result?.projectId || !sameProjectIntent(context)) return;
    if (!(await loadProject(result.projectId))) return;
    setNotice(
      "Archive imported without executing referenced code. Review Dependencies for unresolved content, then validate before running.",
    );
  }
  async function importEvidence(file: File) {
    if (file.size > 6 * 1024 * 1024)
      throw new Error("Select an evidence archive smaller than 6 MiB.");
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (let i = 0; i < bytes.length; i += 8192)
      binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
    setEvidenceImport(
      await api("/evidence/imports", {
        method: "POST",
        body: { archiveBase64: btoa(binary) },
        key: mutationKey(),
      }),
    );
    setModal("evidence-import");
  }
  // Domain terms for the shared workflows; the core terms apply until they load.
  const presentation = usePresentationData(
    project?.projectId,
    project?.revision,
  );
  if (authenticated === null)
    return (
      <div className="startup">
        <div className="brand-mark">X</div>
        <p>Opening your local workspace…</p>
      </div>
    );
  if (!authenticated)
    return (
      <Login
        onLogin={async (token) => {
          const session = await api("/session", {
            method: "POST",
            body: { bootstrapToken: token },
          });
          setCsrfToken(session.csrfToken);
          setCsrf(session.csrfToken);
          setAuthenticated(true);
          await loadBoot();
        }}
      />
    );
  const runStatus = String(run?.status || run?.state || "No active run");
  return (
    <PresentationContext.Provider value={presentation}>
      <div className="application">
        <a
          className="skip-link"
          href="#main-content"
          onClick={() => {
            if (project && section === "workspace")
              workspaceInteractionSequence.current++;
          }}
        >
          Skip to workspace
        </a>
        <header className="topbar">
          <button
            className="brand"
            onClick={() => showHome()}
            aria-label="X-Verse Studio home"
          >
            <span className="brand-mark">X</span>
            <span>
              X-VERSE <b>STUDIO</b>
            </span>
          </button>
          <div className="top-divider" />
          <span className="environment">
            <span className="status-dot" />
            Local workspace
          </span>
          <span className="top-spacer" />
          <Badge>REFERENCE PREVIEW</Badge>
          <button className="top-button" onClick={() => changeSection("settings")}>
            <Icon name="settings" />
            <span>Environment</span>
          </button>
          <span className="avatar" aria-label="Local operator">
            LO
          </span>
        </header>
        <div className="app-body">
          <nav className="rail" aria-label="Main navigation">
            <button
              className={section === "workspace" ? "active" : ""}
              title="Workspace"
              aria-label="Workspace"
              aria-current={section === "workspace" ? "page" : undefined}
              onClick={() => changeSection("workspace")}
            >
              <Icon name="model" size={22} />
              <span>Workspace</span>
            </button>
            <button
              className={section === "catalog" ? "active" : ""}
              title="Catalog"
              aria-label="Catalog"
              aria-current={section === "catalog" ? "page" : undefined}
              onClick={() => changeSection("catalog")}
            >
              <Icon name="catalog" size={22} />
              <span>Catalog</span>
            </button>
            <button
              className={section === "lab" ? "active" : ""}
              title="Laboratory"
              aria-label="Laboratory"
              aria-current={section === "lab" ? "page" : undefined}
              onClick={() => changeSection("lab")}
            >
              <Icon name="lab" size={22} />
              <span>Lab</span>
            </button>
            <div className="rail-spacer" />
            <button
              className={section === "settings" ? "active" : ""}
              aria-label="Compatibility and environment"
              aria-current={section === "settings" ? "page" : undefined}
              onClick={() => changeSection("settings")}
            >
              <Icon name="settings" size={22} />
              <span>Settings</span>
            </button>
            <span className="rail-version">v0.1</span>
          </nav>
          <main
            id="main-content"
            className="main-content"
            onPointerDownCapture={workspaceInteraction}
            onKeyDownCapture={workspaceInteraction}
            onInputCapture={workspaceInteraction}
          >
            <div className="alerts" aria-live="polite">
              {busy && (
                <div className="notice busy">
                  <span className="spinner" />
                  {busy}…
                </div>
              )}
              {notice && (
                <div className="notice">
                  <Icon name="info" />
                  {notice}
                  <button
                    aria-label="Dismiss notice"
                    onClick={() => setNotice("")}
                  >
                    <Icon name="close" size={14} />
                  </button>
                </div>
              )}
              {pendingStart &&
                pendingStart.projectId === project?.projectId && (
                  <PendingStartNotice
                    pending={pendingStart}
                    sending={startSending}
                    onRetry={() =>
                      void doAction("Resolving the pending Start", () =>
                        deliverStart(pendingStart),
                      )
                    }
                    onDismiss={() => {
                      clearPendingStart(pendingStart.projectId);
                      setPendingStart(null);
                    }}
                  />
                )}
              {project?.sourceIntegrity === "modified" && (
                <div className="notice error" role="alert">
                  <Icon name="info" />
                  <div>
                    <strong>Source files changed outside Studio</strong>
                    <p>
                      Inspect and copy the source before recovery. The recorded
                      revision has not admitted these bytes; saving, validation
                      and execution are blocked.
                    </p>
                    <Diagnostics
                      diagnostics={project.sourceDiagnostics || []}
                    />
                    <RecoveryPanel
                      key={`${project.projectId}:${project.revision}`}
                      project={project}
                      {...recoveryHandlers(project.projectId)}
                    />
                  </div>
                </div>
              )}
              {error && (
                <div
                  className="notice error"
                  role="alert"
                  aria-label="Operation error"
                  tabIndex={-1}
                  ref={operationError}
                >
                  <Icon name="info" />
                  <div>
                    <strong>
                      {(error as ApiError).code || "Operation unavailable"}
                    </strong>
                    <p>{error.message}</p>
                    <Diagnostics
                      diagnostics={(error as ApiError).details?.diagnostics}
                    />
                    {(error as ApiError).code === "PROJECT_UNAVAILABLE" &&
                      (() => {
                        // Unreadable committed sources can still be restored from history.
                        const listed = projects.find(
                          (p) => p.projectId === (
                            (error as ProjectRequestError).requestedProjectId ||
                            selectedProjectRef.current
                          ),
                        );
                        return listed ? (
                          <RecoveryPanel
                            key={`${listed.projectId}:${listed.revision}`}
                            project={listed}
                            adoptable={false}
                            {...recoveryHandlers(listed.projectId)}
                          />
                        ) : null;
                      })()}
                    {(error as ApiError).status === 412 && (
                      <button
                        onClick={() =>
                          void doAction(
                            "Loading current revision",
                            async () => {
                              const target = (error as ProjectRequestError).requestedProjectId,
                                accepted = target
                                  ? await loadProject(target)
                                  : await refreshProject();
                              if (!accepted) return;
                              setNotice(
                                "Current revision loaded. Compare it with your draft before saving again.",
                              );
                            },
                          )
                        }
                      >
                        Load current revision
                      </button>
                    )}
                  </div>
                  <button
                    aria-label="Dismiss error"
                    onClick={() => setError(null)}
                  >
                    <Icon name="close" size={14} />
                  </button>
                </div>
              )}
            </div>
            {section === "settings" ? (
              <Environment
                capabilities={capabilities}
                providers={providers}
                project={project}
                onIntent={() => {
                  if (project && selectedProjectRef.current === project.projectId)
                    workspaceInteractionSequence.current++;
                }}
                onCommitted={(saved, navigate, origin) => {
                  const visible = commitProjectRevision(saved);
                  if (visible && navigate) {
                    setSection("workspace");
                    setNotice(
                      "Profile locks saved with exact schema and presentation identities.",
                    );
                    setProjectActionFocus({
                      projectId: saved.projectId,
                      loadSequence: renderedLoadSequence,
                      intentSequence: preflightRequestSequence.current,
                      origin,
                      target: "source",
                    });
                  }
                  return visible;
                }}
                onRefused={(origin) => {
                  if (
                    !project ||
                    selectedProjectRef.current !== project.projectId ||
                    projectLoadSequence.current !== renderedLoadSequence ||
                    preflightRequestSequence.current !== renderedIntentSequence
                  )
                    return false;
                  setProjectActionFocus({
                    projectId: project.projectId,
                    loadSequence: renderedLoadSequence,
                    intentSequence: renderedIntentSequence,
                    origin,
                    target: "error",
                  });
                  return true;
                }}
                doAction={doAction}
              />
            ) : section === "lab" ? (
              <LabView providers={providers} doAction={doAction} />
            ) : section === "catalog" ? (
              <Catalog
                entries={catalog}
                onCreate={(id) =>
                  void doAction("Creating project", () => createProject(id))
                }
                onClose={() => changeSection("workspace")}
                onRegister={() => setModal("artifact")}
                onTemplate={(template) => {
                  setAddTemplate(template);
                  setAddKind("component");
                  setModal("add");
                }}
                onRetention={(entry) =>
                  setRetentionTarget({
                    kind: "artifact",
                    id: entry.entryId || entry.id || "",
                    name: entry.name,
                  })
                }
                hasProject={!!project}
              />
            ) : !project ? (
              <Home
                onRetention={(value) =>
                  setRetentionTarget({
                    kind: "project",
                    id: value.projectId,
                    name: value.name,
                  })
                }
                projects={projects}
                catalog={catalog}
                onOpen={(id) =>
                  void doAction("Opening project", () => loadProject(id))
                }
                onCreate={(id) =>
                  void doAction("Creating project", () => createProject(id))
                }
                onNew={() => setModal("new")}
                onImport={(file) =>
                  void doAction("Inspecting archive", () => importFile(file))
                }
                onImportEvidence={(file) =>
                  void doAction("Inspecting evidence without execution", () =>
                    importEvidence(file),
                  )
                }
              />
            ) : (
              <>
                <div className="project-header">
                  <div>
                    <div className="breadcrumb">
                      <button
                        onClick={() => showHome(true)}
                      >
                        Workspace
                      </button>
                      <Icon name="chevron" size={12} />
                      <span>System</span>
                    </div>
                    <div className="title-row">
                      <span className="system-icon">
                        <Icon
                          name={presentation.icons?.System || "model"}
                          size={22}
                        />
                      </span>
                      <h1>{project.name}</h1>
                      <Badge tone="info">Draft</Badge>
                      <DomainBadge />
                      <span className="revision">
                        rev {String(project.revision).slice(0, 8)}
                      </span>
                    </div>
                  </div>
                  <div className="header-actions">
                    <InspectionButton
                      projectId={project.projectId}
                      revision={project.revision}
                      onOpen={() => setModal("inspection")}
                    />
                    <button
                      ref={undoControl}
                      className="button"
                      disabled={!!busy || !editHistory.undo.length}
                      aria-keyshortcuts="Control+Z"
                      title={
                        editHistory.undo.length
                          ? `Undo ${editHistory.undo[editHistory.undo.length - 1].label}`
                          : "No graph edit to undo in this tab"
                      }
                      onClick={(event) => historyFromControl("undo", event.currentTarget)}
                    >
                      Undo
                    </button>
                    <button
                      ref={redoControl}
                      className="button"
                      disabled={!!busy || !editHistory.redo.length}
                      aria-keyshortcuts="Control+Shift+Z"
                      title={
                        editHistory.redo.length
                          ? `Redo ${editHistory.redo[editHistory.redo.length - 1].label}`
                          : "No graph edit to redo in this tab"
                      }
                      onClick={(event) => historyFromControl("redo", event.currentTarget)}
                    >
                      Redo
                    </button>
                    <button
                      className="button"
                      onClick={() =>
                        void doAction("Exporting project", exportProject)
                      }
                    >
                      <Icon name="download" />
                      Export
                    </button>
                    <button
                      className="button"
                      onClick={() => void doAction("Validating XDL", validate)}
                    >
                      <Icon name="check" />
                      Validate
                    </button>
                    <button
                      className="button primary"
                      data-preflight-trigger=""
                      disabled={!!busy}
                      onClick={() =>
                        void doAction("Checking readiness", checkPreflight)
                      }
                    >
                      <Icon name="play" />
                      Preflight & run
                    </button>
                  </div>
                </div>
                <div
                  className="view-tabs"
                  role="tablist"
                  aria-label="System workflows"
                >
                  {(Object.keys(viewIcons) as View[]).map((v) => (
                    <button
                      key={v}
                      role="tab"
                      aria-selected={view === v}
                      className={view === v ? "active" : ""}
                      onClick={() => setView(v)}
                    >
                      <Icon
                        name={
                          presentation.icons?.[viewTerms[v]] || viewIcons[v]
                        }
                        size={17}
                      />
                      {v}
                      {v === "Results" && run && (
                        <span className="tab-count">1</span>
                      )}
                    </button>
                  ))}
                  <span className="tab-fill" />
                  <button
                    ref={sourceControl}
                    className="source-toggle"
                    onClick={() => openSource()}
                  >
                    <Icon name="code" size={17} />
                    XDL source
                  </button>
                </div>
                <div className="workspace-context">
                  <span>
                    <span className="tiny-dot" />
                    Draft revision{" "}
                    <code>{String(project.revision).slice(0, 8)}</code>
                  </span>
                  <span>
                    {projection.elements.length} elements ·{" "}
                    {projection.connections.length} connections
                  </span>
                  <span className="context-spacer" />
                  <span>
                    {run ? (
                      <>
                        Run snapshot <code>{run.snapshotId.slice(0, 12)}</code>{" "}
                        <Badge tone={statusTone(runStatus)}>{runStatus}</Badge>{" "}
                        <RunDivergenceBadge
                          divergence={divergence}
                          state={snapshotState}
                          open={divergenceOpen}
                          onToggle={() => setDivergenceOpen((open) => !open)}
                          onRetry={retrySnapshot}
                        />
                      </>
                    ) : (
                      <>
                        Execution scope <Badge>Owned reference</Badge>
                      </>
                    )}
                  </span>
                </div>
                {divergenceOpen && divergence && (
                  <RunDivergencePanel
                    divergence={divergence}
                    onSelectElement={(ref) => {
                      setSelected(ref);
                      setView("Model");
                    }}
                    onOpenDocument={(path) => {
                      const documentId = Object.entries(project.documents).find(
                        ([, d]: [string, any]) => d.path === path,
                      )?.[0];
                      if (documentId) openSource({ documentId });
                    }}
                    onFrozenInputs={() => setFrozenOpen(true)}
                  />
                )}
                {frozenOpen && runSnapshot && (
                  <FrozenInputs
                    snapshot={runSnapshot}
                    onClose={() => setFrozenOpen(false)}
                  />
                )}
                {view === "Model" ? (
                  <ModelView
                    runChanges={divergence?.byElement}
                    project={project}
                    projection={projection}
                    parameters={parameters}
                    selected={selected}
                    setSelected={setSelected}
                    edit={(edits) =>
                      doAction("Saving semantic edit", () => edit(edits))
                    }
                    saveLayout={(layout) =>
                      doAction("Saving layout", async () => {
                        await api(`/projects/${project.projectId}/layout`, {
                          method: "PUT",
                          revision:
                            project.presentationRevision || project.revision,
                          body: { positions: layout.positions },
                        });
                        await refreshProject();
                        setNotice(
                          "Layout saved separately from executable XDL.",
                        );
                      })
                    }
                    onSource={openSource}
                    onCatalog={() => {
                      setAddTemplate("");
                      setModal("add");
                    }}
                  />
                ) : view === "Connections" ? (
                  <ConnectionsView
                    projection={projection}
                    projectId={project.projectId}
                    revision={project.revision}
                    onOpenView={(next) => setView(next as typeof view)}
                    runId={
                      run?.projectId === project.projectId
                        ? run.runId
                        : undefined
                    }
                    runState={
                      run?.projectId === project.projectId
                        ? run.state
                        : undefined
                    }
                    edit={(edits) =>
                      doAction("Validating connection", () => edit(edits))
                    }
                  />
                ) : view === "Deployment" ? (
                  <DeploymentComposer
                    project={project}
                    projection={projection}
                    providers={providers}
                    providerId={executionProvider}
                    selection={executionSelection}
                    onSelection={chooseExecution}
                    onCommitted={commitProjectRevision}
                    doAction={doAction}
                  />
                ) : view === "Experiments" ? (
                  <ExperimentsView
                    project={project}
                    projection={projection}
                    selection={executionSelection}
                    edit={edit}
                    authoringLimits={
                      capabilities.limits?.scenarioAuthoring || {}
                    }
                    preflight={preflight}
                    run={run}
                    doAction={doAction}
                    refresh={refreshProject}
                    onSource={openSource}
                  />
                ) : (
                  <ResultsView
                    run={run}
                    events={events}
                    omitted={omitted}
                    streamState={streamState}
                    selected={selected}
                    setSelected={(id) => {
                      setSelected(id);
                      setView("Model");
                    }}
                    doAction={doAction}
                    onRunUpdated={runUpdated}
                    onRun={checkPreflight}
                    rerunEnabled={Boolean(
                      capabilities.supportedOperations?.includes("rerun"),
                    )}
                    onSelectRun={(created) => {
                      if (created.projectId)
                        localStorage.setItem(
                          "studio.lastRun." + created.projectId,
                          created.runId,
                        );
                      if (created.projectId === selectedProjectRef.current) {
                        setRun(created);
                        lastRun.current = created.runId;
                        localStorage.setItem("studio.lastRun", created.runId);
                        setView("Results");
                      }
                    }}
                  />
                )}
                <footer className="workspace-footer">
                  <span>
                    <Icon name="folder" size={13} />
                    Local project ·{" "}
                    {project.sourceIntegrity === "modified"
                      ? "External source changes"
                      : "Saved on backend"}
                  </span>
                  <span>Authoritative XDL · Layout stored separately</span>
                  <span>
                    {
                      providers.filter(
                        (p) => p.available || p.availability === "available",
                      ).length
                    }{" "}
                    provider(s) available
                  </span>
                </footer>
              </>
            )}
          </main>
        </div>
        {modal === "evidence-import" && evidenceImport && (
          <Modal
            title="Imported evidence inspection"
            wide
            onClose={() => setModal("")}
          >
            <p>
              This is recorded evidence inspection. Import creates no run and
              grants no execution authority.
            </p>
            <KeyValues
              values={{
                Bundle: evidenceImport.bundleId,
                Integrity: evidenceImport.inspection?.integrity,
                "Source run": evidenceImport.inspection?.sourceRunId,
                "Source snapshot": evidenceImport.inspection?.sourceSnapshotId,
                Availability: evidenceImport.inspection?.availability,
                "Execution allowed": "No",
              }}
            />
            <Json value={evidenceImport} expanded />
          </Modal>
        )}
        {modal === "new" && (
          <Modal title="Create a System workspace" onClose={() => setModal("")}>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void doAction("Creating project", () => createProject());
              }}
            >
              <p>
                Begin with the owned reference blueprint. You can inspect and
                edit its XDL before execution.
              </p>
              <label>
                Project name
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={120}
                  placeholder="My System"
                />
              </label>
              <div className="form-actions">
                <button
                  type="button"
                  className="button"
                  onClick={() => setModal("")}
                >
                  Cancel
                </button>
                <button className="button primary" disabled={!!busy}>
                  Create project
                </button>
              </div>
            </form>
          </Modal>
        )}
        {retentionTarget && (
          <RetentionDialog
            target={retentionTarget}
            onClose={() => setRetentionTarget(null)}
            restoreFocusSelector={
              retentionTarget.kind === "project"
                ? "#recent-projects-heading"
                : "#catalog-heading"
            }
            onChanged={async (result) => {
              const removed = result.outcomes?.some(
                (row: Data) =>
                  row.projectId === project?.projectId &&
                  row.status === "removed",
              );
              if (removed) {
                setProject(null);
                setRun(null);
                setPreflight(null);
                selectedProjectRef.current = "";
                localStorage.removeItem("studio.projectId");
              }
              await refreshProjects();
              setCatalog(items<CatalogEntry>(await api("/catalog")));
            }}
          />
        )}
        {modal === "inspection" && project && (
          <Modal
            title="Dependencies and unresolved content"
            wide
            onClose={() => setModal("")}
          >
            <InspectionDialogBody
              projectId={project.projectId}
              revision={project.revision}
              onOpenSource={(documentId) => {
                // Close first so focus returns to the header before the source dialog takes it.
                setModal("");
                window.setTimeout(() => openSource({ documentId }), 0);
              }}
            />
          </Modal>
        )}
        {modal === "source" && project && (
          <Modal title="Authored XDL source" wide onClose={() => setModal("")}>
            <SourceEditor
              key={project.projectId}
              project={project}
              target={sourceContext}
              doAction={(label, action) =>
                doAction(label, async () => {
                  try {
                    return await action();
                  } catch (error) {
                    if (
                      selectedProjectRef.current === project.projectId &&
                      projectLoadSequence.current === renderedLoadSequence &&
                      preflightRequestSequence.current ===
                        renderedIntentSequence
                    )
                      throw error;
                  }
                })
              }
              onSaved={(saved) => {
                const current = commitProjectRevision(saved);
                if (current)
                  setNotice(
                    "Source revision saved. Validate it before running.",
                  );
                return current;
              }}
            />
          </Modal>
        )}
        {modal === "preflight" && preflight && project && (
          <PreflightReview
            preflight={preflight}
            currentRevision={project.revision}
            providers={providers}
            onClose={() => {
              preflightRequestSequence.current++;
              setModal("");
            }}
            onStart={start}
            projectId={project.projectId}
            startBlockedReason={
              startBlocked(project.projectId)
                ? unresolvedStartReason
                : undefined
            }
            onRecheck={checkPreflight}
          />
        )}
        {modal === "artifact" && (
          <Modal
            title="Register an inert artifact reference"
            onClose={() => setModal("")}
          >
            <ArtifactRegistrationForm
              providers={providers}
              doAction={doAction}
              onSaved={async () => {
                setCatalog(items<CatalogEntry>(await api("/catalog")));
                setModal("");
                setNotice(
                  "Artifact metadata registered. No artifact was downloaded or executed.",
                );
              }}
            />
          </Modal>
        )}
        {modal === "add" && (
          <Modal
            title={`Add ${presentation.labels?.Element || "element"}`}
            onClose={() => setModal("")}
          >
            <label>
              Element family
              <select
                aria-label="Element family"
                value={addKind}
                onChange={(e) => setAddKind(e.target.value)}
              >
                <option value="component">Reusable component instance</option>
                <option value="logical">
                  Device, Sensor, Actuator or Model
                </option>
              </select>
            </label>
            {addKind === "logical" ? (
              <LogicalAssetForm
                projection={projection}
                onSave={async (edits) => {
                  await edit(edits);
                  setModal("");
                  setView("Model");
                }}
              />
            ) : (
              <InstanceWizard
                initialTemplate={addTemplate}
                admittedApiVersions={capabilities.xdl?.apiVersions}
                catalog={catalog}
                projection={projection}
                onSubmit={async (edits) => {
                  await edit(edits);
                  setModal("");
                  setView("Model");
                }}
                doAction={doAction}
              />
            )}
          </Modal>
        )}
      </div>
    </PresentationContext.Provider>
  );
}
function InspectionDialogBody({
  projectId,
  revision,
  onOpenSource,
}: {
  projectId: string;
  revision: number;
  onOpenSource: (documentId: string) => void;
}) {
  const { report, failure } = useProjectInspection(projectId, revision);
  return (
    <ProjectInspection
      report={report}
      failure={failure}
      onOpenSource={onOpenSource}
    />
  );
}

function Login({ onLogin }: { onLogin: (token: string) => Promise<void> }) {
  const [token, setToken] = useState(""),
    [error, setError] = useState(""),
    [pending, setPending] = useState(false);
  return (
    <div className="login-shell">
      <div className="login-art">
        <div className="brand">
          <span className="brand-mark">X</span>
          <span>
            X-VERSE <b>STUDIO</b>
          </span>
        </div>
        <div>
          <span className="eyebrow">YOUR SYSTEM. ONE WORKSPACE.</span>
          <h1>
            From model
            <br />
            to evidence.
          </h1>
          <p>
            Compose systems, run admitted experiments,
            <br />
            and understand what happened.
          </p>
        </div>
        <div className="login-foot">LOCAL FIRST · INDUSTRY AGNOSTIC</div>
      </div>
      <main className="login-panel">
        <span className="eyebrow">LOCAL WORKSPACE</span>
        <h2>Connect to Studio</h2>
        <p id="bootstrap-instructions">
          Enter the one-use bootstrap token from the local launcher’s session
          file. Your session stays on this backend.
        </p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setPending(true);
            setError("");
            try {
              await onLogin(token);
            } catch (e) {
              setError(e instanceof Error ? e.message : "Connection failed");
            } finally {
              setPending(false);
              setToken("");
            }
          }}
        >
          <label>
            Bootstrap token
            <input
              type="password"
              value={token}
              onChange={(e) => {
                setToken(e.target.value);
                setError("");
              }}
              aria-describedby={`bootstrap-instructions bootstrap-help${error ? " bootstrap-error" : ""}`}
              aria-invalid={!!error}
              autoComplete="off"
              autoFocus
              required
              spellCheck={false}
            />
          </label>
          {error && (
            <p id="bootstrap-error" className="field-error" role="alert">
              {error}
            </p>
          )}
          <button className="button primary" disabled={pending}>
            {pending ? "Connecting…" : "Open workspace"}
            <Icon name="arrow" />
          </button>
        </form>
        <div id="bootstrap-help" className="login-help">
          <Icon name="info" />
          <span>
            The launcher creates a short-lived token locally. It is never sent
            in a URL or included in run evidence.
          </span>
        </div>
      </main>
    </div>
  );
}
function Home({
  projects,
  catalog,
  onOpen,
  onCreate,
  onNew,
  onImport,
  onImportEvidence,
  onRetention,
}: {
  onRetention: (project: Project) => void;
  projects: Project[];
  catalog: CatalogEntry[];
  onOpen: (id: string) => void;
  onCreate: (id: string) => void;
  onNew: () => void;
  onImport: (file: File) => void;
  onImportEvidence: (file: File) => void;
}) {
  const input = useRef<HTMLInputElement>(null),
    evidenceInput = useRef<HTMLInputElement>(null);
  return (
    <div className="home">
      <div className="home-heading">
        <div>
          <span className="eyebrow">LOCAL WORKSPACE</span>
          <h1>
            Build understanding.
            <br />
            <span>One System at a time.</span>
          </h1>
          <p>
            Model, connect, and explore cyber-physical systems.
            <br />
            Keep every experiment connected to its evidence.
          </p>
        </div>
        <div className="home-actions">
          <button className="button primary" onClick={onNew}>
            <Icon name="plus" />
            New project
          </button>
          <button className="button" onClick={() => input.current?.click()}>
            <Icon name="upload" />
            Import project
          </button>
          <button
            className="button"
            onClick={() => evidenceInput.current?.click()}
          >
            <Icon name="upload" />
            Import evidence
          </button>
          <input
            ref={evidenceInput}
            className="visually-hidden"
            type="file"
            accept=".zip,application/zip"
            aria-label="Import evidence archive"
            onChange={(e) => {
              if (e.target.files?.[0]) onImportEvidence(e.target.files[0]);
              e.target.value = "";
            }}
          />
          <input
            ref={input}
            className="visually-hidden"
            type="file"
            accept=".zip,application/zip"
            aria-label="Import project archive"
            onChange={(e) => {
              if (e.target.files?.[0]) onImport(e.target.files[0]);
              e.target.value = "";
            }}
          />
        </div>
      </div>
      <section className="home-section">
        <div className="section-heading">
          <div>
            <h2>Start with an example</h2>
            <p>A guided path from a model to a recorded result.</p>
          </div>
          <Badge tone="info">OWNED REFERENCE PROVIDER</Badge>
        </div>
        <div className="example-grid">
          {catalog
            .filter((c) => !c.kind || c.kind === "blueprint" || c.documents)
            .map((entry, index) => (
              <button
                key={entry.id || entry.entryId}
                className="example-card"
                onClick={() => onCreate(entry.id || entry.entryId || "")}
              >
                <div className={`example-illustration art-${index % 3}`}>
                  <span className="art-node a">
                    <Icon name="settings" size={25} />
                  </span>
                  <span className="art-line" />
                  <span className="art-node b">
                    <Icon name="model" size={25} />
                  </span>
                  <span className="art-orbit" />
                  <Badge>{entry.maturity || "Reference"}</Badge>
                </div>
                <div className="example-copy">
                  <h3>
                    {entry.name}
                    <Icon name="arrow" size={19} />
                  </h3>
                  <p>
                    {entry.description ||
                      "Inspect the model, validate its inputs, and execute a bounded reference experiment."}
                  </p>
                  <div className="card-tags">
                    <span>Guided example</span>
                    <span>{entry.scope || "Owned reference"}</span>
                  </div>
                  {!!entry.limitations?.length && (
                    <p className="card-limit">
                      Scope limit: {entry.limitations[0]}
                    </p>
                  )}
                </div>
              </button>
            ))}
        </div>
        {!catalog.length && (
          <Empty title="No examples admitted" icon="catalog">
            Environment capability discovery will explain missing dependencies.
          </Empty>
        )}
        <p className="scope-note">
          <Icon name="info" size={15} />
          Reference runs verify Studio workflows. Their results do not establish
          external simulator or physical-device integration.
        </p>
      </section>
      <section className="home-section">
        <div className="section-heading">
          <div>
            <h2 id="recent-projects-heading" tabIndex={-1}>
              Recent projects
            </h2>
            <p>Continue from your last saved draft.</p>
          </div>
          <span className="muted">
            {projects.length} project{projects.length === 1 ? "" : "s"}
          </span>
        </div>
        {projects.length ? (
          <div className="project-list">
            {projects.map((p) => (
              <div
                className="project-list-row"
                key={p.projectId}
                data-project-id={p.projectId}
              >
                <button
                  className="project-open"
                  onClick={() => onOpen(p.projectId)}
                >
                  <span className="project-list-icon">
                    <Icon name="model" size={22} />
                  </span>
                  <span>
                    <strong>{p.name}</strong>
                    <small>
                      System workspace · rev{" "}
                      {String(p.revision || "").slice(0, 8)}
                    </small>
                  </span>
                  <Badge>Local</Badge>
                  <Icon name="chevron" size={17} />
                </button>
                <button
                  className="button project-retention"
                  aria-label={`Review retention for project ${p.name}`}
                  onClick={() => onRetention(p)}
                >
                  Retention
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-projects">
            <Icon name="folder" />
            <span>
              Your projects will appear here. Explore an example to get started.
            </span>
          </div>
        )}
      </section>
    </div>
  );
}
function Catalog({
  entries,
  onCreate,
  onClose,
  onRegister,
  onTemplate,
  hasProject,
  onRetention,
}: {
  onRetention: (entry: CatalogEntry) => void;
  onRegister: () => void;
  onTemplate: (template: string) => void;
  hasProject: boolean;
  entries: CatalogEntry[];
  onCreate: (id: string) => void;
  onClose: () => void;
}) {
  const [search, setSearch] = useState(""),
    [kind, setKind] = useState("");
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">ADMITTED CONTENT</span>
          <h1 id="catalog-heading" tabIndex={-1}>
            Catalog
          </h1>
          <p>
            Blueprints compose examples. Profiles provide semantics. Providers
            implement integration.
          </p>
        </div>
        <div className="header-actions">
          <button className="button" onClick={onRegister}>
            <Icon name="plus" />
            Register artifact metadata
          </button>
          <button className="button" onClick={onClose}>
            Back to workspace
          </button>
        </div>
      </div>
      <div className="search-field">
        <Icon name="search" />
        <input
          aria-label="Search catalog"
          placeholder="Search by name, role, profile, or maturity"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <label className="catalog-kind-filter">
        Catalog kind
        <select
          aria-label="Catalog kind"
          value={kind}
          onChange={(event) => setKind(event.target.value)}
        >
          <option value="">All admitted entries</option>
          <option value="blueprint">Blueprints</option>
          <option value="component">Reusable components</option>
          <option value="artifact">Artifact references</option>
        </select>
      </label>
      <div className="catalog-grid">
        {entries
          .filter(
            (e) =>
              (!kind || e.kind === kind) &&
              JSON.stringify(e).toLowerCase().includes(search.toLowerCase()),
          )
          .map((e) => (
            <article className="panel" key={e.id || e.entryId}>
              <div className="section-heading">
                <Icon name="catalog" />
                <Badge>{e.maturity || "Unknown"}</Badge>
              </div>
              <h2>{e.name}</h2>
              <p>{e.description}</p>
              <KeyValues
                values={{
                  Version: e.version || "Not declared",
                  Scope: e.scope || "Not declared",
                  Identity: e.digest || e.id || e.entryId,
                }}
              />
              <ul className="limits-list">
                {e.limitations?.map((l, i) => (
                  <li key={i}>{l}</li>
                ))}
              </ul>
              <Json value={e} />
              {!e.kind || e.kind === "blueprint" ? (
                <button
                  className="button primary"
                  onClick={() => onCreate(e.id || e.entryId || "")}
                >
                  Open as project
                  <Icon name="arrow" />
                </button>
              ) : e.kind === "component" ? (
                <button
                  className="button"
                  disabled={!hasProject}
                  onClick={() => onTemplate(e.templateId)}
                >
                  Add to current System
                </button>
              ) : (
                <div>
                  <p className="field-hint">
                    Registered reference only. Availability and provider
                    execution remain unresolved.
                  </p>
                  <button
                    className="button"
                    aria-label={`Review retention for artifact ${e.name}`}
                    onClick={() => onRetention(e)}
                  >
                    Review registration retention
                  </button>
                </div>
              )}
            </article>
          ))}
      </div>
    </div>
  );
}
function Environment({
  capabilities,
  providers,
  project,
  onCommitted,
  onRefused,
  onIntent,
  doAction,
}: {
  capabilities: Data;
  providers: Data[];
  project: Project | null;
  onCommitted: ProfileBindingCommit;
  onRefused: ProfileBindingRefusal;
  onIntent: () => void;
  doAction: DoAction;
}) {
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">COMPATIBILITY & AUTHORITY</span>
          <h1>Environment</h1>
          <p>
            Studio host support and each provider’s compatibility are
            independent.
          </p>
        </div>
      </div>
      <section className="panel">
        <h2>Studio backend</h2>
        <KeyValues
          values={{
            "API version":
              capabilities.apiVersion || capabilities.contractVersion || "1.0",
            "Host OS":
              capabilities.host?.os || capabilities.hostOS || "Unknown",
            Architecture:
              capabilities.host?.architecture ||
              capabilities.architecture ||
              "Unknown",
            "Native target OS":
              capabilities.studio?.nativeTargets || "Not declared",
            "Verified native OS":
              capabilities.studio?.verifiedNativeOS || "Not declared",
            "Windows checks":
              capabilities.studio?.windowsAcceptance || "NOT_RUN",
            "Execution owner": "Backend and admitted provider",
            Exposure: "Local authenticated session",
          }}
        />
        <Json value={capabilities} />
      </section>
      <h2 className="section-title">Provider compatibility</h2>
      <div className="catalog-grid">
        {providers.map((p) => (
          <section className="panel" key={p.providerId || p.id}>
            <div className="section-heading">
              <h3>{p.name || p.providerId || p.id}</h3>
              <Badge tone={p.available ? "success" : "warning"}>
                {p.available ? "Available" : p.availability || "Unavailable"}
              </Badge>
            </div>
            <p>{p.description || p.unavailableReason || p.reason}</p>
            <KeyValues
              values={{
                Version: p.providerVersion || p.version || "Unknown",
                Scope: p.evidenceScope || p.scope || "Unknown",
                "Supported OS":
                  p.supportedHostOS ||
                  p.supportedOS ||
                  p.hostOS ||
                  p.supportedPlatforms ||
                  "Unknown",
                Maturity: p.maturity || "Unknown",
              }}
            />
            <Diagnostics diagnostics={p.diagnostics || p.blockedReasons} />
            <Json value={p} />
          </section>
        ))}
      </div>
      <ProfileBindingsPanel
        project={project}
        onCommitted={onCommitted}
        onRefused={onRefused}
        onIntent={onIntent}
        doAction={doAction}
      />
    </div>
  );
}
