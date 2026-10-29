# ADR-0019 — Scenario intent and recorded-evidence timeline

Status: implementation in progress; UI and combined acceptance evidence pending.
Date: 2026-10-27.

## Context

T084/T088 and FR-053/FR-057 require a timeline that distinguishes authored intent,
recorded events and observations, fault requests/effects and immutable evaluation
outcomes. The current schedule list presents the first step's clock as a scenario
summary. It does not correlate the selected run's frozen intentions and evidence.
Current draft edits cannot supply an executed scenario's identity or intentions.

## Decision

Add Studio's read-only `GET /runs/{runId}/timeline` projection, version `1.0`, over
the existing verified snapshot, canonical journal reader and immutable evaluation
records. This is an additive Studio facade, not a new platform/provider operation.
It never starts, probes, reserves, evaluates, recompiles an alternative model or
modifies source, snapshots, journal bytes or derived evaluation results.
The read model belongs to the `timeline` feature package, above the foundational
reader/XDL packages. The architecture checker recognizes that feature explicitly;
foundational packages cannot import it. Scenario editing remains in the existing
XDL semantic helpers rather than gaining an orchestration dependency.

The report identifies the exact run, snapshot/digest, project revision and selected
System/Deployment/Scenario. Snapshot verification and authoritative full-source
validation precede source projection. Only the selected frozen Scenario contributes
intentions. The current project is not a fallback. Unknown versions, invalid source,
unverifiable snapshots and foreign selections cannot yield a resolved timeline.

Rows distinguish `intent`, `recorded` and `evaluation` layers. Source declarations
remain intentions, fault-request records remain requests, and observed fault records
remain observations within their actual evidence scope. Evaluation execution status,
verdict/value, definition identity/window and exact evidence provenance stay separate.
An evaluation covering a window is a range, not a source event at evaluation receipt
time. A metric value is not an assertion verdict or a lifecycle result.

Original source tick strings and clocks remain intact. The existing owned-reference
v1 codec alone admits simulation-time microsecond ticks. Its frozen configuration
and exact provider identity can additionally admit the authored seconds encoding
for display in that same clock. The conversion is an explicit backend presentation
codec, never a generic unit table, clock synchronization or runtime permission.
Other clocks/units, unknown mappings, nonintegral positions, missing times and opaque
fault activation/recovery strings remain unplaced with reasons. Receipt time is
displayed independently and never substitutes for source time. Same-axis ordering
establishes neither causality nor proof that an intention produced an effect.

Journal integrity, original gaps, incomplete coverage, retained-page omission and
projection limits remain visible. Unavailable observations do not establish absence.
The endpoint returns at most 200 rows per page. Processing considers at most 50,000
canonical records, 1,000 authored declarations and 200 recent evaluation records,
with explicit incomplete/truncated metadata. Existing reader acquisition/byte bounds
still apply. No chart reduction can attest full-data assertion coverage.

Opaque cursors bind the route version, run/snapshot, selected clock and exact current
record/evaluation input identities. Changed inputs or a foreign context refuse the
cursor and require a fresh read; the browser must not merge pages into a supposedly
unchanged live timeline. Unsupported/private payload fields are not copied into
timeline rows. Canonical references remain exact; source/raw evidence access retains
its existing separate contracts.

The browser will offer clock selection, a structured keyboard alternative and
clearly labelled placed/unplaced rows, preserving exact ticks beyond JavaScript's
safe integer range. Draft authoring remains a projection of canonical XDL through
existing forms. Native completion tests must preserve newer drafts, project/scenario
selection, history, focus and run snapshots while backend acknowledgements arrive.

The owned reference profile's frozen `fault` parameter also appears as a distinct
configuration-intent row with its source field and configuration digest. It is
not a fabricated Scenario fault element and has no inferred authored position.
Its requested/observed records retain their actual independent event identities,
provider/version and source times. The observed tick-unit codec remains separate
from the frozen-input codec that admits authored seconds; unavailable effective
input agreement cannot align source declarations. Evaluation rows preserve reason
codes and the bounded evaluator identity, including its implementation digest.

The implemented browser uses explicit abortable reads, exact context/version
checking and bounded independent pages. It clears a report on clock/project/run/
revision/Scenario changes and refuses changed-input page continuations. Exact
integer strings remain strings/BigInt; only bounded relative screen coordinates
use Number. A current-draft timeline uses original declared units without mapping,
and opens the existing canonical typed edit forms. Local form completion requires
an authoritative current-intent acknowledgement. Newer/reopened drafts and dialogs
survive older acknowledgements, and synchronous submission guards prevent overlap.
These are implementation decisions; their actual verification and limitations are
recorded separately, and they do not close the full native-platform acceptance gates.

## Compatibility and verification

HTTP major v1, XDL/profile definitions, evaluator semantics, runtime/provider
capabilities and the original task/requirement IDs remain unchanged. Advertise the
new read projection through the actual generated HTTP contract. T084/T088 remain
partial until their complete scope and native-platform gates have evidence.

The committed generated HTTP schema had lagged existing inspection, connection,
presentation, recovery, revision, diagnostics and binding/resolution routes.
Regeneration synchronizes those existing routes and the existing Recovery request
type as well as the new timeline. Generation from the exact unchanged predecessor
server proves all other server contract semantics unchanged; this is a generated
artifact reconciliation, not additional implementation or new provider support.

Verify actual owned reference fault-request/observed records, frozen-versus-draft
identity, evaluation windows/provenance, unsupported clocks, exact large ticks,
missing/gapped/unavailable evidence, duplicate/foreign selectors, cursor expiry,
bounded pages and immutable input preservation. Synthetic transport/reader fixtures
must be labelled and cannot establish live-device or external-provider support.
Windows, actual assistive technology, permitted live fault operations and milestone
acceptance retain separate evidence requirements.
