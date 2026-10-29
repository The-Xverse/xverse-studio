# ADR-0007: Bounded transactional Scenario intent

Status: implemented component; final combined-candidate/browser evidence is recorded separately. Native Windows installation/testing is on user hold.

The existing Scenario view required source editing for schedules and observers. Typed operations now
author the public pinned XDL Scenario fields for initial conditions, steps, faults, observers and
metrics. They share the existing optimistic-revision project transaction and authoritative full-set
validator. IDs remain immutable; update merges preserve unselected payloads, and removal cannot
silently delete dependent declarations. Source bytes outside touched documents remain unchanged.

Public XDL validation does not establish the reference integrity of Studio's owned bounded assessment
extension. A pure `source_definitions` check therefore validates that extension's observer and metric
dependencies after the entire Scenario transaction. `snapshot_definitions` still verifies its immutable
snapshot digest before delegating to the same checker; draft validation grants no run/evaluation authority.
An explicit `set_assessment_definitions` operation can repair references atomically with an item removal.
It preserves other namespaces, rejects unadmitted versions, and validates existing version/digest pins.

Typed edits are bounded before copying: 64 KiB encoded envelope, depth 64 and 10,000 value nodes. A
Scenario has authoring limits of 64 steps, 32 faults, 32 observers and 64 metrics; an assessment set has
at most 32 definitions under its existing v1 contract. Capabilities advertise the limits. Deep/nonfinite
or oversized edits produce typed rejections rather than uncaught recursion failures. These limits also
protect other semantic edit kinds. Existing bounded source editing/import remains available for data
outside the typed authoring envelope; unsupported execution stays blocked rather than normalized away.

Action objects, fault activation/recovery strings, calculation references, schema URIs and evidence
sinks remain inert declarations. No schedule language, arbitrary code evaluator, URI fetch or provider
privilege is introduced. The owned reference provider's exact source/configuration admission is unchanged;
unsupported topology/schedule intent cannot fall back to a preset. Recorded requested effects and observed
effects remain distinct.

Compatibility: additive Studio HTTP v1 edit operations, unchanged XDL/profile/evaluator versions and
stable requirement/task IDs. The tighter typed payload bounds are an explicit resource-failure repair;
immutable historical source/evidence is not rewritten. Affected tasks T042, T082–T088; requirements
FR-053–FR-057, NFR-004; AC-025/AC-026 remain open beyond the evidenced component/provider scope.
