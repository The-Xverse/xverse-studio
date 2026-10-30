# Provider fixture scopes

`catalog.json` records the original T011 fixture roles and their source owners.
It is data for reviewers and tests, never an executable project or dispatcher.

`studio.reference` is the existing native executable in the application source.
Its fixed worker runs the bounded reference model and produces its own samples.
Source ticks use the declared simulation clock; host receipt times stay separate.
The nine closed scenarios in `run_failures/host.py` affect only newly owned native
test roots and original verified handles. This host is developer tooling, with
no application or project-supplied fault switch.

`fake_provider.py` supplies six deliberately incompatible descriptions based on
an actual enrolled Autoverse descriptor. Its clock is synthetic, its lifecycle
callback fails if reached, and it has no native launch binding. These cases test
refusal before effects; they establish no running workload or simulator clock.

The separate recording under `tests/fixtures/runs/` contains exact bytes from a
previous complete Autoverse run. Inspection/replay cannot start a process or grant
current ownership. Its original `external_demo` scope is retained; an imported
reader limitation must remain visible. It is not `studio.reference` execution.
