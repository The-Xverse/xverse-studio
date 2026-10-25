import type { Data, RunEvent } from "../../api/types";
export type EvidenceFilters = {
  sourceProviderId: string;
  observerRef: string;
  field: string;
  timeBasis: "none" | "source" | "recorded";
  clockDomain: string;
  startTick: string;
  endTick: string;
  recordedFrom: string;
  recordedUntil: string;
};
export const emptyFilters = (): EvidenceFilters => ({
  sourceProviderId: "",
  observerRef: "",
  field: "",
  timeBasis: "none",
  clockDomain: "",
  startTick: "",
  endTick: "",
  recordedFrom: "",
  recordedUntil: "",
});
export function tick(value: unknown): bigint | null {
  return typeof value === "string" &&
    value.length <= 32 &&
    /^-?(?:0|[1-9][0-9]*)$/.test(value)
    ? BigInt(value)
    : null;
}
export function sourceTime(
  sample: Data,
): { tick: bigint; raw: string; domain: string } | null {
  const t = sample.sourceTime,
    parsed = tick(t?.tick),
    domain = t?.clockDomain ?? t?.clockDomainRef;
  return parsed !== null && typeof domain === "string" && domain
    ? { tick: parsed, raw: t.tick, domain }
    : null;
}
function utc(value: string): bigint | null {
  const match =
    /^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(?:\.(\d{1,6}))?(Z|[+-]\d\d:\d\d)$/.exec(
      value,
    );
  if (!match) return null;
  const [, year, month, day, hour, minute, second, fraction, zone] = match;
  const y = Number(year),
    m = Number(month),
    d = Number(day),
    h = Number(hour),
    min = Number(minute),
    sec = Number(second);
  const leap = y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (
    y < 1 ||
    m < 1 ||
    m > 12 ||
    d < 1 ||
    d > days[m - 1] ||
    h > 23 ||
    min > 59 ||
    sec > 59
  )
    return null;
  if (
    zone !== "Z" &&
    (Number(zone.slice(1, 3)) > 23 || Number(zone.slice(4)) > 59)
  )
    return null;
  const base = Date.parse(
    `${year}-${month}-${day}T${hour}:${minute}:${second}${zone}`,
  );
  return Number.isFinite(base)
    ? BigInt(base) * 1000000n + BigInt((fraction || "").padEnd(9, "0"))
    : null;
}
export function validateFilters(value: EvidenceFilters): string {
  if (value.timeBasis === "source") {
    if (!value.clockDomain)
      return "Select an original source clock. Receipt time is a separate basis.";
    if (!!value.startTick !== !!value.endTick)
      return "Supply both source boundaries, or leave both empty for the selected clock.";
    if (
      value.startTick &&
      (tick(value.startTick) === null || tick(value.endTick) === null)
    )
      return "Ticks must be signed decimal integers of at most 32 characters.";
    if (value.startTick && tick(value.startTick)! >= tick(value.endTick)!)
      return "The source window must be nonempty: start is inclusive and end is exclusive.";
  }
  if (value.timeBasis === "recorded") {
    const start = utc(value.recordedFrom),
      end = utc(value.recordedUntil);
    if (start === null || end === null)
      return "Supply RFC3339 receipt boundaries with an explicit timezone, for example 2026-10-25T12:00:00Z.";
    if (start >= end)
      return "The receipt window must be nonempty: start is inclusive and end is exclusive.";
  }
  return "";
}
export function queryFilters(
  value: EvidenceFilters,
  selected: string,
  observation: boolean,
): URLSearchParams {
  const query = new URLSearchParams({ limit: "200" });
  for (const key of ["sourceProviderId", "observerRef"] as const)
    if (value[key]) query.set(key, value[key]);
  if (observation && value.field) query.set("field", value.field);
  if (selected) query.set("elementRef", selected);
  if (value.timeBasis === "source") {
    query.set("clockDomain", value.clockDomain);
    if (value.startTick) {
      query.set("startTick", value.startTick);
      query.set("endTick", value.endTick);
    }
  }
  if (value.timeBasis === "recorded") {
    query.set("recordedFrom", value.recordedFrom);
    query.set("recordedUntil", value.recordedUntil);
  }
  return query;
}
export function receipt(
  event: Data,
  presentation: Data = {},
): { utc: string | null; label: string; encoding: string } {
  const meta = presentation[event.eventId];
  // A projected unavailable timestamp is authoritative; raw data cannot override it.
  const stamp =
    meta !== undefined
      ? meta?.receiptEncoding !== "unavailable" &&
        typeof meta?.recordedAtUtc === "string" &&
        utc(meta.recordedAtUtc) !== null
        ? meta.recordedAtUtc
        : null
      : typeof event.recordedAt === "string" && utc(event.recordedAt) !== null
        ? event.recordedAt
        : null;
  return {
    utc: stamp,
    label: stamp || "Receipt time unavailable",
    encoding: meta?.receiptEncoding || (stamp ? "rfc3339" : "unavailable"),
  };
}
export function liveMatches(
  event: RunEvent,
  filters: EvidenceFilters,
  eventType: string,
  severity: string,
  presentation: Data = {},
): boolean {
  if (
    (eventType && event.type !== eventType) ||
    (severity && event.payload?.severity !== severity) ||
    (filters.sourceProviderId &&
      event.source?.providerId !== filters.sourceProviderId) ||
    (filters.observerRef && event.payload?.observerRef !== filters.observerRef)
  )
    return false;
  if (filters.timeBasis === "source") {
    const time = sourceTime(event);
    if (!time || time.domain !== filters.clockDomain) return false;
    if (
      filters.startTick &&
      (time.tick < tick(filters.startTick)! ||
        time.tick >= tick(filters.endTick)!)
    )
      return false;
  }
  if (filters.timeBasis === "recorded") {
    const shown = receipt(event, presentation).utc,
      raw = shown ? utc(shown) : null;
    if (
      raw === null ||
      raw < utc(filters.recordedFrom)! ||
      raw >= utc(filters.recordedUntil)!
    )
      return false;
  }
  return true;
}
