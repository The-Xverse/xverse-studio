import type { Data, RunEvent } from "./types";
let csrfToken = "";
export class ApiError extends Error {
  code: string;
  status: number;
  details: Data;
  constructor(status: number, body: Data) {
    super(body.message || body.detail || `Request failed (${status})`);
    this.code = body.code || "REQUEST_FAILED";
    this.status = status;
    this.details = body;
  }
}
export function setCsrfToken(value: string) {
  csrfToken = value;
}
export async function api<T = Data>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    revision?: string | number;
    key?: string;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const method = options.method || "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    headers["X-CSRF-Token"] = csrfToken;
  }
  if (options.revision !== undefined)
    headers["If-Match"] = `"${options.revision}"`;
  if (options.key) headers["Idempotency-Key"] = options.key;
  const response = await fetch(`/api/v1${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });
  if (!response.ok) {
    let body: Data = {};
    try {
      body = await response.json();
    } catch {
      /* Body is optional on transport errors. */
    }
    throw new ApiError(response.status, body);
  }
  if (response.status === 204) return {} as T;
  return response.json();
}
export function mutationKey() {
  return crypto.randomUUID();
}
export function items<T>(response: any): T[] {
  return Array.isArray(response)
    ? response
    : response?.items ||
        response?.entries ||
        response?.providers ||
        response?.assets ||
        [];
}
/** Fetch SSE explicitly so each retry sends only its latest cursor, with a bounded UI buffer. */
export function subscribe(
  runId: string,
  onEvent: (event: RunEvent) => void,
  onState: (state: string) => void,
  onGap: () => void,
) {
  const controller = new AbortController();
  let cursor = "";
  let stopped = false;
  const sleep = (ms: number) =>
    new Promise<void>((resolve) => {
      const timer = setTimeout(resolve, ms);
      controller.signal.addEventListener(
        "abort",
        () => {
          clearTimeout(timer);
          resolve();
        },
        { once: true },
      );
    });
  async function run() {
    let delay = 500;
    while (!stopped) {
      try {
        onState(cursor ? "Reconnecting" : "Connecting");
        const response = await fetch(
          `/api/v1/runs/${encodeURIComponent(runId)}/events${cursor ? `?after=${encodeURIComponent(cursor)}` : ""}`,
          {
            credentials: "same-origin",
            headers: { Accept: "text/event-stream" },
            signal: controller.signal,
          },
        );
        if (response.status === 410) {
          cursor = "";
          onGap();
          await sleep(500);
          continue;
        }
        if (!response.ok || !response.body)
          throw new Error(`Event stream unavailable (${response.status})`);
        onState("Connected");
        delay = 500;
        const reader = response.body.getReader(),
          decoder = new TextDecoder();
        let buffer = "";
        while (!stopped) {
          const chunk = await reader.read();
          if (chunk.done) break;
          buffer += decoder
            .decode(chunk.value, { stream: true })
            .replace(/\r\n/g, "\n");
          if (buffer.length > 262144)
            throw new Error("Event frame limit exceeded");
          let boundary;
          while ((boundary = buffer.indexOf("\n\n")) >= 0) {
            const frame = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            let id = "",
              data = "";
            for (const line of frame.split("\n")) {
              if (line.startsWith("id:")) id = line.slice(3).trim();
              if (line.startsWith("data:")) data += line.slice(5).trim();
            }
            if (data) {
              const event = JSON.parse(data) as RunEvent;
              if (event.schemaVersion !== "1.0") {
                onGap();
                throw new Error("Incompatible event envelope");
              }
              if (id) cursor = id;
              onEvent(event);
            }
          }
        }
      } catch (error) {
        if (stopped) return;
        onState("Disconnected — retrying");
      }
      await sleep(delay);
      delay = Math.min(delay * 2, 5000);
    }
  }
  void run();
  return () => {
    stopped = true;
    controller.abort();
  };
}
