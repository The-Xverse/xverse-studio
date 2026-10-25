# X-Verse Studio Constitution

Version: 1.0.0 | Established: 2026-10-25 | Last amended: 2026-10-25

Status: initial constitution authored from the user's Studio planning request. This defines
implementation obligations; it is not product acceptance or evidence of runtime capability.

## I. Industry-agnostic composition

Studio SHALL use domain-neutral cyber-physical concepts. Industry vocabulary/templates SHALL live
in namespaced profiles and blueprints. A second industry SHALL use the same core model, authoring,
execution, and evidence contracts without a core industry fork. Role, realization, and placement
SHALL remain independent. Physical devices SHALL be first-class realizations.

## II. One executable source of truth

XDL SHALL remain authoritative. Studio SHALL reuse platform validation and compilation, preserve
stable identities, and separate presentation state from executable identity. Unsupported profiles and
versions SHALL remain intact and unresolved; they SHALL NOT silently become executable. GUI/CLI
semantic equivalence SHALL be tested using the same compiler and contributing inputs.

## III. Explicit authority and capability

The backend SHALL enforce capabilities, ownership, preconditions, resource/time limits, and permissions.
The browser SHALL NOT own execution processes or privileged device interfaces. Imports SHALL NOT
implicitly execute code. Runtime/physical operations SHALL require admitted integrations verified in
the claimed environment. Implementation authorization is not authorization to modify or stimulate
unrelated systems. Continue independent authorized tasks when one external operation is blocked.

## IV. Truthful state and evidence

Validity, readiness, liveness, functional observations, assertions, cleanup, and evidence integrity SHALL
remain distinct. Runs SHALL bind immutable inputs to provenance-bearing results. Draft edits SHALL NOT
silently change active runs. Observed, inferred, unknown, unsupported, partial, and failed states SHALL
be distinguishable. Missing data and clock uncertainty SHALL be visible. Observation replay SHALL be
separate from re-execution and from evidence of determinism.

## V. Accessible operation and useful failures

Studio SHALL be a web application with a browser UI and a backend that runs natively on Linux and
Windows. Installation and core operation SHALL NOT implicitly require WSL, Bash, or containers.
Each provider SHALL expose its own verified OS compatibility independently of Studio's core support.

First use SHALL guide a user through a supported example. Controls SHALL explain purpose, units,
constraints, failures, and recovery actions. Expert source access SHALL use the same model. Essential
operations SHALL support keyboard use and avoid reliance on colour or hover. Actual novice-task
measurements SHALL establish usability outcomes.

## VI. Modular integration and bounded operation

Studio SHALL consume versioned platform contracts. Maestro retains lifecycle ownership; X-COM retains
communication boundaries; Argus supplies evidence. Communication, physical coupling, deployment, and
traceability relationships SHALL remain distinct. Profile presentation metadata SHALL NOT execute
plugins. Browser availability and rendering SHALL NOT govern simulation timing or evidence recording.
Queues, storage, telemetry, campaigns, and resource use SHALL have declared bounds/failure semantics.

## VII. Traceable incremental delivery

Every committed requirement SHALL map to tasks and acceptance cases. Milestones SHALL retain
exact-candidate evidence, meaningful failure tests, independent review, and residual limitations.
Mocks and skipped tests SHALL NOT establish live capabilities. Admit and pin dependencies explicitly;
source inspection is not runtime admission. Future scope SHALL remain separate. Never rewrite recorded
failures to create a false acceptance history.

## Governance

Architecture and technology allocation are in `specs/001-industry-agnostic-studio/plan.md`. Changes to
shared semantics, authority, persistence, security, or timing require a short ADR with rationale,
compatibility impact, and affected verification. Routine authorized implementation does not need a
new user approval. Amend this constitution with a version, reason, and impact assessment.

Specification completion differs from product acceptance. The planning package requires structural
checks and content review. Each implemented milestone requires its own evidence and environment.
