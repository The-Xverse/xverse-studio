import type { Data, Run, RunEvent } from "../../api/types";
export const ZERO_DIGEST = "0".repeat(64);
export const MAX_FRAME = 262144,
  MAX_RECOVERY = 1048576;
const sequence = /^(?:0|[1-9][0-9]*)$/;
const digest = /^[a-f0-9]{64}$/;
export const eventKinds = new Set([
  "command.accepted",
  "command.delegated",
  "command.completed",
  "command.rejected",
  "command.failed",
  "command.unknown",
  "run.state_changed",
  "run.reconciling",
  "run.ownership_unknown",
  "element.state_changed",
  "readiness.observed",
  "connection.observed",
  "log.appended",
  "observation.available",
  "observation.gap",
  "fault.activation_requested",
  "fault.activation_observed",
  "fault.recovery_observed",
  "cleanup.updated",
  "evidence.updated",
  "evaluation.updated",
  "stream.gap",
  "stream.resync_required",
  "capabilities.changed",
]);
export type Cursor = { r: string; s: string; q: string; d: string };
export type StreamControl = Data & {
  streamVersion: "1.1";
  type: "stream.gap" | "stream.resync_required" | "stream.error" | "stream.end";
  runId: string;
  snapshotId: string;
  missingCount: number | null;
  reason: string;
};
export type Recovery = Data & {
  streamVersion: "1.1";
  run: Run;
  snapshotId: string;
  history: {
    items: RunEvent[];
    nextCursor: null;
    integrity: string;
    omittedRecords: number;
  };
  resumeCursor: string;
  watermark: { sequence: string; digest: string };
};
export function validSequence(value: unknown): value is string {
  return (
    typeof value === "string" && value.length <= 32 && sequence.test(value)
  );
}
export function cursorValue(
  value: string,
  runId: string,
  snapshotId?: string,
): Cursor {
  if (
    !value.startsWith("st1.") ||
    value.length > 2048 ||
    !/^[-_a-zA-Z0-9]+$/.test(value.slice(4))
  )
    throw Error("Incompatible resumable cursor");
  const raw = atob(value.slice(4).replaceAll("-", "+").replaceAll("_", "/"));
  const parsed = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(
      Uint8Array.from(raw, (c) => c.charCodeAt(0)),
    ),
  );
  if (
    !parsed ||
    Object.keys(parsed).sort().join(",") !== "d,q,r,s" ||
    parsed.r !== runId ||
    typeof parsed.s !== "string" ||
    !parsed.s ||
    parsed.s.length > 512 ||
    (snapshotId !== undefined && parsed.s !== snapshotId) ||
    !validSequence(parsed.q) ||
    typeof parsed.d !== "string" ||
    !digest.test(parsed.d)
  )
    throw Error("Cursor context or proof is incompatible");
  return parsed;
}
export function canonicalEvent(
  value: Data,
  runId: string,
  snapshotId?: string,
): RunEvent {
  if (
    !value ||
    value.schemaVersion !== "1.0" ||
    value.runId !== runId ||
    typeof value.snapshotId !== "string" ||
    !value.snapshotId ||
    (snapshotId !== undefined && value.snapshotId !== snapshotId) ||
    typeof value.eventId !== "string" ||
    !value.eventId ||
    value.eventId.length > 512 ||
    !validSequence(value.sequence) ||
    !eventKinds.has(value.type) ||
    !value.payload ||
    typeof value.payload !== "object" ||
    Array.isArray(value.payload) ||
    typeof value.digest !== "string" ||
    !digest.test(value.digest) ||
    typeof value.previousDigest !== "string" ||
    !digest.test(value.previousDigest)
  )
    throw Error("Canonical stream envelope, context or proof is incompatible");
  return value as RunEvent;
}
export function streamControl(
  value: Data,
  runId: string,
  snapshotId?: string,
): StreamControl {
  if (
    !value ||
    value.streamVersion !== "1.1" ||
    ![
      "stream.gap",
      "stream.resync_required",
      "stream.error",
      "stream.end",
    ].includes(value.type) ||
    value.runId !== runId ||
    typeof value.snapshotId !== "string" ||
    !value.snapshotId ||
    (snapshotId !== undefined && value.snapshotId !== snapshotId) ||
    typeof value.reason !== "string" ||
    (value.missingCount !== null &&
      (!Number.isSafeInteger(value.missingCount) || value.missingCount < 0))
  )
    throw Error("Transport control context is incompatible");
  for (const key of ["firstMissingSequence", "lastMissingSequence"])
    if (
      value[key] !== null &&
      value[key] !== undefined &&
      !validSequence(value[key])
    )
      throw Error("Transport loss boundary is incompatible");
  return value as StreamControl;
}
export function recoveryValue(
  value: Data,
  runId: string,
  snapshotId?: string,
): Recovery {
  if (
    value?.streamVersion !== "1.1" ||
    value.run?.runId !== runId ||
    value.snapshotId !== value.run?.snapshotId ||
    (snapshotId !== undefined && value.snapshotId !== snapshotId) ||
    !Number.isSafeInteger(value.run.stateVersion) ||
    value.run.stateVersion < 0 ||
    !Array.isArray(value.history?.items) ||
    value.history.items.length > 200 ||
    value.history.nextCursor !== null ||
    !["valid", "verified_prefix"].includes(value.history.integrity) ||
    !Number.isSafeInteger(value.history.omittedRecords) ||
    value.history.omittedRecords < 0
  )
    throw Error("Bounded recovery source is unavailable or invalid");
  const cursor = cursorValue(value.resumeCursor, runId, value.snapshotId);
  if (
    value.watermark?.sequence !== cursor.q ||
    value.watermark?.digest !== cursor.d
  )
    throw Error("Recovery watermark does not match the resume cursor");
  let previous: RunEvent | undefined;
  const ids = new Set<string>();
  for (const raw of value.history.items) {
    const event = canonicalEvent(raw, runId, value.snapshotId);
    if (
      ids.has(event.eventId) ||
      BigInt(event.sequence) > BigInt(cursor.q) ||
      (previous && BigInt(event.sequence) <= BigInt(previous.sequence)) ||
      (previous &&
        BigInt(event.sequence) === BigInt(previous.sequence) + 1n &&
        event.previousDigest !== previous.digest)
    )
      throw Error("Recovery history is not an ordered verified tail");
    ids.add(event.eventId);
    previous = event;
  }
  if (previous?.sequence === cursor.q && previous.digest !== cursor.d)
    throw Error("Recovery tail proof does not match watermark");
  return value as Recovery;
}
/** Fresh non-state facets may advance independently; lifecycle never regresses. */
export function mergeRun(current: Run | null, candidate: Run): Run | null {
  if (
    !current ||
    candidate.runId !== current.runId ||
    candidate.snapshotId !== current.snapshotId ||
    !Number.isSafeInteger(candidate.stateVersion) ||
    candidate.stateVersion < current.stateVersion
  )
    return current;
  if (candidate.stateVersion > current.stateVersion) return candidate;
  const observed = (run: Run): number =>
    Number.isSafeInteger(run.observationVersion) && run.observationVersion >= 0
      ? run.observationVersion
      : -1;
  const priorObservation = observed(current),
    nextObservation = observed(candidate);
  if (nextObservation > priorObservation) return candidate;
  if (nextObservation < priorObservation) return current;
  return {
    ...current,
    ...candidate,
    state: current.state,
    status: current.status,
    stateVersion: current.stateVersion,
  };
}
export type SseFrame = { id: string; event: string; data: string };
/** Per-frame bounds apply before JSON parsing; CRLF may cross arbitrary chunks. */
export class SseParser {
  private decoder = new TextDecoder("utf-8", { fatal: true });
  private buffer = "";
  private frameBytes = 0;
  private id = "";
  private event = "message";
  private data: string[] = [];
  feed(chunk: Uint8Array): SseFrame[] {
    if (chunk.byteLength > MAX_RECOVERY)
      throw Error("Stream read buffer limit exceeded");
    this.buffer += this.decoder.decode(chunk, { stream: true });
    const frames: SseFrame[] = [];
    let total = 0,
      canonicalFrames = 0,
      controls = 0;
    while (true) {
      const at = this.buffer.search(/[\r\n]/);
      if (at < 0 || (this.buffer[at] === "\r" && at === this.buffer.length - 1))
        break;
      const width =
          this.buffer[at] === "\r" && this.buffer[at + 1] === "\n" ? 2 : 1,
        line = this.buffer.slice(0, at);
      this.buffer = this.buffer.slice(at + width);
      this.frameBytes += new TextEncoder().encode(line).byteLength + width;
      if (this.frameBytes > MAX_FRAME)
        throw Error("Event frame limit exceeded");
      if (line === "") {
        if (this.data.length) {
          const frame = {
            id: this.id,
            event: this.event,
            data: this.data.join("\n"),
          };
          total += new TextEncoder().encode(frame.data).byteLength;
          frames.push(frame);
          if (frame.event === "studio.stream_control") controls++;
          else canonicalFrames++;
          if (canonicalFrames > 200 || controls > 1 || total > MAX_RECOVERY)
            throw Error("Presentation read queue limit exceeded");
        }
        this.id = "";
        this.event = "message";
        this.data = [];
        this.frameBytes = 0;
        continue;
      }
      if (line.startsWith(":")) continue;
      const colon = line.indexOf(":"),
        name = colon < 0 ? line : line.slice(0, colon);
      let value = colon < 0 ? "" : line.slice(colon + 1);
      if (value.startsWith(" ")) value = value.slice(1);
      if (name === "data") this.data.push(value);
      else if (name === "event") this.event = value;
      else if (name === "id") {
        if (value.includes("\0")) throw Error("Invalid SSE cursor");
        this.id = value;
      }
    }
    if (
      this.frameBytes + new TextEncoder().encode(this.buffer).byteLength >
      MAX_FRAME
    )
      throw Error("Event frame limit exceeded");
    return frames;
  }
  finish() {
    this.buffer += this.decoder.decode();
    if (this.buffer || this.data.length)
      throw Error("Incomplete event frame; acknowledged cursor preserved");
  }
}
