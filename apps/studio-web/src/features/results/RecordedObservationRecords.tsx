import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { Data, RunEvent } from "../../api/types";
import { receipt, sourceTime } from "./evidenceFilters";
import "./recordedObservationRecords.css";

const PAGE_SIZE = 20;
const DISPLAY_CHARACTERS = 65536;
/** Original event payloads; never a signal decoder, clock mapping or runtime. */
export function RecordedObservationRecords({ runId, snapshotId, query, fieldFilter }: {
  runId: string; snapshotId: string; query: string; fieldFilter: boolean;
}) {
  const [page, setPage] = useState<Data | null>(null),
    [loading, setLoading] = useState(false), [error, setError] = useState(""),
    [opened, setOpened] = useState(false), [position, setPosition] = useState(0),
    [playing, setPlaying] = useState(false), [trail, setTrail] = useState([""]);
  const request = useRef<AbortController | null>(null),
    recordDisplay = useRef<HTMLPreElement | null>(null),
    refreshButton = useRef<HTMLButtonElement | null>(null),
    focusEpoch = useRef(0),
    focusIntent = useRef<{ origin: HTMLElement; epoch: number } | null>(null);
  useEffect(() => {
    const moved = (event: Event) => {
      if (event.type !== "focusin" || event.target !== document.body) focusEpoch.current++;
    };
    for (const name of ["focusin", "keydown", "pointerdown"]) document.addEventListener(name, moved, true);
    return () => {
      request.current?.abort(); request.current = null; focusIntent.current = null;
      for (const name of ["focusin", "keydown", "pointerdown"]) document.removeEventListener(name, moved, true);
    };
  }, []);
  useLayoutEffect(() => {
    if (!page && !error) return;
    const intent = focusIntent.current;
    focusIntent.current = null;
    if (!intent || intent.epoch !== focusEpoch.current || !document.hasFocus() ||
        (document.activeElement !== document.body && document.activeElement !== intent.origin)) return;
    if (intent.origin.isConnected && !intent.origin.matches(":disabled")) intent.origin.focus();
    else (recordDisplay.current || refreshButton.current)?.focus();
  }, [page, error]);
  const records: RunEvent[] = page?.items || [];
  const record = records[position];
  const encoded = record ? JSON.stringify(record, null, 2) : "";
  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => {
      if (position + 1 >= records.length) setPlaying(false);
      else setPosition(position + 1);
    }, 500);
    return () => clearTimeout(timer);
  }, [playing, position, records.length]);
  async function load(nextTrail = [""]) {
    const origin = document.activeElement;
    focusIntent.current = origin instanceof HTMLElement ? { origin, epoch: focusEpoch.current } : null;
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    setOpened(true); setPlaying(false); setLoading(true); setError(""); setPage(null); setPosition(0);
    const selectors = new URLSearchParams(query);
    selectors.set("limit", String(PAGE_SIZE)); selectors.set("type", "observation.available");
    const cursor = nextTrail.at(-1)!;
    if (cursor) selectors.set("cursor", cursor);
    let timedOut = false;
    const deadline = setTimeout(() => { timedOut = true; controller.abort(); }, 15000);
    try {
      const result = await api(`/runs/${runId}/history?${selectors}`, { signal: controller.signal });
      if (controller.signal.aborted || request.current !== controller) return;
      const ids = new Set<string>();
      const incompatibleRecord = (row: Data) => {
        if (!row || typeof row !== "object" || row.type !== "observation.available" ||
            row.runId !== runId || row.snapshotId !== snapshotId ||
            typeof row.eventId !== "string" || !row.eventId || ids.has(row.eventId)) return true;
        ids.add(row.eventId);
        return false;
      };
      if (!Array.isArray(result.items) || result.items.length > PAGE_SIZE ||
          !["valid", "invalid", "unavailable", "unknown"].includes(result.integrity) ||
          result.items.some(incompatibleRecord) ||
          (result.nextCursor !== null && (typeof result.nextCursor !== "string" ||
            !result.nextCursor || result.nextCursor.length > 2048 || nextTrail.includes(result.nextCursor))) ||
          (result.nextCursor !== null && !result.items.length) ||
          !Number.isSafeInteger(result.counts?.matchedRecords) || result.counts.matchedRecords < result.items.length ||
          result.counts.returnedRecords !== result.items.length ||
          result.counts.omittedRecords !== result.counts.matchedRecords - result.items.length)
        throw new Error("The reader returned an incompatible original-record page. Refresh to read the original evidence again.");
      setPage(result); setTrail(nextTrail);
    } catch (problem) {
      if (request.current === controller && (!controller.signal.aborted || timedOut))
        setError(timedOut ? "The original-record read timed out. Refresh to try again." :
          problem instanceof Error ? problem.message : "Original records unavailable.");
    } finally {
      clearTimeout(deadline);
      if (request.current === controller) { setLoading(false); request.current = null; }
    }
  }
  const move = (next: number) => { setPlaying(false); setPosition(next); };
  const time = record ? sourceTime(record) : null;
  return (
    <section className="original-records" role="region" aria-label="Original observation records" aria-busy={loading}>
      <h4>Original observation records</h4>
      <p>Inspect original payloads in journal order. Playback uses a 500 ms display interval;
        it does not reproduce source timing, align clocks or run a workload. Receipt time is not simulation time.</p>
      {fieldFilter ? <p>Clear the signal-field filter to inspect opaque original payloads. Their fields have no admitted signal interpretation.</p> : <>
        <button ref={refreshButton} className="small-button" disabled={loading} onClick={() => void load()}>
          {opened ? "Refresh original records" : "Load original observation records"}
        </button>
        {loading && <p role="status">Loading original observation records…</p>}
        {error && <p role="alert" className="notice error">{error}</p>}
        {page && <>
          <p>{records.length} of {page.counts.matchedRecords} matching records on this page;
            {" "}{page.counts.omittedRecords} records are outside this page. Integrity: {page.integrity}.</p>
          {page.integrity !== "valid" && <p className="notice">Original integrity is {page.integrity}. Automatic playback is unavailable; inspection does not establish valid evidence.</p>}
          {!record ? <p>No original observation records match these history selectors.</p> : <>
            <div className="button-row">
              <button className="small-button" disabled={position === 0} onClick={() => move(position - 1)}>Previous record</button>
              <button className="small-button" disabled={position + 1 >= records.length} onClick={() => move(position + 1)}>Next record</button>
              <button className="small-button" disabled={page.integrity !== "valid"} onClick={() => {
                if (!playing && position + 1 >= records.length) setPosition(0);
                setPlaying(!playing);
              }}>{playing ? "Pause payload playback" : "Play recorded payloads"}</button>
            </div>
            <p role="status" aria-live="polite">Record {position + 1} of {records.length} on this page.</p>
            <dl className="key-values">
              <div><dt>Event</dt><dd>{record.eventId}</dd></div>
              <div><dt>Source time</dt><dd>{time ? `${time.domain}: ${time.raw}` : "Source time unavailable"}</dd></div>
              <div><dt>Receipt UTC</dt><dd>{receipt(record, page.presentation).label}</dd></div>
            </dl>
            {encoded.length > DISPLAY_CHARACTERS && <p className="notice">Displaying the first {DISPLAY_CHARACTERS} characters. The complete immutable record remains in the source journal.</p>}
            <div className="json-details"><pre ref={recordDisplay} tabIndex={0} aria-label="Original observation record JSON" data-original-record>{encoded.slice(0, DISPLAY_CHARACTERS)}</pre></div>
          </>}
          <div className="history-pagination">
            <button className="small-button" disabled={loading || trail.length < 2} onClick={() => void load(trail.slice(0, -1))}>Previous payload page</button>
            <button className="small-button" disabled={loading || !page.nextCursor || trail.length >= 128} onClick={() => void load([...trail, page.nextCursor])}>Next payload page</button>
          </div>
          {trail.length >= 128 && page.nextCursor && <p>Page history reached its 128-page display bound. Refresh to begin again; original evidence is retained.</p>}
        </>}
      </>}
    </section>
  );
}
