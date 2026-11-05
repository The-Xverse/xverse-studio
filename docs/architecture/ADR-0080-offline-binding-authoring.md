# ADR-0080 — Save authored bindings without installing their runtime

Date: 2026-11-05. Status: implementation under verification.
Traces: T057/T058/T059, T038/T097; FR-039/040/042, NFR-006; AC-018/031.
Windows remains independently frozen.

Native keyboard substitution on the actual copied Autoverse project reaches a
404 `PROVIDER_UNAVAILABLE` before its valid draft edit commits. The ordinary
backend has no installed Autoverse descriptor, so provider-dependent resolution
cannot succeed. Requiring that descriptor for source authoring unnecessarily
blocks the existing realization/placement form, even though source editing is
independent of execution admission.

Keep expected-revision, source integrity, semantic edit and authoritative selection
validation before publication. After a valid compile, a missing descriptor permits
only the authored source transaction: compatibility remains `blocked` with explicit
`PROVIDER_UNAVAILABLE` and the requested provider identity, and resolution is null.
Never substitute a reference descriptor or invoke provider configuration. Discovery
exceptions still propagate and roll back; they are not classified as absence.

Existing installed-descriptor compatibility behavior is unchanged. Explicit
resolution/comparison and execution paths keep their required descriptor lookup;
this authoring exception grants no installation, readiness, lifecycle or physical
authority. Unsupported authored combinations remain inspectable but cannot execute.
No industry/provider-specific dispatch is added.

Verify absent-provider virtual/physical/hybrid authoring, preserved logical/source
identity, invalid target refusal, stale revision refusal, discovery failure rollback
and strict missing-provider resolution. Native keyboard journeys use the actual
recorded Autoverse source, retain blocked compatibility and immutable historical
evidence, and exercise late-response focus/navigation/selection/dialog boundaries.
Live device substitution, fresh provider admission and full accessibility/milestone
acceptance remain separate gates.
