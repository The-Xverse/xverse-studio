import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, ApiError, mutationKey } from "../../api/client";
import type { Data, Preflight, Project } from "../../api/types";
import type { Campaign } from "../../../../../packages/contracts/api";
import { Badge, KeyValues, statusTone } from "../../app/ui";
import { campaignPage, campaignReport, canonical } from "./campaign-report";
import "./campaigns.css";

type Slot = { abort: AbortController; sequence: number; tag: string };
export function CampaignWorkspace({
  project,
  preflight,
  limits,
  enabled,
}: {
  project: Project;
  preflight: Preflight | null;
  limits: Data;
  enabled: boolean;
}) {
  const [matrix, setMatrix] = useState('{"gain": [0.5, 0.8, 1.2]}'),
    [budget, setBudget] = useState("8"),
    [seconds, setSeconds] = useState("240"),
    [concurrency, setConcurrency] = useState("1"),
    [policy, setPolicy] = useState<Campaign["stopPolicy"]>("continue"),
    [preview, setPreview] = useState<{ signature: string; value: Data } | null>(
      null,
    ),
    [history, setHistory] = useState<Data | null>(null),
    [cursors, setCursors] = useState<(string | null)[]>([null]),
    [page, setPage] = useState(0),
    [selected, setSelected] = useState<Data | null>(null),
    [childInputs, setChildInputs] = useState<Data | null>(null),
    [errors, setErrors] = useState<Record<string, string>>({}),
    [busy, setBusy] = useState<Record<string, boolean>>({}),
    [commandBusy, setCommandBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [completion, setCompletion] = useState<{
      origin: Element;
      intent: number;
      context: string;
      target: string;
    } | null>(null);
  const context = canonical([
      project.projectId,
      project.revision,
      preflight?.snapshotId,
    ]),
    current = useRef(context),
    alive = useRef(false),
    intent = useRef(0),
    reads = useRef(new Map<string, Slot>()),
    sequence = useRef(0),
    mutationPending = useRef(false),
    mutationAbort = useRef<AbortController | null>(null),
    submission = useRef<{ signature: string; key: string } | null>(null),
    cancellation = useRef<{ id: string; key: string } | null>(null),
    selectedId = useRef(""),
    previewHeading = useRef<HTMLHeadingElement>(null),
    historyHeading = useRef<HTMLHeadingElement>(null),
    selectedHeading = useRef<HTMLHeadingElement>(null),
    errorHeading = useRef<HTMLParagraphElement>(null);
  current.current = context;
  useLayoutEffect(() => {
    alive.current = true;
    setBusy({});
    return () => {
      alive.current = false;
      intent.current++;
      for (const slot of reads.current.values()) slot.abort.abort();
      reads.current.clear();
    };
  }, [context]);
  useEffect(() => () => mutationAbort.current?.abort(), []);
  useEffect(() => {
    if (!completion) return;
    setCompletion(null);
    if (
      !alive.current ||
      completion.context !== current.current ||
      completion.intent !== intent.current ||
      document.querySelector('[role="dialog"]') ||
      (document.activeElement !== document.body &&
        document.activeElement !== completion.origin)
    )
      return;
    (completion.target === "preview"
      ? previewHeading
      : completion.target === "history"
        ? historyHeading
        : completion.target === "selected"
          ? selectedHeading
          : errorHeading
    ).current?.focus();
  }, [completion]);
  function changed() {
    intent.current++;
    setPreview(null);
    setCompletion(null);
    reads.current.get("preview")?.abort.abort();
    reads.current.delete("preview");
    setBusy((b) => ({ ...b, preview: false }));
    setErrors((e) => ({ ...e, preview: "" }));
  }
  function message(error: unknown) {
    return `${error instanceof ApiError ? error.code + ": " : ""}${error instanceof Error ? error.message : "The request could not be confirmed."}`.slice(
      0,
      1000,
    );
  }
  async function read(
    channel: string,
    tag: string,
    operation: (signal: AbortSignal) => Promise<Data>,
    accept: (value: Data) => void,
    origin?: Element,
  ) {
    const previous = reads.current.get(channel);
    if (previous?.tag === tag) return;
    previous?.abort.abort();
    const slot = {
        abort: new AbortController(),
        sequence: ++sequence.current,
        tag,
      },
      submitted = current.current,
      submittedIntent = intent.current;
    reads.current.set(channel, slot);
    setBusy((b) => ({ ...b, [channel]: true }));
    setErrors((e) => ({ ...e, [channel]: "" }));
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      slot.abort.abort();
    }, 30000);
    const active = () =>
      alive.current &&
      current.current === submitted &&
      reads.current.get(channel) === slot;
    try {
      const value = await operation(slot.abort.signal);
      if (active() && !slot.abort.signal.aborted) {
        accept(value);
        if (origin && submittedIntent === intent.current)
          setCompletion({
            origin,
            intent: submittedIntent,
            context: submitted,
            target: channel,
          });
      }
    } catch (error) {
      if (active() && (!slot.abort.signal.aborted || timedOut)) {
        setErrors((e) => ({
          ...e,
          [channel]: timedOut
            ? "The campaign read timed out. Refresh to retry."
            : message(error),
        }));
        if (origin && submittedIntent === intent.current)
          setCompletion({
            origin,
            intent: submittedIntent,
            context: submitted,
            target: "error",
          });
      }
    } finally {
      clearTimeout(timer);
      if (reads.current.get(channel) === slot) {
        reads.current.delete(channel);
        if (alive.current) setBusy((b) => ({ ...b, [channel]: false }));
      }
    }
  }
  function historyRead(cursor: string | null, index: number, origin?: Element) {
    return read(
      "history",
      cursor || "first",
      async (signal) =>
        campaignPage(
          await api(
            `/campaigns?limit=20${cursor ? "&cursor=" + encodeURIComponent(cursor) : ""}`,
            { signal },
          ),
        ),
      (value) => {
        setHistory(value);
        setPage(index);
        setCursors((old) =>
          cursor ? [...old.slice(0, index), cursor] : [null],
        );
      },
      origin,
    );
  }
  function detail(id: string, origin?: Element) {
    return read(
      "selected",
      id,
      async (signal) =>
        campaignReport(
          await api(`/campaigns/${encodeURIComponent(id)}`, { signal }),
          id,
        ),
      (value) => {
        if (selectedId.current === id) setSelected(value);
      },
      origin,
    );
  }
  function inspect(id: string, origin: Element) {
    intent.current++;
    selectedId.current = id;
    setSelected(null);
    setChildInputs(null);
    reads.current.get("child")?.abort.abort();
    void detail(id, origin);
  }
  useEffect(() => {
    if (
      !selected ||
      !["pending", "running", "cancelling"].includes(selected.status)
    )
      return;
    // Read-only serial polling; scheduling and recovery continue on the backend.
    const timer = setTimeout(() => void detail(selected.campaignId), 2000);
    return () => clearTimeout(timer);
  }, [selected, context, busy.selected, errors.selected]);
  let body: Campaign | null = null,
    inputError = "";
  const maxRuns =
      Number.isSafeInteger(limits.campaignRuns) && limits.campaignRuns > 0
        ? Math.min(32, limits.campaignRuns)
        : 0,
    maxConcurrency =
      Number.isSafeInteger(limits.campaignConcurrency) &&
      limits.campaignConcurrency > 0
        ? Math.min(1, limits.campaignConcurrency)
        : 0,
    ready =
      enabled &&
      maxRuns > 0 &&
      maxConcurrency > 0 &&
      preflight?.status === "ready" &&
      preflight.revision === project.revision;
  try {
    if (matrix.length > 32768)
      throw new Error("Keep the matrix within 32,768 characters.");
    const parsed = JSON.parse(matrix);
    if (
      !parsed ||
      typeof parsed !== "object" ||
      Array.isArray(parsed) ||
      !Object.keys(parsed).length
    )
      throw new Error("Enter a parameter object with finite value arrays.");
    if (
      !Number.isSafeInteger(Number(budget)) ||
      Number(budget) < 1 ||
      Number(budget) > maxRuns ||
      !Number.isFinite(Number(seconds)) ||
      Number(seconds) <= 0 ||
      !Number.isSafeInteger(Number(concurrency)) ||
      Number(concurrency) < 1 ||
      Number(concurrency) > maxConcurrency
    )
      throw new Error(
        "Choose positive budgets and concurrency within the advertised limits.",
      );
    if (preflight)
      body = {
        snapshotId: preflight.snapshotId,
        matrix: parsed,
        budget: { maxRuns: Number(budget), maxTotalSeconds: Number(seconds) },
        concurrency: Number(concurrency),
        stopPolicy: policy,
      };
  } catch (error) {
    inputError = message(error);
  }
  const signature = canonical([context, body]),
    shownPreview = preview?.signature === signature ? preview.value : null;
  async function previewRead(origin: Element) {
    if (!ready || !body) return;
    const submitted = body;
    await read(
      "preview",
      signature,
      async (signal) =>
        campaignReport(
          await api("/campaigns/preview", {
            method: "POST",
            body: submitted,
            signal,
          }),
          undefined,
          submitted,
        ),
      (value) => {
        if (
          value.baseInput.projectId !== project.projectId ||
          value.baseInput.revision !== project.revision
        )
          throw new Error(
            "The preview belongs to another frozen project revision.",
          );
        setPreview({ signature, value });
      },
      origin,
    );
  }
  async function command(kind: "create" | "cancel", origin: Element) {
    if (
      mutationPending.current ||
      (kind === "create" && (!ready || !body || !shownPreview)) ||
      (kind === "cancel" &&
        (!selected ||
          selected.baseInput.status !== "verified" ||
          selected.baseInput.projectId !== project.projectId))
    )
      return;
    const submitted = current.current,
      submittedIntent = intent.current,
      id = selected?.campaignId;
    let key: string;
    if (kind === "create") {
      if (submission.current?.signature !== signature)
        submission.current = { signature, key: mutationKey() };
      key = submission.current!.key;
    } else {
      if (cancellation.current?.id !== id)
        cancellation.current = { id, key: mutationKey() };
      key = cancellation.current!.key;
    }
    mutationPending.current = true;
    setCommandBusy(true);
    setNotice("");
    setErrors((e) => ({ ...e, command: "" }));
    const abort = new AbortController();
    mutationAbort.current = abort;
    const timer = setTimeout(() => abort.abort(), 30000);
    try {
      const value = await api(
        kind === "create"
          ? "/campaigns"
          : `/campaigns/${encodeURIComponent(id)}/cancel`,
        {
          method: "POST",
          key,
          body: kind === "create" ? body : {},
          signal: abort.signal,
        },
      );
      if (!alive.current || current.current !== submitted) return;
      if (kind === "create") {
        if (
          typeof value.campaignId !== "string" ||
          !value.campaignId ||
          value.campaignId.length > 80
        )
          throw new Error(
            "Campaign acceptance could not be identified. Refresh history before submitting again.",
          );
        if (submittedIntent === intent.current) {
          selectedId.current = value.campaignId;
          setSelected(null);
          setChildInputs(null);
          await detail(value.campaignId, origin);
        }
        setNotice(
          "Campaign accepted. Each child still requires backend admission. Refresh history to reopen the retained record.",
        );
      } else {
        if (
          value.campaignId !== id ||
          !Array.isArray(value.activeCancellationOutcomes) ||
          value.activeCancellationOutcomes.length > 32
        )
          throw new Error(
            "Cancellation acknowledgement is unavailable. Refresh the campaign to observe its state.",
          );
        const outcomes = value.activeCancellationOutcomes;
        setNotice(
          `Scheduling cancellation acknowledged. Active children: ${outcomes.length ? outcomes.map((o: Data) => `${String(o.runId).slice(0, 80)}: ${String(o.status).slice(0, 64)}${o.reason ? " (" + String(o.reason).slice(0, 256) + ")" : ""}`).join("; ") : "none reported"}. This acknowledgement is not proof of terminal cleanup.`,
        );
        if (selectedId.current === id) await detail(id);
      }
    } catch (error) {
      if (
        alive.current &&
        current.current === submitted &&
        submittedIntent === intent.current
      ) {
        setErrors((e) => ({
          ...e,
          command: `${message(error)} Submission may have been accepted; refresh history/state or retry the unchanged request with the same idempotency key.`,
        }));
        setCompletion({
          origin,
          intent: submittedIntent,
          context: submitted,
          target: "error",
        });
      }
    } finally {
      clearTimeout(timer);
      mutationPending.current = false;
      if (alive.current) setCommandBusy(false);
    }
  }
  function inspectChild(c: Data, origin: Element) {
    intent.current++;
    setChildInputs(null);
    const campaign = selected!;
    void read(
      "child",
      c.runId,
      async (signal) => {
        const run = await api(`/runs/${encodeURIComponent(c.runId)}`, {
          signal,
        });
        if (run.runId !== c.runId || typeof run.snapshotId !== "string")
          throw new Error("The child run identity is unavailable.");
        const result = await api(
            `/runs/${encodeURIComponent(c.runId)}/snapshot`,
            { signal },
          ),
          s = result.snapshot;
        if (
          result.integrity !== "valid" ||
          !s ||
          s.snapshotId !== run.snapshotId ||
          s.projectId !== campaign.baseInput.projectId ||
          s.parentSnapshotId !== campaign.baseSnapshotId ||
          s.campaignId !== campaign.campaignId ||
          s.campaignChildKey !== c.childKey ||
          typeof s.snapshotDigest !== "string" ||
          !/^sha256:[a-f0-9]{64}$/.test(s.snapshotDigest) ||
          !Object.entries(c.parameters).every(
            ([k, v]) => s.configuration?.[k] === v,
          )
        )
          throw new Error(
            "The immutable child input identities do not match this campaign.",
          );
        return {
          "Child run": run.runId,
          "Child key": c.childKey,
          "Child snapshot": s.snapshotId,
          "Snapshot digest": s.snapshotDigest,
          "Parent snapshot": s.parentSnapshotId,
          Project: s.projectId,
          "Frozen revision": s.revision,
          "Plan digest": s.planDigest,
          "Semantic digest": s.semanticDigest,
          Provider: s.providerId,
          Parameters: c.parameters,
        };
      },
      (value) => {
        if (selectedId.current === campaign.campaignId) setChildInputs(value);
      },
      origin,
    );
  }
  return (
    <div className="campaign-workspace">
      <section className="panel" aria-label="Campaign planning">
        <h3>Bounded parameter campaign</h3>
        <p>
          Preview exact frozen inputs before scheduling. The backend owns child
          admission, budgets, execution and restart reconciliation.
        </p>
        <p className="field-hint">
          Only admitted numeric parameter axes are supported. Seeds and physical
          repetition require a separately admitted provider contract; a campaign
          does not promise deterministic replay.
        </p>
        {!ready && (
          <p role="status">
            A ready preflight from this project revision and advertised campaign
            capability are required. Use Preflight &amp; run, then return to the
            draft without starting a run.
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void command(
              "create",
              e.currentTarget.querySelector('button[type="submit"]')!,
            );
          }}
        >
          <label>
            Parameter matrix (JSON)
            <textarea
              maxLength={32768}
              rows={5}
              spellCheck={false}
              value={matrix}
              onChange={(e) => {
                changed();
                setMatrix(e.target.value);
              }}
            />
          </label>
          <div className="two-fields">
            <label>
              Maximum runs
              <input
                type="number"
                min={1}
                max={maxRuns || undefined}
                value={budget}
                onChange={(e) => {
                  changed();
                  setBudget(e.target.value);
                }}
              />
            </label>
            <label>
              Maximum total simulated seconds
              <input
                type="number"
                min="0.001"
                step="any"
                value={seconds}
                onChange={(e) => {
                  changed();
                  setSeconds(e.target.value);
                }}
              />
            </label>
            <label>
              Concurrency
              <input
                type="number"
                min={1}
                max={maxConcurrency || undefined}
                value={concurrency}
                onChange={(e) => {
                  changed();
                  setConcurrency(e.target.value);
                }}
              />
            </label>
            <label>
              Stop policy
              <select
                value={policy}
                onChange={(e) => {
                  changed();
                  setPolicy(e.target.value as Campaign["stopPolicy"]);
                }}
              >
                <option value="continue">Continue after a failed child</option>
                <option value="stop_on_failure">
                  Stop pending children after a failure
                </option>
              </select>
            </label>
          </div>
          <p className="field-hint">
            Advertised limit: {maxRuns || "unavailable"} runs; concurrency{" "}
            {maxConcurrency || "unavailable"}. Each child receives an immutable
            snapshot.
          </p>
          {inputError && <p role="status">{inputError}</p>}
          <div className="form-actions">
            <button
              type="button"
              className="button"
              disabled={!ready || !body || busy.preview || commandBusy}
              onClick={(e) => {
                intent.current++;
                void previewRead(e.currentTarget);
              }}
            >
              Preview campaign
            </button>
            <button
              type="submit"
              className="button primary"
              disabled={!ready || !body || !shownPreview || commandBusy}
            >
              Create campaign
            </button>
            {submission.current && (
              <button
                type="button"
                className="button"
                disabled={commandBusy}
                onClick={() => {
                  changed();
                  submission.current = null;
                  setNotice(
                    "A new campaign request needs a fresh preview. Retained campaigns remain unchanged.",
                  );
                }}
              >
                New campaign request
              </button>
            )}
          </div>
        </form>
        {busy.preview && (
          <p role="status">Reading authoritative campaign preview…</p>
        )}
        {shownPreview && (
          <div className="campaign-preview-report">
            <h4 tabIndex={-1} ref={previewHeading}>
              Authoritative campaign preview
            </h4>
            <KeyValues
              values={{
                "Child runs": shownPreview.cardinality,
                "Base snapshot": shownPreview.baseSnapshotId,
                "Snapshot digest": shownPreview.baseInput.snapshotDigest,
                Project: shownPreview.baseInput.projectId,
                "Frozen revision": shownPreview.baseInput.revision,
                "Estimated total simulated seconds":
                  shownPreview.estimatedTotalSeconds,
                "Maximum total simulated seconds":
                  shownPreview.budget.maxTotalSeconds,
                "Stop policy": shownPreview.stopPolicy,
              }}
            />
            <p>
              This preview creates no campaign or child run. Creation rechecks
              admission.
            </p>
          </div>
        )}
      </section>
      <section
        className="panel"
        aria-label="Retained campaign history"
        aria-busy={!!busy.history}
      >
        <div className="section-heading">
          <h3 ref={historyHeading} tabIndex={-1}>
            Campaign history
          </h3>
          <button
            className="button"
            disabled={busy.history}
            onClick={(e) => {
              intent.current++;
              void historyRead(null, 0, e.currentTarget);
            }}
          >
            Refresh campaign history
          </button>
        </div>
        <p>
          Workspace history, 20 records per page. Frozen project identities
          distinguish other projects. Refresh starts a new list observation;
          pages may change as history changes.
        </p>
        {!history ? (
          <p role="status">
            {busy.history
              ? "Reading retained campaigns…"
              : "History has not been read."}
          </p>
        ) : history.items.length === 0 ? (
          <p role="status">No campaigns were returned on this page.</p>
        ) : (
          <ul className="campaign-history-list">
            {history.items.map((c: Data) => (
              <li key={c.campaignId}>
                <button
                  className="button"
                  aria-label={`Inspect campaign ${c.campaignId}`}
                  onClick={(e) => inspect(c.campaignId, e.currentTarget)}
                >
                  {c.campaignId}
                </button>
                <span>
                  {c.status} ·{" "}
                  {c.baseInput.status === "verified"
                    ? `${c.baseInput.projectId} · revision ${c.baseInput.revision}`
                    : "Frozen project unavailable"}
                </span>
              </li>
            ))}
          </ul>
        )}
        {history && (
          <div className="form-actions">
            <button
              className="button"
              disabled={busy.history || page === 0}
              onClick={(e) => {
                intent.current++;
                void historyRead(cursors[page - 1], page - 1, e.currentTarget);
              }}
            >
              Previous campaign page
            </button>
            <button
              className="button"
              disabled={busy.history || !history.nextCursor}
              onClick={(e) => {
                intent.current++;
                void historyRead(history.nextCursor, page + 1, e.currentTarget);
              }}
            >
              Next campaign page
            </button>
          </div>
        )}
      </section>
      <section
        className="panel"
        aria-label="Selected campaign"
        aria-busy={!!busy.selected}
      >
        <div className="section-heading">
          <h3 ref={selectedHeading} tabIndex={-1}>
            Selected campaign
          </h3>
          <button
            className="button"
            disabled={!selectedId.current || busy.selected}
            onClick={(e) => {
              intent.current++;
              void detail(selectedId.current, e.currentTarget);
            }}
          >
            Refresh selected campaign
          </button>
        </div>
        {!selected ? (
          <p role="status">
            {busy.selected
              ? "Reading campaign…"
              : "Open a retained campaign or create one after preview."}
          </p>
        ) : (
          <>
            <div className="section-heading">
              <code>{selected.campaignId}</code>
              <Badge tone={statusTone(selected.status)}>
                {selected.status}
              </Badge>
            </div>
            <p>
              Scheduling status is not an assertion verdict. Automatic refresh
              only reads; closing the browser does not stop backend scheduling.
            </p>
            <KeyValues
              values={{
                "Base snapshot": selected.baseSnapshotId,
                "Campaign base identity": selected.baseSnapshotDigest,
                Project: selected.baseInput.projectId || "Unavailable",
                "Frozen revision": selected.baseInput.revision || "Unknown",
                "Snapshot digest":
                  selected.baseInput.snapshotDigest || "Unverified",
                Provider: selected.baseInput.providerId || "Unknown",
                "Frozen System":
                  selected.baseInput.selection?.systemRef || "Unknown",
                "Frozen Deployment":
                  selected.baseInput.selection?.deploymentRef || "Unknown",
                "Frozen Scenario":
                  selected.baseInput.selection?.scenarioRef || "Unknown",
                "Stop policy": selected.stopPolicy,
                Budget: selected.budget,
                Concurrency: selected.concurrency,
                "Observed campaign revision": selected.revision,
              }}
            />
            {selected.baseInput.status !== "verified" ? (
              <p role="status">
                Frozen input provenance is unavailable (
                {selected.baseInput.reason}). Child states remain observations;
                no new scheduling or cancellation is authorized by this display.
              </p>
            ) : (
              (selected.baseInput.projectId !== project.projectId ||
                selected.baseInput.revision !== project.revision) && (
                <p role="status">
                  This campaign uses a different frozen project or revision. The
                  current draft does not replace its inputs.
                </p>
              )
            )}
            <div className="table-scroll">
              <table>
                <caption>Immutable campaign children</caption>
                <thead>
                  <tr>
                    <th>Child / key</th>
                    <th>Parameters</th>
                    <th>Observed state</th>
                    <th>Run / inputs</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.children.map((c: Data) => (
                    <tr key={c.childKey}>
                      <td>
                        {c.index + 1}
                        <br />
                        <code>{c.childKey}</code>
                      </td>
                      <td>
                        <code>{JSON.stringify(c.parameters)}</code>
                      </td>
                      <td>
                        {c.state}
                        {c.reason && <p>{c.reason}</p>}
                      </td>
                      <td>
                        {c.runId ? (
                          <>
                            <code>{c.runId}</code>
                            <button
                              className="small-button"
                              disabled={
                                busy.child ||
                                selected.baseInput.status !== "verified"
                              }
                              aria-label={`Inspect child inputs ${c.runId}`}
                              onClick={(e) => inspectChild(c, e.currentTarget)}
                            >
                              Inspect child inputs
                            </button>
                          </>
                        ) : (
                          "No run identity observed"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {selected.children.some((c: Data) => c.state === "unknown") && (
              <p role="status">
                A child dispatch is unknown. Only backend reconciliation can
                resolve it; refresh never retries or restarts a child.
              </p>
            )}
            <button
              className="button"
              disabled={
                commandBusy ||
                ["complete", "cancelled"].includes(selected.status) ||
                selected.baseInput.status !== "verified" ||
                selected.baseInput.projectId !== project.projectId
              }
              onClick={(e) => {
                intent.current++;
                void command("cancel", e.currentTarget);
              }}
            >
              Stop scheduling
            </button>
            <p className="field-hint">
              Stops pending scheduling and separately requests admitted
              cancellation of active children. Acceptance does not attest
              observed termination or cleanup.
            </p>
          </>
        )}
        {busy.child && <p role="status">Reading immutable child inputs…</p>}
        {childInputs && (
          <div>
            <h4>Verified child inputs</h4>
            <KeyValues values={childInputs} />
          </div>
        )}
      </section>
      {commandBusy && (
        <p role="status">
          Waiting for campaign acknowledgement. Repeated submission is disabled;
          editing the next draft does not change this request.
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {Object.values(errors).some(Boolean) && (
        <p role="alert" tabIndex={-1} ref={errorHeading}>
          {Object.values(errors).filter(Boolean).join(" ")} Previous displayed
          observations have not been refreshed.
        </p>
      )}
    </div>
  );
}
