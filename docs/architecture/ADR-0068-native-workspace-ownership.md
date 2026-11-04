# ADR-0068 — Anchored native workspace ownership

Date: 2026-11-04. Status: implementation; Windows native verification open.
Traces: T002, T039; NFR-003, NFR-009; AC-003, AC-032. No task closure.

ADR-0067 supplies native file handles but the host still acquires `studio.lock`
through a path. Its Windows branch writes a byte before trying the lock. The
Linux branch accepts hardlinks, follows linked ancestors and does not recheck
the named lock after acquisition. An unsupported lock is labelled as contention.
The ordinary launcher also resolves a root alias before checking it and creates
a directory with default permissions before application construction.

Add a managed `lock_directory` context. Acquire the root and original regular
single-link lock through checked directory handles. Create missing lock files
exclusively with private permissions; opening an existing lock never writes its
bytes. Separate native contention from unavailable primitives and unsafe paths.
Expose the held `AnchoredDirectory` to host callers, with native exceptions mapped
at entry and exit while preserving the caller's original exception.

On Linux, require current-user ownership of the root/lock, take `flock` with
exclusive/nonblocking flags, and recheck the acquired file against its directory
entry before returning authority and on normal exit. Tighten the acquired root
to0700 after winning the lock; a refused contender changes neither existing lock
bytes nor root permissions. This advisory lock coordinates cooperating Studio
processes. It does not prevent a process with existing same-user filesystem
authority from renaming Linux directories after acquisition.

On Windows, require the root and lock to have the protected owner-only ACL from
ADR-0067. Only ownership-lock opens allow write sharing, so contenders can open
the same original file and reach the native locking decision. Keep delete sharing
disabled, preserving held root/ancestor and lock names. Use documented `LockFile`
for an immediate exclusive byte-range lock, including beyond the end of an empty
file; no initial byte write is needed. Check file attributes/ACL again after
acquiring the lock. Unlock explicitly, then close the original descriptor. Closing
also releases ownership if the process terminates. No mapped-file or general
process-control guarantee is inferred from this primitive.

The foreground launcher now creates a private root or opens the original existing
directory without resolving aliases, keeps that anchor through application life,
and takes ownership through it. Inspect `.recovery-incomplete` under the same
anchor after ownership, before constructing the application. Existing Windows
roots with unsafe inherited/broader ACLs are refused; no ACL tree rewrite occurs.
Existing Linux roots receive the same private permission policy as application
initialization, enforced before constructing the application.

Recovery passes its already-acquired source/destination anchors directly to
ownership instead of manufacturing `/proc/self/fd` lock paths. Its Linux-specific
inventory/SQLite URI work remains separate and unimplemented on Windows. Provider
and worker process authority are unchanged. A root lock is not a provider permit.

Owned Linux counterexamples/failure/recovery and native ordinary-launcher/browser
checks qualify only their recorded candidate and environment. Windows ownership
cases use actual native files, junctions, hardlinks, ACLs and owned child processes;
they remain NOT_RUN without a permitted Windows host. No fixture, collection or
Linux result promotes Windows support or closes T002/T039/AC-032.

Primary references:

- [LockFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfile).
- [UnlockFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-unlockfile).
- [ADR-0067 acquisition and ACL contracts](ADR-0067-windows-managed-file-handles.md).

Evidence: `evidence/studio/M1-native-root-ownership-20261104/`.
