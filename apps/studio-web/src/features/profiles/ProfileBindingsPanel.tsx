import { useEffect, useState, useRef, useId } from "react";
import { PresentationPreview } from "./presentation";
import type { ProfileBindings } from "../../../../../packages/contracts/api";
import type { Data, Project } from "../../api/types";
import { api, ApiError } from "../../api/client";
import type { DoAction } from "../../app/App";
import { Badge, Json, KeyValues } from "../../app/ui";

export type ProfileBindingCommit = (
  saved: Project,
  navigate: boolean,
  origin: Element | null,
) => boolean;
export type ProfileBindingRefusal = (origin: Element | null) => boolean;
type Discovery = {
  status: "loading" | "available" | "unavailable";
  profiles: Data[];
  error?: string;
};

function discoveredProfiles(response: Data): Data[] {
  const text = (value: unknown, bound: number) =>
      typeof value === "string" && value.length > 0 && value.length <= bound,
    digest = (value: unknown) =>
      typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
  if (
    !response ||
    !Array.isArray(response.items) ||
    response.items.length > 200 ||
    response.nextCursor != null ||
    response.items.some(
      (profile: Data) =>
        !profile ||
        !text(profile.profileId, 512) ||
        !text(profile.namespace, 512) ||
        !text(profile.version, 128) ||
        !digest(profile.schemaDigest) ||
        !digest(profile.presentationDigest) ||
        !profile.presentation ||
        typeof profile.presentation !== "object" ||
        Array.isArray(profile.presentation) ||
        ["name", "description", "domain", "documentation"].some(
          (key) =>
            profile.presentation[key] !== undefined &&
            typeof profile.presentation[key] !== "string",
        ) ||
        (profile.maturity !== undefined &&
          typeof profile.maturity !== "string"),
    ) ||
    new Set(response.items.map((p: Data) => p.profileId)).size !==
      response.items.length ||
    new Set(response.items.map((p: Data) => p.namespace)).size !==
      response.items.length
  )
    throw new Error(
      "The admitted profile response is incomplete or malformed.",
    );
  return response.items;
}

