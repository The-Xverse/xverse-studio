# Linux keyboard source completion and recovery — 2026-10-26

Partial T038/T067 evidence for AC-031/NFR-006 at 1024×768 and 1440×900. All 26 focused
checks and the complete 171-check browser successor pass without failures/skips/flakes.
Application/runtime/test inputs match the final focused run. Full and performance maps
are identical, including ADR-0013/0015 and fixed inputs, unchanged during each run.
The targeted runner uses a narrower application/test map. Count remains 47/100 components;
no milestone is accepted. Native Windows and actual assistive-technology acceptance remain open.

## Authored source transactions

Critical source actions use native Tab/Enter, select arrows and keyboard text entry.
The existing helper/API prepares private authentication and isolated owned projects before
those journeys. Both Ctrl/Meta+S and the focused Save button submit exactly one real PUT
of exact authored YAML, advancing once. Ctrl/Meta+Z and Ctrl/Meta+Shift+Z restore the exact
text. Saved bytes reopen intact; document IDs and every other document's bytes remain
unchanged. Matching recovery cache clears, the saved control disables, and focus returns
to the enabled textarea with a visible outline and viewport bounds. The guidance is
associated with that textarea. Actual platform validation passes. Focused journeys never
Start a run and retain each project's run identity set; the broader regression suite has
its own separately scoped owned-reference lifecycle checks.

Held real PUT responses preserve Home, a newer same-project revision and exact tab history,
a reopened same-document draft, another document's draft, deliberately moved focus, and the
exact newer ready preflight ID. The endpoint has already committed; only browser delivery
is delayed. Current state uses the authoritative returned Project rather than a captured
refresh. Project/load/intent/head guards prevent obsolete completion or errors from applying
in another context. Cache cleanup uses the latest known baseline and removes only matching
submitted text; it cannot erase a newer editor's draft.

## Refusal and explicit recovery

A real other-session PUT advances the owned project, then the stale UI receives actual
412 REVISION_CONFLICT. The refused request leaves canonical documents/revision unchanged
and retains the exact local draft/cache. Its current error appears inside the source modal;
after Escape, native Load current revision and Compare changes expose the actual newer
baseline. An explicit retry makes a new forward revision of the retained local text.
The intervening revision's listed digest matches the other session's source. This browser
assertion establishes that historical identity, not a separate restoration of those bytes;
inherited backend integrity/restoration cases cover the latter. A departed conflict cannot
publish a late global error on Home.

The Unicode journey seeds a cache of exactly 524288 UTF-8 bytes with fewer UTF-16 code units.
Adding one four-byte character reports the recovery limit and preserves that bounded cache.
A larger authored draft sends a real PUT above the backend's one-MiB bound and receives
413 LIMIT_EXCEEDED, without advancing revision or changing any canonical document. Its
text remains in the editor; guidance recommends correction rather than an irrelevant reload.
Reopening explicitly recovers the last bounded cache and warns that newer uncached edits
may be missing. Assertions and attachments use digests rather than dumping large draft text.

Four narrowly scoped browser fixtures make Storage.prototype.getItem fail only for
studio.draft.* reads during open or document switch. Canonical fallback stays editable,
a persistent warning reports unavailable recovery, and new fallback edits/Escape cleanup
cannot overwrite the unread prior cache. Restored read access and switching recover that
prior text. These are controlled browser-storage failure cases, not evidence of host
filesystem failure, external-file adoption, hardware integration or Windows operation.

## Original failures and review

initial-red/ retains 12 failures and eight passing counterchecks on the original source,
with exact original tests, source maps, report and raw log. It reproduced uppercase redo,
unassociated guidance, disabled-control focus loss, Home/readiness replacement, inaccessible
current-modal conflict/departed errors and saved-source contrast 2.9787:1. recovery-red/
retains all six additional failures on the first repair: the character/byte limit, non-412
guidance, stale cache wording and unhandled draft reads. The independent reader identified
the unhandled-read gap before its countercheck. Both sets remain failed evidence.

twenty-before-recovery/ is a superseded report-only success checkpoint; its source maps
were not retained separately. Final 26-case maps/results establish the verified successor.
No harness correction, retry, skipped case or test-specific product bypass was used for
these failures. Independent bounded review found no remaining blocker after repair,
including the final immediate-warning change; review is separate from execution proof.

## Final verification and limits

Type/build, architecture, descriptive compatibility consistency and planning-structure checks
pass. Backend/Python/contributor/compatibility inputs are byte-identical to the passing
851-test 13ff409 cohort, revalidated by hashes rather than rerun for frontend-only changes.
The environment recorder covers tracked inputs; the full source map includes the new test.
All 6 selected guidance/comparison text/paint pairs pass 4.5:1, minimum
4.6849:1. This is selected supported paint and native Linux Chromium, not
global contrast/AT conformance or complete AC-031 acceptance.

Separate final-source performance uses one warm-up plus 30 measured repetitions per workload
and viewport: 200 elements/400 connections and 50000 retained events. Raw samples/warm-ups
and actual validation outcomes are retained under performance/. Cold preparation is excluded
by the existing declared profile; these measure Studio presentation rather than provider,
simulator or physical-device capacity.

| Viewport | Selection p95 | Open/validation p95 | 200-row history p95 |
| --- | --- | --- | --- |
| 1024x768 | 25.1 ms | 1651.2 ms | 446.6 ms |
| 1440x900 | 29.1 ms | 1709.2 ms | 445.2 ms |

Clean `7ec222b` package extraction also passes native Linux offline provisioning with the
prepared dependency cache, startup/UI, Unicode persistence, public compilation and owned
shutdown. Its clean 100-file manifest, archive/file hashes and tested UI bytes are verified
in `package/`. This is a prepared-cache installation lane; candidate CI is recorded separately.
