import { CampaignWorkspace } from "../features/campaigns/CampaignWorkspace";
import { ScenarioAdmission } from "../features/experiments/ScenarioAdmission";
import { ScenarioAuthoring } from "../features/experiments/ScenarioAuthoring";
import { ScenarioTimeline } from "../features/experiments/ScenarioTimeline";
import type { SourceTarget } from "../features/model/Views";
import { useState } from "react";
import { FrozenAssessments } from "../features/experiments/FrozenAssessments";
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
  providerId,
  provider,
  onAuthoringIntent,
  campaignLimits,
  campaignEnabled,
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
  providerId: string;
  provider?: Data;
  onAuthoringIntent: () => void;
  campaignLimits: Data;
  campaignEnabled: boolean;
}) {
  const [tab, setTab] = useState("Scenario");
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
        {["Scenario", "Timeline", "Assertions", "Campaigns"].map((t) => (
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
            <ScenarioAdmission projectId={project.projectId} revision={project.revision} providerId={providerId}
              scenarioRef={`xdl://${scenario.metadata.namespace}/scenario/${scenario.metadata.name}`} />
            <ScenarioAuthoring
              key={JSON.stringify([
                project.projectId,
                scenario.documentId,
                scenario.metadata.namespace,
                scenario.metadata.name,
              ])}
              scenario={scenario}
              projection={projection}
              limits={authoringLimits}
              provider={provider}
              edit={edit}
              onSource={onSource}
              onIntent={onAuthoringIntent}
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
                    "Declared clocks":
                      [
                        ...new Set(
                          [...(spec.steps || []), ...(spec.observers || [])]
                            .map((item: Data) => item.timeDomainId)
                            .filter(Boolean),
                        ),
                      ].join(", ") || "Not declared",
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
      ) : tab === "Timeline" ? (
        <ScenarioTimeline
          key={JSON.stringify([project.projectId, run?.runId, run?.snapshotId])}
          projectId={project.projectId}
          revision={project.revision}
          scenarioRef={selection.scenarioRef}
          run={run}
        />
      ) : tab === "Assertions" ? (
        <FrozenAssessments
          key={JSON.stringify([project.projectId, run?.runId, run?.snapshotId])}
          projectId={project.projectId}
          run={run}
          doAction={doAction}
        />
      ) : (
        <CampaignWorkspace
          key={project.projectId}
          project={project}
          preflight={preflight}
          limits={campaignLimits}
          enabled={campaignEnabled}
        />
      )}
    </div>
  );
}

export { LabView } from "../features/lab/LabView";