export function ProfileBindingsPanel({
  project,
  onCommitted,
  onRefused,
  onIntent,
  doAction,
}: {
  project: Project | null;
  onCommitted: ProfileBindingCommit;
  onRefused: ProfileBindingRefusal;
  onIntent: () => void;
  doAction: DoAction;
}) {
  const [discovery, setDiscovery] = useState<Discovery>({
      status: "loading",
      profiles: [],
    }),
    [selected, setSelected] = useState<string[]>([]),
    [attempt, setAttempt] = useState(0),
    [pending, setPending] = useState(false),
    [receipt, setReceipt] = useState("");
  const mounted = useRef(true),
    currentProject = useRef(project),
    sending = useRef(false),
    discovering = useRef(true),
    selectionGeneration = useRef(0),
    retryOrigin = useRef<Element | null>(null),
    firstChoice = useRef<HTMLInputElement>(null),
    retryControl = useRef<HTMLButtonElement>(null),
    emptyNotice = useRef<HTMLParagraphElement>(null),
    guidanceId = useId(),
    errorId = useId();
  currentProject.current = project;
  const profiles = discovery.profiles,
    choices = profiles.filter((profile) =>
      selected.includes(profile.profileId),
    ),
    canBind =
      !!project &&
      discovery.status === "available" &&
      choices.length > 0 &&
      choices.length <= 16;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    discovering.current = true;
    setDiscovery({ status: "loading", profiles: [] });
    void api("/profiles", { signal: controller.signal })
      .then((response) => {
        const profiles = discoveredProfiles(response);
        if (!controller.signal.aborted)
          setDiscovery({ status: "available", profiles });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setDiscovery({
            status: "unavailable",
            profiles: [],
            error:
              `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "Profile discovery failed."}`.slice(
                0,
                1000,
              ),
          });
      })
      .finally(() => {
        if (!controller.signal.aborted) discovering.current = false;
      });
    return () => controller.abort();
  }, [attempt]);
  useEffect(() => {
    if (discovery.status === "loading" || !retryOrigin.current) return;
    const origin = retryOrigin.current;
    retryOrigin.current = null;
    if (
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== origin)
    )
      return;
    (discovery.status === "unavailable"
      ? retryControl.current
      : profiles.length
        ? firstChoice.current
        : emptyNotice.current
    )?.focus();
  }, [discovery, profiles.length]);

  async function bindProfiles() {
    if (sending.current || !project || !canBind) return;
    onIntent();
    const submitted = project,
      generation = selectionGeneration.current,
      origin = document.activeElement,
      locks = choices.map((profile) => ({
        profileId: profile.profileId,
        version: profile.version,
        schemaDigest: profile.schemaDigest,
        presentationDigest: profile.presentationDigest,
      })),
      current = () =>
        mounted.current &&
        currentProject.current?.projectId === submitted.projectId;
    sending.current = true;
    setPending(true);
    setReceipt("");
    try {
      await doAction("Binding immutable profile identities", async () => {
        try {
          const saved = await api<Project>(
            `/projects/${encodeURIComponent(submitted.projectId)}/profile-bindings`,
            {
              method: "POST",
              revision: submitted.revision,
              body: {
                baseRevision: submitted.revision,
                profiles: locks,
              } satisfies ProfileBindings,
            },
          );
          if (!current()) return;
          const navigate =
            generation === selectionGeneration.current &&
            (document.activeElement === origin ||
              document.activeElement === document.body) &&
            !document.querySelector('[role="dialog"]');
          if (onCommitted(saved, navigate, origin) && !navigate)
            setReceipt(
              `Saved the submitted profile locks as revision ${saved.revision}. Current project locks are listed below.`,
            );
          return saved;
        } catch (error) {
          if (
            current() &&
            currentProject.current?.revision === submitted.revision &&
            generation === selectionGeneration.current &&
            onRefused(origin)
          )
            throw error;
        }
      });
    } finally {
      sending.current = false;
      if (mounted.current) setPending(false);
    }
  }
  return (
    <section
      className="panel profile-binding-panel"
      aria-busy={pending || discovery.status === "loading"}
      onPointerDownCapture={onIntent}
      onKeyDownCapture={onIntent}
      onInputCapture={onIntent}
    >
      <h2>Admitted profile locks</h2>
      <p>
        Profiles supply versioned semantics and inert presentation metadata.
        Provider installation and execution authority are separate.
      </p>
      <p id={guidanceId} className="field-hint">
        Select one to 16 admitted profiles. Binding adds these exact locks and
        keeps existing locks. Unchecking a box only changes your next
        submission; it does not remove a project lock. Changes made while a
        request is pending are not included in that request.
      </p>
      {discovery.status === "loading" && (
        <p role="status">Checking admitted profiles…</p>
      )}
      {discovery.status === "unavailable" && (
        <p id={errorId} role="alert" className="notice error">
          Could not check admitted profiles. Availability is unknown.{" "}
          {discovery.error} Retry profile discovery.
        </p>
      )}
      {(discovery.status === "unavailable" ||
        (discovery.status === "loading" && attempt > 0)) && (
        <button
          ref={retryControl}
          className="button"
          type="button"
          disabled={discovery.status === "loading" || pending}
          onClick={(event) => {
            if (discovering.current || sending.current) return;
            discovering.current = true;
            retryOrigin.current = event.currentTarget;
            setDiscovery({ status: "loading", profiles: [] });
            setAttempt((value) => value + 1);
          }}
        >
          Retry profile discovery
        </button>
      )}
      {discovery.status === "available" && !profiles.length && (
        <p ref={emptyNotice} tabIndex={-1} role="status">
          No admitted profiles were returned by this discovery request.
        </p>
      )}
      {pending && (
        <p role="status">
          Binding the submitted profile locks. This request is still pending.
        </p>
      )}
      {receipt && <p role="status">{receipt}</p>}
      <form
        aria-label="Bind admitted profile locks"
        aria-describedby={`${guidanceId}${discovery.status === "unavailable" ? " " + errorId : ""}`}
        onSubmit={(event) => {
          event.preventDefault();
          void bindProfiles();
        }}
      >
        <div className="catalog-grid">
          {profiles.map((profile, index) => (
            <article className="profile-choice" key={profile.profileId}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  ref={index === 0 ? firstChoice : undefined}
                  aria-describedby={guidanceId}
                  checked={selected.includes(profile.profileId)}
                  onChange={(event) => {
                    onIntent();
                    selectionGeneration.current++;
                    setReceipt("");
                    setSelected((ids) =>
                      event.target.checked
                        ? [...ids, profile.profileId]
                        : ids.filter((id) => id !== profile.profileId),
                    );
                  }}
                />
                <span>
                  Select profile{" "}
                  {profile.presentation?.name || profile.profileId}
                </span>
              </label>
              <Badge>{profile.maturity}</Badge>
              <p>{profile.presentation?.description}</p>
              <PresentationPreview presentation={profile.presentation} />
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
            aria-describedby={guidanceId}
            disabled={!canBind || pending}
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
