# Initial selected-source focus and real Escape announcements

Candidate `2391af416aa7fb0b8b5136b903be0509060152d2` repairs the recorded source-dialog Escape announcement
gap in Chromium156/Orca42 at1024×768 and1440×900. Four final actual AT journeys
pass: direct Escape and keyboard Close at both sizes. Fourteen final native-browser
checks pass, comprising eight existing authoring journeys and six new initial-focus
counterchecks. No task or milestone closes.

The same current test tools/backend reproduce the missing utterance with the old
six-asset UI at1440. That control restores DOM/AT focus but fails the unchanged
ten-second actual SSIP assertion. All current601 source hashes match Git for the
four final AT cases, old-UI supervision/backend control and final native run.
The control deliberately serves the previously reproduced240778b UI; it is not a
shipping candidate. The final candidate serves six newly reproduced assets.

| Source exit | Width | XTest commands | Key presses/releases | AT snapshots | AT events | Captured processes exited / failed captures |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| escape | 1024 | 197 | 293 | 28 | 563 | 31 / 2 |
| escape | 1440 | 198 | 294 | 28 | 568 | 32 / 0 |
| close-button | 1024 | 197 | 293 | 29 | 563 | 33 / 0 |
| close-button | 1440 | 198 | 294 | 29 | 568 | 32 / 2 |

All final AT snapshots have zero query/event errors, dropped events and tree
truncation. Every native XTest key press has a matching release. Sampling gaps
are counted; complete coverage of short-lived children is not claimed. Original
AT/backend handles terminate, all captured pidfds exit and roots release.

## Change and actual behavior

The prior trace showed a hidden Resource-select selection event replacing Orca's
internal focus context after the source textarea received focus. On Escape its
silent context repair then suppressed the returning button's utterance. Diagnostic
line buffering and the installed reader source remain unchanged in this comparison.

Only the initial SourceEditor effect changes. Two browser animation frames let
the dialog render before the automatic declaration anchor moves focus. The pending
frame is cancelled on cleanup. The callback requires the original focus to be
this dialog's Close button, that focus still current, a connected textarea and
the same top modal. Newer focus, a placed caret or a closed dialog wins. The
explicit Go to selected declaration action remains immediate. Declaration lookup,
selection ranges, source bytes and ordinary modal restoration stay unchanged.

Actual mapped XTest input creates a stimulus, inspects its selected YAML through
AT-SPI, closes the source dialog and verifies the returning button's real AT focus
and new Orca SSIP utterance. The same flow then edits its schedule, cancels removal
and removes it. Each complete case has three real SDK-validated semantic edits,
revisions16→19 and32 exact new files. Independent readback checks each intermediate
Scenario, restores its original semantics and preserves every earlier project
byte, other document/record, unknown payload, frozen input and execution ledger.
Original recording/database bytes remain unchanged. YAML serialization-byte
restoration is not claimed. No provider or workload is registered or started.

The failed old-UI control is independently checked as exactly one accepted edit,
with the same original-data guarantees. Its actual final focus event and complete
post-restoration debug excerpt remain retained. The preceding component's two
older viewport failures remain historical failures; this candidate resolves that
specific recorded Chromium/Orca gap without rewriting their outcomes.

## Browser counterchecks and candidate binding

The14 final source-only browser cases include the eight unchanged conditions,
stimulus/source, observer/metric-reference and opaque-fault journeys. Six additional
cases activate the source opener with native browser keys, then countercheck the
earliest post-mount Resource focus, placed source caret or Escape at both widths.
Those counterchecks explicitly use instrumented DOM focus/caret or a dispatched
keyboard event. Three real browser frames observe any late anchor; no scheduler,
application listener, animation clock or source response is replaced. Each new
case asserts unchanged project/API state and zero mutating requests. They complement
the four actual XTest/Orca journeys and are not presented as human or auditory use.

The preliminary14-case run also passed. It reported its actual earlier checkout
identity; all601 runtime source hashes and six served assets already equal the
final candidate. A preliminary actual AT probe used the first frame-deferral
implementation before the extra origin guard/counterchecks; its distinct input
hashes and UI remain labelled exploratory. No separate source archive of that
early uncommitted variation is claimed. Final candidate inputs match exactly.

Byte comparison againstad87 proves that only Views.tsx and the authoring test file
changed among601 tracked runtime/test inputs. Within Views.tsx only the initial
effect changes. All other599 inputs, including backend/compiler/AT tools, stay
equal. Previous unrelated backend and AT results are inherited through those
unchanged inputs, not rerun here. No latency improvement or whole-matrix claim is
derived from timings. ADR0083 records focus ownership and the affected gates.

## Ownership, retention and limits

Actual AT uses a private process/mount/IPC namespace, authenticated CPU Xvfb,
private D-Bus/AT-SPI/XDG state and real Speech Dispatcher/eSpeak NG through ALSA
null. Native-browser cases use the existing user/mount/minimal-device isolation
with display variables removed; they share the host PID namespace. Their original
browser/backend handles and root release are verified, without an all-descendant
pidfd claim. The native backend's recorded exit-15 follows identity-verified
original-handle SIGTERM, permitted by the existing helper; it is not rewritten to0.
The14-case reports contain the original frozen observation count21, which is not
a process count. No host desktop, audio device, GPU, guest or physical interface is
used. These are contributor prerequisites, not application dependencies.

Two pre-export verifier assumptions failed before creating this evidence folder:
the exporter initially demanded exit0 despite that SIGTERM contract, then compared
native sha256:-tagged hashes with bare AT/Git hashes. The corrected comparison
strictly validates the tag/hex form; original receipts and terminal outcomes remain
unchanged. Both failed exporter revisions and their report are retained. No product
test was rerun or promoted because of those exporter corrections.

The manifest retains 295 source/derivative pairs and excludes
22 known session/control strings from
8 private session databases, including both native
data roots resolved through private locators. Consumed bootstrap files were absent;
no consumed value was recovered or scanned. Nested JSON report attachments are
decoded, sanitized and re-encoded. Critical final AT trees are complete, other
trees are labelled summaries. Orca/SSIP files are declared speech/focus/protocol
subsets plus a labelled control restoration excerpt. Raw source hashes remain;
credentials, databases, full project/SQL baselines and native locators stay private.
The finalizer checks decoded attachments and every artifact hash.

This verifies automated behavior in the recorded Linux Chromium/Orca environment,
not actual auditory or human usability outcomes, another reader/browser or Windows.
Windows work stays independently frozen. Counts remain72 completed /18 in progress
/10 blocked, zero accepted milestones. T038/T097 still require their complete
original matrix, fault/other added AT flows, lab/binding/reservation, campaign,
export/retention, required-host and human gates. All current component services are
off and roots released; the full goal stays active without checkpoint pauses.
