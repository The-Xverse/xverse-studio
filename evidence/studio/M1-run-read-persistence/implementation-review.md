# Run observation persistence review

This is an implementation self-review. The separate independent milestone review remains open. The actual full
successor verification result is recorded below.

The repair changes only whether identical run/operation JSON is written. It keeps
the existing store lock, observation order, identity checks, journal verification,
assessment computation and pending-command reconciliation. Canonical comparison
preserves JSON type/numeric representation changes that Python equality could
otherwise collapse. No provider, process, snapshot, XDL or schema is introduced.

Changed cleanup/state-version observations and newly invalid journal evidence must
still persist once. Failed persistence of a changed observation must propagate;
the caller cannot receive an invented durable acknowledgement. Stable reads then
require no further record writes. Actual worker files and response bodies remain
unchanged in the200-run measurement; no old run lifecycle command is requested.

The measured stable phase improves only modestly and cold verification does not
improve. The existing authoritative compiler/evidence work remains in place.
The original browser failure's exact scheduling was not captured, so redundant
writes are a proven separate finding, not a declared original root cause.

The metadata-only browser diagnostics address that observation gap without
changing any original assertion, request or response. They have an explicit512
event bound and omission count, use relative paths, and avoid authentication or
body capture. Their inverse restores the original source bytes.

The five new regressions and20 affected existing checks pass. Fresh full backend, affected/full browser and performance stages now pass
on the 321-input successor; the exact final result is recorded below. The earlier107-case native cohort and515/1 full browser result
retain their original source identities. Windows remains held; fixtures cannot
establish physical-provider recovery, actual cleanup or full milestone acceptance.


Final successor verification passes1078/73/full516/performance2 with321 unchanged inputs. This closes the pending execution scope of this review, not independent milestone acceptance or the original trace-failure scheduling investigation. Clean committed source/package binding is still required.
