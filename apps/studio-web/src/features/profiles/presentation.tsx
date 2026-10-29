import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Data } from "../../api/types";
import { Badge } from "../../app/ui";

// Sanitized, inert domain presentation (T062). Terms relabel the shared workflows; they never change
// semantics. Everything renders as plain text; documentation references are shown, never fetched.

export const CORE_TERMS: Record<string, string> = {
  System: "System",
  Element: "Element",
  Flow: "Flow",
  Deployment: "Deployment",
  Scenario: "Scenario",
};

const EMPTY: Data = {
  source: "core",
  labels: CORE_TERMS,
  icons: {},
  formGroups: [],
  domains: [],
  knownDomains: [],
  conflicts: [],
  limitations: [],
};

export const PresentationContext = createContext<Data>(EMPTY);

export function usePresentationData(projectId?: string, revision?: number) {
  const [state, setState] = useState<{ key: string; value: Data } | null>(null);
  const key = `${projectId}:${revision}`;
  useEffect(() => {
    if (!projectId) return;
    const controller = new AbortController();
    api(`/projects/${encodeURIComponent(projectId)}/presentation`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setState({ key, value });
      })
      // Presentation is optional; the core terms remain on any failure.
      .catch(() => undefined);
    return () => controller.abort();
  }, [key]);
  return state?.key === key ? state.value : EMPTY;
}

export function useTerm() {
  const presentation = useContext(PresentationContext);
  return (key: string) => presentation.labels?.[key] || CORE_TERMS[key] || key;
}

/** The domain a namespace belongs to, among all admitted domain presentations. */
export function useDomainOf() {
  const presentation = useContext(PresentationContext);
  return (namespace?: string) =>
    (presentation.knownDomains || []).find((d: Data) =>
      (d.namespaces || []).includes(namespace),
    )?.domain as string | undefined;
}

export function DomainBadge() {
  const presentation = useContext(PresentationContext);
  if (!presentation.domains?.length) return null;
  const names = presentation.domains.map((d: Data) => d.domain).join(" + ");
  const detail = [
    presentation.source === "bound"
      ? "Bound domain presentation"
      : "Blueprint default presentation (not bound)",
    presentation.conflicts?.length
      ? `core terms kept for ${presentation.conflicts.join(", ")}`
      : "",
    ...(presentation.limitations || []),
  ]
    .filter(Boolean)
    .join(". ");
  return (
    <span className="domain-badge" title={detail}>
      <Badge tone="neutral">{names} terms</Badge>
      <span className="visually-hidden">{detail}</span>
    </span>
  );
}

/** Terminology preview for a domain presentation profile in the profile list. */
export function PresentationPreview({ presentation }: { presentation: Data }) {
  if (!presentation?.domain) return null;
  return (
    <div className="presentation-preview">
      <p>
        Domain <strong>{presentation.domain}</strong>: terminology only; it
        never changes semantics or execution.
      </p>
      <ul>
        {Object.entries(presentation.labels || {}).map(([core, term]) => (
          <li key={core}>
            {core} → {String(term)}
          </li>
        ))}
      </ul>
      {presentation.documentation && (
        <p className="field-hint">
          Documentation reference (not fetched):{" "}
          <code>{presentation.documentation}</code>
        </p>
      )}
    </div>
  );
}
