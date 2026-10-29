# ADR-0034: Correlated Maestro, native X-COM and Argus views

Status: implementation in progress; new user-authorized goal, not acceptance.
This amends the existing Studio plan without replacing requirements, task IDs,
contracts or previous decisions. The working Autoverse preview remains separate.

## Required result

One actual experiment must be executable through an admitted Maestro interface,
exchange messages through native C++ X-COM, persist its actual lifecycle and
communication evidence through Argus, and expose three linked Studio views:
Orchestration, Communications and Evidence. The original run, plan, semantic,
logical element, event, correlation and causation identities must survive every
projection. Transport labels, unknown clocks, gaps and integrity remain explicit.
The goal is not satisfied by Studio lifecycle events, Zenoh/SOME/IP messages,
Lite flow emulation, generated display records or three disconnected fixtures.

## Historical baseline and original prerequisite

The original selected platform was commit `7fab6a290c3731533c2b88517158055c768b9d4e`.
Its installed distribution includes public `xverse.argus.EvidenceStore` readers.
Its native headers expose X-COM observation and local tool-gateway contracts;
compiled artifacts and the host/provider/payload permissions need admission.

Maestro's top-level exports expose preparation only. The candidate
`runtime_service.RuntimeService` is execution-disabled by default and its
`RuntimeSubmission.run` requires `_OriginalRuntimeRun`. The release record also
keeps this candidate service closed to the blueprint. No Studio adapter may
construct/import the private run class or synthesize readiness/review approvals.
An accepted public execution submission boundary is therefore required upstream.
The user subsequently authorized this separately scoped platform work on 2026-10-29,
including specification, implementation, tests and review. Capability
022-maestro-public-execution tracks that work in the platform. The following
acceptance amendment supersedes the original outstanding platform prerequisite.

`AGENTS.md` authorizes Studio implementation but reserves companion changes for
separately scoped work. The later user authorization grants the described platform implementation scope;
it did not grant automatic platform acceptance. Independent Argus, observation,
identity and projection work proceeds.

## Accepted public boundary and dependency amendment — 2026-10-29

The user's explicit “I accept” accepted the frozen public platform boundary.
Accepted code merge `f0e57c844bf9a23b18836c86ca6ca11b4f4b1282` was rebuilt and
verified in an isolated assembled checkout before local main was fast-forwarded.
Platform main `ce2d5558cd36de5b29ab1e3c622303c7a77c61eb` adds the assembled
verification record without changing the accepted runtime/test source. Its 190
Python checks and three CTest cases passed; all nine installed implementation
modules and the rebuilt native helper matched the accepted candidate. Source
fingerprint: `0f1c5bd2040c1a8e1a0b6997269ec27ab5edcf32c0924a2a9fa2388595069045`.
The platform acceptance decision and `docs/engineering/maestro-public/evidence/main/verification.json`
retain that scope. No publication was authorized or performed.

Studio now pins that exact local main revision in its dependency, lock and adapter.
The admitted public package is `xverse.maestro.execution`: actual effective-input
inspection, host-bound `PublicExecutionService`, explicit per-binding lifecycle
phases, bounded start/stop and registered native observation collection. It writes
actual Argus lifecycle/evidence records. Host permits bind the actual root,
installation, inspected inputs, lifecycle and finite execution budget; they are
never supplied by browser/project metadata. This does not open the older private
runtime service or admit physical, hybrid, remote or Windows execution.

The neutral native platform experiment is boundary verification. Platform T07,
the actual Studio/Autoverse integration, remains open after acceptance and main
integration. The production demo must expose actual per-binding acquisition,
readiness and reverse cleanup through Maestro; wrapping the old complete worker
as one phase would not meet this contract. Actual demo payloads must traverse
native C++ X-COM, with original ingress facts, observation/snapshot counters and
unknown upstream causes preserved. The three linked browser views and their
bounded payload policy are still required. Existing task IDs, counts, dependencies
and milestone gates are unchanged.

## Concrete upstream execution contract proposal

The platform must own the public operation names and implementation. This is an
input/output requirement for that capability, not an invented callable API:

1. Accept explicit canonical XDL documents/selection, authoritative compiled plan,
   semantic/plan digests and caller run identity. A host-owned allowlist pins fixed
   provider commands, binaries, OS, limits, resource ownership and permits outside
   submitted project content. No project command strings or self-issued approvals.
