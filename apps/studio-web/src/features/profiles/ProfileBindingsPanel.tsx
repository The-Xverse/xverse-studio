import { useEffect, useState } from "react";
import type { ProfileBindings } from "../../../../../packages/contracts/api";
import type { Data, Project } from "../../api/types";
import { api, items } from "../../api/client";
import type { DoAction } from "../../app/App";
import { Badge, Json, KeyValues } from "../../app/ui";
export function ProfileBindingsPanel({
  project,
  refresh,
  doAction,
}: {
  project: Project | null;
  refresh: () => Promise<unknown>;
  doAction: DoAction;
}) {
  const [profiles, setProfiles] = useState<Data[]>([]),
    [selected, setSelected] = useState<string[]>([]);
  useEffect(() => {
    void api("/profiles")
      .then((response) => setProfiles(items(response)))
      .catch(() => {});
  }, []);
  return (
    <section className="panel profile-binding-panel">
      <h2>Admitted profile locks</h2>
      <p>
        Profiles supply versioned semantics and inert presentation metadata.
        Provider installation and execution authority are separate.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void doAction("Binding immutable profile identities", async () => {
            if (!project)
              throw new Error(
                "Open a System project before binding profile locks.",
              );
            await api(`/projects/${project.projectId}/profile-bindings`, {
              method: "POST",
              revision: project.revision,
              body: {
                baseRevision: project.revision,
                profiles: profiles
                  .filter((profile) => selected.includes(profile.profileId))
                  .map((profile) => ({
                    profileId: profile.profileId,
                    version: profile.version,
                    schemaDigest: profile.schemaDigest,
                    presentationDigest: profile.presentationDigest,
                  })),
              } satisfies ProfileBindings,
            });
            await refresh();
          });
        }}
      >
        <div className="catalog-grid">
          {profiles.map((profile) => (
            <article className="profile-choice" key={profile.profileId}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selected.includes(profile.profileId)}
                  onChange={(event) =>
                    setSelected((ids) =>
                      event.target.checked
                        ? [...ids, profile.profileId]
                        : ids.filter((id) => id !== profile.profileId),
                    )
                  }
                />
                <span>
                  Select profile{" "}
                  {profile.presentation?.name || profile.profileId}
                </span>
              </label>
              <Badge>{profile.maturity}</Badge>
              <p>{profile.presentation?.description}</p>
              <KeyValues
                values={{
                  Namespace: profile.namespace,
                  Version: profile.version,
                  "Schema identity": profile.schemaDigest,
                  "Presentation identity": profile.presentationDigest,
                  "Execution allowed": "No; provider authority is independent",
                }}
              />
              <Json value={profile} />
            </article>
          ))}
        </div>
        <div className="form-actions">
          <span className="field-hint">
            {project
              ? `Selected project: ${project.name} · revision ${project.revision}`
              : "Open a project to bind these exact profile identities."}
          </span>
          <button
            className="button primary"
            disabled={!project || !selected.length}
          >
            Bind selected profile locks
          </button>
        </div>
      </form>
      {project?.manifest?.profiles?.length > 0 && (
        <div>
          <h4>Current project locks</h4>
          <Json value={project?.manifest?.profiles} expanded />
        </div>
      )}
    </section>
  );
}
