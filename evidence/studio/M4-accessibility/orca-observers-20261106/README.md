# Actual AT observer/metric references and validation

Candidate `dfaef4ef4743e1300ed5645fc718755814df2593` passes six actual Linux Orca/AT-SPI journeys: observer
and metric authoring, stimulus regression via the keyboard Close button, and
retained-results navigation, each at1024×768 and1440×900. All601 source inputs
match Git and every final cohort. No production file changes. The six UI assets
are exactly those previously reproduced for candidate240778b.

| Suite | Width | Native input commands | Key presses/releases | Typed characters | AT snapshots | AT events | Captured processes exited / failed captures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| scenario-observer-metric | 1024 | 287 | 418 | 129 | 30 | 755 | 35 / 0 |
| scenario-observer-metric | 1440 | 289 | 420 | 129 | 30 | 761 | 32 / 0 |
| scenario-stimulus | 1024 | 197 | 293 | 78 | 29 | 561 | 32 / 0 |
| scenario-stimulus | 1440 | 200 | 296 | 78 | 29 | 572 | 31 / 1 |
| retained-results | 1024 | 73 | 73 | 0 | 10 | 407 | 31 / 1 |
| retained-results | 1440 | 73 | 73 | 0 | 9 | 407 | 31 / 1 |

All final snapshots have zero query/event errors, drops and tree truncation.
Every emitted press has a matching release. Original handles terminate, captured
pidfds exit and native backend roots release. Failed sampled captures are counted;
complete coverage of short-lived processes is not claimed.

## Native authoring and reference refusal

Actual XTest events open the Scenario editor, type a stable new observer ID,
select a declared System target and enter an opaque sampling intent. The normal
backend validates and saves revision17. The actual AT-SPI Text interface reads
the entered sampling value; focus and actual Orca SSIP speech return to Add observer.

Native input creates a metric intent, selecting the newly authored observer by
Space on its labelled checkbox. The actual AT tree exposes that checked state.
AT-SPI reads the typed acceptance string; the backend saves revision18 and the
reader announces restored focus. These strings are authored intent only: no
observation, calculation, acceptance verdict or runtime permission is inferred.

Removing the still-referenced observer reaches the actual validation endpoint
and returns422. Its real dialog alert is exposed through AT-SPI and announced by
Orca. Project/API readback stays exactly equal to revision18. Escape dismisses the
failed confirmation, restores meaningful focus/speech and leaves the draft intact.

Removing the metric first creates revision19 and restores Add metric intent.
Removing the now-unreferenced observer creates revision20 and restores Add observer.
Both deleted controls disappear. Five UI edit requests comprise four accepted
semantic changes and one refusal. Final Scenario semantics equal the original.
No provider is registered and no workload, guest, evaluation or physical request
is created. Source serialization-byte equality is not claimed for rewritten YAML.

## Independent integrity checks

The readback verifier constructs all four expected Scenario states independently.
It admits only the selected project record, four sealed revisions, their40 revision
files and two content-addressed Scenario objects. Every prior project byte,
other document, unknown payload and other non-session record remains equal.
Original recording/database bytes, copied frozen sources, immutable evidence and
execution ledgers remain unchanged. Read-only results retain full project equality.

The audit accepts the three actual four-edit histories (the initial probe and
both final widths) and rejects27 in-memory corruptions involving authored
identifiers/intent, unrelated/deleted/new records, file changes/additions/omissions,
source digests and edit origins. Database and project hashes show the audit itself
is read-only. AST comparison proves all four preceding readback function bodies
are unchanged; the new observer/metric path has its own actual and negative checks.

The stimulus pair repeats validation speech, source selection, keyboard Close,
schedule editing and removal/cancellation on this candidate. The retained pair
repeats fresh-browser run selection, actual diagnosis and evidence navigation.
The previous conditions/inventory and44 native browser results are inherited
through unchanged production/native-test bytes and unchanged existing verifier
bodies; they are not rerun or counted among these six journeys.

## Remaining gap and evidence scope

The preceding [source-dialog Escape speech failures](../orca-stimulus-20261106/README.md)
remain unresolved. They restore DOM/AT focus but Orca42 suppresses the returning
button's utterance. This component changes only test tools and does not rerun or
promote those cases. The separately passing keyboard Close route establishes no
direct-Escape correction. Fault authoring and the complete lab/binding/reservation,
campaign and export/retention AT matrix remain open.

The normal native backend operates on fresh copies of the existing real Autoverse
recording. Chromium, unmodified installed Orca, AT-SPI and Speech Dispatcher with
eSpeak NG use the existing authenticated CPU Xvfb/private D-Bus/process/mount/IPC
session and explicit ALSA null sink. No host desktop, physical input, audio or
device interface is used. Those are contributor test prerequisites. Diagnostic
line buffering/own-child stack capture remain unchanged. Native input, tree,
event, snapshot and time bounds remain unchanged; each new case uses30 of32
available snapshots. Actual installed versions and Orca source hashes are retained.

One exploratory probe passed on the preceding uncommitted tools. Its source hashes
remain distinct from the final Git candidate; no separate archive of that early
tool revision is claimed. All final source/asset inputs are identical.

The manifest retains 289 source/derivative pairs, excluding
21 known session/control strings from
7 private session databases. Consumed bootstrap files
were absent; no consumed token was recovered or scanned. Critical final AT trees
are complete, others are labelled summaries. Orca/SSIP logs retain declared
speech/protocol subsets with raw source hashes. Machine paths and credentials
are excluded; authentication files, databases and full project/SQL baselines stay
private. The finalizer checks decoded JSON attachments and all artifact hashes.

No actual auditory, human usability or milestone acceptance follows. Counts stay
72 completed /18 in progress /10 blocked, zero accepted milestones. T038/T097
remain open for all original requirements. Windows stays independently frozen.
All current component handles have exited and roots released; cached assets
remain intact. The full original goal continues without checkpoint pauses.
