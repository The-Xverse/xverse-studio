import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Data, Project } from "../../api/types";
import type { DoAction } from "../../app/App";

export interface RecoveryResult {
  project: Project;
  recovery: Data;
}

/** Explicit resolution of externally changed sources; observed bytes are backed up first. */
export function RecoveryPanel({
  project,
  doAction,
  onRecovered,
  adoptable = true,
}: {
  project: { projectId: string; revision: number };
  doAction: DoAction;
  onRecovered: (result: RecoveryResult) => Promise<void>;
  adoptable?: boolean;
}) {
  const [recorded, setRecorded] = useState<boolean | null>(null);
  useEffect(() => {
    // Only a revision with recorded history can be restored.
    const controller = new AbortController();
    setRecorded(null);
    api(
      `/projects/${encodeURIComponent(project.projectId)}/revisions?before=${project.revision + 1}&limit=1`,
      { signal: controller.signal },
    )
      .then((history) => {
        if (!controller.signal.aborted)
          setRecorded(history.items?.[0]?.revision === project.revision);
      })
      .catch(() => {
        if (!controller.signal.aborted) setRecorded(false);
      });
    return () => controller.abort();
  }, [project.projectId, project.revision]);
  const recover = (action: "adopt_external" | "restore_revision") =>
    doAction("Recovering project sources", async () => {
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
      await onRecovered(result);
    });
  return (
    <div className="recovery-panel" role="group" aria-label="Source recovery">
      <p>
        Recovery first preserves the bytes now on disk in a recovery backup and
        then commits a new revision; revision {project.revision} stays in
        history. Sidecars keep their recorded content.
      </p>
      <div className="button-row">
        {adoptable && (
          <button
            className="button"
            onClick={() => void recover("adopt_external")}
          >
            Adopt external changes as a new revision
          </button>
        )}
        {recorded && (
          <button
            className="button"
            onClick={() => void recover("restore_revision")}
          >
            Restore committed revision {project.revision}
          </button>
        )}
      </div>
      {recorded === false && (
        <p className="hint">
          Revision {project.revision} predates recorded history, so it cannot be
          restored here.
          {adoptable
            ? " Adopting the external changes remains available."
            : " Preserve the data root and follow the recovery guide."}
        </p>
      )}
    </div>
  );
}
