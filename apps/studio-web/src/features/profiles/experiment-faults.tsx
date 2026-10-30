import { useState } from "react";
import type { Data } from "../../api/types";
import type { Projection } from "../model/projection";

export const FAULT_PROFILE = "io.xverse.experiment";
const SCHEMA = "https://xverse.io/profiles/experiment-lite/v0.1/schema.json";
const units = ["s", "ms", "us", "ns"];
const isNumber = (v: unknown) => typeof v === "number" && Number.isFinite(v) && v >= 0;
export function useExperimentFaultTiming(scenario: Data, projection: Projection, item?: Data) {
  const profile = projection.resources.some(r => r.kind === "Profile" &&
    r.spec?.extensionNamespace === FAULT_PROFILE && r.metadata?.version === "0.1.0" && r.spec.schemaRef === SCHEMA);
  const original = item?.extensions?.[FAULT_PROFILE];
  const supported = original === undefined || original && original.schemaVersion === "0.1" && original.kind === "fault-intent" &&
    original.trigger?.kind === "time" && isNumber(original.trigger.at) && isNumber(original.duration?.value) &&
    units.includes(original.trigger.unit) && units.includes(original.duration.unit) && typeof original.timeDomainId === "string";
  const available = profile && supported;
  const system = projection.resources.find(r => r.kind === "System" && r.metadata.namespace === scenario.spec.systemRef?.namespace && r.metadata.name === scenario.spec.systemRef?.name);
  const clocks: Data[] = (system?.spec.timeDomains || []).slice(0, 64);
  const [clock, setClock] = useState(original?.timeDomainId || system?.spec.defaultTimeDomainId || clocks[0]?.id || ""),
    [at, setAt] = useState(String(original?.trigger?.at ?? 2)),
    [atUnit, setAtUnit] = useState(original?.trigger?.unit || "s"),
    [duration, setDuration] = useState(String(original?.duration?.value ?? 2)),
    [durationUnit, setDurationUnit] = useState(original?.duration?.unit || "s");
  function properties(identifier: string) {
    if (!available) return {};
    if (!at.trim() || !duration.trim() || !isNumber(Number(at)) || !isNumber(Number(duration)) ||
        Number(duration) <= 0 || !units.includes(atUnit) || !units.includes(durationUnit) || !clocks.some(c => c.id === clock))
      throw Error("Choose a declared fault clock and finite nonnegative activation time with positive duration.");
    return { extensions: { ...item?.extensions, [FAULT_PROFILE]: {
      ...original, schemaVersion: "0.1", kind: "fault-intent",
      target: { ...original?.target, apiVersion: scenario.apiVersion, kind: "Scenario", namespace: scenario.metadata.namespace, name: scenario.metadata.name, element: identifier },
      trigger: { ...original?.trigger, kind: "time", at: Number(at), unit: atUnit },
      duration: { ...original?.duration, value: Number(duration), unit: durationUnit }, timeDomainId: clock,
    } } };
  }
  const fields = !available ? <p className="notice">Timed fault authoring is unavailable for this profile declaration or payload version. Existing extensions remain intact; inspect XDL source. Provider execution still requires fresh preflight.</p> :
    <fieldset><legend>Experiment-lite timed fault intent</legend>
      <p>Activation and duration use the declared clock and original units. Recovery is at activation plus duration. The compiler and selected provider validate bounds and conflicts before execution.</p>
      <div className="form-grid">
        <label>Fault clock<select aria-label="Fault clock" value={clock} onChange={e => setClock(e.target.value)} required>
          {!clocks.some(c => c.id === clock) && <option value={clock}>{clock || "Select a declared clock"}</option>}
          {clocks.map(c => <option key={c.id} value={c.id}>{c.id}</option>)}
        </select></label>
        <label>Fault activation time<input aria-label="Fault activation time" type="number" min="0" step="any" required value={at} onChange={e => setAt(e.target.value)} /></label>
        <label>Fault activation unit<select aria-label="Fault activation unit" value={atUnit} onChange={e => setAtUnit(e.target.value)}>{units.map(u => <option key={u}>{u}</option>)}</select></label>
        <label>Fault duration<input aria-label="Fault duration" type="number" min="0" step="any" required value={duration} onChange={e => setDuration(e.target.value)} /></label>
        <label>Fault duration unit<select aria-label="Fault duration unit" value={durationUnit} onChange={e => setDurationUnit(e.target.value)}>{units.map(u => <option key={u}>{u}</option>)}</select></label>
      </div>
    </fieldset>;
  return { available, fields, properties, setClock };
}

// Provider-owned choices are inert metadata; no provider IDs or industry semantics are dispatched here.
export function faultChoices(provider?: Data): Data[] {
  const contract = provider?.scenarioContracts;
  if (provider?.available !== true || provider.hostCompatible !== true || contract?.contractVersion !== "1.0" ||
      contract.timingProfile?.namespace !== FAULT_PROFILE || contract.timingProfile?.version !== "0.1" ||
      typeof contract.clockDomain !== "string" || !Array.isArray(contract.faults) || contract.faults.length > 32) return [];
  return contract.faults.filter((f: Data) => f && ["kind", "target", "activation", "recovery", "maturity", "inputSurface"].every(k => typeof f[k] === "string" && f[k].length > 0 && f[k].length <= 512))
    .map((f: Data) => ({ ...f, clockDomain: contract.clockDomain }));
}

/** Original declared coordinates only; this does not admit a runtime codec. */
export function declaredFaultTiming(scenario: Data, projection: Projection, item: Data) {
  const declared = projection.resources.some(r => r.kind === "Profile" && r.spec?.extensionNamespace === FAULT_PROFILE && r.metadata?.version === "0.1.0" && r.spec.schemaRef === SCHEMA);
  const p = item.extensions?.[FAULT_PROFILE];
  if (!declared || !p || p.schemaVersion !== "0.1" || p.kind !== "fault-intent" || p.trigger?.kind !== "time" ||
      !isNumber(p.trigger.at) || !isNumber(p.duration?.value) || !units.includes(p.trigger.unit) || !units.includes(p.duration.unit) ||
      p.target?.kind !== "Scenario" || p.target.namespace !== scenario.metadata.namespace || p.target.name !== scenario.metadata.name || p.target.element !== item.id || typeof p.timeDomainId !== "string") return null;
  return { at: p.trigger.at, unit: p.trigger.unit, duration: p.duration.value, durationUnit: p.duration.unit, clock: p.timeDomainId };
}
