# Independent review — draft/run snapshot overlay (2026-10-25)

A read-only reviewer inspected the first T047 candidate against FR-028, FR-015, AC-014 and AC-027.
Confirmed findings were repaired before the verified successor (the pre-review candidate's 575 backend
/ 61 browser run is superseded).

| # | Finding | Disposition |
|---|---|---|
| 1 | The comparison used the authored revision (`projectDocuments`) instead of the executed inputs (`documents`); a campaign child could show "matches" despite different inputs, and unused documents counted as run-input changes. | Baseline is the executed `documents`; other draft documents are listed as "not used by this run" and not counted. Pure regression for a campaign-style child. |
| 2 | Profile-lock (and sidecar) changes were never compared. | Draft manifest profiles are compared with the frozen `profileLocks` (their digests cover sidecars). |
| 3 | Parameters came from every scenario, dropped added/removed ones and used non-unique keys. | Only the run's scenario; added, removed and changed; keyed by scenario and id. |
| 4 | An empty node's placeholder produced a false "only in run"; definition changes left instances unmarked. | Nodes compared as declarations; instances of a changed definition marked "definition changed". |
| 5 | Any fetch error showed a permanent "unverified" without reason. | Integrity failure and unavailability are distinct, the reason is shown, and unavailability can be retried. |
| 6 | "Inspect frozen run inputs" only switched tabs; the snapshot digest was not shown. | Opens the read-only frozen inputs directly; panel shows snapshot ID and digest. |

Also addressed: frozen projection memoised per snapshot; panel closes when the selected run changes;
`aria-controls` only while open; singular/plural wording.

Retained limitations: changed documents open the draft source (frozen sources are read in the frozen
inputs view); canvas positions dragged but unsaved can be re-laid out when divergence first arrives.
