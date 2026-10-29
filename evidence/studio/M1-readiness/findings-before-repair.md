# T020 readiness review before repair

Baseline 21df9dc462ada7104b72c357d772e5a703c4c358, native Linux.

- READINESS-001: Runs.preflight returns `dimensions` and `limits`; App's modal reads nonexistent `checks`. Users see an aggregate ready/blocked badge while individual readiness and bounds are invisible.
- READINESS-002: FR-008 requires separate backend availability, provider OS/architecture compatibility, model validity, artifact availability, capability compatibility, target readiness, resources, ownership, clocks and authority. Existing backend strings report only model/target/ownership/scope. Missing facts must be shown as unreported, never inferred from aggregate readiness.
- READINESS-003: the modal shows a plan digest but offers no read-only compiled-plan inspection bound to the frozen snapshot. Fetching a later draft compilation would introduce a race; the backend owner will provide the frozen plan preview.
- READINESS-004: an unavailable-provider request currently retains reference-provider configuration/identity/limits in the snapshot. Backend owner is repairing the admission boundary separately. UI must display the requested provider's actual report and cannot substitute reference limits or claim live admission.

New browser checks will cover actual ready, valid-but-unsupported topology, and unavailable Lite provider requests without launching a workload; keyboard/focus and 1024x768/1440x900 verification remain required. Native Windows and live-provider acceptance are held, not passed.

Successor: backend owner supplied readinessVersion1.0 with ten independent facts, actual requested provider identity/limits and frozen planPreview. The UI consumes those records directly, renders exact refs/limits/remediation, keeps missing/unknown checks explicit, and gates Start on supported positive states, request identity and expiry. The two original browser failures were retained. Four affected native Linux browser/response-contract checks now pass (7.8s, no skips); see after/verification.json, sanitized report and screenshots. No workload was started. Separate Windows/live/full-milestone acceptance remains open.

READINESS-005, visual review after the first four-pass browser run: full identity rows occupy the opening viewport before any actual readiness fact is visible. Preserve exact identities in an explicit disclosure, with snapshot/revision/expiry/scope always visible, so the independent fact rows appear immediately. This is a presentation repair; no readiness/admission rule or acceptance criterion changes.

READINESS-005 repair verified: exact hashes are in keyboard-accessible Frozen request identities disclosure; snapshot/revision/expiry/scope remain visible. The first readiness row is asserted inside the initial viewport. Four affected checks passed again (9.6s, no skips); final/ retains sanitized report, exact owned-source hashes and screenshots, with raw report under ignored loop10 .studio-local/evidence-raw/readiness-final-2026-10-25/. No application source changes follow this receipt.