2. Provide side-effect-free effective-input inspection before admission. Return
   actual effective document/plan/semantic identities and unsupported semantics.
   Studio rejects any mismatch before process, message or device activation.
3. Accept start idempotently for the exact inspected submission; Maestro owns
   preparation, scheduling, process/container resources and bounded orderly stop.
   Return stable run/operation identities and monotonic observed state versions.
4. Publish original lifecycle records with logical element and evidence references,
   distinguish requested/observed/unknown outcomes and expose disconnect/reconnect,
   ownership loss, failure and cleanup results. No restart from an observation gap.
5. Bind the same run and plan identities to admitted X-COM routes/observations and
   Argus output. Expose a read-only evidence handle under declared finite limits.
6. Exercise start/stop, stale inspection, effective-input mismatch, missing permits,
   repeated start, partial launch, lost ownership, slow observers, journal failure
   and honest cleanup against the actual native components. Source review and
   acceptance must be recorded by the platform's own workflow.

## Studio implementation and boundaries

The explicit `autoverse.platform` / `urn:xverse:studio:autoverse:platform:1.0`
contract is distinct from the historical classic demo. It preserves logical
resource URIs, uses new executable resource versions and a separately digested
integration artifact, and leaves the classic authored bytes unchanged. The
existing generic native-runtime schema admits its explicit provider/contract
identity; no unknown extension is dropped to make execution possible.

Scenario observer timing denotes host-scheduled collection. Original native
process elapsed clocks are declared separately to Argus, without conversion to
host or simulator time. An initial two-clock scenario failed the authoritative
compiler's required mapping check; that source and diagnostic remain retained.
The final contract does not assert a nonexistent synchronization mapping or use
native source clocks for scenario scheduling.

Host enrollment explicitly selects the verified native build and a persistent
private Maestro root under the Studio data root. A per-run grant binds the actual
current artifact/installation identity, compiled inputs, phase graph and runtime
root to at most 2700 seconds (requested driving duration plus 900 startup) and
60 seconds cleanup. This is the public interface's host policy, not a private
runtime review/containment waiver. Imports cannot nominate a root, binary or grant.
All runs in that registration reuse the same root; unresolved claims are never
bypassed by allocating a new run root. Shared installation ownership still fences
classic and platform providers against simultaneous acquisition.

The provider delegates individual component acquisitions and cleanup through
Maestro. Separate supervision can cancel a start without calling Stop from a
callback holding the SDK operation lock. Normal running Stop first quiesces the
native bridge and imports its final batch, then requests public Maestro Stop.
Native faults abort through an actual provider observation and retain incomplete
evidence. Backend shutdown allows the installed provider's bounded cleanup budget.
Signed bounded SDK read snapshots are derived metadata; canonical records remain
in Argus. Complete live/browser acceptance remains required.

A host-installed binding selects admitted service/reader implementations and roots;
HTTP requests choose opaque IDs, never host paths, binaries, sockets or credentials.
The evidence adapter calls the actual public Argus reader, preserves raw accepted
records and both recorded and assessed evidence states, and never upgrades partial
or invalid evidence. Browser projections are derived and carry source references.
Explicit correlation/causation IDs form links; receipt ordering never invents cause.

The Orchestration view will consume actual Maestro lifecycle facts and operations.
Communications will consume native X-COM observations, with payload policy, routes,
sequences, original clocks and drop counters. Evidence will expose Argus verification,
original records and links to the other views. A missing binding is unavailable;
a fixture is labelled fixture and cannot complete the live acceptance case.

## Acceptance and existing traces

The new goal adds scoped work under T001/T004/T010/T012/T020–T024/T027–T030 and
T034–T035; existing dependencies and milestone gates remain. Verification must
show one live shared-identity experiment, GUI start/stop, cross-view navigation,
native X-COM exchange, actual Argus verification and failure/gap behavior on the
same candidate. Native Windows and physical providers are separate held claims.
No broader task or milestone closes from this amendment or isolated reader tests.


Argus naming note: the selected Argus manifest field `plan.semanticDigest` contains
`compiledPlan.digest`, which is Studio's `planDigest`. Studio's authored-input
`semanticDigest` comes from `plan.provenance.inputSemanticDigest`. The reader adapter
must preserve that distinction; it cannot infer the latter from the former. The
first internal adapter exposes original accepted Argus records only to trusted
host code. A browser projection still needs a declared payload/log policy and
live snapshot/paging behavior; this internal reader is not a completed dashboard.
