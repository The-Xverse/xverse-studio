# Separate read-only history/focus review — 2026-10-26

Reviewer `t076_hybrid_tests`; bounded calls, no writes, mutations or suites. Design audit one read,
initial repair review four reads, final follow-up one read. Final verdict: **PASS for scoped Linux
slice**, no remaining blocking finding in the inspected repair. T038/T067 stay open.

The design audit confirmed the departed-project race: after awaiting `applyStep`, the old handler
unconditionally updated visible history and started `refreshProject`, recapturing obsolete navigation
intent. The repair preserves verified per-project history without replacing a newer head, guards
visible state/errors by project and load generation and applies the full restore response directly.
Response equivalence was checked through `restore → mutate → _commit → projects.read`.

Initial repair review found a remaining shortcut bypass: Ctrl+Z/Shift+Ctrl+Z while Undo/Redo itself
was focused did not arm the shared completion/focus path. The main runner reproduced it, retained
the red results and repaired it. Follow-up review confirmed toolbar-origin shortcuts now share the
path, other origins retain their prior behavior, and focus preference follows the originating
control with an enabled opposite fallback.

Post-busy context/active-element guards prevent focus theft. Delayed real-response checks separately
cover departure, deliberately moved focus and a newer same-project edit/history head; semantic bytes,
persisted history and focus are asserted independently. The main runner reports eight focused checks
passing; the reviewer did not execute them.

Limits: selected Linux Chromium workflows/text/paint only, no actual screen reader, native Windows
or complete accessibility/milestone acceptance. Backend authority and immutable revisions remain
unchanged; adding a binding grants no provider support.
