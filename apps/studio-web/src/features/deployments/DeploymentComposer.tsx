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
import { useTerm } from "../profiles/presentation";
import {
  ResolutionPanel,
  VariantComparison,
  useResolution,
} from "./ResolutionPanel";
export interface ExecutionSelection {
  deploymentRef?: string;
  scenarioRef?: string;
}
export function DeploymentComposer({
  project,
  projection,
  providers,
  providerId,
  selection,
  onSelection,
  refresh,
  doAction,
}: {
  project: Project;
  projection: Projection;
  providers: Data[];
  providerId: string;
  selection: ExecutionSelection;
  onSelection: (selection: ExecutionSelection) => void;
  refresh: () => Promise<unknown>;
  doAction: DoAction;
}) {
  const term = useTerm();
  const [variants, setVariants] = useState<Data[]>([]),
    [name, setName] = useState(""),
    [diagnostics, setDiagnostics] = useState<Data[]>([]),
    [compatibility, setCompatibility] = useState<Data | null>(null),
    [compareRef, setCompareRef] = useState(""),
    [resourceBinding, setResourceBinding] = useState(""),
    [mappingForm, setMappingForm] = useState({
      mappingId: "",
      sourceTimeDomainId: "",
      targetTimeDomainId: "",
      mapping: "",
      toleranceValue: "",
      toleranceUnit: "s",
    }),
    [resourceDraft, setResourceDraft] = useState<{
      key: string;
      ids: string[];
    } | null>(null);
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
  const resolved = useResolution(
      project.projectId,
      project.revision,
      chosen?.documentId,
      providerId,
    ),
    compareVariant = variants.find(
      (variant) => variant.ref === compareRef && variant.ref !== chosen?.ref,
    ),
    compared = useResolution(
      project.projectId,
      project.revision,
      compareVariant?.documentId,
      providerId,
    );
  const binding = chosen?.bindings.find(
      (value: Data) => value.id === resourceBinding,
    ),
    bindingTarget = chosen?.targets.find(
      (target: Data) => target.id === binding?.targetId,
    ),
    offered = new Set<string>(bindingTarget?.offeredResourceIds || []),
    declaredResources = new Set<string>(
      (chosen?.resources || []).map((resource: Data) => resource.id),
    ),
    // Unsaved choices belong to one variant, binding and revision; anything else shows the authored binding.
    draftKey = `${chosen?.documentId}:${resourceBinding}:${project.revision}`,
    resourceChoice: string[] =
      resourceDraft?.key === draftKey
        ? resourceDraft.ids
        : binding?.resourceIds || [];
  async function timeMappingEdit(edit: Data) {
    const result = await api(`/projects/${project.projectId}/edits`, {
      method: "POST",
      revision: project.revision,
      body: {
        baseRevision: project.revision,
        edits: [
          {
            kind: "set_time_mapping",
            documentId: (
              project.documents[chosen!.documentId] as { path: string }
            ).path,
            ...edit,
          },
        ],
      },
    });
    await refresh();
    return result;
  }
  async function patchBinding(change: Partial<BindingUpdate>) {
    const result = await api(
      `/projects/${project.projectId}/deployment-variants/${chosen!.documentId}?providerId=${encodeURIComponent(providerId)}`,
      {
        method: "PATCH",
        revision: project.revision,
        body: { baseRevision: project.revision, ...change } as BindingUpdate,
      },
    );
    setCompatibility(result.compatibility);
    await refresh();
  }
  return (
    <div className="view-page deployment-composer">
      <div className="section-heading">
        <div>
          <h2>{term("Deployment")} variants</h2>
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
                setResourceBinding("");
                if (variant?.ref === compareRef) setCompareRef("");
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
      {chosen && (
        <section className="panel" aria-labelledby="resolution-heading">
          <h3 id="resolution-heading">
            Resolution and effective configuration
          </h3>
          <ResolutionPanel
            report={resolved?.value}
            failure={resolved?.failure}
          />
        </section>
      )}
      {chosen && (chosen.resources || []).length > 0 && (
        <section className="panel" aria-labelledby="resource-heading">
          <h3 id="resource-heading">Bound resources</h3>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void doAction("Saving bound resources", () =>
                patchBinding({
                  bindingId: resourceBinding,
                  resourceIds: resourceChoice.filter((id) =>
                    declaredResources.has(id),
                  ),
                }),
              );
            }}
          >
            <label>
              Binding
              <select
                aria-label="Binding for resources"
                value={resourceBinding}
                onChange={(event) => setResourceBinding(event.target.value)}
              >
                <option value="">Choose a binding</option>
                {chosen.bindings.map((value: Data) => (
                  <option key={value.id} value={value.id}>
                    {value.id} ({value.logicalRef?.element})
                  </option>
                ))}
              </select>
            </label>
            <fieldset disabled={!binding}>
              <legend>Resources declared by this deployment</legend>
              {(chosen.resources || []).map((resource: Data) => (
                <label key={resource.id} className="resource-choice">
                  <input
                    type="checkbox"
                    checked={resourceChoice.includes(resource.id)}
                    onChange={(event) =>
                      setResourceDraft({
                        key: draftKey,
                        ids: event.target.checked
                          ? [...resourceChoice, resource.id]
                          : resourceChoice.filter((id) => id !== resource.id),
                      })
                    }
                  />
                  {resource.id} — {resource.resourceClass},{" "}
                  {resource.capacity?.value} {resource.capacity?.unit},{" "}
                  {resource.allocationPolicy}
                  {binding &&
                    (!bindingTarget?.offeredResourceIds ? (
                      <small>
                        {" "}
                        ({binding.targetId} declares no offered resources;
                        placement stays unknown)
                      </small>
                    ) : (
                      !offered.has(resource.id) && (
                        <small> (not offered by {binding.targetId})</small>
                      )
                    ))}
                </label>
              ))}
            </fieldset>
            <p className="field-hint">
              Studio records the binding exactly; placement and requirement
              checks are shown in the resolution above. Time mappings are edited
              in XDL source.
            </p>
            <button className="button" disabled={!binding}>
              Save bound resources
            </button>
          </form>
        </section>
      )}
      {chosen && (
        <section className="panel" aria-labelledby="time-heading">
          <h3 id="time-heading">Time mappings</h3>
          {(chosen.timeMappings || []).length ? (
            <ul className="time-mappings">
              {chosen.timeMappings.map((value: Data) => (
                <li key={value.id}>
                  <code>{value.id}</code>: {value.sourceTimeDomainRef?.element}{" "}
                  → {value.targetTimeDomainRef?.element} ({value.mapping}, ±
                  {value.tolerance?.value} {value.tolerance?.unit}){" "}
                  <button
                    type="button"
                    className="small-button"
                    aria-label={`Remove time mapping ${value.id}`}
                    onClick={() =>
                      void doAction("Removing time mapping", () =>
                        timeMappingEdit({ mappingId: value.id, remove: true }),
                      )
                    }
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">
              No time mappings. Elements share the System's declared clocks.
            </p>
          )}
          <form
            className="time-mapping-form"
            onSubmit={(event) => {
              event.preventDefault();
              void doAction("Saving time mapping", async () => {
                await timeMappingEdit({
                  mappingId: mappingForm.mappingId,
                  sourceTimeDomainId: mappingForm.sourceTimeDomainId,
                  targetTimeDomainId: mappingForm.targetTimeDomainId,
                  mapping: mappingForm.mapping,
                  tolerance: {
                    value: Number(mappingForm.toleranceValue),
                    unit: mappingForm.toleranceUnit,
                  },
                });
                setMappingForm({ ...mappingForm, mappingId: "", mapping: "" });
              });
            }}
          >
            <label>
              Mapping identifier
              <input
                required
                pattern="[a-z][a-z0-9]*(-[a-z0-9]+)*"
                maxLength={63}
                value={mappingForm.mappingId}
                onChange={(event) =>
                  setMappingForm({
                    ...mappingForm,
                    mappingId: event.target.value,
                  })
                }
              />
            </label>
            {(["sourceTimeDomainId", "targetTimeDomainId"] as const).map(
              (field) => (
                <label key={field}>
                  {field === "sourceTimeDomainId"
                    ? "Source clock"
                    : "Target clock"}
                  <select
                    required
                    value={mappingForm[field]}
                    onChange={(event) =>
                      setMappingForm({
                        ...mappingForm,
                        [field]: event.target.value,
                      })
                    }
                  >
                    <option value="">Choose a declared time domain</option>
                    {(chosen.timeDomains || []).map((domain: string) => (
                      <option key={domain} value={domain}>
                        {domain}
                      </option>
                    ))}
                  </select>
                </label>
              ),
            )}
            <label>
              Mapping description
              <input
                required
                maxLength={200}
                value={mappingForm.mapping}
                onChange={(event) =>
                  setMappingForm({
                    ...mappingForm,
                    mapping: event.target.value,
                  })
                }
              />
            </label>
            <label>
              Tolerance
              <input
                required
                type="number"
                min={0}
                step="any"
                value={mappingForm.toleranceValue}
                onChange={(event) =>
                  setMappingForm({
                    ...mappingForm,
                    toleranceValue: event.target.value,
                  })
                }
              />
            </label>
            <label>
              Tolerance unit
              <input
                required
                maxLength={32}
                value={mappingForm.toleranceUnit}
                onChange={(event) =>
                  setMappingForm({
                    ...mappingForm,
                    toleranceUnit: event.target.value,
                  })
                }
              />
            </label>
            <p className="field-hint">
              A mapping with an existing identifier replaces it. Studio records
              the declared relation; its accuracy is never evaluated.
            </p>
            <button className="button">Save time mapping</button>
          </form>
        </section>
      )}
      {chosen && variants.length > 1 && (
        <section className="panel" aria-labelledby="compare-heading">
          <h3 id="compare-heading">Compare with another variant</h3>
          <label>
            Comparison variant
            <select
              aria-label="Comparison variant"
              value={compareVariant?.ref || ""}
              onChange={(event) => setCompareRef(event.target.value)}
            >
              <option value="">Choose a variant</option>
              {variants
                .filter((variant) => variant.ref !== chosen.ref)
                .map((variant) => (
                  <option key={variant.documentId} value={variant.ref}>
                    {variant.name}
                  </option>
                ))}
            </select>
          </label>
          {compareVariant &&
            (resolved?.value?.sourceValid && compared?.value?.sourceValid ? (
              <VariantComparison
                left={resolved.value}
                right={compared.value}
                leftName={chosen.name}
                rightName={compareVariant.name}
              />
            ) : (
              <p className="muted" role="status">
                {resolved?.failure ||
                  compared?.failure ||
                  "Resolving both variants…"}
              </p>
            ))}
        </section>
      )}
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
          providerId={providerId}
          edit={async (edits) =>
            doAction("Saving selected deployment binding", async () => {
              const { kind, documentId, ...change } = edits[0];
              await patchBinding(change);
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
