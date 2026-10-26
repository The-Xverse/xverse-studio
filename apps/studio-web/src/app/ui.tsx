import { useLayoutEffect, useRef, type ReactNode } from "react";
import type { Data, Diagnostic } from "../api/types";
export function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    home: (
      <>
        <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" />
      </>
    ),
    model: (
      <>
        <rect x="8" y="2" width="8" height="6" rx="1.5" />
        <rect x="2" y="16" width="8" height="6" rx="1.5" />
        <rect x="14" y="16" width="8" height="6" rx="1.5" />
        <path d="M12 8v4M6 16v-4h12v4" />
      </>
    ),
    connection: (
      <>
        <circle cx="5" cy="6" r="3" />
        <circle cx="19" cy="18" r="3" />
        <path d="M8 6h6a5 5 0 0 1 5 5v4M16 18h-6a5 5 0 0 1-5-5V9" />
      </>
    ),
    deployment: (
      <>
        <path d="m12 2 10 5-10 5L2 7Z M2 12l10 5 10-5 M2 17l10 5 10-5" />
      </>
    ),
    experiment: (
      <>
        <path d="M9 3h6M10 3v6L4 19a1.5 1.5 0 0 0 1.3 2h13.4a1.5 1.5 0 0 0 1.3-2L14 9V3M7 15h10" />
      </>
    ),
    results: (
      <>
        <path d="M3 3v18h18M7 15l4-6 4 4 6-9" />
      </>
    ),
    catalog: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    lab: (
      <>
        <rect x="3" y="7" width="18" height="12" rx="2" />
        <path d="M7 7V3h10v4M7 11h4M7 15h4M16 11v4" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    play: <path d="m8 4 12 8-12 8Z" />,
    check: <path d="m5 12 4 4L19 6" />,
    chevron: <path d="m9 5 7 7-7 7" />,
    back: <path d="m15 5-7 7 7 7" />,
    code: (
      <>
        <path d="m8 6-6 6 6 6M16 6l6 6-6 6M14 3l-4 18" />
      </>
    ),
    close: <path d="m6 6 12 12M6 18 18 6" />,
    search: (
      <>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m16 16 5 5" />
      </>
    ),
    download: (
      <>
        <path d="M12 3v12m-5-5 5 5 5-5M3 16v5h18v-5" />
      </>
    ),
    upload: (
      <>
        <path d="M12 17V5m-5 5 5-5 5 5M3 16v5h18v-5" />
      </>
    ),
    refresh: (
      <>
        <path d="M20 7a9 9 0 1 0 1 9M20 2v6h-6" />
      </>
    ),
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v6M12 7h.01" />
      </>
    ),
    folder: <path d="M3 5h6l2 3h10v12H3Z" />,
    stop: <rect x="5" y="5" width="14" height="14" rx="1" />,
    settings: (
      <>
        <path d="M5 5h14M5 12h14M5 19h14" />
        <circle cx="9" cy="5" r="2" />
        <circle cx="15" cy="12" r="2" />
        <circle cx="9" cy="19" r="2" />
      </>
    ),
  };
  return (
    <svg
      aria-hidden="true"
      data-icon={name}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name] || paths.model}
    </svg>
  );
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function statusTone(status: unknown) {
  return [
    "running",
    "ready",
    "complete",
    "completed",
    "valid",
    "pass",
    "connected",
  ].includes(String(status))
    ? "success"
    : ["failed", "error", "invalid", "fail", "blocked"].includes(String(status))
      ? "danger"
      : [
            "unknown",
            "partial",
            "indeterminate",
            "unavailable",
            "reconciling",
          ].includes(String(status))
        ? "warning"
        : "neutral";
}
export function Json({
  value,
  expanded = false,
}: {
  value: unknown;
  expanded?: boolean;
}) {
  return (
    <details className="json-details" open={expanded}>
      <summary>Inspect exact data</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}
export function Empty({
  title,
  children,
  icon = "info",
}: {
  title: string;
  children: ReactNode;
  icon?: string;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon name={icon} size={27} />
      </span>
      <h3>{title}</h3>
      <div>{children}</div>
    </div>
  );
}
export function Diagnostics({
  diagnostics = [],
}: {
  diagnostics?: Diagnostic[];
}) {
  if (!diagnostics.length) return null;
  return (
    <ul className="diagnostic-list">
      {diagnostics.map((d, i) => (
        <li key={i} className={d.severity === "error" ? "error" : ""}>
          <strong>{d.code}</strong>
          <span>{d.message}</span>
          {d.elementRef && (
            <code>
              {typeof d.elementRef === "string"
                ? d.elementRef
                : JSON.stringify(d.elementRef)}
            </code>
          )}
          {d.remediation && <small>{d.remediation}</small>}
        </li>
      ))}
    </ul>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
  restoreFocusSelector,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
  restoreFocusSelector?: string;
}) {
  const returnFocus = useRef(document.activeElement as HTMLElement | null),
    section = useRef<HTMLElement | null>(null),
    close = useRef(onClose);
  close.current = onClose;
  useLayoutEffect(() => {
    const handle = (event: KeyboardEvent) => {
      const dialogs = document.querySelectorAll(
        '[role="dialog"][aria-modal="true"]',
      );
      if (dialogs[dialogs.length - 1] !== section.current) return;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        close.current();
      }
      if (event.key === "Tab") {
        const nodes = section.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled),input:not([type=hidden]):not(:disabled),select:not(:disabled),textarea:not(:disabled),summary,a[href],[tabindex="0"]',
        );
        const visible = Array.from(nodes || []).filter(
            (node) => node.getClientRects().length,
          ),
          first = visible[0],
          last = visible[visible.length - 1];
        if (
          !section.current?.contains(document.activeElement) ||
          (event.shiftKey && document.activeElement === first)
        ) {
          event.preventDefault();
          (event.shiftKey ? last : first)?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handle, true);
    return () => {
      document.removeEventListener("keydown", handle, true);
      // StrictMode simulates cleanup while the dialog is still connected.
      queueMicrotask(() => {
        if (section.current?.isConnected) return;
        const target = restoreFocusSelector
          ? document.querySelector<HTMLElement>(restoreFocusSelector)
          : returnFocus.current;
        target?.focus();
      });
    };
  }, []);
  return (
    <div className="modal-scrim" onClick={onClose}>
      <section
        ref={section}
        className={`modal ${wide ? "wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        aria-labelledby="modal-heading"
        onClick={(e) => e.stopPropagation()}
      >
        <header>
          <h2 id="modal-heading">{title}</h2>
          <button
            autoFocus
            className="icon-button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <Icon name="close" />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
export function KeyValues({ values }: { values: Data }) {
  return (
    <dl className="key-values">
      {Object.entries(values).map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>
            {typeof value === "object"
              ? JSON.stringify(value)
              : String(value ?? "Unknown")}
          </dd>
        </div>
      ))}
    </dl>
  );
}
