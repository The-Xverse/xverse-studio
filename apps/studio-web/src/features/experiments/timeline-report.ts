import type { Data } from "../../api/types";
import { text } from "../lab/public-observations";
import { tick } from "../results/evidenceFilters";

export type TimelineContext = {
  projectId: string;
  runId: string;
  snapshotId: string;
  clock?: string;
  inputIdentity?: string;
  offset: number;
};
const object = (v: any): v is Data =>
  !!v && typeof v === "object" && !Array.isArray(v);
const hash = (v: unknown) =>
  typeof v === "string" && /^sha256:[a-f0-9]{64}$/.test(v);
const count = (v: unknown) => Number.isSafeInteger(v) && Number(v) >= 0;
const strings = (v: any, max: number, length = 4096) =>
  Array.isArray(v) && v.length <= max && v.every((s) => text(s, length));
const scalar = (v: any) =>
  v === null ||
  typeof v === "boolean" ||
  (typeof v === "number" && Number.isFinite(v)) ||
  text(v, 4096);
const fields = (v: any, max = 64) =>
  object(v) &&
  Object.keys(v).length <= max &&
  Object.entries(v).every(([key, val]) => text(key, 512) && scalar(val));

// Resource/shape guard for inert declarations, not a browser evaluator or XDL validator.
function boundedDeclaration(value: unknown) {
  const pending: [unknown, number][] = [[value, 0]];
  let nodes = 0;
  while (pending.length) {
    const [v, depth] = pending.pop()!;
    if (++nodes > 8192 || depth > 64) return false;
    if (v === null || typeof v === "boolean") continue;
    if (typeof v === "number") {
      if (!Number.isFinite(v)) return false;
      continue;
    }
    if (typeof v === "string") {
      if (v.length > 32768) return false;
      continue;
    }
    if (Array.isArray(v)) {
      if (v.length > 256) return false;
      pending.push(
        ...v.map((child) => [child, depth + 1] as [unknown, number]),
      );
    } else if (object(v)) {
      const entries = Object.entries(v);
      if (entries.length > 64 || entries.some(([k]) => !text(k, 256)))
        return false;
      pending.push(
        ...entries.map(([, child]) => [child, depth + 1] as [unknown, number]),
      );
    } else return false;
  }
  return true;
}

