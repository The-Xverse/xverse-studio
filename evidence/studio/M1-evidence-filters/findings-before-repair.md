# T030 evidence-filter findings before repair

Baseline de395ff26b6ddaa83f1b8a647db9cebaf5fb4efe. Numeric owned-reference recordedAt is Unix seconds but Results treats it as JavaScript milliseconds. Missing source time becomes tick0 in the reader and array-index time in plots. Events have no emitter/time filters; observations do not use observer/field/time/element predicates. Observation/evidence responses lack abort+generation identity guards. Existing annotation context guards must remain intact. Original records, integrity, snapshots and lifecycle are read-only; no filter triggers Start/commands.


EF-004 — Independent review found that the provisional local RFC3339 helper accepted nine fractional digits while the API contract permits six, allowed Date.parse to normalize invalid dates, and fell back to raw receipt strings after the server explicitly reported receiptEncoding unavailable. Record this before repair. The successor must honor explicit projection metadata, reject invalid calendar dates and precision, and keep unavailable receipts distinct from known UTC timestamps. Browser contract probes will cover invalid raw dates and server-unavailable valid-looking raw timestamps.


EF-005 — First successor native browser run passed missing-time display and delayed-observation isolation, but applying evidence filters invoked the existing setSelected callback, which unconditionally navigates to Model. Preserve that callback for explicit element navigation. Evidence predicates need local state initialized/synchronized from the Model selection so Apply/Clear stays in Results. Two focused browser cases failed before this correction; the original receipt check passed its UTC assertion before encountering this navigation failure.

EF-006 — Self-review found an aborted retained request may leave historyLoading true after switching to live delivery. Live filter Apply and busy state must depend on the live view, independently of the aborted retained request. Add an intentionally delayed read probe before repair.

EF-007 — Self-review found the initial plot gates clock domain but could compare ticks with different declared resolutions or share one numeric axis across incompatible units. Preserve the raw table and refuse an assumed alignment/conversion for these cases. Add explicit inert response fixtures before repair; they do not claim runtime verification.


EF-008 — Final1024 visual review shows intentionally bounded table overflow, but its div currently lacks focusability. A keyboard user cannot reliably scroll to the original-time/receipt columns. Add a named focusable scroll region and verify horizontal ArrowRight movement when content actually overflows, while preserving focus visibility. This is a product access gap, not a reason to widen the application viewport. Source held for independent review before repair.

Interpretation clarification: sourceTime.resolution is raw declared metadata, not a general tick-unit conversion. Charts use original signed ticks only; no physical seconds conversion is inferred. A null top-level tickUnit remains Not declared. Different declared resolutions are conservatively displayed in the table, and fixture clock/provider labels do not establish runtime admission.


Independent review: xdl_baseline inspected the final filter/time helpers, controls, plot/table and Results request guards read-only and reported no concrete remaining issue in that requested scope before the focusability successor. Six native browser tests subsequently passed in33.7s including original-receipt preservation, both viewport keyboard focus, and actual ArrowRight scrolling where1024 content overflows868px width (1151px content, scrollLeft283).1440 content fits1260px and focus remains available. Complete receipts/hashes are retained under keyboard-green/. These Linux browser/reader checks do not satisfy native Windows, external runtime or physical acceptance.
