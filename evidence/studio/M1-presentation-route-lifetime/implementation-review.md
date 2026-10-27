# Root review

The prior failed CI reports body disposal and context cleanup, not a failed focus
assertion. Source review found removal of registration without handler completion.
A real native gated-body/context-close countercheck reproduces both errors; waiting
for active callbacks removes them. The pinned framework implementation reserves
exception suppression for ignoreErrors, which is not used. The final source differs
by one cleanup call only, with an exact inverse-byte control. Actual HTTP bodies,
focus/edit/history/no-run assertions and every threshold remain unchanged.

Fresh affected 48 pass after the controlled old2 failures/wait2 successes. All other
315 selected inputs and all 110 packaged payloads match e441 API evidence. The exact
original CI timing remains unobserved, and new full474/Windows/AT/human/provider or
milestone acceptance is not inferred. The original CI failures remain retained.
