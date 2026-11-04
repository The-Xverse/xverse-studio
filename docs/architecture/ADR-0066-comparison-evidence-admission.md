# ADR-0066 — Numeric comparison requires an admitted evidence interpretation

Date: 2026-11-04. Status: repair implemented; final verification pending.
Traces: T091; FR-059/FR-060; NFR-002/NFR-009; AC-029.

The recorded comparison decoder currently assigns owned-reference unit definitions
to matching numeric payload shapes from any provider. A complete inert external
source fixture becomes compatible, and reference-shaped decoded copies of actual
Autoverse records acquire the reference unit definition despite lacking that
interpretation. Canonical integrity and matching field text do not admit quantity,
clock or coverage semantics.

Gate the existing numeric decoder with the same protected source-identity checks
already used by the owned-reference evidence interpreter. Reuse evidence_support
without supplying an installed assessment provider: a provider's Boolean/event
assessment mapping is not numeric comparison admission. This admits no new reader,
provider, version, callback, runtime operation or hardware authority. Historical
reference reader/journal metadata omissions retain their existing compatibility.
Required run/snapshot/project context and the protected snapshot digest must be
nonempty strings. Equal null, empty or numeric values do not establish identity.

Unsupported sources return COMPARISON_EVIDENCE_UNSUPPORTED and no interpreted
numeric observations. Preserve original integrity, lifecycle, effective-input and
frozen configuration facts; configuration differences remain inspectable. The
comparison explanation directs the user to original observation records. Raw
history and ADR-0065 playback remain available and unchanged. Do not mark original
evidence invalid or rewrite it to fit an owned schema.
Do not interpret an unsupported source's original evidence-status vocabulary as
owned-reference completeness. Keep its original status visible and compatibility
blocked by unsupported interpretation. Known reference partial evidence still
blocks every field; original reader integrity checks remain independent for all
sources.

The backend comparison API continues to verify protected snapshots before this
pure decoder. Project/profile/log declarations cannot opt into its interpretation.
A future external numeric interpretation needs explicit admission for its actual
quantity, unit definition, clock and coverage contract; an assessment callback or
shared JSON envelope cannot stand in for it.

Verify the false positive before repair, the known-codec and legacy positive
controls, individual context/scope/reader mismatches, forged support declarations,
and actual immutable Autoverse sources with labelled decoded-copy negatives.
Repeat affected pure comparison checks and real read-only Autoverse comparison/
playback browser journeys. No new reference workload, simulator or physical
execution is needed or authorized by this repair. Full T091 rerun/Windows and
milestone acceptance remain open.
