# ADR-0001: Industry-agnostic Studio over authoritative X-Verse contracts

Date: 2026-10-25. Status: design baseline for feature 001; implementation evidence pending.

## Context

The user needs a friendly model-based workspace across industries. Existing XDL already separates
logical system identity, realization and experiment intent. Studio must preserve that distinction while
making operation understandable. A graphical editor alone cannot establish missing runtime capabilities.

## Decision

1. Use a System-centric UI and Element as a presentation umbrella over existing XDL types. Industry
   semantics enter through profiles, reusable compositions through blueprints, and execution through providers.
2. Keep XDL and its admitted validator/compiler authoritative. Layout is separate; runs preserve exact
   input snapshots; graph projections and source views cannot establish competing execution definitions.
3. Use a local browser frontend and a typed Python backend over versioned admitted platform contracts.
   Ship native Linux and Windows backend operation with a shared browser UI; require no implicit WSL,
   Bash, or container runtime. Qualify runtime/device providers separately on each supported host OS.
   Maestro owns intra-run execution and cleanup; Studio may queue bounded independent campaign runs.
   Argus evidence is immutable; X-COM communication is separate from physical-model coupling.
4. Make capabilities and authority backend-enforced. An existing command/harness is only an integration
   candidate until conformance proves effective input identity, lifecycle ownership and evidence semantics.
   Reject unsupported edited configurations instead of running an unrelated preset.
5. Prove industry neutrality with automotive and independent process-control examples through the shared
   core, and prove physical support separately with an actual identified device/provider.

## Alternatives and consequences

An ECU-specific core would force domain forks. A generic untyped block model would lose interface and
realization semantics. A browser-owned launcher would lose durable run ownership. Direct private runtime
imports would freeze accidental interfaces and bypass admission. These approaches are not selected.

The selected boundary requires an explicit adapter assessment before real Lite execution, a reliable
XDL round-trip, durable operation IDs, typed observation/evaluation state, and separate evidence for
fixtures versus live integrations. Missing adapters block only dependent capabilities. Later native
X-COM, distributed execution, model import and numerical coupling require their own scoped work.

## Verification and maintenance

Use [feature acceptance](../../specs/001-industry-agnostic-studio/acceptance.md) and its traceability graph.
Amend this ADR if core semantics, integration authority, ownership or deployment scope changes. Record
compatibility and affected checks; preserve the original rationale and candidate evidence.
