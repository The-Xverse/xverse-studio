# Bounded source-read findings before repair

2026-10-25. Base ba5ef0a33c8d161096420cad4b868205830ba1fd. The independent retention review RET-I03 exposed shared `Projects.read`/`assert_intact` calls that load externally mutable bytes without a pre-read allocation bound.

READ-001: a committed file grown externally beyond the advertised 1 MiB document limit is loaded without refusal. Retention's aggregate budget cannot recover memory already allocated by this reader.

READ-002: externally invalid UTF-8 escapes as UnicodeDecodeError, rather than an actionable typed unavailable-source diagnostic.

READ-003: a source symlink to another file inside the managed data root can be read as authored XDL. Refuse source-path symlinks, including links to private managed material, before opening it. No external bytes should be rewritten or deleted.

Tests before repair: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 TMPDIR=<loop10-cache>/tmp .venv/bin/python -I -m pytest tests/integration/test_project_read_bounds.py --basetemp=.studio-local/read-bounds-first -q --tb=short`: **3 failed**, 1.52 seconds. Oversized bytes were retained, not deleted; all reproduction data lives on loop10. No Windows installation/test executed.

READ-004: the bounded reader still returns externally changed bytes with the prior committed digest but no explicit integrity marker; the browser can label them Saved revision. An initial new probe expected GET412 and failed because read access deliberately remains available for inspection (the existing revision regression requires this). Preserve that read/inspection contract: return200 with `sourceIntegrity=modified` and exact expected/actual digest diagnostics, keep the external bytes untouched, and retain412 on authoritative revision operations. The browser must distinguish inspected external bytes from a committed revision and refuse Save until recovery.

DOC-PLATFORM-001: the support guide still described CI as future/unexecuted even though retained native Ubuntu24 candidate receipts exist. Reconciled the prose with actual Linux passes and the current Windows hold; no new support claim is inferred for uncommitted changes.

READ-005: per-document bounds alone still allow many externally grown documents to exceed the complete 16 MiB project read envelope. A retained invalid-draft project with 17 documents, each externally grown to exactly1 MiB, is read successfully before repair. The focused regression failed in0.62s (`-k complete_project`, `.studio-local/project-aggregate-first`). Enforce a remaining aggregate byte budget before each opened-descriptor read; preserve every external file and the committed revision.
