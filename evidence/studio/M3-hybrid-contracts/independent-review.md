# T076 independent clause audit — 2026-10-26

The primary agent reviewed tests authored by the separate `t076_hybrid_tests` agent, including all
assertions and mutation harness. No application behavior was changed for this task. Verdict: fixture
clauses covered; live AC-023/024 remain blocked. Final successor regression results are recorded
separately after T072's adjacent binding changes.

| Clause | Evidence |
| --- | --- |
| Virtual/physical substitution | Real source-backed Deployment save/rebind retains System bytes and graph refs, while authoritative compiler reports unsupported physical realization; fixture binding keeps logical identity and exposes changed controls without equivalence claims |
| Interface mismatch | Missing/different interfaces reject; input remains unchanged; only fixture inventory is read |
| Missing clock evidence | Missing domain/tick, incomplete mapping proof and invalid uncertainty remain unknown; receipt time never substitutes |
| Unplug | In-memory disconnect rejects access, reconciles ownership to unknown, preserves held fixture resource and reports unconfirmed physical state / failed stop request |
| Refused stop | Raw refusal retained, no retry or inferred safe/clean state |
| Failed restore | Synthetic provider stop evidence retains failed cleanup/restore and observed stop independently; no restore capability invented |
| No physical pause/rewind assumption | Unsupported restore, rewind, pause and reset policies never call the provider |

The three source mutations have passing controls and failing mutated tests: receipt-as-source,
unsupported restoration delegation and failed cleanup interpreted as complete. They execute only in
isolated child-process memory. Initial test assertions used the wrong authoritative diagnostic and
expected a resolution report even though the compiler rejected first; corrected outcomes preserve
`XDL1-PLAN-REALIZATION-UNSUPPORTED` and a missing provider-resolution report.

Limits: fixture contracts and actual pinned XDL validation/compilation only, no actual hardware,
physical clock measurement, live restore/stop or native Windows result. These tests do not close
T077 implementation or M3 acceptance.
