# Draft revision and run snapshot overlay — T047

The workspace context shows the draft revision beside the selected run's immutable snapshot with a
divergence badge. The panel compares the draft with the executed run inputs (documents, elements and
nodes, run-scenario parameters, profile locks), lists unused draft documents separately, navigates to
elements and draft sources, and opens the verified frozen inputs with snapshot identity and digest.
The canvas marks instances new in the draft or changed since the run. Everything is read-only; the
browser test proves the snapshot bytes never change while editing and undoing during a running run.
See `verification.json` and `independent-review.md`.
