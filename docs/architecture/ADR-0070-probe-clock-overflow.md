# ADR-0070 — Typed failure for oversized observation clocks

Date: 2026-11-05. Status: implemented; scoped Linux verification.
Traces: T075; NFR-004, NFR-005; existing explicit observation contract (ADR-0027).

The existing observation service uses `math.isfinite` for backend timestamps,
persisted receipt times and provider uncertainty values. A Python integer outside
the floating-point range raises `OverflowError` there. A malformed host clock or
controlled corrupt receipt consequently escapes the existing typed refusal as an
HTTP500. Provider uncertainty overflows and clock failures during delegation are
instead reduced to the generic `PROBE_UNKNOWN` diagnostic. These are owned test
inputs, not a claim that an HTTP caller can select the backend clock or edit storage.

Treat an integer that cannot be checked by the existing finite-real clock policy
as invalid, preserving exact type checks and the current floating-point policy.
Do not convert source tick strings, clamp values or create a replacement timestamp.
Retain `PROBE_CLOCK_UNAVAILABLE` through the worker's closed diagnostic allowlist.
The existing boundary then returns `PROBE_CLOCK_UNAVAILABLE` before admission,
`PROBE_STATE_UNAVAILABLE` for corrupt stored clocks and `PROBE_RESPONSE_INVALID`
for malformed provider uncertainty. A failure after durable acceptance remains
unknown with no result; it does not become a successful observation.

This changes no endpoint, request schema, status vocabulary, permission, binding
pin, callback deadline, receipt identity, provider permit or physical action surface.
Historical corrupt bytes are not repaired or rewritten. Inspection/retry cannot
re-delegate the original observation. The provider's signed decimal source tick
remains separate from the backend receipt clock and its exact encoding is retained.

Authenticated ASGI tests use the existing owned in-process observation fixture on
Linux. They contact no equipment/socket/provider installation and launch no model.
New cases cover both signs of oversized backend times, stored clock fields,
provider uncertainty and clock failure before/after the callback. Existing HTTP
conformance tests remain unchanged. No Windows source or Windows-specific tests
are changed/executed; ADR-0069's Windows hold remains active.

The physical-command conformance and admitted runtime/Maestro integration gaps in
T073/T074 are unaffected. An observation or reservation permit does not supply that
missing contract. No standalone device-action endpoint is added. T075 stays open
for its original prerequisite/integrated workflow; this repair closes no task or
milestone and supplies no actual hardware acceptance.

Evidence: `evidence/studio/M3-probe-clock-overflow-20261105/`.
