# Retained results are reachable in a fresh browser

Component verification completed 2026-11-06, following work begun 2026-11-05.
Candidate `240778b94ba96bdbab9a036c36b065bf7fb902f4` passes 44 native browser journeys and two actual Linux
Orca journeys on 595 identical recorded source inputs and six reproduced assets.
No task or milestone is closed: T038/T097 and full AC-031 remain open.

A browser with no last-run preference could open its project but could not select
its completed Autoverse recording: Results hid the recorded-run selector when no
run was selected. Two original-UI counterexamples reproduce the missing control.
Results now always offers a project-filtered recorded-run picker, with bounded
pages, explicit refresh, labelled read errors and stable keyboard focus. A second
pair of controlled counterexamples showed an older list response overwriting the
selected run's newer status; the selected projection now takes precedence.

The backend and its public contracts are unchanged. Selection reads retained
metadata and does not create, replay or evaluate a run. The actual target is the
preserved completed full Autoverse demo recording; all current hosts use the normal
unregistered native launcher. Failure, incompatible identity/shape/cursor, paging,
stale metadata and delayed response cases use explicitly labelled HTTP fixtures.
The 200-row page fixture is not evidence of 200 actual executed runs or capacity.

## Native browser verification

| Suite | Passing journeys | Recorded duration |
| --- | ---: | ---: |
| selection | 16 | 33.52 s |
| diagnostics | 6 | 18.38 s |
| playback | 22 | 58.21 s |

Each suite covers 1024×768 and 1440×900, with no skips or flaky passes. The 16
selector journeys include genuine initial selection plus read/retry, wrong project,
null response, cursor regression, first/next page focus, late Home navigation and
selected-status precedence. The six diagnosis and 22 original-record playback
journeys are unchanged regressions on the final assets. The 16-case run began
before the commit was created; its recorded 595 input hashes match that commit and
all subsequent final cohorts exactly. This is a source-content binding, not a
claim that its initial HEAD field already named the later commit.

## Actual assistive technology

The actual installed Orca 42.0, AT-SPI 2.44.0, Speech Dispatcher 0.11.1 and eSpeak NG
operate with admitted Chromium 156.0.8078.4. The native backend runs outside the
contributor test isolation. The browser and assistive technology run in a fresh
private process/mount/IPC namespace, with their own D-Bus/AT-SPI session, private
XDG directories and authenticated CPU Xvfb display. The synthesizer uses an explicit
ALSA null sink. The host desktop, sound devices and full demo infrastructure are
not used. These are optional contributor prerequisites, not application runtime
requirements.

Each journey uses actual XTest key events to open Home, the existing Autoverse
project, Results, its recorded-run selector, Diagnosis, the clock finding's evidence
action and Events & logs. The test requires actual AT-SPI focus and newly submitted
Orca speech payloads at the key controls. It verifies the diagnostic code in the
actual accessible tree and visible, unclipped focus outlines. Ordinary Orca
SayAllOnLoad behavior remains enabled; the test searches the real tab order rather
than assuming a fixed initial focus sequence. There are no mutating UI requests.

| Width | Native keys | AT snapshots | Captured AT events | Captured processes exited | Failed process capture attempts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1024 | 73 | 9 | 407 | 34 | 0 |
| 1440 | 73 | 9 | 407 | 31 | 1 |

Both final AT cohorts have zero snapshot/query errors, event errors, dropped events
or tree truncations. Complete final trees and bounded event logs are retained;
older exploratory trees are labelled summaries. Both final raw Orca debug files
decode as UTF-8 without replacement. Earlier exploratory debug corruption remains
qualified in the retention manifest. Process observations are sampled: a failed
capture is reported and complete short-lived process coverage is not claimed.
The original backend handles exit and private workspace roots release.

These are actual automated AT interoperability checks. They do not measure audible
speech intelligibility, human screen-reader usability, novice task success or every
critical authoring/lab/campaign/export flow. Windows remains independently frozen.

## Integrity, history and limits

All final cohorts preserve original recording/database bytes, copied canonical
inputs and execution ledgers. The final AT checks additionally compare copied
project files and every non-session SQLite record. No provider model, guest,
campaign, derived evaluation or physical operation starts. The earlier complete
Autoverse runtime evidence retains its original scope; this component adds no new
simulator execution claim.

The exact six assets reproduce. Typecheck, new Python-tool Ruff, JavaScript syntax,
architecture and planning checks pass. Every backend source input remains identical
to the prior semantic-context candidate; its 65 contract and 32 backend regression
results are inherited through those bytes, not rerun. Earlier binding timeouts
remain unexplained and are not declared repaired here.

The retained history includes the original missing-selector and stale-status reds,
the initial test syntax error, intermediate passes and exploratory AT setup failures.
Private exploratory harness revisions were edited in place and were not separately
snapshotted; they are diagnostic history, not reproducible final-candidate acceptance.
The final published driver revisions are pinned by the recorded Git/source hashes.
Setup corrections include buffered Orca debug readiness, native UI versus renderer
AT roots, duplicate evidence-action labels and SSIP XML entity decoding. Speech
Dispatcher deliberately omits its dummy module from its advertised module list;
see the [upstream 0.11.1 parser](https://github.com/brailcom/speechd/blob/0.11.1/src/server/parse.c).

The manifest records 510 source/derivative pairs. Authentication files,
full databases, screenshots and raw strace remain private. Paths, loopback origins
and 75 private session/control strings are
excluded, including recursively decoded JSON attachments. Orca and SSIP public
logs contain declared speech/protocol subsets with original raw hashes; they are
not complete raw debug exports. Consumed bootstrap files were absent; zero consumed
bootstrap values were recovered or scanned. All current test and private AT
services are off. Cached runtime assets remain available for later authorized work.

The full goal remains active without automatic checkpoint pauses. Continue the
original remaining browser/AT, required-host, human and external acceptance gates.
