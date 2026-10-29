# Research and decision record

**Date**: 2026-10-25. **Status**: design decisions for implementation, not measured product results.

This record resolves the architectural choices needed to begin M0. Exact dependency versions and integration admission remain M0 tasks, with explicit failure outcomes rather than unspecified assumptions. Source identities and observed implementation boundaries are collected in [sources.md](sources.md).

| Decision | Selected approach | Alternatives considered / rationale |
|---|---|---|
| D-01 — Product abstraction | System-centric core; neutral Element action; XDL semantic types underneath | ECU-centric core would require domain forks. A universal untyped block would lose compatibility rules. |
| D-02 — Canonical representation | Existing XDL resources and authoritative validator/compiler | A second Studio graph language would create divergence. Editor layout stays in a sidecar. |
| D-03 — Extension boundaries | Declarative profiles, composed blueprints, separately installed providers | Loading arbitrary plugin code from project archives would conflate data import and code execution. |
| D-04 — Client technology | Browser-delivered React/TypeScript with React Flow graph projection | The user requires a web-based application. A desktop wrapper is optional; a custom graph engine would add work unrelated to X-Verse semantics. Browser technology does not imply cloud hosting. |
| D-05 — Control backend | Python FastAPI service with typed requests | Python reuses XDL package APIs. Implementing the control plane in C++ provides no demonstrated benefit here. Existing performance-critical data plane remains with its owners. |
| D-06 — Local persistence | Authored files plus SQLite metadata and immutable run snapshots | Browser-only state cannot survive independent runtime ownership. A distributed database is unnecessary for the initial single-host scope. |
| D-07 — Streaming | SSE for ordered event delivery; REST commands | A bidirectional socket is unnecessary for commands. Event cursors and resync remain explicit. High-rate data does not flow through command handling. |
| D-08 — Runtime integration | Narrow admitted adapter facade | Direct frontend shell launch and web routes importing a private runtime class would bypass lifecycle contracts and freeze accidental implementation details. |
| D-09 — Lifecycle truth | Independent lifecycle, cleanup, evidence and evaluation statuses | One success flag cannot express partial startup, orphan ownership, incomplete evidence or unevaluated assertions. |
| D-10 — Runs and editing | Immutable snapshot per run; edits create later revisions | Mutable in-place configuration makes results untraceable. Live changes require explicit provider capability and run events. |
| D-11 — Cross-industry validation | Automotive and process-control examples plus mixed-profile negative cases | Merely changing icon labels does not demonstrate domain neutrality. Second-domain fidelity is limited to the actual model evidence. |
| D-12 — Physical controls | Asset identity, reservations and capability-gated operations | Generic pause/reset/stimulate controls are not meaningful on every physical device. Logical identity is independent of asset address. |
| D-13 — Experiment evaluation | Versioned bounded evaluator with declared missing-data and time policies | Opaque XDL expressions are declarations, not proof of an existing evaluator. General-purpose eval would be unsafe and non-portable. |
| D-14 — Physical model coupling | Separate typed relationship, admitted only with modelling-provider semantics | Treating energy/force/fluid coupling as an ordinary message wire would hide numerical and physical compatibility requirements. General solvers are M5. |
| D-15 — Packaging | Native Linux and Windows local installation, offline core operation, locked toolchains | WSL or a Linux container is not a substitute for native Windows support. Hosted multi-user deployment introduces authentication, tenancy and scheduling requirements outside the initial scope. |
| D-16 — Host portability | Shared Python packaging/launcher with explicit OS path and process adapters | POSIX-only process control and Bash launch assumptions cannot meet Windows support. Keep OS mechanics out of domain semantics and prove both native lanes. |
| D-17 — Provider portability | Per-provider OS/architecture capability admission | Studio supports both hosts while individual simulators, emulators or hardware integrations may support only one. Explicit unavailable controls are more accurate than claiming provider parity or silently requiring WSL. |

## Current-source findings that constrain implementation

1. The domain-neutral metamodel already separates system, realization and experiment concepts. Studio should reuse it.
2. XDL Lite hashes declared resource content; presentation metadata must not be inserted into semantic fields merely because the schema allows labels/annotations.
3. The inspected Lite release implements a bounded integration; arbitrary launchable elements and unlimited run horizons are not implied.
4. The inspected rc.1 live blueprint uses a trusted-host runtime path and generates XDL internally. A fixed-argv wrapper of its documented run-live.sh entry point is the first integration candidate; it may expose only configurations whose effective XDL/plan identities can be proven before launch. GUI-edited input support requires an admitted successor input contract when absent. Newer 2026-10-25 heads require inspection in M0.
5. Lite flow evidence is not proof of an activated C++ X-COM core or a browser-accessible native gateway.
6. Argus integrity/availability and readiness limitations must remain visible in the product.
7. Existing model expressions and physical concepts do not imply general-purpose numeric solvers, assertion engines or hardware providers.

## Primary design references

- [X-Verse metamodel](https://github.com/The-Xverse/xverse-platform/blob/main/docs/architecture/METAMODEL.md)
- [XDL resource model](https://github.com/The-Xverse/xverse-platform/blob/main/xdl/specification/RESOURCE_MODEL.md)
- [XDL Lite identity and API maintenance](https://github.com/The-Xverse/xverse-platform/blob/main/docs/engineering/xdl-lite/maintenance.md)
- [Lite release record](https://github.com/The-Xverse/xverse-platform/blob/main/docs/releases/xverse-lite-1.0.md)
- [CARLA blueprint integration boundary](https://github.com/The-Xverse/xverse-blueprints/blob/main/automotive/thesis-lite-carla-closed-loop/README.md)
- [React Flow custom nodes](https://reactflow.dev/learn/customization/custom-nodes) and [connection validation](https://reactflow.dev/examples/interaction/validation)

These URLs are navigation references; use pinned source identities from sources.md for evidence. Toolchain admission must verify current official library documentation and license/dependency suitability before pinning. No cost, throughput or deterministic-replay claim is inferred from these technology choices.

## Decisions to finish during M0

Select and record exact toolchain versions, supported platform compatibility set per native Linux/Windows host, admitted real Lite execution adapter, resource/retention limits, reference performance environments and packaged distribution format. These are bounded implementation tasks. If no compatible runtime integration exists on a host, record DEP-RUN blocked for that provider/host, retain native model-only and fixture-backed operation, and continue independent work. Physical asset selection belongs to M3 and cannot be fabricated during offline planning.
