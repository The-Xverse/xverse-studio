# ADR-0074 — Recorded-run provider controls frozen rerun availability

Date: 2026-11-05. Status: scoped presentation repair; verification pending.
Traces: T091; FR-059/FR-060; AC-029. Backend admission remains authoritative.

A current native browser check on a copy of the successful Autoverse frozen rerun
finds the rerun button enabled without an installed Autoverse provider. The UI uses
the backend's global rerun operation, which the executable reference supports, for
every recorded provider. No execution occurs; the backend still refuses unsupported
sources. The enabled control nevertheless misrepresents current provider support.

Retain the global operation gate and require a current descriptor matching the
recorded provider and evidence scope, with available/host-compatible facts and
Start support. The built-in reference retains its existing rerun path. Other
providers require their explicit nonphysical version1.0 rerun declaration. Unknown
or missing facts leave the control disabled and explain how to restore an admitted
compatible provider. Historical evidence remains inspectable without that provider.
This is current control availability, not preflight readiness or execution authority;
the backend still verifies frozen identity/version/installation, effective inputs,
full readiness, ownership and independent Start admission on every new request.

Keep provider-specific logic independent of industry profiles. No endpoint, contract,
installation, provider permissions or executable behavior changes. Verify absent,
foreign, unavailable, host-incompatible and undeclared provider presentation plus
declared external and existing reference controls using labelled descriptor replies,
without sending execution requests. Repeat real recorded comparison and original
payload playback at both desktop sizes with browser device isolation. Preserve the
original three native browser failures separately. Windows remains frozen; broader
T091 and milestone acceptance require their original evidence audit.
