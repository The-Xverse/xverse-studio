# Evidence imports preserve current navigation and selection

Source `36861b2` passes **43 selected browser checks**:14 new keyboard import
cases,1 unchanged existing inspection case,6 unchanged diagnostic cases and22
unchanged original-record playback cases. No failure, skip or flaky result occurs
in these final cohorts. All555 selected inputs match Git and remain unchanged
through all four cohorts; six reproduced UI assets also stay unchanged.

Delayed actual import replies previously opened an obsolete dialog after choosing
Home/Catalog or starting a newer import. Actual malformed-archive failures added
obsolete errors to Catalog. An older completion also cleared the newer action's
busy indication. The repair captures navigation/selection identity, gates only the
current import's UI result/error, and clears the busy label only for its latest
action. Accepted bundles remain stored; no backend operation is cancelled, deleted
or repeated by this change. Action return values and existing general error
handling remain unchanged.

The first14-case counterexample cohort passed2 and failed12. Four failures came
from selecting an older dependencies1.0 archive without compiled-profile metadata;
eight reproduce the UI context defects. The existing prepared1.1 archive passes
the four normal keyboard cases on the original product. That source correction
does not alter either archive or invent missing legacy metadata. Initial repaired14
and final committed14 have separate records. The overlapping-selection test's busy
expectation was strengthened from0 to1 while the newer response is held, with an
actual-response/body/browser-frame barrier. The exact test amendment is retained.

New cases use native Tab/Enter navigation to the browser filechooser, actual valid
and damaged Autoverse archives, original/current integrity distinctions, exact
provider/profile identities, preserved evaluations/annotations, modal Escape/focus
restoration, selected text contrast and actual malformed-ZIP refusal. Delay
controls forward actual201/422 responses. Browser filechooser handoff is covered;
OS file-dialog keyboard behavior and assistive technology are not certified.

The final keyboard cohort retains12 accepted imports; the existing inspection case
retains4. Run, operation, evaluation, snapshot, campaign, preflight and idempotency
counts stay unchanged. The ordinary native backend runs on disposable target
copies without registering a live Autoverse provider. No model, simulator, workload,
physical device or companion change is involved.

Browser-only contributor CPU/device isolation is verified before launch; this is
not an application dependency. Captured original process handles all report exit,
root locks release and no GPU file descriptor is observed. Sampling does not prove
complete coverage of short-lived children. Final exchange cohorts additionally
hash every pre-existing imported canonical file;14 copied files match the original
source. Earlier cohorts keep their narrower run/snapshot/database hash scope.
Original source database/recordings remain unchanged throughout.

Component review: the sole production file changes browser intent and busy-label
ownership. There is no industry dispatch, endpoint, import schema, authority or
canonical-evidence change. The native contributor helper admits only fixed suites,
keeps the original whole-inspection4-import expectation, and enforces12 imports for
the whole new suite. Filtered diagnostic cohorts record bounded actual counts and
are not whole-suite acceptance. No further finding requires repair within this
scoped change. Build/typecheck, targeted helper lint, architecture and planning
checks pass; build warnings remain retained.

Counts remain **71 completed /19 in progress /10 blocked**, zero accepted
milestones. T038/T097 retain the broader workflow/browser/accessibility obligations.
No full backend/browser, performance, package, live provider, hardware, Windows or
milestone pass is claimed. Windows remains frozen; the full goal stays active.
