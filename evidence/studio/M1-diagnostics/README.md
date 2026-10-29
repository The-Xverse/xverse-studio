# Evidence-linked diagnostic explanations — T031/T032 owned components

T031 and T032 are component-complete for owned reference and recorded-fixture evidence on Linux.
No milestone, live-provider, Windows or physical acceptance is claimed. See `verification.json` for
the exact source digest, test hashes and results, and ADR-0012 for the contract.

## What is covered

Run explanations: process exit (cause not inferred; not-started runs explain that nothing executed),
lost verified ownership, cleanup failure or uncertainty, unavailable/invalid/partial evidence
(information-only while an active journal is momentarily unreadable), incompatible or missing source
time, declared telemetry gaps, observed faults with diverging measurements, accepted commands that did
not take effect, no-traffic ambiguity (`info`, never failure) and liveness-only health.

Preflight explanations: invalid model with authoritative source diagnostics, unsupported capability or
unavailable provider, missing artifact, clock mapping, resource limit, authority, grouped unestablished
facts and stale plans (expiry, revision, capability digest).

Every finding keeps facts (with bounded evidence references), consequences citing only its own facts,
unconfirmed hypotheses, unknowns and closed next actions. Browser views render these without adding
inference and offer only performable actions. Explanations never change original evidence.

## Verification

531 backend tests, typecheck/build and 47/47 browser checks with performance measurements on an
unchanged candidate. `tests/contract/test_diagnostics.py` checks every class with shared invariants
and real API cases (owned completed run, recorded fixture, real invalid model, unavailable provider,
stale preflight, cross-project 404). `tests/e2e/diagnostics.spec.ts` checks the Results and preflight
views, keyboard action use, unchanged journal bytes and the 1024×768 viewport.
`independent-review.md` records nine repaired review findings.

## Limits

- `lost_connection` here is loss of verified ownership of the owned workload. Communication-link loss
  needs an admitted provider emitting `connection.observed`; none is admitted.
- US4's live failure repetition, AC-005/007/011 environment clauses, Windows and physical evidence
  remain open. The owned reference and recorded fixture are not a simulator or device.
