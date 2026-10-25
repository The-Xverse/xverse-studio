import { useEffect, useState } from "react";
import type {
  BindingUpdate,
  VariantCreate,
} from "../../../../../packages/contracts/api";
import type { Data, Project } from "../../api/types";
import { api, items } from "../../api/client";
import type { DoAction } from "../../app/App";
import type { Projection } from "../model/projection";
import { DeploymentView } from "../model/Views";
import { Icon, Badge, Diagnostics, Empty, KeyValues } from "../../app/ui";
export interface ExecutionSelection {
  deploymentRef?: string;
  scenarioRef?: string;
}
export function DeploymentComposer({
  project,
  projection,
  providers,
  selection,
  onSelection,
  refresh,
  doAction,
}: {
  project: Project;
  projection: Projection;
  providers: Data[];
  selection: ExecutionSelection;
  onSelection: (selection: ExecutionSelection) => void;
  refresh: () => Promise<unknown>;
  doAction: DoAction;
}) {
  const [variants, setVariants] = useState<Data[]>([]),
    [name, setName] = useState(""),
    [diagnostics, setDiagnostics] = useState<Data[]>([]),
    [compatibility, setCompatibility] = useState<Data | null>(null);
  useEffect(() => {
    let active = true;
    void api(`/projects/${project.projectId}/deployment-variants`)
      .then((response) => {
        if (!active) return;
        const values = items<Data>(response);
        setVariants(values);
        setDiagnostics(response.diagnostics || []);
        if (!selection.deploymentRef && values.length === 1)
          onSelection({
            deploymentRef: values[0].ref,
            scenarioRef:
              values[0].scenarioRefs.length === 1
                ? values[0].scenarioRefs[0]
                : undefined,
          });
      })
      .catch((error) => {
        if (active)
          setDiagnostics([
            {
              code: error.code || "VARIANT_UNAVAILABLE",
              message: error.message,
            },
          ]);
      });
    return () => {
      active = false;
    };
  }, [project.projectId, project.revision]);
  const chosen =
    variants.find((variant) => variant.ref === selection.deploymentRef) ||
    (variants.length === 1 ? variants[0] : undefined);
  const document = projection.deployments.find(
    (resource) => resource.documentId === chosen?.documentId,
  );
  return (
    <div className="view-page deployment-composer">
      <div className="section-heading">
        <div>
          <h2>Deployment variants</h2>
          <p>
            Select an authored Deployment and its associated Scenario. Logical
            System identities remain stable.
          </p>
        </div>
        <Badge>Explicit compiler selection</Badge>
      </div>
      <Diagnostics diagnostics={diagnostics as any} />
      <section className="panel">
        <div className="variant-selection">
          <label>
            Deployment variant
            <select
              aria-label="Deployment variant"
              value={chosen?.ref || ""}
              onChange={(event) => {
                const variant = variants.find(
                  (v) => v.ref === event.target.value,
                );
                onSelection(
                  variant
                    ? {
                        deploymentRef: variant.ref,
                        scenarioRef:
                          variant.scenarioRefs.length === 1
                            ? variant.scenarioRefs[0]
                            : undefined,
                      }
                    : {},
                );
                setCompatibility(null);
              }}
            >
              <option value="">Choose an authored deployment</option>
              {variants.map((variant) => (
                <option key={variant.documentId} value={variant.ref}>
                  {variant.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Associated Scenario
            <select
              aria-label="Associated Scenario"
              value={selection.scenarioRef || ""}
              onChange={(event) =>
                onSelection({
                  deploymentRef: chosen?.ref,
                  scenarioRef: event.target.value || undefined,
                })
              }
              disabled={!chosen}
            >
              <option value="">Choose a matching Scenario</option>
              {(chosen?.scenarioRefs || []).map((ref: string) => (
                <option key={ref} value={ref}>
                  {ref.split("/").pop()}
                </option>
              ))}
            </select>
          </label>
        </div>
        {chosen && (
          <KeyValues
            values={{
              "Requested Deployment": chosen.ref,
              "Requested Scenario":
                selection.scenarioRef || "Selection required",
              Readiness: "Fresh preflight required before every new run",
            }}
          />
        )}
        <p className="field-hint">
          Selection does not rewrite either resource. The backend rejects
          mismatched contributors and freezes exact selected inputs before
          execution.
        </p>
      </section>
      <section className="panel">
        <h3>Create a named variant</h3>
        <p className="field-hint">
          Clone the selected Deployment together with its matching Scenario.
          Parameters, assessment references, and logical topology retain
          explicit authored provenance.
        </p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void doAction(
              "Creating authored deployment and scenario",
              async () => {
                if (!chosen || !selection.scenarioRef)
                  throw new Error(
                    "Choose one source Deployment and its matching Scenario.",
                  );
                const scenario = projection.scenarios.find(
                  (resource) =>
                    `xdl://${resource.metadata.namespace}/scenario/${resource.metadata.name}` ===
                    selection.scenarioRef,
                );
                const result = await api(
                  `/projects/${project.projectId}/deployment-variants`,
                  {
                    method: "POST",
                    revision: project.revision,
                    body: {
                      baseRevision: project.revision,
                      name,
                      sourceDeploymentId: chosen.documentId,
                      ...(scenario
                        ? { sourceScenarioId: scenario.documentId }
                        : {}),
                    } satisfies VariantCreate,
                  },
                );
                onSelection({
                  deploymentRef: result.variant.ref,
                  scenarioRef: result.variant.scenarioRefs[0],
                });
                setName("");
                await refresh();
              },
            );
          }}
        >
          <div className="variant-create">
            <label>
              New variant name
              <input
                aria-label="New variant name"
                required
                maxLength={120}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Alternative reference deployment"
              />
            </label>
            <button
              className="button primary"
              disabled={!chosen || !selection.scenarioRef || !name.trim()}
            >
              <Icon name="plus" />
              Create deployment variant
            </button>
          </div>
        </form>
      </section>
      {compatibility && (
        <section className="panel">
          <h3>Binding compatibility</h3>
          <Badge tone={compatibility.status === "blocked" ? "warning" : "info"}>
            {compatibility.status}
          </Badge>
          <Diagnostics diagnostics={compatibility.diagnostics} />
        </section>
      )}
      {document ? (
        <DeploymentView
          header={false}
          projection={{ ...projection, deployments: [document] }}
          providers={providers}
          edit={async (edits) =>
            doAction("Saving selected deployment binding", async () => {
              const { kind, documentId, ...change } = edits[0];
              const result = await api(
                `/projects/${project.projectId}/deployment-variants/${chosen!.documentId}`,
                {
                  method: "PATCH",
                  revision: project.revision,
                  body: {
                    baseRevision: project.revision,
                    ...change,
                  } as BindingUpdate,
                },
              );
              setCompatibility(result.compatibility);
              await refresh();
            })
          }
        />
      ) : (
        <Empty title="Choose an authored deployment" icon="deployment">
          Unsupported or invalid resources remain available in XDL source with
          authoritative diagnostics.
        </Empty>
      )}
    </div>
  );
}
