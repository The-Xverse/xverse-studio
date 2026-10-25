# Read-only follow-up after the combined browser run

The root-owned full run passed 35 checks and failed three with unchanged source; this is retained as a failing predecessor in `M1-session/full-before`, not counted as a successful final cohort. Root's findings-before-repair are `M1-session/full-browser-findings.md`. This follow-up does not overwrite that record or alter product/tests.

BROWSER-R02 source inspection agrees with the root finding: the parser's original 200-total-frame limit does not admit the backend's advertised 200 canonical frames plus reserved control. An unknown lifecycle state does not imply an unknown presentation loss count. The fixture's exact 1,015-record delivery gap is valid; the unknown-loss protocol case must remain a separate explicit fixture. A successor should accept the complete intended bounded batch and retain both canonical-data and total resource bounds. Independent successor inspection/probe is pending root's repair freeze.

BROWSER-R03 remains root-owned investigation. The current modal cleanup reads a mutable section ref inside a queued microtask; that observation alone is not independent proof of the focus failure's cause. The real keyboard expectation to return focus to Preflight should remain, with controlled before/after evidence rather than replacing it with mouse interaction.

No Windows, equipment, external provider or broader browser suite was run by this reviewer for this follow-up.

## Reserved-control successor

The repaired parser independently passes six finite actual-function framing probes in `reserved_slot_probe.cjs` / `reserved-slot-successor.json`, with identical protocol source hashes before/after. It accepts the 201-frame batch with one reserved control followed by 200 data frames, the reversed ordering, and 200 data alone. It rejects 201 data frames, two controls, and 200 data plus two controls. The resource cap remains 200 canonical candidates plus one control; it was not changed to an unqualified 201 canonical frames. These are synthetic framing checks on the production TypeScript class transformed in memory, not canonical evidence validation or a native browser suite.

The original known-count versus unknown-count distinction remains unchanged by this review. The separate pure unknown-loss test is retained; an unknown-lifecycle fixture can truthfully report an exact known presentation gap. Modal successor and root's focused/browser receipts remain pending at this record.

## Modal source successor inspection

The candidate replaces Modal's passive effect with `useLayoutEffect` (source SHA `7ac16243a360ca2330be59945a7fc626257adea8af63e7223790d22ca01cee42`). The topmost-dialog Escape/Tab listener is therefore installed during the DOM commit before browser paint/input can observe a newly visible dialog. Its cleanup still removes the listener and retains the existing connected-dialog guard before restoring focus. This is a narrow timing repair; it does not remove the keyboard focus expectation, add a mouse workaround, or change Start behavior.

Read-only source inspection found no new issue. It supports the early-listener timing explanation, while the original mutable-ref cleanup suspicion remains unproven and is not adopted as a confirmed cause. Root's focused/native focus evidence and successful full successor cohort remain required; this reviewer has not executed those browser cases.

The production parser successor hash is `52c3e21890865d67805203d77ab0a35b7c70e1c980387c304fa4d3f774619247`, matching its six-case independent framing receipt and root's separate red/green receipt. The known-count assertion now uses the actual fixture record count minus the bounded 200-record tail, while the distinct unknown-loss fixture remains. The recovery-scope erratum correctly separates initial pending-window SSE gap recovery from the independently demonstrated native HTTP410 replay expiry.
