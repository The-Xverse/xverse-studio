# ADR-0042: Anchored native writes and owned revision publication

Status: implemented;153 target API/native CLI and4 native browser checks pass.
Installed complete Autoverse verification is mixed at cleanup; T010 remains open
for its complete security review. Linux delivery scope is unchanged.

Autoverse project fault tests reproduce a check/reopen gap in revision writes.
After a checked parent becomes a link, the old atomic helper writes into a foreign
owned test directory. Rollback can then delete a foreign empty revision directory.
Returning409 after a later secure read does not undo those unauthorized effects.

The shared atomic byte writer now acquires every ancestor with the existing native
no-follow directory APIs. It creates a private exclusive temporary file relative
to a retained parent descriptor, verifies complete writes and the temporary inode,
checks parent continuity and the regular single-link destination, then replaces
relative to that descriptor. Temporary cleanup uses the original inode identity.
Files use0600 and newly created directories0700 independently of the caller's umask.
An uncertain parent/name is a refusal, not permission to follow it or delete it.

Project revision creation records the exact staged directory device/inode.
Publication uses anchored same-parent Linux `renameat2(RENAME_NOREPLACE)` so a
late existing destination cannot be overwritten. The public native contract is
documented in the [Linux rename manual](https://man7.org/linux/man-pages/man2/rename.2.html);
the recorded host's installed headers declare the same flag and function.
There is no shell helper or overwrite fallback. Missing libc/kernel/filesystem
support reports503 `PLATFORM_IO_UNAVAILABLE` rather than weakening the boundary.

Both immediate exception cleanup and transactional rollback remove only the
original staged/published directory identity through anchored native access.
Rebound names and uncertain/unavailable locations remain untouched. Uncommitted
private files may remain for recovery when ownership cannot be verified; they are
not a committed revision or execution input. Metadata publication and immutable
source, layout, plan and receipt identities retain their existing contracts.

Confirmation uses actual enrolled Autoverse classic/platform projects, native
directory swaps, late collisions, short writes and transaction failures. Current
full-demo confirmation must also exercise the shared writer through actual native
worker preparation, controls and owned cleanup. This change alone does not close
T010's remaining session/origin, redaction, import and complete execution-boundary
review, full AC-003/032, or any milestone. It changes no companion repository.
