# Independent literal T018/T019 component audit

Read-only source, test and requirement review on 2026-10-25. This reviewer did not author the preflight implementation or its new admission tests. No additional tests or product/tracker changes were performed for this audit. Root separately retains the actual 30-pass admission receipt and source identity; this document does not claim independent execution of that suite.

## Recommendation

Close T018 and T019 for the implemented owned reference component. No concrete gap remains in their literal task bodies. Native Windows, external/live-provider and complete acceptance/milestone gates retain their own requirements and status; this is not milestone closure.

T018 explicitly requires stale-input/capability, missing-artifact, unknown-limit, exceeded-budget, missing-clock and ownership-conflict tests. Inspected coverage includes authored revision changes, expiry and changed provider identities, canonical snapshot corruption, current resource occupancy, unknown/incompatible version/OS/architecture/start/authority facts, advertised duration and sample overruns, one/all artifact-binding omissions and digest mismatch, unavailable clock admission and public required-mapping validation, uncertain owner capacity, conflicting authority and unsupported parameter units. Negative dispatch sentinels ensure refusal precedes process creation. Unsupported-source fixtures are not described as supported external runtime evidence.

T019 binds plan preview to snapshot ID/digest, revision, selected resources, compiler and plan/semantic identities. Start verifies canonical frozen bytes, profile locks and current project inputs, recompiles the selected contributing sources and immediately repeats current descriptor/host/capability, target, resource/capacity, clock and authority checks inside durable admission. Fresh configuration and plan identities must match the snapshot before dispatch; the owned worker independently confirms effective compilation identities. Unsupported edits cannot become an executed fixed preset.

The selected unavailable provider is retained in blocked preflight/snapshot records with unknown/unavailable dimensions; it is not substituted with the reference provider. Campaigns require their original matching ready preflight and frozen snapshot and delegate children through the same Start guard. Fresh reruns verify original frozen inputs and use current Start admission. The internal frozen-input option skips draft equality intentionally; it does not skip provider, authority, budget, clock or effective-plan checks.

The owned implementation exposes read-only declared admission, not equipment liveness, physical ownership, simulator support or externally measured clock synchronization. This scope matches the admitted reference provider and does not waive any acceptance requirement.

## Inspected source identities

- `services/studio-api/src/xverse_studio/preflight/__init__.py`: `sha256:69d4cfbe456925385cc868a8f9da58edc21cccdb566c608954cb1055dffc598e`
- `services/studio-api/src/xverse_studio/runs/service.py`: `sha256:ead5c3b2f96edecfbd69f3d819b5ad35280b9832b1980fa4c9fb51576e3dca8e`
- `services/studio-api/src/xverse_studio/api/advanced.py`: `sha256:e756904c8fe6db108e12e5b9e377b35953206c33c243cce9f06928917e8ffc0d`
- `tests/integration/test_preflight.py`: `sha256:578134b935d2af3fdf657e8eb465136d60eeba20a7789ca5f45bea45a5b8fd93`
- `tests/contract/test_runtime_lifecycle.py`: `sha256:449ea84b08a8b24b52c61d00ee39ea7cd95c9e7ff2576fa0f47559b511735aa5`
