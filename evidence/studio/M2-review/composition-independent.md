# Independent M2 composition review

Date: 2026-10-25. Reviewer: `experiments_lab`, independent of the new composition
implementation. Scope: catalog/profile/deployment facades, project persistence,
selected compiler contributors and backend authority. No implementation files were
edited by this review. Probes use uniquely named temporary directories on loop10;
no run/provider/device start is requested.

Findings are recorded before repairs and updated with exact isolated repro outcomes.
No M2 or native Windows acceptance is established by this review.

| ID | Severity | Finding | Evidence / required repair |
|---|---|---|---|
| M2-I01 | High | Project export currently returns HTTP 500 before the profile-lock import probe can proceed. `api/exchange.py` calls `check_portable_text` from `make_bundle` and the canonical journal export path, but imports only `check_text, safe_name`. | Independent HTTP project export after exact profile binding returned `500 INTERNAL_ERROR`; source inspection confirms the undefined name. Restore the import and rerun affected project/run export cases. |

Additional composition probes are in progress; static candidates are not yet
reported as verified defects. The first probe attempt stopped at M2-I01 and did not
produce a complete probe-result artifact; that failed review attempt is retained
in the tool history and described here rather than represented as passing.

## Verified composition findings before repair

The complete owned repro ran with all six reviewed composition/persistence/runtime
source hashes unchanged. Exact results and hashes are retained in
`composition-probes.json`; the reproducible probe is
`reproduce_composition_review.py`. No run was created (`runCount: 0`).

| ID | Severity | Finding | Exact owned repro / required repair |
|---|---|---|---|
| M2-I02 | High | Preflight ignores explicit imported profile schema locks/sidecars and admits conflicting semantics as ready. | Bind exact packaged locks, export/reconstruct the inert project envelope, replace the declared experiment schema with `{}` and update the manifest digest to that unadmitted schema, then import. Import returned 201; preflight returned 200 with `status: ready`, no diagnostics, despite declared schema digest `sha256:44136fa…` differing from admitted registry digest `sha256:a2123b…`. Validate declared namespace/version/schema/presentation identities and actual locked bytes before freezing/admission; retain unsupported source inspectably and block affected execution. |
| M2-I03 | High | A generated variant path can collide with an existing authored resource path; persistence commits two document IDs sharing one path, corrupting the preceding document's committed content/digest. | Start from authoritative-valid resources plus an unused Component stored at `xdl/deployment-review-collision.xdl.yaml`. Create variant “Review collision”. Creation returned revision 2, duplicate paths persisted, and `Projects.assert_intact` failed for the original document. Reject exact and portable NFC/case-insensitive path collisions before staging/commit, including collisions with supporting files. A refused transaction must preserve the previous readable revision. |
| M2-I04 | Medium | Binding compatibility can throw after the authored edit has already committed, so an HTTP/service error does not mean the mutation was rejected. | An authoritative-valid project has two Scenarios for one Deployment. `update_binding` commits revision 2, then `compile_selection` raises `SELECTION_AMBIGUOUS`; caller receives an error while the project advanced from revision 1. Compute fallible compatibility before commit or return the committed edit with explicit blocked/ambiguous compatibility. |
| M2-I05 | Medium | Malformed artifact URIs bypass typed contract rejection. | `POST /catalog/artifacts` with `originRef: https://[broken` returned 500 `INTERNAL_ERROR`; `urlsplit` raises before a typed `Problem`. Catch malformed URI parsing and return a stable 422 without creating metadata or effects. |

Positive independent observations:

- A layout-only save advanced only presentation revision (1 → 2); source revision,
  semantic digest and plan digest remained unchanged.
- An unknown Scenario extension survived a refused known-profile binding byte for
  byte; binding returned 422 and did not advance the project revision.
- Artifact metadata registration returned 201 with `executionAllowed: false` and
  `availability: unavailable`; no run/provider/device action occurred.
- Source inspection shows explicit selected Scenario/Deployment/System contributor
  compilation, full-set validation, retained full-project input digest and
  requested/effective provider equality enforcement. No private runtime entry point
  or imported executable command is introduced by these composition routes.
- Metric-definition cloning validates the source dependency graph and repins
  dependent definition digests in topological order after Scenario identity changes.
  The author's retained tests cover the resulting compiled clones; this review did
  not broaden or change that implementation.

M2-I01 was handed to the root author for repair before this complete probe. The
pre-repair export failure remains recorded; repair/retest outcomes must be appended
separately. M2-I02–I05 remain open in this report until their authors repair and
independent affected verification succeeds. Native Windows, actual independent
industry implementations, performance and usability gates remain NOT_RUN/BLOCKED;
this component review cannot declare M2 complete.
