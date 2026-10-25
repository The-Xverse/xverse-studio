import { useState } from "react";
import type { Data } from "../../api/types";
import type { ElementProjection, Projection } from "./projection";
export type AssetKind = "device" | "sensor" | "actuator" | "model";
export function LogicalAssetForm({
  projection,
  element,
  initialKind = "device",
  onSave,
}: {
  projection: Projection;
  element?: ElementProjection;
  initialKind?: AssetKind;
  onSave: (edits: Data[]) => Promise<unknown>;
}) {
  const systems = projection.resources.filter((r) => r.kind === "System"),
    raw = element?.raw || {};
  const [assetKind, setKind] = useState<AssetKind>(
      (element?.kind as AssetKind) || initialKind,
    ),
    [documentId, setDocumentId] = useState(
      element?.documentId || systems[0]?.documentId || "",
    ),
    [id, setId] = useState(element?.id || ""),
    [nodeId, setNodeId] = useState(raw.nodeId || ""),
    [capabilities, setCapabilities] = useState(
      (raw.capabilities || ["measurement"]).join(", "),
    ),
    [realizations, setRealizations] = useState<string[]>(
      raw.supportedRealizationClasses || ["simulated"],
    ),
    [deviceId, setDeviceId] = useState(raw.deviceId || ""),
    [quantity, setQuantity] = useState(
      raw.observedQuantity || raw.controlledQuantity || "state",
    ),
    [endpointId, setEndpointId] = useState(
      raw.outputEndpointId || raw.inputEndpointId || "",
    ),
    [unit, setUnit] = useState(raw.unitSemantics || "1"),
    [maturity, setMaturity] = useState(raw.maturity || "prototype"),
    [modelKind, setModelKind] = useState(raw.modelKind || "opaque-reference"),
    [externalRef, setExternalRef] = useState(
      raw.externalRef || "urn:example:model:1",
    ),
    [inputs, setInputs] = useState<string[]>(raw.inputs || []),
    [outputs, setOutputs] = useState<string[]>(raw.outputs || []),
    [portDirection, setPortDirection] = useState(""),
    [portId, setPortId] = useState(""),
    [portInterface, setPortInterface] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const system = systems.find((r) => r.documentId === documentId),
    spec = system?.spec || {};
  const declared = (name: string): Data[] =>
    Array.isArray(spec[name]) ? spec[name] : [];
  const endpoints = declared("endpoints").filter(
    (e) =>
      e.direction === "bidirectional" ||
      e.direction === (assetKind === "sensor" ? "output" : "input"),
  );
  const split = (v: string) =>
    v
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  function multi(selected: string[], value: string, checked: boolean) {
    return checked
      ? [...selected, value]
      : selected.filter((id) => id !== value);
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const properties: Data =
        assetKind === "device"
          ? {
              capabilities: split(capabilities),
              supportedRealizationClasses: realizations,
              ...(nodeId ? { nodeId } : {}),
            }
          : assetKind === "model"
            ? { modelKind, externalRef, inputs, outputs, maturity }
            : {
                ...(deviceId ? { deviceId } : {}),
                ...(assetKind === "sensor"
                  ? {
                      observedQuantity: quantity,
                      outputEndpointId: endpointId,
                      maturity,
                    }
                  : {
                      controlledQuantity: quantity,
                      inputEndpointId: endpointId,
                    }),
                unitSemantics: unit,
              };
      const unsetProperties =
        element && assetKind === "device" && raw.nodeId && !nodeId
          ? ["nodeId"]
          : element &&
              ["sensor", "actuator"].includes(assetKind) &&
              raw.deviceId &&
              !deviceId
            ? ["deviceId"]
            : [];
      await onSave([
        {
          kind: element ? "update_logical_asset" : "add_logical_asset",
          documentId,
          assetKind,
          elementId: id,
          properties,
          ...(element
            ? {
                elementRef: element.ref,
                ...(unsetProperties.length ? { unsetProperties } : {}),
              }
            : assetKind === "device" && portDirection
              ? {
                  endpoints: [
                    {
                      id: portId,
                      ownerId: id,
                      interfaceId: portInterface,
                      direction: portDirection,
                    },
                  ],
                }
              : {}),
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The asset edit failed.");
    } finally {
      setBusy(false);
    }
  }
  const interfaces = declared("interfaces");
  return (
    <form onSubmit={(e) => void save(e)} className="logical-asset-form">
      <p className="field-hint">
        Author a logical XDL asset. These edits validate source references
        without accessing devices or starting providers. Additional topology
        requires a compatible execution provider.
      </p>
      <label>
        Element kind
        <select
          aria-label="Logical asset kind"
          disabled={!!element}
          value={assetKind}
          onChange={(e) => {
            setKind(e.target.value as AssetKind);
            setEndpointId("");
          }}
        >
          {["device", "sensor", "actuator", "model"].map((kind) => (
            <option key={kind} value={kind}>
              {kind[0].toUpperCase() + kind.slice(1)}
            </option>
          ))}
        </select>
      </label>
      <label>
        System resource
        <select
          required
          disabled={!!element}
          aria-label="System resource"
          value={documentId}
          onChange={(e) => {
            setDocumentId(e.target.value);
            setNodeId("");
            setDeviceId("");
            setEndpointId("");
            setInputs([]);
            setOutputs([]);
          }}
        >
          {systems.map((s) => (
            <option key={s.documentId} value={s.documentId}>
              {s.metadata.namespace}/{s.metadata.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Element identifier
        <input
          required
          pattern="[a-zA-Z0-9_\-]+"
          maxLength={80}
          disabled={!!element}
          value={id}
          onChange={(e) => setId(e.target.value)}
        />
      </label>
      {assetKind === "device" ? (
        <>
          <label>
            Capabilities (comma separated)
            <input
              required
              value={capabilities}
              onChange={(e) => setCapabilities(e.target.value)}
            />
          </label>
          <fieldset>
            <legend>Supported realization capabilities</legend>
            {["simulated", "virtual", "physical", "hybrid"].map((value) => (
              <label className="check-label" key={value}>
                <input
                  type="checkbox"
                  checked={realizations.includes(value)}
                  onChange={(e) =>
                    setRealizations(
                      multi(realizations, value, e.target.checked),
                    )
                  }
                />
                {value}
              </label>
            ))}
          </fieldset>
          <p className="field-hint">
            These are supported classes. The Deployment selects the actual
            realization and host placement.
          </p>
          <label>
            Logical containing node
            <select
              aria-label="Logical containing node"
              value={nodeId}
              onChange={(e) => setNodeId(e.target.value)}
            >
              <option value="">Unplaced</option>
              {declared("nodes").map((node) => (
                <option key={node.id} value={node.id}>
                  {node.id}
                </option>
              ))}
            </select>
          </label>
          {!element && (
            <>
              <label>
                Optional new device port
                <select
                  aria-label="Optional new device port"
                  value={portDirection}
                  onChange={(e) => setPortDirection(e.target.value)}
                >
                  <option value="">No new port</option>
                  <option value="input">Input</option>
                  <option value="output">Output</option>
                  <option value="bidirectional">Bidirectional</option>
                </select>
              </label>
              {portDirection && (
                <>
                  <label>
                    New port identifier
                    <input
                      required
                      value={portId}
                      pattern="[a-zA-Z0-9_\-]+"
                      onChange={(e) => setPortId(e.target.value)}
                    />
                  </label>
                  <label>
                    New port interface
                    <select
                      aria-label="New port interface"
                      required
                      value={portInterface}
                      onChange={(e) => setPortInterface(e.target.value)}
                    >
                      <option value="">Select declared interface</option>
                      {interfaces.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.id}
                        </option>
                      ))}
                    </select>
                  </label>
                </>
              )}
            </>
          )}
        </>
      ) : assetKind === "model" ? (
        <>
          <label>
            Model kind
            <input
              required
              value={modelKind}
              onChange={(e) => setModelKind(e.target.value)}
            />
          </label>
          <label>
            External reference (inert)
            <input
              required
              value={externalRef}
              onChange={(e) => setExternalRef(e.target.value)}
            />
          </label>
          <p className="field-hint">
            No reference is fetched or executed. Inputs and outputs name
            declared interfaces.
          </p>
          {[
            ["Input interfaces", inputs, setInputs],
            ["Output interfaces", outputs, setOutputs],
          ].map(([label, values, setter]) => (
            <fieldset key={String(label)}>
              <legend>{String(label)}</legend>
              {interfaces.map((value) => (
                <label className="check-label" key={value.id}>
                  <input
                    type="checkbox"
                    checked={(values as string[]).includes(value.id)}
                    onChange={(e) =>
                      (setter as (v: string[]) => void)(
                        multi(values as string[], value.id, e.target.checked),
                      )
                    }
                  />
                  {value.id}
                </label>
              ))}
            </fieldset>
          ))}
        </>
      ) : (
        <>
          <label>
            Associated logical device
            <select
              aria-label="Associated logical device"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
            >
              <option value="">None declared</option>
              {declared("devices").map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id}
                </option>
              ))}
            </select>
          </label>
          <label>
            {assetKind === "sensor"
              ? "Observed quantity"
              : "Controlled quantity"}
            <input
              required
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </label>
          <label>
            {assetKind === "sensor" ? "Output endpoint" : "Input endpoint"}
            <select
              aria-label={
                assetKind === "sensor" ? "Output endpoint" : "Input endpoint"
              }
              required
              value={endpointId}
              onChange={(e) => setEndpointId(e.target.value)}
            >
              <option value="">Select compatible declared endpoint</option>
              {endpoints.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.id} · {v.direction}
                </option>
              ))}
            </select>
          </label>
          <label>
            Unit semantics
            <input
              required
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
            />
          </label>
        </>
      )}
      {assetKind !== "device" && assetKind !== "actuator" && (
        <label>
          Maturity
          <select
            aria-label="Maturity"
            value={maturity}
            onChange={(e) => setMaturity(e.target.value)}
          >
            {[
              "observed",
              "inferred",
              "architectural-target",
              "prototype",
              "verified",
            ].map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>
      )}
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="form-actions">
        <button
          className="button primary"
          disabled={
            busy ||
            !documentId ||
            (assetKind === "device" && !realizations.length)
          }
        >
          {busy
            ? "Validating asset…"
            : element
              ? "Save logical asset"
              : "Add logical asset"}
        </button>
      </div>
    </form>
  );
}
