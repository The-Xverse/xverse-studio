# Actual Orca stimulus authoring and source inspection

Candidate `3ccd39a2445f47428879cf7202c01e128abc3e3b` passes eight actual Linux Orca/AT-SPI journeys:
stimulus authoring with the keyboard Close button, conditions editing, actual
empty inventory and retained-results navigation, each at 1024×768 and 1440×900.
Two additional direct-Escape source-dialog journeys fail their speech assertion
at both sizes and remain an open AT compatibility gap. They are not counted as
passed acceptance cases. No task closes and no production file changes.

All 600 source inputs match Git and all ten final cohorts. The six UI assets are
exactly those previously reproduced for candidate240778b. The earlier 44 native
browser checks are inherited through unchanged production and native-test bytes;
they are not rerun here. Four existing AT Python tools and one new stimulus driver
account for every source difference from the preceding599-input candidate.

| Suite | Width | Native input commands | Key presses/releases | Typed characters | AT snapshots | AT events | Captured processes exited / failed captures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| scenario-stimulus | 1024 | 196 | 292 | 78 | 29 | 559 | 33 / 1 |
| scenario-stimulus | 1440 | 198 | 294 | 78 | 29 | 566 | 32 / 0 |
| scenario-conditions | 1024 | 78 | 384 | 258 | 15 | 279 | 33 / 1 |
| scenario-conditions | 1440 | 80 | 386 | 258 | 15 | 287 | 31 / 1 |
| lab-inventory | 1024 | 31 | 31 | 0 | 4 | 119 | 32 / 0 |
| lab-inventory | 1440 | 29 | 29 | 0 | 4 | 115 | 33 / 1 |
| retained-results | 1024 | 73 | 73 | 0 | 9 | 407 | 32 / 0 |
| retained-results | 1440 | 71 | 71 | 0 | 9 | 403 | 32 / 0 |

All final snapshots have zero query/event errors, dropped events and tree
truncation. Each emitted key press has a matching release. Process sampling does
not prove coverage of every short-lived child; failed captures are reported.
All original test/backend handles terminate, all captured pidfds exit and roots
release. No workload, guest, evaluation, campaign or physical operation starts.

## Actual stimulus journey

Native XTest input opens the Scenario form, types a stable item identifier and
selects its declared target. Submitting an invalid JSON array produces an actual
Orca validation-error utterance and AT alert with no edit request or project change.
Native Ctrl+A and mapped ordinary/Shift keys then type a nonempty action object
with an opaque nested field. The normal UI/backend endpoint validates and saves
one semantic revision. Actual AT focus and SSIP speech return to Add stimulus step.

The real source dialog selects that item's YAML declaration. The AT-SPI Text
interface supplies its selection range and selected text; parsed semantics match
the exact authored step. An AST mapping slice begins after its sequence prefix,
so the comparison restores only the missing indentation context. Saved source
bytes are not changed. The source Save button remains disabled. Native Tab and
Return activate Close dialog and verify restored source-button focus and speech.

Native input then edits Scheduled at to0.5; AT-SPI independently reads0.5 from the
editable control. Saving creates the second revision with only that intended
change. Escape cancels a removal confirmation without another write. Reopening
and activating Remove draft item creates the third revision, removes the control
and restores actual focus/speech to Add stimulus step. Final Scenario semantics
equal the original; serialization-byte equality is not claimed for rewritten YAML.

Independent readback permits only the selected project record, three new sealed
revisions and their exact files/content-addressed objects. It checks every
intermediate Scenario against independently constructed add/update/remove states,
including identifiers, target, clock, units and unknown action fields. Every old
project byte and all other non-session records remain unchanged. Original
recording/database bytes, copied frozen sources, immutable evidence and execution
ledgers remain equal. The read-only suites retain full copied-project equality.

The readback audit accepts three actual positive fixtures (one partial failure
and two full histories) and rejects28 in-memory corruptions: unrelated/deleted/new
records, old/new/missing files, source digests, edit origins, wrong opaque action
content and a partial history falsely claimed complete. SQLite and project hashes
prove the audit itself leaves its private fixtures unchanged.

## Open source-dialog Escape announcement gap

Both final direct-Escape runs restore browser focus and emit the actual AT-SPI
focus event for View source for step orca-step-<width>. Orca emits no new utterance
for that button within the existing ten-second speech bound. Creation before this
failure is independently checked as exactly one revision; no later edit is claimed.
See the two failed browser logs, actual event streams, SSIP subsets and complete
post-restoration debug excerpts.

Line-buffered installed Orca42 debug shows a hidden Resource-select menu's
selection event replacing its internal focus context after the textarea receives
focus. On restoration, the web handler finds a missing caret context, changes its
locus of focus without notification, then the default handler suppresses the
already-current focus. This follows the inspected installed handler source, whose
hashes are retained. Stack samples show the main thread in its event loop; a
screen-reader hang or application focus defect is not established. The keyboard
Close-button route is separate evidence and does not resolve the direct-Escape
announcement gap. No UI workaround or extended speech timeout was introduced.

## Isolation, failures and retention

The native backend runs normally on a fresh private copy of the real Autoverse
recording. Actual Chromium156, Orca42, AT-SPI2.44, Speech Dispatcher0.11.1 and
eSpeak NG1.50 run inside a fresh private process/mount/IPC/D-Bus/XDG session with an
authenticated CPU Xvfb display and explicit ALSA null sink. Host desktop, audio
and physical input devices are not used. These are optional contributor test
prerequisites. Windows remains independently frozen.

The installed Orca entry point is unchanged. An isolated Python runpy wrapper
sets diagnostic-file line buffering in a bounded startup thread and registers a
stack-dump signal for its own original child. No AT handler, keymap or reader
preference is patched. Native input and snapshot bounds remain unchanged.

Earlier failures are retained: an indented selected fragment initially failed
standalone YAML parsing; one invocation mistakenly used the Xvfb path as the
browser-cache directory and failed before browser operation; subsequent probes
reproduced the Escape speech gap. Buffered logs initially suggested a processing
stall. Periodic stack sampling and line buffering corrected that interpretation.
Exploratory tool revisions were not separately archived; their source hashes
identify those observations, while the final Git candidate pins reproducibility.

The manifest holds 554 source/derivative pairs and excludes
54 known session/control strings from
18 private session databases. Consumed bootstrap files
were absent; no consumed value was recovered or scanned. Critical final AT trees
are complete; other snapshots are labelled summaries. Orca/SSIP artifacts are
declared speech/protocol subsets, except the labelled post-restoration debug
excerpts. Raw source hashes remain. Paths and credentials are removed; full project
and SQL baselines, authentication files and databases stay private. The finalizer
checks decoded JSON attachments and all retained artifact hashes.

These automated checks establish no actual auditory or human usability outcome.
Counts remain72 completed /18 in progress /10 blocked, zero accepted milestones.
T038/T097 remain open for the complete matrix, other authoring families,
binding/reservation, campaigns, export/retention, required-host and human gates.
All current component services are off; cached runtime assets remain preserved.
The full original goal stays active without checkpoint pauses.
