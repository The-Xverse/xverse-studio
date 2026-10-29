import { useEffect, useState } from "react";
import type { Data } from "../../api/types";
import {
  emptyFilters,
  validateFilters,
  type EvidenceFilters,
} from "./evidenceFilters";
import "./evidenceFilters.css";
export function EvidenceFilterControls({
  value,
  selected,
  onApply,
  facets,
  complete,
  observation,
  loading,
}: {
  value: EvidenceFilters;
  selected: string;
  onApply: (value: EvidenceFilters, elementRef: string) => void;
  facets: Data;
  complete?: boolean;
  observation: boolean;
  loading: boolean;
}) {
  const [draft, setDraft] = useState(value),
    [element, setElement] = useState(selected),
    [error, setError] = useState("");
  useEffect(() => {
    setDraft(value);
    setElement(selected);
    setError("");
  }, [value, selected]);
  const choices = (key: string): string[] =>
    Array.isArray(facets?.[key])
      ? facets[key].filter((v: unknown) => typeof v === "string")
      : [];
  function select(
    label: string,
    key: "sourceProviderId" | "observerRef" | "field" | "clockDomain",
    values: string[],
  ) {
    const options = [
      ...new Set([...values, ...(draft[key] ? [draft[key]] : [])]),
    ];
    return (
      <label>
        {label}
        <select
          aria-label={label}
          value={draft[key]}
          onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
        >
          <option value="">
            All reported{" "}
            {key === "field"
              ? "fields"
              : key === "clockDomain"
                ? "clocks"
                : "identities"}
          </option>
          {options.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>
    );
  }
  return (
    <form
      className="evidence-filter-form"
      onSubmit={(e) => {
        e.preventDefault();
        const message = validateFilters(draft);
        setError(message);
        if (!message) onApply({ ...draft }, element);
      }}
    >
      <div className="evidence-filter-grid">
        <label>
          Element reference
          <select
            aria-label="Element reference"
            value={element}
            onChange={(e) => setElement(e.target.value)}
          >
            <option value="">All elements</option>
            {[
              ...new Set([
                ...choices("elementRefs"),
                ...(element ? [element] : []),
              ]),
            ].map((ref) => (
              <option key={ref} value={ref}>
                {ref}
              </option>
            ))}
          </select>
        </label>
        {select(
          "Emitter provider",
          "sourceProviderId",
          choices("sourceProviderIds"),
        )}
        {select("Observer", "observerRef", choices("observerRefs"))}
        {observation && select("Observation field", "field", choices("fields"))}
        <label>
          Time basis
          <select
            aria-label="Time basis"
            value={draft.timeBasis}
            onChange={(e) =>
              setDraft({
                ...draft,
                timeBasis: e.target.value as EvidenceFilters["timeBasis"],
              })
            }
          >
            <option value="none">No time window</option>
            <option value="source">Original source clock</option>
            <option value="recorded">Recorded receipt UTC</option>
          </select>
        </label>
      </div>
      {draft.timeBasis === "source" && (
        <>
          <div className="evidence-filter-grid">
            {select("Source clock", "clockDomain", choices("clockDomains"))}
            <label>
              Start tick (inclusive)
              <input
                aria-label="Start tick (inclusive)"
                inputMode="numeric"
                maxLength={32}
                value={draft.startTick}
                onChange={(e) =>
                  setDraft({ ...draft, startTick: e.target.value })
                }
              />
            </label>
            <label>
              End tick (exclusive)
              <input
                aria-label="End tick (exclusive)"
                inputMode="numeric"
                maxLength={32}
                value={draft.endTick}
                onChange={(e) =>
                  setDraft({ ...draft, endTick: e.target.value })
                }
              />
            </label>
          </div>
          <p className="field-hint">
            Original signed integer ticks, [start,end). Leave both boundaries
            empty to inspect the selected clock. Missing time never becomes tick
            zero.
          </p>
        </>
      )}
      {draft.timeBasis === "recorded" && (
        <div className="evidence-filter-grid">
          <label>
            Receipt from (inclusive)
            <input
              required
              aria-label="Receipt from (inclusive)"
              maxLength={64}
              placeholder="2026-10-25T12:00:00Z"
              value={draft.recordedFrom}
              onChange={(e) =>
                setDraft({ ...draft, recordedFrom: e.target.value })
              }
            />
          </label>
          <label>
            Receipt until (exclusive)
            <input
              required
              aria-label="Receipt until (exclusive)"
              maxLength={64}
              placeholder="2026-10-25T12:00:01Z"
              value={draft.recordedUntil}
              onChange={(e) =>
                setDraft({ ...draft, recordedUntil: e.target.value })
              }
            />
          </label>
        </div>
      )}
      {observation && (
        <p className="field-hint">
          The field predicate selects records and the returned value field.
          Original immutable payloads remain inspectable in Events.
        </p>
      )}
      {complete === false && (
        <p className="notice">
          Source/clock discovery is incomplete. The reported choices do not
          establish every available identity.
        </p>
      )}
      {error && (
        <p role="alert" className="field-error">
          {error}
        </p>
      )}
      <div className="evidence-filter-actions">
        <button className="button" disabled={loading}>
          Apply evidence filters
        </button>
        <button
          className="button"
          type="button"
          onClick={() => {
            const clean = emptyFilters();
            setDraft(clean);
            setError("");
            setElement("");
            onApply(clean, "");
          }}
        >
          Reset evidence filters
        </button>
      </div>
    </form>
  );
}
