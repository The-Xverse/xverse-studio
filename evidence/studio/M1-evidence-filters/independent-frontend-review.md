# Independent frontend projection review

Read-only review on 2026-10-25 of the six-green successor found no concrete remaining issue in the reviewed evidence-filter slice. No frontend source or tests were changed by this reviewer, and no duplicate browser workload was launched. This is a source review; browser evidence remains the separately retained six-green receipt.

The source uses BigInt for exact signed tick comparisons and half-open source windows; RFC3339 receipt windows remain a separate time basis. Reader-declared unavailable receipt timestamps override raw values. The live-buffer notice explicitly states that numeric receipt timestamps without reader metadata are unavailable and directs users to retained history. Missing/malformed time is inspectable in tables and is never replaced with an array index or zero. Differing reported resolutions/quantity units select a table-only presentation without inferred conversion.

Observation reads carry run/snapshot/filter/element identities plus abort and generation guards. Retained history reads carry run/filter/tab/source identities and abort guards. Old identities render empty data while fresh reads are pending. Retained pages are bounded at 200 records, predicates precede backend pagination, and page-local text search is labeled. Element filtering stays local to the evidence view; annotation navigation remains separate. The repaired live-loading gate and unit/resolution fallback are present in the reviewed source. No assertion about physical clock mapping or collection completeness is inferred from filtering.

Reviewed source SHA-256:

- evidenceFilters.ts: `fa45adba5d236b0d654943bcff8d4a49141107bafd335f9ed9082bf349b9fd35`
- ObservationDisplay.tsx: `a2998ad2a45f821c0408816f60ed881ea8fc3cde7600dd0dd7d0ef00bb002b9d`
- EvidenceFilterControls.tsx: `1e655c0441994cee7f13c09181075ebf772d075c90688c11319bdc38cd8fae5d`
- ResultsView.tsx: `92f13dac5b75d6e6881fd264962369ca2a1ec94d5c31ebc724c6cc036d592e63`

Windows installation/testing remains held. This review does not close native-platform, external-provider, or milestone acceptance gates.

## Keyboard/raw-receipt successor amendment

Read-only recheck of the keyboard-green successor found no concrete issue in the small follow-up. ObservationTable now has a named focusable scroll region with a visible focus outline, an explicit 8-of-N field caption when columns are bounded, and a disclosure containing the unchanged original recordedAt value. Normalized receipt presentation remains separate from that original value. No plot/filter/request semantics were changed in this follow-up. The retained author receipt reports six native browser checks passing in 33.7 seconds; this reviewer launched no browser or provider.

Successor SHA-256: ObservationDisplay.tsx `19a4fae4cbfc75bd818df753d6e888bf1263707a8698730290b63807ca84aca6`; evidenceFilters.css `03f5186afe6f50f109a49df908868a208b455be92ab80e139f1bfc5812f7a31a`; ResultsView.tsx remains `92f13dac5b75d6e6881fd264962369ca2a1ec94d5c31ebc724c6cc036d592e63`.
