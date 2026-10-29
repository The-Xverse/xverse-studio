# Independent event transport review status

Backend review only; frontend session/App were actively being implemented during this pass. This is not native Windows, external provider, browser reconnect, hardware, or complete milestone acceptance evidence.

Inspected the production event manager, API selectors/resync routes, source reader, advertised capability limits, task T025/T026, and the supplied run-event contract. Independent finite probes use disposable public journals without launching runtime processes. Review drivers derive scratch paths under repository `.studio-local/review-temp`; all receipts retain exact before/after source hashes.

Positive dynamic results (`semantics-before-repair.json`):

- Byte-heavy Unicode records produce an exact explicit presentation gap, keeping combined batch/control bytes below the configured pending bound and data frames below the configured frame bound.
- Resync exposes omitted history count while preserving the exact last canonical sequence/digest as its resume watermark.
- A newly recomputed valid hash-chain fork after an acknowledged position requires resync, with unknown loss count rather than an invented range.
- `unknown` execution state remains live with a heartbeat, not a terminal claim; closing an entered iterator releases admission.
- Transport and resync leave all original fixture journal bytes unchanged.

Source inspection: cursor proofs bind run/snapshot/sequence/digest and check canonical encoding; numeric legacy cursors remain explicitly weaker compatibility positions. Missing/transient source acquisition is distinguished from invalid evidence and verified-prefix evidence. No transport method calls runtime start/command or owns backend process lifetime. Control frames have no canonical SSE id. The advertised reserved control slot explains one extra control alongside the canonical-event bound; recovery has its separately advertised 200-record bound.

Two concrete findings were recorded before repairs in `findings-before-repair.md`. STREAM-I01 has an independent successful successor (`startup-disconnect-successor.json`). STREAM-I02 successor remains pending at this record. Do not interpret positive cases as an exhaustive acceptance pass.
