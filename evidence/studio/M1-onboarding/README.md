# Onboarding, import and parameter scenarios (T015) and profile discovery (T061)

T015: `tests/integration/test_project_import.py` and `tests/e2e/project-onboarding.spec.ts`.

- **Prepared examples.** Both owned blueprints open with the exact example bytes, validate, reach a
  ready preflight and execute nothing. Each guided entry states its scope (`owned_reference`), maturity
  (`fixture`), limitations and expected observations, and the browser card and scope note show them.
  Recent projects reopen a saved draft from the workspace list.
- **Imports.**
  - A round trip preserves sources and layout.
  - Unsupported format versions, undeclared or missing resources, and unsafe archive paths are
    refused, and the project count does not change.
  - Archive hardening for symlinks, oversized input, duplicate entries and credentials is covered by
    `tests/contract/test_review_regressions.py` and `tests/integration/test_exchange_and_retention.py`.
- **Unknown extensions.** An unresolved namespace containing command-like text is preserved byte for
  byte and identified as `XDL-SEMANTIC-PROFILE-MISSING`. That finding blocks preflight in the API and
  in the browser readiness view, and semantic edits are refused. Layout saves and source saves keep
  it; the source save stores exactly the authored text. Exports are unchanged and it never runs. It
  was also imported through the browser file input with the same outcome.
- **Parameters.**
  - The browser form refuses out-of-range values with a validation message. No edit request is sent
    and the revision does not change.
  - The backend accepts such values only as drafts. Admission then blocks numeric bounds with
    `LIMIT_EXCEEDED` (both edges tested) and categorical values outside the domain with
    `CAPABILITY_UNSUPPORTED`.
  - Mistyped values are refused before a draft is saved.

T061: `test_api_profile_discovery_is_exact_and_independent_of_providers_and_blueprints`.

- **Exact metadata.** The versioned profile API returns namespace, version, maturity, limitations and
  digest metadata. These are pinned to the packaged schema bytes and to the profile versions the
  blueprints declare.
- **No OS or provider claims.** Profiles never claim OS, host, architecture, provider or execution
  authority, at any nesting depth. Providers carry `supportedHostOS` and `hostCompatible` instead.
- **Independence.** Binding profiles to a project composed from a blueprint changes neither provider
  availability nor the executable plan, and composing projects leaves discovery unchanged.
- **Where admission lives.** Profile admission and composition (the T060 cases and the authored-profile
  preflight findings) are in `services/studio-api/src/xverse_studio/profiles/`.

Not covered: live Lite onboarding, the five-person study, and Windows (blocked at user request).
See `verification.json`.
