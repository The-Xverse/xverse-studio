import type { Data } from "./types";
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
export { subscribe, mergeRun } from "../features/runs/session";
