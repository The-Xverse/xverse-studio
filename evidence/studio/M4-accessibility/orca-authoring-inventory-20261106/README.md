# Actual Orca authoring, inventory and retained-results verification

Candidate `ee3b17455f7564894c0e5127c4e56166573dda84` passes six actual Linux Orca/AT-SPI journeys: scenario
conditions, the actual empty inventory, and retained-results regression, each at
1024×768 and 1440×900. All 599 recorded source inputs match Git and every final
cohort. No production file changed. The six UI assets are exactly those already
reproduced and verified for candidate240778b; its 44 native browser journeys are
inherited through unchanged production/test bytes, not rerun here.

| Suite | Width | Input commands | Key presses | Typed characters | AT snapshots | AT events | Captured processes exited / failed captures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| scenario-conditions | 1024 | 77 | 383 | 258 | 15 | 278 | 32 / 0 |
| scenario-conditions | 1440 | 77 | 383 | 258 | 15 | 280 | 32 / 1 |
| lab-inventory | 1024 | 30 | 30 | 0 | 4 | 117 | 34 / 0 |
| lab-inventory | 1440 | 6 | 6 | 0 | 4 | 65 | 33 / 1 |
| retained-results | 1024 | 74 | 74 | 0 | 10 | 409 | 32 / 1 |
| retained-results | 1440 | 73 | 73 | 0 | 9 | 407 | 31 / 0 |

All final snapshots have zero query/event errors, dropped events or truncation.
Each emitted key press has a corresponding release. Process sampling does not
cover every short-lived process; failed captures are counted. Every captured pidfd
exits, native backend handles terminate and workspace roots release.

## Scenario conditions

Actual XTest key events select the project and Scenario editor, open the conditions
modal, replace its JSON with an invalid array and submit. Orca announces the real
validation error, the actual AT tree exposes it, and the backend project remains
unchanged. Native Ctrl+A, ordinary keys and Shift-modified punctuation then type a
valid JSON object. The test reads that text through the actual AT-SPI Text interface
as well as the DOM; it uses no composed-string injection, clipboard or script-set
field value. XKB only reads the private server's existing keymap; no key is remapped.
See the primary [XTEST specification](https://xorg.freedesktop.org/archive/current/doc/libXtst/xtestlib.html)
and [XKB key lookup documentation](https://www.x.org/archive/X11R7.7/doc/libX11/XKB/xkblib.html).

The normal UI submits one real semantic-edit request, validated by the selected
backend XDL adapter. Orca follows focus back to the opener, then the test reopens
the dialog and reads the persisted editable value through AT-SPI. Escape closes
the dialog without another edit. Each copied project advances revision16→17.

Independent filesystem/SQLite readback permits only the selected project record,
one sealed revision record, its ten revision files and one new content-addressed
Scenario object. Every previous project byte and other non-session record is
unchanged. The Scenario differs only by the intended opaque initial-conditions
field; other documents and unknown payloads remain equal. Original recording and
database bytes, snapshots, run evidence and all execution ledgers are unchanged.
This verifies authored intent, not runtime admission or an observed simulation
condition. No provider workload or derived evaluation starts.

## Actual inventory and retained results

The ordinary unregistered native backend returns a complete, empty registered
inventory. The test verifies its explicit "No physical provider admitted" heading,
empty-page text and purpose-labelled refresh. Native refresh moves real AT focus
to "Inventory observation", which Orca announces; previous/next pages stay disabled.
There are two actual reads and zero mutating UI requests. This establishes no
physical-device discovery, identity, reservation, stimulation or hardware readiness.
The completion heading has the browser's visible one-pixel auto outline, matching
the existing inventory test's positive-outline criterion. Interactive controls keep
their existing stronger focus-outline check.

The retained-results pair repeats fresh-browser selection, diagnosis and referenced
events navigation through the shared input helpers. AT content readiness is checked
separately from DOM readiness, within a fixed ten-second bound and at most ten
observations. Each observation remains recorded. The 1024 case needed two diagnosis
observations; the 1440 case needed one. A missing diagnostic remains a failure,
rather than causing a whole-test retry or a fabricated accessibility tree.

## Scope, failures and retention

The actual installed Orca, Chromium, Speech Dispatcher/eSpeak NG and Xvfb run in a
fresh private process/mount/IPC namespace with private D-Bus/AT-SPI/XDG state and an
authenticated CPU display. Speech goes to an explicit ALSA null sink. The native
backend runs outside that contributor isolation. No host desktop, audio device,
physical input interface, simulator/guest or full demo infrastructure is used.
These are optional test prerequisites, not application dependencies. Package and
command identities are retained; Windows remains independently frozen.

Exploratory failures remain failures: a static label was initially mistaken for
its editable text field; a verifier initially compared bare hashes to tagged
`sha256:` digests; two inventory probes incorrectly imposed a two-pixel heading
criterion instead of the existing positive-outline criterion; and an immediate
AT snapshot preceded delivery of new diagnosis children. The raw observations and
corrected final candidate remain distinct. Early uncommitted tool revisions were
not separately archived; final source hashes and the two committed tool revisions
pin the reproducible final checks. No application defect is claimed from these
instrumentation failures.

The manifest retains 395 source/derivative pairs, with raw source hashes.
Critical final trees are complete; other trees are explicitly labelled summaries.
Public Orca/SSIP logs are declared speech/protocol subsets, not full raw debug logs.
Authentication files, databases and full project/SQL baselines stay private. Paths
and 48 known session/control strings are
excluded. Sixteen consumed bootstrap files were absent; no consumed bootstrap
value was recovered or scanned. Finalization also checks decoded JSON attachments
and all artifact hashes. No actual auditory or human usability outcome follows.

Tasks remain72 completed /18 in progress /10 blocked, with zero accepted milestones.
T038/T075/T084/T097 and their full original obligations remain unchanged. Remaining
AT work includes other authoring families, reservation/binding, campaigns and
export/retention flows; required-host, physical-provider, human and independent
milestone gates remain separate. The full goal stays active without checkpoint
pauses. All current test services are off and cached runtime assets are preserved.
