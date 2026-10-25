# Independent retention review findings before repair

2026-10-25, Linux. Reviewer did not author retention implementation. Preliminary planner snapshot only; integrated API is still being completed by its owner. Exact source digest and machine-readable outcomes are in preliminary-probes.json. No implementation changes by reviewer.

## RET-I01 — malformed structural links can permit destructive project planning (HIGH)

Given a selected project p and retained snapshot `{snapshotId: 's', projectId: ['p']}`, plan_retention returns p eligible for `owned_project_files_and_index` deletion and no protection. A malformed structural dependency cannot prove historical independence; it must refuse conservatively. The source also calls `.get` on campaign.baseSnapshot without guarding its shape: a list yields AttributeError rather than typed conservative refusal. Review must extend shape validation to relevant record/envelope collections rather than merely special-case these two examples.

Expected repair: validate retained dependency envelope/link shapes, treat malformed/unknown dependency data as unresolved, and reject plan/apply without effects. Preserve the original record/source. Add regression cases for malformed snapshot projectId, campaign baseSnapshot, non-object records/children and invalid dependency list shapes. Rerun exact probes after repair and assess integrated API once source owner confirms freeze.

## RET-I02 — non-resource source and unsupported supporting files can prove false artifact independence (MEDIUM)

Planner snapshot captured in source-shape-probes.json (new source digest recorded there). A retained project document containing YAML null, a scalar or a sequence is treated as a complete empty reference scan, and artifact registration a is eligible for deletion. A supportingFiles entry `opaque.bin: opaque` is likewise treated as safely scanned text. These shapes are not admitted XDL resources/declarative supporting data and cannot prove absence of artifact dependency. Reject malformed source shapes and unsupported supporting formats conservatively; integrated state construction must also detect unknown filesystem files/current-byte changes rather than trusting committed record strings alone. No origin artifact bytes are selected for removal in these probes; the boundary is protected metadata/dependency integrity. Retain valid invalid-draft source unchanged while refusing deletion.

## RET-I03 — source reads can allocate beyond the advertised proof budget before rejection (MEDIUM)

Integrated service snapshot uses `projects.assert_intact(...)` before bounded source reading. That method reads externally mutable document/supporting files with `read_bytes()` before the retention proof budget checks. `_source` itself checks stat size then calls `read_bytes()` and only charges the resulting bytes afterward, so a growing/replaced file can exceed that prechecked size and allocate beyond the stated 64 MiB scan envelope. This violates the bounded failure contract even if subsequent digest mismatch correctly prevents deletion. Use bounded opened-descriptor reads/streaming charged before allocation, avoid duplicate unbounded integrity loads in the retention path, and verify oversized/growing external inputs refuse before an unbounded read. No destructive action is needed to reproduce; do not weaken the cap.
