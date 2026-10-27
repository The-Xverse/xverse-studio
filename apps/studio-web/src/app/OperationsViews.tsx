import { ScenarioAuthoring } from "../features/experiments/ScenarioAuthoring";
import type { SourceTarget } from "../features/model/Views";
import { useEffect, useState, useRef } from "react";
import type { Campaign, Evaluation } from "../../../../packages/contracts/api";
import { api, items, mutationKey } from "../api/client";
import type { Project, Data, Run, Preflight } from "../api/types";
import type { Projection } from "../features/model/projection";
import { textRef } from "../features/model/projection";
import type { DoAction } from "./App";
import {
  Icon,
  Badge,
  Empty,
  Json,
  KeyValues,
  statusTone,
  Diagnostics,
} from "./ui";
export function ExperimentsView({
  project,
  projection,
  selection,
  preflight,
  run,
  doAction,
  refresh,
  onSource,
  edit,
  authoringLimits,
}: {
  project: Project;
  projection: Projection;
  selection: { deploymentRef?: string; scenarioRef?: string };
  preflight: Preflight | null;
  run: Run | null;
  doAction: DoAction;
  refresh: () => Promise<unknown>;
  onSource: (target?: SourceTarget) => void;
  edit: (edits: Data[]) => Promise<unknown>;
  authoringLimits: Data;
}) {
  const [tab, setTab] = useState("Scenario"),
    [matrix, setMatrix] = useState('{"gain": [0.5, 0.8, 1.2]}'),
    [concurrency, setConcurrency] = useState(1),
    [budget, setBudget] = useState(8),
    [campaign, setCampaign] = useState<Data | null>(null),
    [evaluations, setEvaluations] = useState<Data[]>([]),
    [definition, setDefinition] = useState(""),
    [definitions, setDefinitions] = useState<Data[]>([]);
  const campaignKey = useRef(mutationKey());
  useEffect(() => {
    campaignKey.current = mutationKey();
  }, [matrix, budget, concurrency]);
  const scenario = selection.scenarioRef
      ? projection.scenarios.find(
          (resource) =>
            `xdl://${resource.metadata.namespace}/scenario/${resource.metadata.name}` ===
            selection.scenarioRef,
        )
      : projection.scenarios.length === 1
        ? projection.scenarios[0]
        : undefined,
    spec = scenario?.spec || {};
  useEffect(() => {
    if (run?.runId) {
      void api(`/runs/${run.runId}/evaluations`)
        .then((r) => setEvaluations(items(r)))
        .catch(() => {});
      void api(`/runs/${run.runId}/definitions`)
        .then((r) => setDefinitions(items(r)))
        .catch(() => {});
    }
  }, [run?.runId]);
  useEffect(() => {
    if (
      !campaign ||
      !["running", "pending", "cancelling"].includes(campaign.status)
    )
      return;
    const timer = setInterval(
      () =>
        void api(`/campaigns/${campaign.campaignId}`)
          .then(setCampaign)
          .catch(() => {}),
      2000,
    );
    return () => clearInterval(timer);
  }, [campaign?.campaignId, campaign?.status]);
  let cardinality: number | null = null;
  try {
    const values = Object.values(JSON.parse(matrix));
    cardinality = values.length
      ? values.reduce<number>(
          (n, v) => n * (Array.isArray(v) ? v.length : 0),
          1,
        )
      : 0;
  } catch {
    /* Server returns authoritative schema diagnostics. */
  }
  return (
    <div className="view-page">
      <div className="section-heading">
        <div>
          <h2>Experiments</h2>
          <p>
            Author bounded intent, inspect actual events, and assess immutable
            evidence.
          </p>
        </div>
        <button
          className="button"
          onClick={() =>
            onSource(
              scenario
                ? {
                    documentId: scenario.documentId,
                    ref: `xdl://${scenario.metadata.namespace}/scenario/${scenario.metadata.name}`,
                  }
                : undefined,
            )
          }
        >
          <Icon name="code" />
          Edit scenario XDL
        </button>
      </div>
      <div className="sub-tabs" role="tablist" aria-label="Experiment sections">
        {["Scenario", "Assertions", "Campaigns"].map((t) => (
          <button
            role="tab"
            aria-selected={tab === t}
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === "Scenario" ? (
        scenario ? (
          <>
            <ScenarioAuthoring
              scenario={scenario}
              projection={projection}
              limits={authoringLimits}
              edit={edit}
              onSource={onSource}
            />
            <div className="deployment-summary">
              <section className="panel">
                <span className="eyebrow">SCENARIO INTENT</span>
                <h3>{scenario.metadata?.name}</h3>
                <p>{scenario.metadata?.description}</p>
                <KeyValues
                  values={{
                    System: textRef(spec.systemRef),
                    Deployment: textRef(spec.deploymentRef),
                    "Clock domain":
                      spec.steps?.[0]?.timeDomainId || "Not declared",
                    "Initial conditions":
                      spec.initialConditions || "Not declared",
                  }}
                />
                <p className="field-hint">{spec.acceptanceIntent}</p>
              </section>
              <section className="panel">
                <h3>Scheduled actions</h3>
                <div className="schedule-list">
                  {(spec.steps || []).map((s: Data, i: number) => (
                    <div className="schedule-item" key={s.id}>
                      <span className="schedule-tick">
                        {s.schedule?.at ?? "?"}{" "}
                        <small>{s.schedule?.unit || "ticks"}</small>
                      </span>
                      <div>
                        <strong>{s.id}</strong>
                        <p>
                          {s.actionKind} · {textRef(s.targetRef)}
                        </p>
                        <Badge>Intent</Badge>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="field-hint">
                  Requested activation is not proof of an observed effect. Only
                  provider-admitted targets and fault actions may execute.
                </p>
              </section>
            </div>
            <section className="panel">
              <h3>Observers</h3>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Observer</th>
                      <th>Target</th>
                      <th>Sampling intent</th>
                      <th>Clock / units</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(spec.observers || []).map((o: Data) => (
                      <tr key={o.id}>
                        <td>
                          <strong>{o.id}</strong>
                        </td>
                        <td>{textRef(o.targetRef)}</td>
                        <td>{o.samplingIntent}</td>
                        <td>
                          {o.timeDomainId}
                          <small>{o.unitSemantics || "Unit unspecified"}</small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="panel">
              <h3>Metrics and assessment intent</h3>
              {(spec.metrics || []).map((m: Data) => (
                <div key={m.id} className="metric-intent">
                  <strong>{m.id}</strong>
                  <Badge>Not evaluated</Badge>
                  <p>{m.acceptance}</p>
                  <small>{m.calculationRef}</small>
                </div>
              ))}
              <Json value={scenario} />
            </section>
          </>
        ) : (
          <Empty title="No Scenario resource" icon="experiment">
            Use XDL source to add an admitted scenario with explicit time and
            provider semantics.
          </Empty>
        )
      ) : tab === "Assertions" ? (
        <div className="connection-layout">
          <section className="panel">
            <h3>Evaluation results</h3>
            {evaluations.length ? (
              evaluations.map((e) => (
                <article className="evaluation-card" key={e.evaluationId}>
                  <h4>{e.definitionRef || e.evaluationId}</h4>
                  <Badge tone={statusTone(e.verdict || e.status)}>
                    {e.verdict || "Not evaluated"}
                  </Badge>
                  <KeyValues
                    values={{
                      "Execution status": e.status || e.executionStatus,
                      Coverage: e.coverage,
                      Evaluator: e.evaluatorVersion || e.evaluatorId,
                    }}
                  />
                  <Json value={e} />
                </article>
              ))
            ) : (
              <Empty title="No assertions evaluated" icon="check">
                A completed run does not create a passing assertion. Definitions
                must belong to an admitted, frozen XDL profile.
              </Empty>
            )}
          </section>
          <aside className="panel">
            <h3>Evaluate a frozen definition</h3>
            <p className="field-hint">
              Select a definition that already exists in the run snapshot.
              Opaque imported expressions remain unevaluated.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void doAction("Evaluating assertion", async () => {
                  if (!run) throw new Error("Select a run in Results first.");
                  const result = await api(`/runs/${run.runId}/evaluations`, {
                    method: "POST",
                    key: mutationKey(),
                    body: {
                      snapshotId: run.snapshotId,
                      definitionRef: definition,
                      definitionDigest:
                        definitions.find((d) => d.definitionRef === definition)
                          ?.definitionDigest || "",
                      evidenceRefs: [run.runId + ":reference-journal"],
                    } satisfies Evaluation,
                  });
                  setEvaluations(
                    items(await api(`/runs/${run.runId}/evaluations`)),
                  );
                  return result;
                });
              }}
            >
              <label>
                Snapshot definition reference
                <select
                  value={definition}
                  onChange={(e) => setDefinition(e.target.value)}
                  required
                >
                  <option value="">
                    {definitions.length
                      ? "Select a frozen definition"
                      : "No admitted definitions in this snapshot"}
                  </option>
                  {definitions.map((d) => (
                    <option key={d.definitionRef} value={d.definitionRef}>
                      {d.definition?.name || d.definitionRef}
                    </option>
                  ))}
                </select>
              </label>
              <button className="button primary" disabled={!run || !definition}>
                Evaluate assertion
              </button>
            </form>
            {!definitions.length && (
              <p className="field-hint">
                This snapshot has no compatible bounded-evaluator profile
                definitions. Existing expression strings remain preserved and
                not evaluated.
              </p>
            )}
            <hr />
            <h4>Verdict semantics</h4>
            <ul className="limits-list">
              <li>Pass: complete evidence establishes true.</li>
              <li>Fail: complete evidence establishes false.</li>
              <li>
                Indeterminate: missing, invalid, or incompatible evidence.
              </li>
              <li>Not evaluated: capability or definition unavailable.</li>
            </ul>
          </aside>
        </div>
      ) : (
        <div className="connection-layout">
          <section className="panel">
            <h3>Bounded parameter campaign</h3>
            <p>
              Each child receives its own immutable snapshot. Concurrency and
              resource budgets are rechecked by the backend.
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void doAction("Creating campaign", async () => {
                  if (!preflight || preflight.status !== "ready")
                    throw new Error(
                      "Run a ready preflight from the current draft before scheduling a campaign.",
                    );
                  const result = await api("/campaigns", {
                    method: "POST",
                    key: campaignKey.current,
                    body: {
                      snapshotId: preflight.snapshotId,
                      matrix: JSON.parse(matrix),
                      budget: { maxRuns: budget, maxTotalSeconds: budget * 30 },
                      concurrency,
                      stopPolicy: "continue",
                    } satisfies Campaign,
                  });
                  setCampaign(await api(`/campaigns/${result.campaignId}`));
                });
              }}
            >
              <label>
                Parameter matrix (JSON)
                <textarea
                  rows={5}
                  spellCheck={false}
                  value={matrix}
                  onChange={(e) => setMatrix(e.target.value)}
                />
              </label>
              <div className="two-fields">
                <label>
                  Maximum runs
                  <input
                    type="number"
                    min={1}
                    max={32}
                    value={budget}
                    onChange={(e) => setBudget(Number(e.target.value))}
                  />
                </label>
                <label>
                  Concurrency
                  <input
                    type="number"
                    min={1}
                    max={1}
                    value={concurrency}
                    onChange={(e) => setConcurrency(Number(e.target.value))}
                  />
                </label>
              </div>
              <div className="campaign-preview">
                <Icon name="catalog" />
                <span>
                  <strong>{cardinality ?? "Invalid JSON"}</strong> child runs in
                  this matrix
                </span>
                <Badge
                  tone={
                    cardinality !== null && cardinality <= budget
                      ? "info"
                      : "danger"
                  }
                >
                  Budget {budget}
                </Badge>
              </div>
              <button
                className="button primary"
                disabled={
                  cardinality === null ||
                  cardinality < 1 ||
                  cardinality > budget
                }
              >
                Create campaign
              </button>
            </form>
          </section>
          <section className="panel">
            <h3>Campaign history</h3>
            {campaign ? (
              <>
                <div className="section-heading">
                  <code>{campaign.campaignId}</code>
                  <Badge tone={statusTone(campaign.status)}>
                    {campaign.status}
                  </Badge>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>Child</th>
                      <th>Parameters</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(campaign.children || []).map((c: Data) => (
                      <tr key={c.childKey || c.index}>
                        <td>{c.index + 1}</td>
                        <td>
                          <code>{JSON.stringify(c.parameters)}</code>
                        </td>
                        <td>
                          <Badge tone={statusTone(c.state)}>{c.state}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button
                  className="button"
                  disabled={["complete", "cancelled"].includes(campaign.status)}
                  onClick={() =>
                    void doAction("Cancelling campaign", async () => {
                      await api(`/campaigns/${campaign.campaignId}/cancel`, {
                        method: "POST",
                        body: {},
                        key: mutationKey(),
                      });
                      setCampaign(
                        await api(`/campaigns/${campaign.campaignId}`),
                      );
                    })
                  }
                >
                  Stop scheduling
                </button>
                <Json value={campaign} />
              </>
            ) : (
              <Empty title="No campaign selected" icon="catalog">
                Preview a finite matrix, create the campaign, and inspect each
                child independently.
              </Empty>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export { LabView } from "../features/lab/LabView";
