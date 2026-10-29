import { useState } from "react";
import type { Data } from "../../api/types";
import type { Projection } from "../model/projection";
import { textRef } from "../model/projection";
import "./scenarioTimeline.css";

type Kind = "step" | "fault" | "observer" | "metric";
/** Authored coordinates only; no unit/clock mapping or execution inference. */
export function DraftScenarioTimeline({
  scenario,
  projection,
  onEdit,
}: {
  scenario: Data;
  projection: Projection;
  onEdit: (kind: Kind, item: Data) => void;
}) {
  const system = projection.resources.find(
    (r) =>
      r.kind === "System" &&
      r.metadata.namespace === scenario.spec.systemRef?.namespace &&
      r.metadata.name === scenario.spec.systemRef?.name,
  );
  const clocks: Data[] = Array.isArray(system?.spec.timeDomains)
    ? system.spec.timeDomains
        .filter((c: Data) => c && typeof c.id === "string")
        .slice(0, 64)
    : [];
  const [clock, setClock] = useState(
      system?.spec.defaultTimeDomainId || clocks[0]?.id || "",
    ),
    [unit, setUnit] = useState("s");
  const rows = (
    [
      ["steps", "step"],
      ["faults", "fault"],
      ["observers", "observer"],
      ["metrics", "metric"],
    ] as const
  ).flatMap(([collection, kind]) =>
    (Array.isArray(scenario.spec[collection]) ? scenario.spec[collection] : [])
      .slice(0, 1000)
      .filter((item: Data) => item && typeof item.id === "string")
      .map((item: Data) => ({ kind, item })),
  );
  const steps = rows.filter(
    ({ kind, item }) =>
      kind === "step" &&
      item.timeDomainId === clock &&
      item.schedule?.unit === unit &&
      typeof item.schedule.at === "number" &&
      Number.isFinite(item.schedule.at),
  );
  const reduced = ["steps", "faults", "observers", "metrics"].some(
    (key) =>
      Array.isArray(scenario.spec[key]) &&
      (scenario.spec[key].length > 1000 ||
        scenario.spec[key].some(
          (item: Data) => !item || typeof item.id !== "string",
        )),
  );
  const display = (v: unknown) =>
    typeof v === "string" || typeof v === "number" ? String(v) : "Unknown";
  const at: number[] = steps.map(({ item }) => item.schedule.at),
    low = Math.min(...at),
    high = Math.max(...at),
    span = high - low;
  const units = [
    ...new Set(
      rows
        .filter(({ kind }) => kind === "step")
        .map(({ item }) => item.schedule?.unit)
        .filter((v) => typeof v === "string" && v.length <= 256),
    ),
  ] as string[];
  return (
    <section
      className="scenario-timeline"
      aria-label="Authored scenario timeline"
    >
      <h4>Authored scenario timeline</h4>
      <p>
        Current draft intent in original source order. Choose a declared clock
        and schedule unit to inspect its markers. This is separate from the
        selected run’s frozen evidence.
      </p>
      {reduced && (
        <p role="status">
          Authored entries are truncated or include unsupported shapes. Inspect
          XDL source for the complete draft.
        </p>
      )}
      {Array.isArray(system?.spec.timeDomains) &&
        system.spec.timeDomains.length > 64 && (
          <p>Clock choices are truncated to 64 declarations.</p>
        )}
      <div className="form-grid">
        <label>
          Authoring clock
          <select
            aria-label="Authoring clock"
            value={clock}
            onChange={(e) => setClock(e.target.value)}
          >
            {!clocks.some((c) => c.id === clock) && (
              <option value={clock}>{clock || "No declared clock"}</option>
            )}
            {clocks.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id}
              </option>
            ))}
          </select>
        </label>
        <label>
          Authoring schedule unit
          <select
            aria-label="Authoring schedule unit"
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
          >
            {!units.includes(unit) && <option value={unit}>{unit}</option>}
            {units.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
        </label>
      </div>
      {at.length > 0 && Number.isFinite(span) && (
        <figure className="timeline-plot">
          <figcaption>
            Declared step positions · {clock} · {unit}. No conversion or runtime
            admission is implied.
          </figcaption>
          <svg
            viewBox="0 0 900 70"
            role="img"
            aria-label="Authored step markers; edit and exact schedule alternatives in Authored timeline entries table"
          >
            <path d="M 25 25 H 875" className="timeline-axis" />
            {steps.map(({ item }) => (
              <circle
                key={item.id}
                className="timeline-marker intent"
                cx={
                  span === 0
                    ? 450
                    : 25 + ((item.schedule.at - low) / span) * 850
                }
                cy="25"
                r="5"
              >
                <title>
                  {item.id}: {item.schedule.at} {unit}
                </title>
              </circle>
            ))}
            <text x="25" y="60">
              {low}
            </text>
            <text x="875" y="60" textAnchor="end">
              {high}
            </text>
          </svg>
        </figure>
      )}
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label="Scrollable authored timeline"
      >
        <table aria-label="Authored timeline entries">
          <thead>
            <tr>
              <th>Intent</th>
              <th>Declared time</th>
              <th>Target / interpretation</th>
              <th>Edit draft</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ kind, item }) => (
              <tr key={kind + ":" + item.id}>
                <td>
                  {kind} · {item.id}
                </td>
                <td>
                  {kind === "step" ? (
                    <>
                      {display(item.schedule?.at)}{" "}
                      {display(item.schedule?.unit)}
                      <small>{display(item.timeDomainId)}</small>
                    </>
                  ) : kind === "observer" ? (
                    display(item.timeDomainId)
                  ) : (
                    "Unplaced"
                  )}
                </td>
                <td>
                  {textRef(item.targetRef)}
                  <small>
                    {kind === "fault"
                      ? "Opaque activation/recovery; not an observed event"
                      : kind === "metric"
                        ? "Unevaluated metric intent"
                        : kind === "observer"
                          ? "Declared sampling intent; not a point event"
                          : steps.some((s) => s.item === item)
                            ? "Marker in selected clock and original unit"
                            : "Unplaced in selected clock/unit; no mapping inferred"}
                  </small>
                </td>
                <td>
                  <button
                    className="small-button"
                    aria-label={`Edit timeline ${kind} ${item.id}`}
                    onClick={() => onEdit(kind, item)}
                  >
                    Edit intent
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!rows.length && (
        <p>
          No authored timeline entries. Add an intent through the forms below.
        </p>
      )}
    </section>
  );
}
