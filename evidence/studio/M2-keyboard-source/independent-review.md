# Independent scoped review — 2026-10-26

Separate read-only reviewer `t076_hybrid_tests`; no edits or test execution.
The initial review inspected SourceEditor, the source modal/shared revision guard,
comparison CSS and the actual source accessibility tests. Async commit/load/head guards,
departed-error suppression, conditional focus/cache handling and real PUT/412 identity
checks were sound. It identified an additional blocking recovery-read gap: uncaught
sessionStorage.getItem could break opening or switching the editor. It requested a
scoped read-failure countercheck and honest handling of prior cached text when a newer
draft exceeds the recovery bound. UTF-8 byte counting and non-412 guidance were already
identified by root and remained open at that review.

Root reproduced all six additional recovery cases on the first repair: both exact-byte
boundary/real size-refusal journeys and all four controlled storage open/switch failures.
The failed reports, original test and source maps remain retained. The implementation
then catches reads, marks fallback drafts as recovery-unavailable, keeps canonical text
editable and prevents any fallback persistence from overwriting/removing unread cache.
Read access restored through the scoped fixture permits recovery of the original draft.
UTF-8 bytes define the unchanged 512 KiB bound; oversized drafts preserve the last bounded
cache. The recovered notice explicitly identifies last cached text and potentially missing
uncached edits. Actual backend size refusal retains current text without a success claim
or irrelevant reload advice.

Follow-up review PASS for this Linux partial scope; no remaining blocker found. The reviewer
found the exact-boundary, actual413/no-mutation and storage restoration tests meaningful.
A final bounded read confirmed that the computed current-byte/dirty warning is immediate
and cannot be erased by the delayed successful persistence cleanup; unread-cache warnings
remain independent. The final 26-case successor subsequently passed on unchanged inputs.
Full regression, separate performance and clean-package results are independent execution
evidence, not conclusions established by this read-only review.

T038/T067 remain in progress. Native Windows, actual assistive technology and complete
accessibility/milestone acceptance remain open. Source saves and explicitly scoped recovery
cache fixtures establish no external-file adoption, live-provider mutation or physical action.
