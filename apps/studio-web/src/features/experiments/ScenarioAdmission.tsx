import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge, Diagnostics, KeyValues } from "../../app/ui";

type Context = { projectId: string; revision: number; providerId: string; scenarioRef: string };
type Result = { key: string; report?: Data; error?: string; loading?: boolean };
const states = ["blocked", "preflight_required"];
function reportFor(value: Data, context: Context) {
  if (
    value.scenarioAdmissionVersion !== "1.0" || value.readOnly !== true ||
    value.projectId !== context.projectId || value.revision !== context.revision ||
    value.providerId !== context.providerId || value.selection?.scenarioRef !== context.scenarioRef ||
    !states.includes(value.status) || typeof value.sourceValid !== "boolean" ||
    !["supported", "unsupported", "unknown"].includes(value.sourceMapping) ||
    !Array.isArray(value.diagnostics) || value.diagnostics.length > 100 ||
    value.observations?.observationAdmissionVersion !== "1.0" ||
    !Array.isArray(value.observations.items) || value.observations.items.length > 32 ||
    !Array.isArray(value.observations.budgets) || value.observations.budgets.length > 8
  ) throw Error("Scenario inspection does not match the selected source, provider or supported contract. Inspect again.");
  const observation = value.observations;
  if (!observation.items.every((v: Data) => v && typeof v.observerId === "string") ||
      !observation.budgets.every((v: Data) => v && typeof v.unit === "string" &&
        ["satisfied", "exceeded", "unknown"].includes(v.status) &&
        typeof v.maximum === "number" && Number.isFinite(v.maximum) && v.maximum >= 0 &&
        (v.total === null || typeof v.total === "number" && Number.isFinite(v.total) && v.total >= 0)))
    throw Error("Observation inspection has an unsupported shape. Inspect its source and retry.");
  return value;
}
function declaration(value: Data | undefined) {
  return value?.status === "declared" && typeof value.value === "string" ? value.value :
    value?.status === "withheld" ? "Withheld from public metadata" : "Not declared";
}
export function ScenarioAdmission(context: Context) {
  const key = JSON.stringify(context), current = useRef(key), sequence = useRef(0),
    controller = useRef<AbortController | null>(null),
    [result, setResult] = useState<Result>({ key });
  current.current = key;
  useEffect(() => () => { sequence.current++; controller.current?.abort(); }, [key]);
  const visible = result.key === key ? result : { key }, report = visible.report;
  async function inspect() {
    const submitted = key, request = ++sequence.current, abort = new AbortController();
    controller.current?.abort(); controller.current = abort;
    setResult({ key, loading: true });
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; abort.abort(); }, 30000);
    try {
      const query = new URLSearchParams({ revision: String(context.revision), providerId: context.providerId, scenarioRef: context.scenarioRef });
      const value = reportFor(await api(`/projects/${encodeURIComponent(context.projectId)}/scenario-admission?${query}`, { signal: abort.signal }), context);
      if (!abort.signal.aborted && current.current === submitted && sequence.current === request)
        setResult({ key: submitted, report: value });
    } catch (error) {
      if ((!abort.signal.aborted || timedOut) && current.current === submitted && sequence.current === request)
        setResult({ key: submitted, error: timedOut ? "Inspection timed out. Inspect again to retry." : error instanceof Error ? error.message : "Inspection unavailable." });
    } finally { clearTimeout(timer); }
  }
  const observations = report?.observations;
  return <section className="panel" aria-label="Scenario support and observation budgets" aria-busy={visible.loading || false}>
    <div className="section-heading"><h3>Scenario support and observation budgets</h3>
      <button className="button" disabled={visible.loading} onClick={() => void inspect()}>Inspect scenario support</button></div>
    <p>Inspect the current draft for <code>{context.providerId}</code>, revision {context.revision}. This read-only check does not contact runtime resources or create a run. Fresh preflight and Start are required.</p>
    {visible.loading && <p role="status">Inspecting the selected Scenario and provider declarations…</p>}
    {visible.error && <p role="alert">Scenario inspection unavailable: {visible.error.slice(0, 1000)}</p>}
    {report && <>
      <p role="status"><Badge tone={report.status === "blocked" ? "warning" : "neutral"}>{report.status === "preflight_required" ? "Preflight required" : "Source support blocked"}</Badge> Source mapping: {report.sourceMapping}. Declared intent does not establish observed effects.</p>
      <Diagnostics diagnostics={report.diagnostics} />
      {report.diagnosticsComplete === false && <p>Diagnostics are truncated. Inspect XDL for the full source.</p>}
      <KeyValues values={{ "Observer count": observations.observerCount ?? "Unavailable", "Observer count limit": observations.maxObservers ?? "Not declared", "Undeclared CPU, memory, latency and retention costs": "Unknown" }} />
      <h4>Declared cost budgets</h4>
      {observations.budgets.length ? <table><caption>Provider-declared costs; no unit conversion or measured resource use</caption><thead><tr><th>Unit</th><th>Total</th><th>Maximum</th><th>Status</th></tr></thead><tbody>{observations.budgets.map((b: Data) => <tr key={b.unit}><td>{b.unit}</td><td>{b.total ?? "Unknown"}</td><td>{b.maximum}</td><td>{b.status}</td></tr>)}</tbody></table> : <p>No cost budget is available for this selection. Unknown costs are not zero.</p>}
      <h4>Observer declarations</h4>
      {observations.items.map((o: Data) => <section key={o.observerId} aria-label={`Observer declaration ${o.observerId}`}>
        <h5>{o.observerId}</h5><KeyValues values={{ "Source": o.targetRef ? `${o.targetRef.kind} ${o.targetRef.name} / ${o.targetRef.element}` : "Not declared", "Clock": o.clockDomain ?? "Not declared", "Sampling / trigger intent": declaration(o.sampling), "Units": declaration(o.units), "Payload schema": declaration(o.payloadSchema), "Evidence sink": declaration(o.evidenceSink), "Intrusiveness": declaration(o.intrusiveness), "Retention": declaration(o.retention), "Resource cost": o.resourceCost?.status === "declared" && Array.isArray(o.resourceCost.quantities) ? o.resourceCost.quantities.map((q: Data) => `${q.value} ${q.unit}`).join(", ") : "Not declared" }} />
      </section>)}
      {observations.itemsComplete === false && <p>Observer inspection is incomplete or unavailable. Counts and missing costs cannot establish admission.</p>}
    </>}
  </section>;
}
