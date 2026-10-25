import { test, expect } from "@playwright/test";
import { subscribe, mergeRun } from "../../apps/studio-web/src/api/client";
import { SseParser } from "../../apps/studio-web/src/features/runs/sessionProtocol";
const runId = "run-session-fixture",
  snapshotId = "snapshot-session-fixture",
  zeros = "0".repeat(64),
  digest = "a".repeat(64);
const cursor = (q: string, d = digest) =>
  "st1." +
  Buffer.from(JSON.stringify({ r: runId, s: snapshotId, q, d })).toString(
    "base64url",
  );
const event = {
  schemaVersion: "1.0",
  eventId: "event-1",
  runId,
  snapshotId,
  sequence: "1",
  type: "log.appended",
  recordedAt: "2026-01-01T00:00:00Z",
  evidenceClass: "unknown",
  payload: { severity: "info", message: "inert transport contract fixture" },
  digest,
  previousDigest: zeros,
};
const recovery = {
  streamVersion: "1.1",
  run: { runId, snapshotId, state: "running", stateVersion: 3 },
  snapshotId,
  history: {
    items: [],
    nextCursor: null,
    integrity: "valid",
    omittedRecords: 0,
  },
  resumeCursor: cursor("0", zeros),
  watermark: { sequence: "0", digest: zeros },
};
const sse = (text: string) =>
  new Response(
    new ReadableStream({
      start(c) {
        c.enqueue(new TextEncoder().encode(text));
        c.close();
      },
    }),
    { headers: { "Content-Type": "text/event-stream" } },
  );
