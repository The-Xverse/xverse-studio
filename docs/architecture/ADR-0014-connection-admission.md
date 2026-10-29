# ADR-0014: Connection admission over declared semantics

Status: implemented owned components under verification; no M2 acceptance claim.

Amended by ADR-0016: a provider that declares the owned connection contracts admits a declared linear
converter and a unit-delay feedback cycle; without such a provider both stay unsupported as below.

FR-034, FR-035 and FR-038 require connections to be checked against direction, interface, units,
multiplicity, timing and feedback semantics, conversions to be explicit, and feedback cycles to be
judged by declared causality contracts rather than a universal acyclicity rule. The pinned XDL validator
checks flow endpoint membership, direction capability, interface identity and network/time-domain
membership; it treats `quality` as opaque and does not interpret multiplicity, compatibility modes or
cycles.

Connection admission 1.0 (`GET /projects/{projectId}/connections`, and blocking preflight diagnostics)
evaluates only what declarations state and never reports an unevaluated declaration as a pass. Check
statuses are `pass` (evaluated and holds), `declared` (a required intent such as delivery intent or time
domain is recorded, not evaluated), `unknown` (facts not established, e.g. the source set is invalid
elsewhere), `unsupported` (needs a contract nobody admits; blocking) and `fail` (violated; blocking).
Each data flow reports `structure` (the validator's verdict), `conversion`/`version` (interface
`compatibility`: `exact` passes; `explicit-converter` and `backward` are unsupported because no converter
or version-compatibility contract is admitted), `multiplicity` (Studio's interpretation `n`, `n..m`,
`n..*`, `*` over distinct attached flows, including lower bounds of endpoints with no flows; other text,
including inverted ranges, is unsupported), `clock` (`fail` when several time domains exist without a
flow or System default, otherwise `declared`), `quality` (declared quality is unsupported; delivery intent
alone is `declared`) and `causality` (flows inside a feedback cycle). A flow is `admitted` only when all
checks are `pass` or `declared`. Feedback cycles over structurally valid flows are unsupported until a
causality contract is admitted; a drawn edge or acyclic graph is never proof of correctness. System
models with inputs or outputs are model couplings and are unsupported until a coupling provider is
admitted. Network links are communication connectivity, not coupling. More than 400 flows in a System
block execution rather than leaving the excess unevaluated.

Studio never converts units, discards fields, fabricates bridges or rewrites sources. Rejected and
unsupported flows and unsupported cycles become blocking preflight diagnostics; the owned reference
provider independently refuses any topology change. The browser shows admission per flow with its
checks, cycles, links, coupling status and admitted contracts, and guides the connect form to
same-interface, input-capable destinations while listing others with their reason.

Compatibility: the baseline reference flows are admitted (their clock and delivery intent are `declared`); existing readiness records are unchanged.
Verification: `tests/contract/test_connections.py` with `tests/fixtures/connections/` (declared expected
semantics per fixture) and `tests/e2e/connections.spec.ts`. Resolved routes and observed communication
projections (T056) and admitted converter/causality contracts remain open.
