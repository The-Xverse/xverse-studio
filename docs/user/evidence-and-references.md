# External references on recorded results

In Results, select a run and choose **Add external reference**. Enter the external URI and referenced
revision. The target is stored as inert text; Studio does not retrieve or verify the external document.
Use a stable revision identifier, or explicitly record `unknown` when it is unavailable.

The optional **Include reported claim status** field preserves the external party's reported text.
It does not change the run's execution status, assertion verdict, cleanup outcome or evidence integrity.
A link with no reported status displays **Not supplied**. A reported pass can coexist with a failed
Studio assertion; neither result is silently replaced.

Select the frozen model/Scenario subjects, frozen assertion or metric definitions, and run evidence
that the link concerns. Definition links retain the exact frozen definition digest. Editing the current
project does not retarget a historical link. Source unavailable or changed may prevent new subject
associations; ordinary comments remain separate metadata.

Editing a reference saves a new annotation revision. Previous revisions remain visible, including a
previously absent claim status. Removing a reference records a tombstone. Evidence exchange preserves
annotation content/history while integrity checks protect canonical snapshot and journal bytes.

External targets cannot include credentials or query strings. Reported status is bounded to 256
characters, and each subject collection to 32 entries. Unsupported or invalid references produce a
specific error instead of being silently omitted. These limits do not establish external compliance.
