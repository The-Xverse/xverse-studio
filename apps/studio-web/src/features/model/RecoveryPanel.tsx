import { useEffect, useState, useRef, useId } from "react";
import { api, ApiError } from "../../api/client";
import type { Data, Project } from "../../api/types";
import type { DoAction } from "../../app/App";

export interface RecoveryResult {
  project: Project;
  recovery: Data;
}

type HistoryObservation = {
  identity: string;
  status: "loading" | "recorded" | "absent" | "unavailable";
  error?: string;
};

/** Explicit resolution of externally changed sources; observed bytes are backed up first. */
export function RecoveryPanel({
  project,
  doAction,
  onRecovered,
  adoptable = true,
}: {
  project: { projectId: string; revision: number };
  doAction: DoAction;
  onRecovered: (
    result: RecoveryResult,
    origin: HTMLButtonElement,
  ) => void | Promise<void>;
  adoptable?: boolean;
}) {
  const identity = `${project.projectId}:${project.revision}`;
  const [history, setHistory] = useState<HistoryObservation>({
    identity,
    status: "loading",
  });
  const [attempt, setAttempt] = useState(0),
    [pending, setPending] = useState(false);
  const sending = useRef(false),
    mounted = useRef(true),
    descriptionId = useId();
  const restoreControl = useRef<HTMLButtonElement>(null),
    retryControl = useRef<HTMLButtonElement>(null),
    historyNotice = useRef<HTMLParagraphElement>(null),
    retryOrigin = useRef<HTMLButtonElement | null>(null);
  const status = history.identity === identity ? history.status : "loading";
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setHistory({ identity, status: "loading" });
    api(
      `/projects/${encodeURIComponent(project.projectId)}/revisions?before=${project.revision + 1}&limit=1`,
      { signal: controller.signal },
    )
      .then((value) => {
        if (
          !Array.isArray(value.items) ||
          value.items.length > 1 ||
          value.items.some(
            (item: Data) =>
              !Number.isSafeInteger(item?.revision) ||
              item.revision < 1 ||
              item.revision > project.revision,
          )
        )
          throw new Error(
            "The history response did not contain a valid revision list.",
          );
        if (!controller.signal.aborted)
          setHistory({
            identity,
            status:
              value.items[0]?.revision === project.revision
                ? "recorded"
                : "absent",
          });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setHistory({
            identity,
            status: "unavailable",
            error: `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The history request failed."}`,
          });
      });
    return () => controller.abort();
  }, [project.projectId, project.revision, identity, attempt]);
  useEffect(() => {
    if (status === "loading" || !retryOrigin.current) return;
    const origin = retryOrigin.current;
    retryOrigin.current = null;
    if (
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== origin)
    )
      return;
    (status === "recorded"
      ? restoreControl.current
      : status === "unavailable"
        ? retryControl.current
        : historyNotice.current
    )?.focus();
  }, [history, status]);
  async function recover(
    action: "adopt_external" | "restore_revision",
    origin: HTMLButtonElement,
  ) {
    if (
      sending.current ||
      (action === "restore_revision" && status !== "recorded")
    )
      return;
    sending.current = true;
    setPending(true);
    try {
      await doAction("Recovering project sources", async () => {
        const result = await api<RecoveryResult>(
          `/projects/${encodeURIComponent(project.projectId)}/recoveries`,
          {
            method: "POST",
            revision: project.revision,
            body: {
              expectedRevision: project.revision,
              action,
              ...(action === "restore_revision"
                ? { revision: project.revision }
                : {}),
            },
          },
        );
        await onRecovered(result, origin);
      });
    } finally {
      sending.current = false;
      if (mounted.current) setPending(false);
    }
  }
  return (
    <div
      className="recovery-panel"
      role="group"
      aria-label="Source recovery"
      aria-describedby={descriptionId}
      aria-busy={pending || status === "loading"}
    >
      <p id={descriptionId}>
        Recovery first preserves the bytes now on disk in a recovery backup and
        then commits a new revision; revision {project.revision} stays in
        history. Sidecars keep their recorded content.
      </p>
      <div className="button-row">
        {adoptable && (
          <button
            className="button"
            disabled={pending}
            onClick={(event) =>
              void recover("adopt_external", event.currentTarget)
            }
          >
            Adopt external changes as a new revision
          </button>
        )}
        {status === "recorded" && (
          <button
            ref={restoreControl}
            className="button"
            disabled={pending}
            onClick={(event) =>
              void recover("restore_revision", event.currentTarget)
            }
          >
            Restore committed revision {project.revision}
          </button>
        )}
        {(status === "unavailable" ||
          (status === "loading" && attempt > 0)) && (
          <button
            ref={retryControl}
            className="button"
            disabled={pending || status === "loading"}
            onClick={(event) => {
              retryOrigin.current = event.currentTarget;
              setAttempt((value) => value + 1);
            }}
          >
            Retry revision history
          </button>
        )}
      </div>
      {pending && (
        <p role="status">
          Recovering project sources. The current request is still pending.
        </p>
      )}
      {status === "loading" && (
        <p role="status">Checking recorded revision history…</p>
      )}
      {status === "unavailable" && (
        <p role="alert">
          Could not check revision history. Restoration availability is unknown.{" "}
          {history.error} Retry the history lookup.
        </p>
      )}
      {status === "absent" && (
        <p ref={historyNotice} role="status" tabIndex={-1} className="hint">
          No recorded copy is available for revision {project.revision}, so it
          cannot be restored here.
          {adoptable
            ? " Adopting the external changes remains available."
            : " Preserve the data root and follow the recovery guide."}
        </p>
      )}
    </div>
  );
}