const frame = `event: log.appended\nid: ${cursor("1")}\ndata: ${JSON.stringify(event)}\n\n`;
const end = `event: studio.stream_control\ndata: ${JSON.stringify({ streamVersion: "1.1", type: "stream.end", runId, snapshotId, reason: "terminal", missingCount: null, firstMissingSequence: null, lastMissingSequence: null, integrity: "valid" })}\n\n`;
function gate() {
  let release!: () => void;
  const promise = new Promise<void>((r) => (release = r));
  return { promise, release };
}
const pause = (ms: number) => new Promise((r) => setTimeout(r, ms));
test("session contract: reserved control slot coalesces with 200 data frames while canonical and control queues stay bounded", () => {
  const control = `event: studio.stream_control\ndata: ${JSON.stringify({ streamVersion: "1.1", type: "stream.gap", runId, snapshotId, reason: "SLOW_CONSUMER", missingCount: 1015, firstMissingSequence: "1", lastMissingSequence: "1015" })}\n\n`;
  const data = frame.repeat(200);
  for (const wire of [control + data, data + control]) {
    const parsed = new SseParser().feed(new TextEncoder().encode(wire));
    expect(parsed).toHaveLength(201);
    expect(parsed.filter((f) => f.event === "studio.stream_control")).toHaveLength(1);
    expect(parsed.filter((f) => f.event !== "studio.stream_control")).toHaveLength(200);
  }
  expect(() => new SseParser().feed(new TextEncoder().encode(frame.repeat(201)))).toThrow(/queue limit/i);
  expect(() => new SseParser().feed(new TextEncoder().encode(control.repeat(2)))).toThrow(/queue limit/i);
});
test("session contract: callback acceptance precedes acknowledged reconnect cursor", async () => {
  const original = globalThis.fetch,
    g = gate(),
    calls: string[] = [];
  let entered = false;
  globalThis.fetch = async (input) => {
    calls.push(String(input));
    return sse(calls.length === 1 ? frame : end);
  };
  const stop = subscribe(
    runId,
    async () => {
      entered = true;
      await g.promise;
    },
    () => {},
    async () => {},
    { snapshotId },
  );
  try {
    await expect.poll(() => entered).toBe(true);
    await pause(650);
    expect(calls).toHaveLength(1);
    g.release();
    await expect.poll(() => calls.length).toBe(2);
    expect(new URL(calls[1], "http://fixture").searchParams.get("after")).toBe(
      cursor("1"),
    );
  } finally {
    g.release();
    stop();
    globalThis.fetch = original;
  }
});
test("session contract: expiry awaits full state and history resynchronization before reconnect", async () => {
  const original = globalThis.fetch,
    g = gate(),
    calls: string[] = [];
  let entered = false;
  let received: any;
  globalThis.fetch = async (input) => {
    const url = String(input);
    calls.push(url);
    if (url.includes("/resync")) return Response.json(recovery);
    if (calls.filter((c) => c.includes("/events")).length === 1)
      return Response.json(
        { code: "CURSOR_EXPIRED", runId, snapshotId },
        { status: 410 },
      );
    return sse(end);
  };
  const stop = subscribe(
    runId,
    () => {},
    () => {},
    async (value: any) => {
      received = value;
      entered = true;
      await g.promise;
    },
    { snapshotId },
  );
  try {
    await expect.poll(() => entered).toBe(true);
    await pause(650);
    expect(calls.filter((c) => c.includes("/events"))).toHaveLength(1);
    expect(received.history.integrity).toBe("valid");
    g.release();
    await expect
      .poll(() => calls.filter((c) => c.includes("/events")).length)
      .toBe(2);
    expect(
      new URL(calls.at(-1)!, "http://fixture").searchParams.get("after"),
    ).toBe(recovery.resumeCursor);
  } finally {
    g.release();
    stop();
    globalThis.fetch = original;
  }
});
test("session contract: SSE CRLF split across chunks preserves one canonical frame", async () => {
  const original = globalThis.fetch;
  const seen: any[] = [];
  let requests = 0;
  globalThis.fetch = async () => {
    requests++;
    const text = (frame + end).replaceAll("\n", "\r\n");
    return new Response(
      new ReadableStream({
        start(c) {
          for (let i = 0; i < text.length; i++)
            c.enqueue(new TextEncoder().encode(text[i]));
          c.close();
        },
      }),
      { headers: { "Content-Type": "text/event-stream" } },
    );
  };
  const stop = subscribe(
    runId,
    (e) => {
      seen.push(e);
    },
    () => {},
    async () => {},
    { snapshotId },
  );
  try {
    await expect.poll(() => seen.length, { timeout: 1500 }).toBe(1);
    await pause(100);
    expect(requests).toBe(1);
    expect(seen[0].eventId).toBe(event.eventId);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});
test("session contract: unknown presentation loss stays unknown and outside canonical records", async () => {
  const original = globalThis.fetch,
    controls: any[] = [],
    records: any[] = [];
  let streams = 0;
  const control = {
    streamVersion: "1.1",
    type: "stream.gap",
    runId,
    snapshotId,
    reason: "unknown interval",
    firstMissingSequence: null,
    lastMissingSequence: null,
    missingCount: null,
    integrity: "unavailable",
  };
  globalThis.fetch = async (input) =>
    String(input).includes("/resync")
      ? Response.json(recovery)
      : sse(
          ++streams === 1
            ? `event: studio.stream_control\ndata: ${JSON.stringify(control)}\n\n`
            : end,
        );
  const stop = subscribe(
    runId,
    (e) => {
      records.push(e);
    },
    () => {},
    async () => {},
    {
      snapshotId,
      onControl: (c: any) => {
        controls.push(c);
      },
    },
  );
  try {
    await expect
      .poll(() => controls.some((c) => c.type === "stream.gap"), {
        timeout: 1500,
      })
      .toBe(true);
    expect(records).toEqual([]);
    expect(
      controls.find((c) => c.type === "stream.gap").missingCount,
    ).toBeNull();
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: retry timers remove completed abort listeners", async () => {
  const originalFetch = globalThis.fetch,
    OriginalController = globalThis.AbortController;
  const proto = AbortSignal.prototype,
    add = proto.addEventListener,
    remove = proto.removeEventListener;
  const signals = new Set<AbortSignal>(),
    active = new Set<any>();
  let requests = 0;
  globalThis.AbortController = class extends OriginalController {
    constructor() {
      super();
      signals.add(this.signal);
    }
  };
  proto.addEventListener = function (type: any, listener: any, options?: any) {
    if (type === "abort" && signals.has(this)) active.add(listener);
    return add.call(this, type, listener, options);
  };
  proto.removeEventListener = function (
    type: any,
    listener: any,
    options?: any,
  ) {
    if (type === "abort" && signals.has(this)) active.delete(listener);
    return remove.call(this, type, listener, options);
  };
  globalThis.fetch = async () => {
    requests++;
    return Response.json(
      { code: "STREAM_SOURCE_UNAVAILABLE" },
      { status: 503 },
    );
  };
  const stop = subscribe(
    runId,
    () => {},
    () => {},
    async () => {},
    { snapshotId },
  );
  try {
    await expect
      .poll(() => requests, { timeout: 3000 })
      .toBeGreaterThanOrEqual(3);
    expect(active.size).toBeLessThanOrEqual(1);
  } finally {
    stop();
    globalThis.fetch = originalFetch;
    globalThis.AbortController = OriginalController;
    proto.addEventListener = add;
    proto.removeEventListener = remove;
  }
});

test("session contract: disposal cancels an idle reader without another request", async () => {
  const original = globalThis.fetch;
  let cancelled = false,
    requests = 0;
  globalThis.fetch = async () => {
    requests++;
    return new Response(
      new ReadableStream({
        cancel() {
          cancelled = true;
        },
      }),
      { headers: { "Content-Type": "text/event-stream" } },
    );
  };
  const stop = subscribe(
    runId,
    () => {},
    () => {},
    async () => {},
    { snapshotId },
  );
  try {
    await expect.poll(() => requests).toBe(1);
    stop();
    await expect.poll(() => cancelled, { timeout: 1000 }).toBe(true);
    expect(requests).toBe(1);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: equal lifecycle version keeps state while fresh cleanup and evidence advance", async () => {
  const current = {
    runId,
    snapshotId,
    state: "unknown",
    stateVersion: 8,
    cleanup: "unknown",
    evidence: "partial",
  };
  expect(
    mergeRun(current, {
      ...current,
      state: "running",
      stateVersion: 7,
      cleanup: "complete",
    }),
  ).toBe(current);
  const next = mergeRun(current, {
    ...current,
    state: "stopped",
    stateVersion: 8,
    cleanup: "complete",
    evidence: "invalid",
  });
  expect(next?.state).toBe("unknown");
  expect(next?.cleanup).toBe("complete");
  expect(next?.evidence).toBe("invalid");
  expect(
    mergeRun(current, { ...current, snapshotId: "other", stateVersion: 9 }),
  ).toBe(current);
  expect(
    mergeRun(current, { ...current, runId: "other", stateVersion: 9 }),
  ).toBe(current);
  expect(
    mergeRun(current, { ...current, state: "stopped", stateVersion: 9 })?.state,
  ).toBe("stopped");
});

test("session contract: invalid recovery cannot acknowledge a replacement watermark", async () => {
  const original = globalThis.fetch,
    calls: string[] = [],
    records: any[] = [];
  let recoveries = 0,
    streams = 0;
  const gap = `event: studio.stream_control\ndata: ${JSON.stringify({ streamVersion: "1.1", type: "stream.resync_required", runId, snapshotId, reason: "fixture discontinuity", missingCount: null, firstMissingSequence: null, lastMissingSequence: null, integrity: "unavailable" })}\n\n`;
  globalThis.fetch = async (input) => {
    const url = String(input);
    calls.push(url);
    return url.includes("/resync")
      ? Response.json({ ...recovery, snapshotId: "wrong-snapshot" })
      : sse(++streams === 1 ? frame + gap : end);
  };
  const stop = subscribe(
    runId,
    (e) => {
      records.push(e);
    },
    () => {},
    async () => {
      recoveries++;
    },
    { snapshotId },
  );
  try {
    await expect.poll(() => streams).toBe(2);
    expect(recoveries).toBe(0);
    expect(records).toHaveLength(1);
    expect(
      new URL(calls.at(-1)!, "http://fixture").searchParams.get("after"),
    ).toBe(cursor("1"));
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: duplicate delivery deduplicates before consumer acceptance", async () => {
  const original = globalThis.fetch,
    records: any[] = [];
  globalThis.fetch = async () => sse(frame + frame + end);
  const stop = subscribe(
    runId,
    (e) => {
      records.push(e);
    },
    () => {},
    async () => {},
    { snapshotId },
  );
  try {
    await expect.poll(() => records.length).toBe(1);
    await pause(50);
    expect(records).toHaveLength(1);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: mismatched cursor proof rejects frame before consumer acceptance", async () => {
  const original = globalThis.fetch,
    records: any[] = [],
    controls: any[] = [];
  let streams = 0;
  globalThis.fetch = async (input) =>
    String(input).includes("/resync")
      ? Response.json(recovery)
      : sse(
          ++streams === 1
            ? frame.replace(cursor("1"), cursor("1", "b".repeat(64)))
            : end,
        );
  const stop = subscribe(
    runId,
    (e) => {
      records.push(e);
    },
    () => {},
    async () => {},
    {
      snapshotId,
      onControl: (c) => {
        controls.push(c);
      },
    },
  );
  try {
    await expect.poll(() => streams).toBe(2);
    expect(records).toEqual([]);
    expect(controls.some((c) => String(c.reason).includes("proof"))).toBe(true);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: incompatible schema and oversized frames require verified recovery", async () => {
  const original = globalThis.fetch;
  const records: any[] = [];
  let streams = 0,
    recoveries = 0;
  globalThis.fetch = async (input) => {
    if (String(input).includes("/resync")) return Response.json(recovery);
    streams++;
    return sse(
      streams === 1
        ? frame.replace('"schemaVersion":"1.0"', '"schemaVersion":"99.0"')
        : streams === 2
          ? "data: " + "x".repeat(262145) + "\n\n"
          : end,
    );
  };
  const stop = subscribe(
    runId,
    (e) => {
      records.push(e);
    },
    () => {},
    async () => {
      recoveries++;
    },
    { snapshotId },
  );
  try {
    await expect.poll(() => recoveries).toBe(2);
    expect(records).toEqual([]);
    expect(streams).toBe(3);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: running verified-prefix recovery preserves limited integrity and resumes", async () => {
  const original = globalThis.fetch;
  let streams = 0,
    received: any;
  globalThis.fetch = async (input) =>
    String(input).includes("/resync")
      ? Response.json({
          ...recovery,
          history: { ...recovery.history, integrity: "verified_prefix" },
        })
      : ++streams === 1
        ? Response.json(
            { code: "CURSOR_EXPIRED", runId, snapshotId },
            { status: 410 },
          )
        : sse(end);
  const stop = subscribe(
    runId,
    () => {},
    () => {},
    async (value) => {
      received = value;
    },
    { snapshotId },
  );
  try {
    await expect
      .poll(() => received?.history.integrity, { timeout: 1500 })
      .toBe("verified_prefix");
    expect(streams).toBe(2);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});

test("session contract: invalid and unavailable recovery bodies remain unaccepted", async () => {
  const original = globalThis.fetch;
  try {
    for (const integrity of ["invalid", "unavailable"]) {
      let streams = 0,
        accepted = 0;
      globalThis.fetch = async (input) =>
        String(input).includes("/resync")
          ? Response.json({
              ...recovery,
              history: { ...recovery.history, integrity },
            })
          : ++streams === 1
            ? Response.json(
                { code: "CURSOR_EXPIRED", runId, snapshotId },
                { status: 410 },
              )
            : sse(end);
      const stop = subscribe(
        runId,
        () => {},
        () => {},
        async () => {
          accepted++;
        },
        { snapshotId },
      );
      try {
        await expect.poll(() => streams).toBe(2);
        expect(accepted).toBe(0);
      } finally {
        stop();
      }
    }
  } finally {
    globalThis.fetch = original;
  }
});

test("session contract: typed oversized recovery stops without acknowledgement or retry and releases its body", async () => {
  const original = globalThis.fetch,
    states: string[] = [],
    requests: string[] = [];
  let accepted = 0,
    cancelled = false;
  globalThis.fetch = async (input) => {
    const url = String(input);
    requests.push(url);
    if (url.includes("/resync"))
      return new Response(
        new ReadableStream({
          start(controller) {
            controller.enqueue(
              new TextEncoder().encode(
                JSON.stringify({
                  code: "STREAM_RECOVERY_TOO_LARGE",
                  message:
                    "Recovery metadata exceeds the bounded response limit; use paged retained history.",
                }),
              ),
            );
          },
          cancel() {
            cancelled = true;
          },
        }),
        { status: 413, headers: { "Content-Type": "application/json" } },
      );
    return Response.json(
      { code: "CURSOR_EXPIRED", runId, snapshotId },
      { status: 410 },
    );
  };
  const stop = subscribe(
    runId,
    () => {
      accepted++;
    },
    (state) => {
      states.push(state);
    },
    async () => {
      accepted++;
    },
    { snapshotId },
  );
  try {
    await expect
      .poll(() => requests.some((url) => url.includes("/resync")))
      .toBe(true);
    await pause(650);
    expect(requests).toHaveLength(2);
    expect(accepted).toBe(0);
    expect(cancelled).toBe(true);
    expect(states.at(-1)).toMatch(/recovery.*limit.*paged retained history/i);
    expect(
      requests.every(
        (url) => !new URL(url, "http://fixture").searchParams.has("after"),
      ),
    ).toBe(true);
  } finally {
    stop();
    globalThis.fetch = original;
  }
});
