# ADR-0055 — Explicit provider fault clocks in timeline 1.1

Date: 2026-10-30. Status: implemented; scoped actual Autoverse/API/browser verification passed.

Keep timeline HTTP 1.0 as the default with its original clock rules. Clients may
explicitly request formatVersion=1.1 to use an installed provider's read-only
fault-clock interpretation. This is a Studio adapter interface, not a new platform
execution API. The generic timeline does not dispatch on industry/provider names.

After protected snapshot/source/selection validation, an optional installed-provider
callback may return a bounded strict clock context. It binds provider/source version,
evidence scope, named codec, declared clock, exact microsecond ticks, epoch, allowed
event kinds, event tick field and fault activation/recovery positions. No imported
project, metadata or log supplies executable callbacks. Invalid/unavailable context
leaves rows unplaced with a bounded sanitized diagnostic. Version and context bind
cursor identity; 1.0/1.1 pages cannot mix.

The classic provider's read adapter recompiles frozen XDL, reproduces the full
configuration and verifies effective plan/semantic identities before recognizing
its existing 0.2.0 input-loss codec. It supports that exact recorded contract; no
current runtime resource contact, installation probe or lifecycle call occurs.
Only matching canonical source/version, declared fault IDs/kinds, original clock,
resolution and tick/payload equality permit recorded placement. Integrity failures,
unknown encodings, foreign events and missing times remain unplaced. Ordinary
telemetry receives no inferred source time. Host-relative placement is not simulation
clock synchronization, causality, physical effects or an assertion verdict.

Frozen fault intentions retain separate rows, activation ticks and recovery end ticks
from the admitted provider's recompiled plan. The current draft timeline separately
displays typed experiment-lite fault timing in original units. It does not convert
units or present drafts as effects. Unsupported profile versions/payloads stay opaque.
The browser explicitly requests 1.1, validates its context and retains exact decimal
string ticks, original gaps, reasons, clocks and provenance.

Verify actual recorded Autoverse positives, legacy behavior, mismatched inputs/codec/
versions/ticks/clocks, gaps/integrity, callback failure/shape bounds and stale cursors.
Finish with the complete GUI-authored native demo and real browser timeline inspection
at both desktop sizes. Preserve original canonical evidence. T084 completion requires
its original forms/clock/intent/observation/unavailable clauses, not this decision alone.

Verification:170 actual Autoverse API/projection/library checks, complete native
GUI-authored demo and two real browser cases spanning both desktop sizes passed.
Source/plan/canonical/native readback and task clause audit complete T084; full
AC025 and independent milestone acceptance remain open. See the
[review](../../evidence/studio/M4-fault-timeline/review.md).
