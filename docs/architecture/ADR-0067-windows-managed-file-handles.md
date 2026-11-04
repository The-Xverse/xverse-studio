# ADR-0067 — Native Windows managed-file handles

Date: 2026-11-04. Status: implementation candidate; native Windows NOT_RUN.
Traces: T002, T039; NFR-003, NFR-009; AC-003, AC-032. No task closure.

ADR-0063 restores the required Windows host target. The existing secure-file layer
only implements Linux directory descriptors. Add a Windows implementation behind
the same managed-file interface, retaining the Linux implementation and its
security boundaries. This is a component of native host support, not a replacement
for installation, browser, persistence, process ownership or recovery acceptance.

Accept explicit local drive paths on fixed NTFS volumes with persistent ACLs.
Reject UNC/device namespaces, drive-relative paths, traversal, reserved device
names, alternate streams and Win32 trailing-name aliases. Check each existing
component using a retained directory handle and a single relative name. Use the
documented user-mode `NtCreateFile` interface and `FILE_OPEN_REPARSE_POINT`, then
check object type, reparse attributes/tag and file link count before use. Do not
rely on `OBJ_DONT_REPARSE` or a multi-component final-path check. Existing directory
opens omit `FILE_DIRECTORY_FILE`, whose documented compatibility list excludes
the reparse-open flag; exclusive directory creation uses the directory flag.
Ancestors remain held without delete sharing through the operation. Read handles
also deny write sharing; verify file state after reading. CRT descriptors retain
the existing `fileno`/`os.fstat` interface and are non-inheritable.

New objects receive a protected DACL granting the current process user full access
at creation. Existing final directories requested through `make_directory` must
already have a protected owner-only ACL. Refuse an inherited/broader ACL instead
of silently accepting it or propagating an ACL rewrite into existing descendants.
This deliberately differs from Linux's final-directory `fchmod` behavior. Existing
ancestors are acquired and checked, without rewriting their permissions.

Use handle-based rename for atomic file replacement and no-replace directory
publication, with identity checks. Delete through held checked handles; recursive
cleanup refuses reparse points/hardlinks and bounds enumeration to 100,000 entries
and 128 descendant levels. Keep uncertain objects on failure. Flush file data
before publication and after file rename. Do not claim a Linux directory-fsync
equivalent, volume-wide durability or power-loss proof, and do not enable a
privilege to obtain one. Unsupported operations fail without a path-based fallback.
Generic atomic writes derive the root from the destination drive, rather than the
process's current drive.

Portable tests check hostile path spellings, UTF-16 byte lengths, fixed-width ABI
layouts and bounded enumeration decoding. A separate native Windows suite exercises
owned temporary files, actual junctions/hardlinks, retained names, private ACLs,
replacement, no-replace publication and identity-protected deletion. It launches no
provider/workload and accesses no arbitrary device. These native tests must execute
on Windows; Linux collection, fixtures or skips do not qualify them.

The native suite is NOT_RUN on the available Linux host. Windows process ownership,
root ACL acquisition, recovery's `/proc`-based inventory and SQLite backup handling,
dependency provisioning, installed/browser workflows and crash/durability behavior
still require implementation or native verification. Provider support remains
separately admitted. Existing Linux evidence and all Windows/milestone gates remain
in their original scopes. Do not add Windows to `verifiedNativeOS` from this code.

Primary API references (consulted for the implementation, not native test evidence):

- [User-mode NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile).
- [Handle-based rename buffer](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info).
- [Directory enumeration](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_both_dir_info).
- [Volume information by handle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew).
- [Protected security descriptor format](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-descriptor-string-format).
- [FlushFileBuffers scope and access requirements](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers).
- [Python CRT handle ownership](https://docs.python.org/3.13/library/msvcrt.html#msvcrt.open_osfhandle) and [CPython 3.13.13 Windows fstat](https://github.com/python/cpython/blob/v3.13.13/Python/fileutils.c).

Component evidence: `evidence/studio/M1-windows-managed-files-20261104/`.
