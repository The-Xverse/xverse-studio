import type { Data, RunEvent } from "../../api/types";
import {
  canonicalEvent,
  cursorValue,
  recoveryValue,
  streamControl,
  SseParser,
  ZERO_DIGEST,
  MAX_RECOVERY,
  type Recovery,
  type StreamControl,
} from "./sessionProtocol";
export { mergeRun } from "./sessionProtocol";
export type { Recovery, StreamControl } from "./sessionProtocol";
type Options = {
  snapshotId?: string;
  onControl?: (control: StreamControl) => void | Promise<void>;
};
/** One read-only session. Only successful consumer acceptance acknowledges a cursor. */
export function subscribe(
  runId: string,
  onEvent: (event: RunEvent) => void | Promise<void>,
  onState: (state: string) => void,
  onRecovery: (recovery: Recovery) => void | Promise<void>,
  options: Options = {},
) {
  const controller = new AbortController();
  let stopped = false,
    cursor = "",
    sequence = 0n,
    lastDigest = ZERO_DIGEST,
    snapshotId = options.snapshotId;
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined,
    jsonReader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let pendingRecovery: StreamControl | undefined;
  const seen = new Map<string, { sequence: string; digest: string }>();
  const current = () => !stopped && !controller.signal.aborted;
  const state = (value: string) => {
    if (current()) onState(value);
  };
  async function sleep(ms: number) {
    if (!current()) return;
    await new Promise<void>((resolve) => {
      const finish = () => {
        clearTimeout(timer);
        controller.signal.removeEventListener("abort", finish);
        resolve();
      };
      const timer = setTimeout(finish, ms);
      controller.signal.addEventListener("abort", finish, { once: true });
      if (controller.signal.aborted) finish();
    });
  }
  async function readJson(response: Response): Promise<Data> {
    if (!response.body) throw Error("Recovery body unavailable");
    const body = response.body.getReader();
    jsonReader = body;
    const chunks: Uint8Array[] = [];
    let size = 0;
    try {
      while (current()) {
        const part = await body.read();
        if (part.done) break;
        size += part.value.byteLength;
        if (size > MAX_RECOVERY)
          throw Error("Recovery response limit exceeded");
        chunks.push(part.value);
      }
      if (!current()) throw Error("Session disposed");
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const c of chunks) {
        bytes.set(c, offset);
        offset += c.byteLength;
      }
      return JSON.parse(
        new TextDecoder("utf-8", { fatal: true }).decode(bytes),
      );
    } finally {
      await body.cancel().catch(() => {});
      body.releaseLock();
      jsonReader = undefined;
    }
  }
  function problem(reason: string): StreamControl {
    return {
      streamVersion: "1.1",
      type: "stream.resync_required",
      runId,
      snapshotId: snapshotId || "",
      reason,
      firstMissingSequence: null,
      lastMissingSequence: null,
      missingCount: null,
      integrity: "unavailable",
    };
  }
  async function control(value: StreamControl) {
    if (current()) await options.onControl?.(value);
  }
  async function recover(reason: StreamControl) {
    state("Resynchronizing — state and history pending");
    await control(reason);
    if (!current()) return;
    const response = await fetch(
      `/api/v1/runs/${encodeURIComponent(runId)}/resync`,
      {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      },
    );
    if (response.status === 401) {
      state("Authentication required");
      stopped = true;
      return;
    }
    if (response.status === 413) {
      await response.body?.cancel().catch(() => {});
      state(
        "Recovery presentation limit reached — inspect paged retained history",
      );
      stopped = true;
      return;
    }
    if (response.status === 422) {
      state("Evidence invalid — inspect retained history");
      stopped = true;
      return;
    }
    if (!response.ok) throw Error(`Recovery unavailable (${response.status})`);
    const recovery = recoveryValue(await readJson(response), runId, snapshotId);
    if (!current()) return;
    await onRecovery(recovery);
    if (!current()) return;
    const accepted = cursorValue(
      recovery.resumeCursor,
      runId,
      recovery.snapshotId,
    );
    snapshotId = recovery.snapshotId;
    sequence = BigInt(accepted.q);
    lastDigest = accepted.d;
    cursor = recovery.resumeCursor;
    seen.clear();
    for (const event of recovery.history.items)
      seen.set(event.eventId, {
        sequence: event.sequence,
        digest: event.digest!,
      });
    state("Resynchronized — reconnecting");
  }
  async function accept(frame: {
    id: string;
    event: string;
    data: string;
  }): Promise<"continue" | "recover" | "end"> {
    const data = JSON.parse(frame.data);
    if (frame.event === "studio.stream_control") {
      if (frame.id)
        throw Error(
          "A transport control cannot acknowledge canonical evidence",
        );
      const value = streamControl(data, runId, snapshotId);
      snapshotId = value.snapshotId;
      if (
        value.type === "stream.gap" ||
        value.type === "stream.resync_required"
      ) {
        pendingRecovery = value;
        return "recover";
      }
      await control(value);
      if (value.type === "stream.end") {
        state("Retained history available");
        stopped = true;
        return "end";
      }
      if (value.integrity === "invalid") {
        state("Evidence invalid — inspect retained history");
        stopped = true;
        return "end";
      }
      throw Error(value.reason);
    }
    const event = canonicalEvent(data, runId, snapshotId),
      token = cursorValue(frame.id, runId, event.snapshotId);
    if (frame.event !== "message" && frame.event !== event.type)
      throw Error("SSE kind does not match canonical event");
    if (token.q !== event.sequence || token.d !== event.digest)
      throw Error("Cursor proof does not match canonical event");
    const prior = seen.get(event.eventId),
      q = BigInt(event.sequence);
    if (prior) {
      if (prior.sequence === event.sequence && prior.digest === event.digest)
        return "continue";
      throw Error("Canonical event identity fork");
    }
    if (q !== sequence + 1n || event.previousDigest !== lastDigest)
      throw Error("Event sequence or chain discontinuity");
    await onEvent(event);
    if (!current()) return "end";
    snapshotId = event.snapshotId;
    sequence = q;
    lastDigest = event.digest!;
    cursor = frame.id;
    seen.set(event.eventId, {
      sequence: event.sequence,
      digest: event.digest!,
    });
    if (seen.size > 2000) seen.delete(seen.keys().next().value!);
    return "continue";
  }
  async function run() {
    let delay = 500;
    while (current()) {
      try {
        state(cursor ? "Reconnecting" : "Connecting");
        const query = new URLSearchParams({ streamVersion: "1.1" });
        if (cursor) query.set("after", cursor);
        const response = await fetch(
          `/api/v1/runs/${encodeURIComponent(runId)}/events?${query}`,
          {
            credentials: "same-origin",
            headers: { Accept: "text/event-stream" },
            signal: controller.signal,
          },
        );
        if (!current()) {
          await response.body?.cancel().catch(() => {});
          return;
        }
        if (response.status === 410) {
          const body = await readJson(response);
          await recover({
            ...problem(body.code || "CURSOR_EXPIRED"),
            ...body,
            streamVersion: "1.1",
            type: "stream.resync_required",
            runId,
            snapshotId: snapshotId || body.snapshotId || "",
            missingCount: body.missingCount ?? null,
          });
          continue;
        }
        if (response.status === 401) {
          state("Authentication required");
          return;
        }
        if (response.status === 422) {
          state(
            "Evidence invalid or cursor rejected — inspect retained history",
          );
          return;
        }
        if (
          !response.ok ||
          !response.body ||
          !response.headers.get("Content-Type")?.includes("text/event-stream")
        )
          throw Error(`Stream unavailable (${response.status})`);
        state("Connected");
        reader = response.body.getReader();
        const parser = new SseParser();
        let shouldRecover = false;
        try {
          while (current()) {
            const chunk = await reader.read();
            if (chunk.done) {
              parser.finish();
              break;
            }
            for (const frame of parser.feed(chunk.value)) {
              const action = await accept(frame);
              if (action !== "continue") {
                shouldRecover = action === "recover";
                break;
              }
            }
            if (shouldRecover || !current()) break;
          }
        } catch (error) {
          if (current())
            pendingRecovery = problem(
              error instanceof Error
                ? error.message
                : "Stream continuity unavailable",
            );
          shouldRecover = true;
        } finally {
          await reader.cancel().catch(() => {});
          reader.releaseLock();
          reader = undefined;
        }
        if (shouldRecover && current()) {
          const reason =
            pendingRecovery || problem("Stream continuity unavailable");
          pendingRecovery = undefined;
          await recover(reason);
          continue;
        }
      } catch {
        if (!current()) return;
        state("Disconnected — retrying; acknowledged cursor retained");
      }
      await sleep(delay);
      delay = Math.min(delay * 2, 5000);
    }
  }
  void run();
  return () => {
    if (stopped && controller.signal.aborted) return;
    stopped = true;
    controller.abort();
    void reader?.cancel().catch(() => {});
    void jsonReader?.cancel().catch(() => {});
  };
}
