# Original Autoverse observation playback

The Observations view now offers read-only playback of original records when no
admitted plot samples exist. The retained Autoverse demo supplies21 real telemetry
receipt records. Their original payloads, units, freshness, metadata conflicts and
missing source-time facts remain inspectable. Playback advances in journal order
at a declared display interval; it performs no runtime operation or clock alignment.

On source `98956756644e8d9022d0e5704607f87eba8f5b66`,22 native Chromium checks pass
at1024×768 and1440×900. Native Tab/Enter controls browse, pause, replay and page
through all21 original records as20+1, with visible focus and no horizontal
overflow. All returned pages equal the original decoded source records. Leaving
the view stops playback; a late original response preserves Home and newer focus.

The source-clock filter correctly returns no telemetry records for an unavailable
source time. Separate labelled response fixtures verify read failure/retry,
invalid integrity, wrong event/snapshot, oversized pages, repeated cursors and a
large payload's explicit bounded display. These are transport/display tests, not
canonical source corruption or newly observed telemetry. Invalid integrity keeps
inspection available and disables automatic playback. No signal decoder, unit
conversion, coverage assertion or numeric comparison is invented.

Review first exposes a real page-focus defect: both viewport checks fail when the
selected record is not focused after paging. The repair restores focus only for
the original action and unchanged user intent. The two deliberate-focus controls
continue to pass. Earlier driver preparation/navigation/selection failures, the
old UI heading failure, initial14 pass, separate2-fail/2-pass focus review and
16-pass successor remain recorded in [attempts](attempts.json).

The existing frozen comparison journey also passes at both viewports. It keeps
configuration differences visible, blocks unsupported numeric pairing/playback
and retains the original acknowledgement/foreign-child transport fixture over
the previously failed real rerun. It issues no new admission or Start. Its one
browser case is separate from the22 playback cases.

The unchanged declared finite benchmark passes30 samples after one warm-up for
each metric and viewport on the same source and exact six UI assets:

| Viewport | Open + validation p95 | Selection p95 | 50,000-event history p95 |
|---|---:|---:|---:|
| 1024×768 | 1277.7 ms | 46.7 ms | 361.7 ms |
| 1440×900 | 1432.2 ms | 47.9 ms | 428.2 ms |
| Threshold | 3000 ms | 150 ms | 2000 ms |

The authoring benchmark remains200 visible Elements/400 connections; history
remains an explicitly inert synthetic50,000-record source with200 returned rows.
It is separate from the actual21 observation records in the93-record demo journal.
Raw arrays and resource samples are retained. Peak sampled backend RSS is
318,451,712 bytes; this is neither a continuous exact peak nor a memory guarantee.
This refresh does not establish T096's producer/control/campaign acceptance.

All541 selected implementation/test/toolchain inputs match Git and remain
unchanged across final playback, comparison and performance. A fresh Vite build
from those committed inputs reproduces all six actual browser assets exactly.
All production backend sources remain unchanged. TypeScript, architecture, spec,
descriptive platform compatibility, changed Python lint and whitespace checks pass.

Each native backend exits through its original handle and releases its copied
root. Original recording/snapshot/journal hashes and execution ledger counts remain
unchanged. No new reference, simulator, campaign, evaluation or physical workload
is executed. Public records are a decoded observation subset, not a standalone
canonical journal. Private originals, DBs, sessions, owner keys and operator paths
remain excluded from this evidence directory.

**Counts remain71 completed /19 in progress /10 blocked; zero accepted milestones.**
T091/T097 stay in progress. A successful fresh rerun still requires resolution of
the unchanged CARLA/GPU startup prerequisite. Current Windows, full critical-flow
accessibility, other engines, human/AT, live producer/control, actual hardware,
packaging and complete M0–M4 acceptance remain open.