/** Display contract only. All source interpretation/evaluation stays on the backend. */
export function timelineReport(value: Data, context: TimelineContext): Data {
  const fail = (): never => {
    throw new Error(
      "The timeline is malformed, unsupported or belongs to another input selection. Inspect again to retry.",
    );
  };
  if (
    !object(value) ||
    value.timelineVersion !== "1.0" ||
    value.readOnly !== true ||
    value.projectId !== context.projectId ||
    value.runId !== context.runId ||
    value.snapshotId !== context.snapshotId ||
    !hash(value.snapshotDigest) ||
    !hash(value.inputIdentity) ||
    (context.inputIdentity !== undefined &&
      value.inputIdentity !== context.inputIdentity) ||
    !Number.isSafeInteger(value.projectRevision) ||
    value.projectRevision < 1 ||
    !object(value.selection) ||
    !["systemRef", "deploymentRef", "scenarioRef"].every(
      (key) =>
        text(value.selection[key], 4096) &&
        value.selection[key].startsWith("xdl://"),
    ) ||
    !(value.clockDomain === null || text(value.clockDomain, 512)) ||
    (context.clock && value.clockDomain !== context.clock) ||
    ![null, "microsecond"].includes(value.tickUnit) ||
    ![null, "studio.reference.seconds-microseconds.v1"].includes(
      value.intentClockCodec,
    ) ||
    !text(value.evidenceScope, 128) ||
    !Array.isArray(value.items) ||
    value.items.length > 200 ||
    !(value.nextCursor === null || text(value.nextCursor, 2048)) ||
    !Array.isArray(value.clockDomains) ||
    value.clockDomains.length > 64 ||
    !value.clockDomains.every(
      (c: any) =>
        object(c) &&
        text(c.id, 512) &&
        typeof c.declared === "boolean" &&
        typeof c.observed === "boolean",
    ) ||
    new Set(value.clockDomains.map((c: Data) => c.id)).size !==
      value.clockDomains.length ||
    typeof value.clockDomainsComplete !== "boolean" ||
    !object(value.counts) ||
    ![
      "matchedRows",
      "returnedRows",
      "unplacedRows",
      "recordedInputs",
      "recordedInputsConsidered",
      "intentInputs",
      "intentInputsConsidered",
      "evaluationInputsConsidered",
    ].every((k) => count(value.counts[k])) ||
    value.counts.returnedRows !== value.items.length ||
    value.counts.unplacedRows > value.counts.matchedRows ||
    !object(value.inputsComplete) ||
    !["intents", "recorded", "evaluations"].every(
      (k) => typeof value.inputsComplete[k] === "boolean",
    ) ||
    !object(value.reduction) ||
    value.reduction.method !== "page" ||
    value.reduction.canonical !== false ||
    value.reduction.pageStart !== context.offset ||
    !count(value.reduction.pageSize) ||
    value.reduction.pageSize < 1 ||
    value.reduction.pageSize > 200 ||
    value.items.length > value.reduction.pageSize ||
    value.reduction.pageStart + value.items.length > value.counts.matchedRows ||
    (value.nextCursor === null) !==
      (value.reduction.pageStart + value.items.length ===
        value.counts.matchedRows) ||
    !object(value.recorded) ||
    !["valid", "invalid", "unavailable", "verified_prefix"].includes(
      value.recorded.integrity,
    ) ||
    value.recorded.coverage !== "not_attested_by_timeline" ||
    value.recorded.qualityScope !== "whole_journal" ||
    !count(value.recorded.gapCount) ||
    typeof value.recorded.gapsComplete !== "boolean" ||
    !Array.isArray(value.recorded.gaps) ||
    value.recorded.gaps.length > 128 ||
    !object(value.recorded.quality) ||
    !Object.values(value.recorded.quality).every(count) ||
    !value.recorded.gaps.every(
      (g: any) =>
        object(g) &&
        (g.reason === null || text(g.reason, 256)) &&
        typeof g.detailUnavailable === "boolean" &&
        fields(g.sourceTime),
    ) ||
    !Array.isArray(value.diagnostics) ||
    value.diagnostics.length > 100 ||
    !value.diagnostics.every((d: any) => object(d) && text(d.code, 128)) ||
    typeof value.diagnosticsComplete !== "boolean" ||
    !strings(value.limitations, 100, 1000)
  )
    fail();
  const declared = value.assessmentDefinitions;
  if (
    !object(declared) ||
    !["available", "unavailable"].includes(declared.status) ||
    typeof declared.complete !== "boolean" ||
    !Array.isArray(declared.items) ||
    declared.items.length > 32 ||
    (declared.status === "unavailable" &&
      (declared.complete || declared.items.length))
  )
    fail();
  const definitions = declared.items.map((entry: Data) => {
    const d = entry?.definition;
    if (
      !object(entry) ||
      !text(entry.definitionRef, 256) ||
      !hash(entry.definitionDigest) ||
      !hash(entry.schemaDigest) ||
      entry.profileNamespace !== "io.xverse.studio.experiments" ||
      entry.profileVersion !== "1.0.0" ||
      !object(d) ||
      !boundedDeclaration(d) ||
      d.version !== "1.0" ||
      d.evaluationId !== entry.definitionRef ||
      !["assertion", "metric"].includes(d.kind) ||
      !text(d.name, 4096) ||
      !object(d.expression) ||
      d.systemRef !== value.selection.systemRef ||
      d.scenarioRef !== value.selection.scenarioRef ||
      !object(d.window) ||
      !text(d.window.clockDomainRef, 512) ||
      tick(d.window.startTick) === null ||
      tick(d.window.endTick) === null ||
      BigInt(d.window.startTick) >= BigInt(d.window.endTick) ||
      d.coveragePolicy !== "complete"
    )
      fail();
    return {
      definitionRef: entry.definitionRef,
      definitionDigest: entry.definitionDigest,
      schemaDigest: entry.schemaDigest,
      profileNamespace: entry.profileNamespace,
      profileVersion: entry.profileVersion,
      definition: d,
    };
  });
  if (
    new Set(definitions.map((d: Data) => d.definitionRef)).size !==
    definitions.length
  )
    fail();
  const rows = value.items.map((row: Data) => {
    if (
      !object(row) ||
      !text(row.id, 1024) ||
      !["intent", "recorded", "evaluation"].includes(row.layer) ||
      !text(row.kind, 256) ||
      !text(row.evidenceScope, 128) ||
      !object(row.position)
    )
      fail();
    const p = row.position;
    if (
      !["aligned", "unplaced"].includes(p.status) ||
      !(p.clockDomain === null || text(p.clockDomain, 512)) ||
      !(p.tick === null || tick(p.tick) !== null) ||
      ![null, "microsecond"].includes(p.tickUnit) ||
      (p.endTick !== undefined && tick(p.endTick) === null) ||
      (p.status === "unplaced" && !text(p.reason, 256)) ||
      (p.status === "aligned" &&
        (tick(p.tick) === null ||
          p.reason !== null ||
          p.clockDomain !== value.clockDomain ||
          !p.tickUnit ||
          p.tickUnit !== value.tickUnit))
    )
      fail();
    const base = {
      id: row.id,
      layer: row.layer,
      kind: row.kind,
      evidenceScope: row.evidenceScope,
      position: {
        status: p.status,
        clockDomain: p.clockDomain,
        tick: p.tick,
        tickUnit: p.tickUnit,
        reason: p.reason,
        ...(p.endTick === undefined ? {} : { endTick: p.endTick }),
      },
    };
    if (row.layer === "intent") {
      if (
        !text(row.intentId, 256) ||
        !text(row.logicalRef, 4096) ||
        row.evidenceScope !== "declared_intent_only" ||
        (row.targetRef !== null && !text(row.targetRef, 4096))
      )
        fail();
      if (
        row.kind === "intent.provider_configuration" &&
        (row.configurationParameter !== "fault" ||
          !text(row.declaredValue, 256) ||
          !hash(row.configurationDigest) ||
          row.sourceField !==
            "extensions.io.xverse.experiment.parameters[id=fault]" ||
          p.status !== "unplaced" ||
          p.tick !== null)
      )
        fail();
      return {
        ...base,
        intentId: row.intentId,
        logicalRef: row.logicalRef,
        targetRef: row.targetRef,
        ...(row.kind === "intent.provider_configuration"
          ? {
              configurationParameter: row.configurationParameter,
              declaredValue: row.declaredValue,
              configurationDigest: row.configurationDigest,
              sourceField: row.sourceField,
            }
          : {}),
        ...(object(row.schedule) &&
        scalar(row.schedule.at) &&
        scalar(row.schedule.unit)
          ? { schedule: { at: row.schedule.at, unit: row.schedule.unit } }
          : {}),
      };
    }
    if (row.layer === "recorded") {
      if (
        !text(row.eventId, 512) ||
        typeof row.sequence !== "string" ||
        !/^(0|[1-9][0-9]{0,31})$/.test(row.sequence) ||
        row.evidenceIntegrity !== value.recorded.integrity ||
        (p.status === "aligned" && row.evidenceIntegrity !== "valid") ||
        !fields(row.sourceTime) ||
        !fields(row.source) ||
        !text(row.sourceTimeStatus, 128) ||
        !fields(row.facts) ||
        !strings(row.evidenceRefs, 64) ||
        !strings(row.elementRefs, 64) ||
        !text(row.receiptEncoding, 128) ||
        !(row.recordedAtUtc === null || text(row.recordedAtUtc, 128)) ||
        (row.values !== undefined &&
          (!fields(row.values) ||
            !fields(row.units) ||
            !count(row.unsupportedValueCount)))
      )
        fail();
      return {
        ...base,
        eventId: row.eventId,
        sequence: row.sequence,
        evidenceIntegrity: row.evidenceIntegrity,
        sourceTime: { ...row.sourceTime },
        source: {
          providerId: row.source.providerId,
          version: row.source.version,
        },
        sourceTimeStatus: row.sourceTimeStatus,
        facts: { ...row.facts },
        evidenceRefs: row.evidenceRefs,
        elementRefs: row.elementRefs,
        recordedAtUtc: row.recordedAtUtc,
        receiptEncoding: row.receiptEncoding,
        ...(row.values === undefined
          ? {}
          : {
              values: { ...row.values },
              units: { ...row.units },
              unsupportedValueCount: row.unsupportedValueCount,
            }),
      };
    }
    if (
      !["assertion", "metric"].includes(row.kind) ||
      !text(row.evaluationId, 256) ||
      !text(row.definitionRef, 4096) ||
      !hash(row.definitionDigest) ||
      !hash(row.resultDigest) ||
      !object(row.window) ||
      tick(row.window.startTick) === null ||
      tick(row.window.endTick) === null ||
      BigInt(row.window.endTick) <= BigInt(row.window.startTick) ||
      row.window.clockDomainRef !== p.clockDomain ||
      row.window.startTick !== p.tick ||
      row.window.endTick !== p.endTick ||
      !["not_started", "running", "complete", "unavailable", "error"].includes(
        row.executionStatus,
      ) ||
      ![null, "pass", "fail", "indeterminate"].includes(row.verdict) ||
      (row.kind === "metric" && row.verdict !== null) ||
      (row.verdict !== null && row.executionStatus !== "complete") ||
      !(
        row.value === null ||
        typeof row.value === "boolean" ||
        (typeof row.value === "number" && Number.isFinite(row.value))
      ) ||
      !(row.unit === null || text(row.unit, 512)) ||
      !(
        ["complete", "incomplete", "invalid"].includes(row.coverage) ||
        (row.executionStatus !== "complete" && row.coverage === null)
      ) ||
      !(
        typeof row.partial === "boolean" ||
        (row.executionStatus !== "complete" && row.partial === null)
      ) ||
      !strings(row.evidenceDigests, 64) ||
      !strings(row.inputEvidenceDigests, 64) ||
      (["pass", "fail"].includes(row.verdict) &&
        (row.coverage !== "complete" || row.partial !== false)) ||
      !strings(row.reasons, 100, 256) ||
      typeof row.reasonsComplete !== "boolean" ||
      !fields(row.evaluatorIdentity) ||
      typeof row.matchesCurrentEvidence !== "boolean"
    )
      fail();
    if (
      !definitions.some(
        (d: Data) =>
          d.definitionRef === row.definitionRef &&
          d.definitionDigest === row.definitionDigest,
      )
    )
      fail();
    return {
      ...base,
      evaluationId: row.evaluationId,
      definitionRef: row.definitionRef,
      definitionDigest: row.definitionDigest,
      resultDigest: row.resultDigest,
      window: { ...row.window },
      executionStatus: row.executionStatus,
      verdict: row.verdict,
      value: row.value,
      unit: row.unit,
      coverage: row.coverage,
      partial: row.partial,
      reasons: row.reasons,
      reasonsComplete: row.reasonsComplete,
      evaluatorIdentity: { ...row.evaluatorIdentity },
      evidenceDigests: row.evidenceDigests,
      inputEvidenceDigests: row.inputEvidenceDigests,
      matchesCurrentEvidence: row.matchesCurrentEvidence,
    };
  });
  if (new Set(rows.map((r: Data) => r.id)).size !== rows.length) fail();
  return {
    timelineVersion: value.timelineVersion,
    readOnly: true,
    projectId: value.projectId,
    runId: value.runId,
    snapshotId: value.snapshotId,
    snapshotDigest: value.snapshotDigest,
    inputIdentity: value.inputIdentity,
    projectRevision: value.projectRevision,
    selection: {
      systemRef: value.selection.systemRef,
      deploymentRef: value.selection.deploymentRef,
      scenarioRef: value.selection.scenarioRef,
    },
    clockDomain: value.clockDomain,
    tickUnit: value.tickUnit,
    intentClockCodec: value.intentClockCodec,
    evidenceScope: value.evidenceScope,
    clockDomains: value.clockDomains.map((c: Data) => ({
      id: c.id,
      declared: c.declared,
      observed: c.observed,
    })),
    clockDomainsComplete: value.clockDomainsComplete,
    counts: { ...value.counts },
    inputsComplete: { ...value.inputsComplete },
    reduction: { ...value.reduction },
    recorded: {
      integrity: value.recorded.integrity,
      collectionStatus: text(value.recorded.collectionStatus, 128)
        ? value.recorded.collectionStatus
        : "Unknown",
      coverage: value.recorded.coverage,
      qualityScope: value.recorded.qualityScope,
      quality: { ...value.recorded.quality },
      gapCount: value.recorded.gapCount,
      gapsComplete: value.recorded.gapsComplete,
      gaps: value.recorded.gaps.map((g: Data) => ({
        reason: g.reason,
        sourceTime: { ...g.sourceTime },
        detailUnavailable: g.detailUnavailable,
      })),
    },
    items: rows,
    assessmentDefinitions: {
      status: declared.status,
      complete: declared.complete,
      items: definitions,
    },
    nextCursor: value.nextCursor,
    diagnostics: value.diagnostics.map((d: Data) => ({ code: d.code })),
    diagnosticsComplete: value.diagnosticsComplete,
    limitations: value.limitations,
  };
}

/** Only bounded relative screen coordinates use Number. Exact ticks stay strings/BigInt. */
export function timelineCoordinates(rows: Data[]) {
  const placed = rows.filter((r) => r.position.status === "aligned");
  const points: bigint[] = placed.flatMap((r) => [
    BigInt(r.position.tick),
    ...(r.position.endTick === undefined ? [] : [BigInt(r.position.endTick)]),
  ]);
  if (!points.length) return null;
  let start = points[0],
    end = points[0];
  for (const value of points) {
    if (value < start) start = value;
    if (value > end) end = value;
  }
  return {
    start: start.toString(),
    end: end.toString(),
    position: (v: string) =>
      end === start
        ? 50
        : Number(((BigInt(v) - start) * 100000n) / (end - start)) / 1000,
  };
}
