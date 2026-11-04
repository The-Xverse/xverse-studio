# Autoverse native authoring/history performance — T067 closure

T067's complete finite reference-workload verification closes: **71 completed /
19 in progress / 10 blocked; zero accepted milestones**. The [clause audit](clause-audit.json)
covers its literal requirements. T038's wider operability matrix, current Windows
requirements and full AC-030/AC-031/SC-008 acceptance remain open.

The actual Autoverse project supplies the resource/profile identities for a separate
synthetic authoring variant. Its197 logical assets plus three standalone placement
nodes make200 visible Elements;400 single-destination flows make400 connections.
Public pinned XDL validation and compilation pass. A separate50,000-record synthetic
history fixture reuses the actual frozen input identity, with no process ownership
or control capability. It never changes the original93-record completed recording
or claims50,000 observed simulator events.

Each metric retains30 samples after one documented warm-up, independently at both
required viewports. The original thresholds and complete end-to-end timers remain.

| Viewport | Open + validation p95 | Selection + inspector p95 | Filtered200-row history p95 |
|---|---:|---:|---:|
| 1024×768 | 1167.5 ms | 47.0 ms | 411.5 ms |
| 1440×900 | 1285.7 ms | 45.9 ms | 407.5 ms |
| Threshold | 3000 ms | 150 ms | 2000 ms |

The same real HTTP/browser journey verifies matching validation replies, all200
nodes/400edges, exact selected inspector identity, native Tab/Enter structured
alternatives, visible focus, keyboard history paging and no horizontal overflow.
A separate rendered readback confirms200 distinct CSS-visible nodes intersect both
the canvas and the browser viewport at each size. The server and DOM retain200
history rows and explicitly report49,800 omitted records; the full immutable
synthetic journal remains hash-valid. Browser writes are validation requests only.

The first cohort exposed a fixture-counting mistake; the next recorded3534.8ms p95
at1024px and stopped before its final history measurement on a Results count-badge
locator. Both remain retained. A corrected full diagnostic cohort passed and
identified1.35–1.40s of background inspection competing with validation. Inspection
decoded the large authored resources twice. The repair passes only already-classified
Profile source documents to the same fresh registry checker. The regression fails
with two decodes before the repair and passes with one afterward; all eight profile,
unknown-payload, unparsed-source and read-only decision checks pass. Direct diagnostic
inspection requests fall to roughly0.68s. This establishes that avoidable delay;
it does not attribute each earlier rare stall to a proven cause.

[Metrics](metrics.json), separate model/history JSON files and four screenshots
retain the actual samples. [Native facts](native.json), [source binding](source-binding.json),
[inspection guards](inspection-guards.json), [visible readback](visible-readback.json),
[owner/semantic readback](readback.json), [attempts](attempts.json),
[commands](commands.json) and [review](review.md) state their scopes separately.
The model-inputs.zip and history-fixture.zip contain exact inert test inputs;
private DBs, sessions, owner keys, host receipts and operator paths are excluded.

The performance/guard cohort uses source `2e0c78209f3f04a80452e8e18de77dffd65529ab`.
All534 contributing source inputs match current `49d4c56d9197ee8f101c4c7c10ec128391ec5081`.
Two additional contributor tools are independently executed: reproducible preparation
and actual rendered visibility. They change no app/runtime/performance-journey bytes.
The six compiled UI assets inherit exact unchanged frontend/build inputs from the
T093 build; no stale compiled UI substitutes for a changed frontend.

The recorded native Ubuntu22.04.5 host has32 logical CPUs/available affinity cores,
24 physical cores,32GB-class memory and local non-rotating storage backing.
Backend RSS sampled across the final journey peaks at312,799,232bytes; this is a
sampled value, not a hard memory limit. Browser heap samples cover the history stage.
The source reader admits64MiB/100,000records and at most two cached contributing
sources within64MiB; those source-byte limits do not describe decoded-object memory.

Original639 resolved payload hashes and93 enrolled host-file hashes match. Original
system Docker stays inactive, host TAP absent, and its pre-existing router mismatch
unchanged. Symlink target strings were not reaudited. No original environment was
restored, new simulator workload launched or physical action performed. Current
Windows, continuous producer/control responsiveness, other browser engines,
human/AT, cross-industry execution, packaging/release and independent milestone
acceptance are not established by this finite Linux benchmark. T091's CARLA/GPU
startup prerequisite remains unresolved.
