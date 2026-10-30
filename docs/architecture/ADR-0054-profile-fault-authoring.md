# ADR-0054 — Profile-backed fault schedules and provider choices

Date: 2026-10-30. Status: implementation candidate.

T084 needs guided timing for faults whose native activation/recovery fields are
opaque text. The admitted experiment-lite 0.1 profile already supplies typed
fault-intent trigger, duration, clock and owner reference. Its public compiler
continues to own validation, normalization and executable plan identity.

Provide an editor adapter under the existing profiles feature for that exact
profile declaration/schema/version. It edits the existing extension in XDL; it
introduces no schedule sidecar, activation-string parser or alternate interpreter.
Keep original units, unknown extensions and unknown payload fields. Unsupported
payload versions remain intact with a source-edit explanation. Target/clock choices
come from the selected System/Deployment. All edits use the existing transactional
semantic-edit API and normal authoritative validation.

Installed providers may expose inert scenarioContracts 1.0 choices with fault
kind, local System target, activation/recovery markers, maturity, input-surface
requirement, clock and timing-profile identity. The generic editor may copy a
matching choice into a draft; it may not grant authority, start a run or infer
support from matching text. Provider readiness and Start independently verify the
complete source, profile, selected deployment, bounds, permits and ownership.
Classic Autoverse publishes its existing closed browser-input-loss choice; its
runtime semantics and authority are unchanged. No industry-specific dispatch is
added to shared editor code. Other providers need their own admitted declarations.

Verify real form creation/editing and source preservation against the enrolled
Autoverse project, unknown/mismatched profile and provider metadata, invalid clocks
and times, and actual positive preflight/complete native demo of GUI-authored
faults. Preserve all failed attempts and exact source/build/environment evidence.
This does not complete T084, timeline codec admission, AC025 or a milestone by itself.
