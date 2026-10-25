# Profile and catalog contract cases — T060 and T049

| Task case | Test (contract) |
|---|---|
| T060 compatible mixed-profile | `test_admitted_profile_lock_materializes_exact_local_schema_and_preserves_execution` (both admitted profiles bound together; plan unchanged) |
| T060 namespace collision | `test_duplicate_namespaces_and_executable_lock_fields_never_mutate_project`, `test_namespace_collisions_are_refused_by_bind_and_lock_validation` (authored duplicate owner refused by bind; duplicate manifest locks refused) |
| T060 core-semantic redefinition | `test_redefining_an_admitted_profile_is_an_explicit_conflict` (changed `schemaRef`, `conflictPolicy`, `compatibleApiVersions` or version: blocking `PROFILE_CONFLICT` in preflight, bytes preserved); `test_core_looking_unadmitted_namespace_is_explicitly_unresolved` |
| T060 malicious presentation | `test_malicious_presentation_is_never_admitted_even_with_a_matching_digest` (self-consistent forged lock refused; import refuses `UNSAFE_PROFILE` or preflight refuses `PROFILE_CONFLICT`; no run) and `test_profile_presentation_has_no_executable_hooks_or_core_redefinitions` |
| T060 unsupported version | `test_profile_digest_conflict_and_unknown_version_do_not_mutate_project`, the `version` case of the redefinition test |
| T049 versions | `test_artifact_versions_are_distinct_immutable_identities`, `test_api_refuses_invalid_artifact_versions_without_metadata`, unsafe/unpinned metadata refusal |
| T049 role/realization/placement independence | `test_role_realization_and_placement_are_independent_choices` (+ semantic-edit binding tests) |
| T049 definition/instance identity | `test_definition_and_instance_identities_are_distinct_and_the_definition_is_unchanged`, `test_an_existing_instance_identity_cannot_be_reused` |
| T049 inert artifacts | `test_artifact_registration_is_inert_idempotent_and_records_unavailability` |
| T049 untrusted form metadata | `test_untrusted_form_metadata_is_stored_as_inert_text`, `test_untrusted_configuration_values_are_stored_as_data_not_interpreted`; the UI renders no raw HTML |

Implementation change found necessary by review: preflight now reports authored Profile resources
(`ProfileRegistry.authored_findings`): unadmitted namespaces are blocking `PROFILE_UNRESOLVED`, and
redefinitions of admitted semantics are blocking `PROFILE_CONFLICT`; `bind` also requires the core API
version. An independent review first found that several new tests passed for unrelated reasons (unknown
profile ID instead of redefinition; digest mismatch before content; incidental reference-contract
blocking); the tests were rewritten to reach the paths they name. See `verification.json`.
