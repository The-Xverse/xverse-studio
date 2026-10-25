# Source register and baseline qualification

Prepared 2026-10-25. This register separates user-authorized product intent, architectural source,
historical release evidence, inspected repository identities, and proposed Studio implementation.

## User intent

The user requested a complete Spec Kit plan in `The-Xverse/xverse-studio`, to be implemented by Codex
or Claude. The correction to the initial proposal is binding: X-Verse is industry agnostic; ECUs are
an example. Studio should let non-experts compose systems, choose simulated/software/emulated/physical
realizations, persist XDL, inspect X-COM-related connections/evidence, run experiments, and understand
logs/results. This planning change does not implement the application or authorize physical operations.

The user's subsequent platform clarification is binding: Studio is a web-based application that must
run on Linux and Windows. This package interprets that as a shared browser UI and natively runnable
backend on both hosts, with separately declared/tested runtime-provider compatibility.

## Inspected repository identities

These main heads were read on 2026-10-25. They are reference identities, not a claim that the three
heads form an admitted interoperable runtime set. M0 must select and verify that set explicitly.

| Repository | Inspected main commit |
|---|---|
| xverse-studio | `9b1d5fe0772feb8bf6110eae5eddb2c1d393588d` — initial README and LICENSE |
| xverse-platform | `7fab6a290c3731533c2b88517158055c768b9d4e` |
| xverse-compat | `f5b3957ca84cccfd98cddd9eb3ab95b0a4643eed` |
| xverse-blueprints | `0741e01b9e86b9bb9360e2feb220807b36bcbdc4` |

## Primary architecture and implementation references

| ID | Reference | Use and evidence limit |
|---|---|---|
| SRC-01 | [Domain-neutral metamodel](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/docs/architecture/METAMODEL.md) | Core meanings, identity/realization distinction, profile boundary. Architecture, not runtime proof. |
| SRC-02 | [XDL resource model](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/xdl/specification/RESOURCE_MODEL.md) | Five resources, endpoints/flows, deployment bindings, unresolved profiles, opaque assessment expressions. |
| SRC-03 | [XDL Lite maintenance](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/docs/engineering/xdl-lite/maintenance.md) | Validator/compiler entry points and semantic/source identity rules. Compilation is not execution. |
| SRC-04 | [Lite 1.0 release record](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/docs/releases/xverse-lite-1.0.md) | Historical 24 October rc.1 compatibility set, bounded execution and evidence limitations. |
| SRC-05 | [Closed-loop blueprint](https://github.com/The-Xverse/xverse-blueprints/blob/0741e01b9e86b9bb9360e2feb220807b36bcbdc4/automotive/thesis-lite-carla-closed-loop/README.md) | Concrete integration entry points; verify current admission before adapting. |
| SRC-06 | [Platform subsystem boundaries](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/docs/architecture/PLATFORM_SUBSYSTEMS.md) | Maestro, X-COM, Argus responsibility and broader target allocation. Older maturity summaries must be reconciled with newer feature evidence. |
| SRC-07 | [SADS allocation register](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/docs/architecture/sads-requirements-traceability.json) | Public source IDs/owners/dispositions; contains allocation, not complete normative source text. |
| SRC-08 | [X-COM communication plan](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/specs/007-xcom-core/contracts/communication-plan.md) | Reference for communication contract integration during M0; no assumption of native core activation by Lite. |
| SRC-09 | [X-COM tool gateway](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/specs/007-xcom-core/contracts/tool-gateway.md) | Host-side controlled observation/stimulation boundary, not direct browser access. |
| SRC-10 | [Lifecycle](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/specs/005-component-catalog-compat-runtime/contracts/lifecycle.md) and [permits](https://github.com/The-Xverse/xverse-platform/blob/7fab6a290c3731533c2b88517158055c768b9d4e/specs/005-component-catalog-compat-runtime/contracts/execution-permit.md) | Ownership and execution constraints to retain behind the Studio facade. |
| SRC-11 | [Spec Kit v1.2.3](https://github.com/github/spec-kit/tree/5ea8b1cf0a38699340a38e00d02770308997d8c0) | Actual initialized tooling; see `../../docs/implementation/SPEC_KIT.md`. |

## Historical verified integration envelope

SRC-04 records platform `a9db0ac39a858c0b2d341149042a8a97b7dcf393`, compat
`30446f6c7f234ec600398ba5db6c57846210c772`, and blueprints
`5fa8bcba3545e5675e512baf5baa5738bac42599` as its compatibility set. It describes XDL Lite,
Maestro Lite, Argus Lite, faults, flows, and a bounded CARLA closed loop.

In that record, the blueprint uses a trusted-host run path while the external RuntimeService path is
closed to it; Python Lite flow evidence does not activate the C++ X-COM core. The admitted configuration
has single-host, five-unit, and approximately 90-second run-closure constraints, with limited active time.
These are historical configuration limits, not universal product limits or assertions about current heads.

Newer heads exist. M0 must read their accepted contracts, review/acceptance records, and capability
declarations, pin the chosen compatible set, and record differences. It must not infer a generic API,
unlimited runtime, native X-COM inspection, or completed hardware support from the presence of files.
Older top-level documentation may be stale. Exact accepted feature evidence takes precedence over a
general maturity summary; unresolved discrepancies stay explicit.

## Allocation to platform requirements

The public register allocates **XVE-SYS-0159 through XVE-SYS-0178** to UI / SDK. Studio is the proposed
owning presentation/control capability for those IDs; status here is **allocated**, never implemented.
The public rows do not include their normative wording, so no statement-level satisfaction is inferred.
M0 records an applicability assessment against an accessible authorized source before claiming SADS
coverage. This does not prevent implementation of the explicit user-derived FR/NFR in this package.

Scenario, results, observability, security, extensibility, time, and fault/recovery areas also have shared
ownership. Allocate Studio's presentation/control portion and retain platform/provider dependencies;
do not claim that building the UI implements the underlying system-level service. Preserve source IDs
exactly and do not copy private source material into this public repository.

## Decisions still requiring implementation evidence

The React/TypeScript graph frontend, Python control service, local persistence, API contracts, reference
performance targets, usability targets, and M0–M4 deliverables are Studio design decisions. They are
not capabilities proven by the sources. Pin actual supported library/runtime versions during M0.
All acceptance cases start NOT_RUN. Planning checks validate document consistency only.
