# Declared, resolved and observed communication projections (T056)

`GET /projects/{projectId}/communication?runId=` (`connections/projections.py`) and the Connections
view's perspective switch (`features/connections/projections.tsx`) keep three facts apart.

- **Declared.** Authored flows with their owned contracts. A run uses its frozen inputs. A run without
  them, or without a selected Scenario, is refused (`409 SNAPSHOT_UNAVAILABLE`) rather than projected
  from the draft.
- **Resolved.** The run provider's frozen `resolvedFlows`, kept separate from evidence `elementRefs`,
  with transport, provider, scope and limitations. A draft says routes resolve only at run start.
- **Observed.** Samples from observers of the run's selected Scenario, attributed by full flow
  reference, with source, clock, ticks, integrity and freshness.
  - Freshness is `live` or `stale` while running, `final` for an ended run with a valid journal, and
    `partial` for a verified prefix. A missing, undecodable or future receipt time, or an unknown run
    state, gives `unknown`.
  - Collection states:
    - `not_collected`: no observer targets the flow; silence is not a fault;
    - `collected_none`: no sample yet;
    - `not_observed`: an ended run recorded nothing, so an expectation was not met;
    - `unverified`: the journal is invalid or unavailable, so nothing is shown as observed.
- **Lite and native X-COM.** The owned reference is labelled "in-process (owned reference worker)",
  with no network transport or native X-COM traffic. Lite is labelled "Lite X-COM bridge". Native
  X-COM is stated as not integrated.
- **Refreshing.** The view re-projects when the run's state changes and every 2 s while it is live.

Tests:
- `tests/integration/test_communication_projections.py`:
  - draft, a real feedback run, and a run/project mismatch;
  - every freshness and collection state, unverified journals, and foreign Scenarios;
  - attribution across two Systems that share flow ids;
  - malformed record fields;
  - `resolvedFlows` kept separate from evidence `elementRefs`;
  - missing frozen inputs or Scenario, including the route-level 409;
  - Lite labelling.
- `tests/e2e/connections.spec.ts`: perspectives before and after a real run, and an open Observed view
  that follows a running run to its final state without navigation (red-checked by removing the
  refresh key).

Native Windows is blocked at user request.
