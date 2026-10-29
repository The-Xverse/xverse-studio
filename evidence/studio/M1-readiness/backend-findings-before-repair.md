# Readiness/admission findings before repair

2026-10-25, baseline21df9dc. Five tests in `tests/integration/test_preflight.py` failed in6.09s before repair.

- READY-001: ten specified independent readiness facts and digest-bound frozen plan preview are absent. The UI reads nonexistent `checks`, hiding even current dimensions and limits.
- READY-002: an explicit unavailable `xverse.lite` selection is recorded as `studio.reference`; its blocked snapshot still carries a valid reference configuration and reference limits.
- READY-003: campaign preview and creation accept that blocked snapshot because they require only configuration/planDigest. Both route probes failed (200/202 instead of422), without a process launch. Prevent alternate admission from silently selecting an unrequested reference provider.
- READY-004: an admitted descriptor with a required resource limit removed is still reported ready; unknown limits must block rather than be replaced with defaults.

Repair scope: preserve selected provider, independent read-only facts, exact limits and plan identity; immutable blocked snapshots cannot become execution/campaign authority. Existing frozen source/evidence stays unchanged. Windows installation/testing remains held.

READY-005: two further valid-XDL probes found optimistic facts: changing the declared simulation clock rate still reports compatible, and a Component model reference changed to an unavailable URN still reports artifacts available because only Deployment artifact bindings were checked. Preserve model-valid versus target-blocked, but inspect the actual declared clock contract and all required model references before those independent facts can be positive.
