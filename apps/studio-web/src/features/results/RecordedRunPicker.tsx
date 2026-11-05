import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { Data, Run } from "../../api/types";

const PAGE_SIZE = 200;

/** Retained metadata is selectable without a browser-local last-run preference. */
export function RecordedRunPicker({ projectId, run, onSelect }: {
  projectId: string;
  run: Run | null;
  onSelect: (run: Run) => void;
}) {
  const [page, setPage] = useState<{ items: Run[]; cursor: string; next: string | null }>({ items: [], cursor: "", next: null });
  const [loading, setLoading] = useState(true), [error, setError] = useState("");
  const request = useRef<AbortController | null>(null);
  async function load(cursor = "") {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setLoading(true); setError("");
    let timedOut = false;
    const deadline = setTimeout(() => { timedOut = true; controller.abort(); }, 15000);
    try {
      const query = new URLSearchParams({ projectId, limit: String(PAGE_SIZE) });
      if (cursor) query.set("cursor", cursor);
      const result = await api<Data>(`/runs?${query}`, { signal: controller.signal });
      if (controller.signal.aborted || request.current !== controller) return;
      const ids = new Set<string>();
      if (!result || typeof result !== "object" || !Array.isArray(result.items) || result.items.length > PAGE_SIZE || result.items.some((item: Data) => {
        if (!item || item.projectId !== projectId || typeof item.runId !== "string" || !item.runId ||
            typeof item.snapshotId !== "string" || !item.snapshotId || typeof item.state !== "string" ||
            ids.has(item.runId)) return true;
        ids.add(item.runId);
        return false;
      }) || (result.nextCursor !== null && (typeof result.nextCursor !== "string" ||
          !/^\d{1,16}$/.test(result.nextCursor) || !Number.isSafeInteger(Number(result.nextCursor)) || Number(result.nextCursor) <= Number(cursor || "0") ||
          result.items.length !== PAGE_SIZE))) {
        throw new Error("The retained run list is incompatible with this project. Refresh recorded runs to try again.");
      }
      setPage({ items: result.items, cursor, next: result.nextCursor });
    } catch (problem) {
      if (request.current === controller && (!controller.signal.aborted || timedOut))
        setError(timedOut ? "The retained run list timed out. Refresh recorded runs to try again." :
          problem instanceof Error ? problem.message : "The retained run list is unavailable. Refresh recorded runs to try again.");
    } finally {
      clearTimeout(deadline);
      if (request.current === controller) setLoading(false);
    }
  }
  useEffect(() => {
    void load();
    return () => { request.current?.abort(); request.current = null; };
  }, [projectId]);
  const selected = run?.projectId === projectId ? run : null;
  const options = [...new Map([...page.items, ...(selected ? [selected] : [])].map(item => [item.runId, item])).values()];
  return (
    <div className="recorded-run-picker" role="group" aria-label="Recorded runs" aria-busy={loading}>
      <label>
        Recorded run
        <select aria-label="Recorded run" value={selected?.runId || ""} disabled={loading || !options.length}
          onChange={event => {
            const chosen = options.find(item => item.runId === event.target.value && item.projectId === projectId);
            if (chosen && !loading) onSelect(chosen);
          }}>
          <option value="" disabled>Choose a recorded run</option>
          {options.map(item => <option key={item.runId} value={item.runId}>{item.runId} · {item.state}</option>)}
        </select>
      </label>
      <div className="form-actions">
        <button className="button" aria-disabled={loading} onClick={() => { if (!loading) void load(); }}>Refresh recorded runs</button>
        <button className="button" aria-disabled={loading || !page.cursor} onClick={() => { if (!loading && page.cursor) void load(); }}>First recorded run page</button>
        <button className="button" aria-disabled={loading || page.next === null} onClick={() => { if (!loading && page.next !== null) void load(page.next); }}>Next recorded run page</button>
      </div>
      <p role="status">{loading ? "Loading recorded runs…" : error ? `Recorded run list unavailable.${page.items.length ? " Previously loaded choices are retained." : ""}` :
        page.items.length ? `${page.items.length} recorded run(s) on this page.${page.next ? " More recorded runs are available." : ""}` : "No recorded runs for this project."}</p>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
