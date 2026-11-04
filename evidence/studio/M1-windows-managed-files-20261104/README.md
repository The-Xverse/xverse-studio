# Windows managed-file implementation candidate

Source `a43147a9a57fad7300de9310c718d757212dc87a` adds a Windows backend for
the existing managed-file interface. It opens single path components through held
native directory handles, rejects reparse points and file hardlinks, creates new
objects with protected owner-only ACLs, and implements handle-based replacement,
no-replace publication and bounded deletion. Generic atomic writes select the
destination's drive root. Linux keeps its original acquisition implementation.
See [ADR-0067](../../../docs/architecture/ADR-0067-windows-managed-file-handles.md).

**Windows native execution is NOT_RUN.** Eleven native cases collect successfully
on Linux; collection is not execution, a pass or acceptance. They cover owned NTFS
files, actual junctions, a parent reparse mutation at acquisition, hardlinks,
concurrent write/rename refusal, private ACLs, publication, identity-protected
cleanup and multi-page enumeration. No Windows support claim follows from them.

On Linux, 63 selected checks pass: portable hostile-path/UTF-16/ABI/enumeration
checks and the existing acquisition/recovery suite. Another 11 checks pass using
the original completed Autoverse recording and explicitly labelled decoded-copy
inputs. They verify immutable source handling and comparison admission; they do
not start or install a provider, replay a workload, or supply Windows evidence.
The [recording identity](recorded-source.json) matches the retained original
93-record journal. The fixture asserts original DB/snapshot/journal hashes before
and after its checks; that statement does not qualify every environment asset.

All 548 selected code/tool/config inputs match committed Git and remain unchanged
through the final recorded phases. [Verification](verification.json) retains exact
commands, host/runtime versions, exit statuses, case counts and scopes; raw XML
and unsanitized output remain private. Public logs replace machine-specific paths.
Architecture, planning-package, descriptive-baseline and new-file lint checks pass.
The two changed legacy files receive the explicitly recorded F821/F401 check;
no whole-file style claim is made. The earlier preliminary 63-pass run precedes
the bound final cohort and is not a separate source-wide acceptance result.

Same-agent source review checked relative-name validation, fixed-width ABI fields,
handle ownership/closure, caller exception preservation, ACL acquisition and
publication/deletion boundaries. Findings incorporated before the recorded cohort:
retain all ancestors rather than only the final parent; recheck the parent before
each native acquisition; reject a successful native status without a valid handle;
and verify an existing final directory's private ACL without propagating a rewrite
through descendants. This review cannot prove native API or filesystem behavior.
There is no independent milestone review or native Windows acceptance result.

Outstanding Windows work includes actual execution of the native file suite,
process/root ownership and ACL handling, recovery's Linux-specific inventory and
SQLite handling, dependency provisioning, installation, startup/shutdown, browser
workflows, persistence/restart and crash behavior. File flushing does not establish
volume-wide or power-loss durability. Fixed local NTFS support is an implementation
restriction pending verification; other filesystems fail explicitly. No Bash,
WSL, container or privileged-volume fallback is introduced.

No new browser/build/performance/package/full-regression result is claimed. No
runtime, simulator, physical device, desktop/driver or companion-repository change
is performed. The existing Autoverse recording is reused without new execution.
Broader native/provider/human/hardware and M0–M4 acceptance gates remain open.

**71 completed / 19 in progress / 10 blocked; zero accepted milestones.**
T002/T039 remain in progress; task statuses, descriptions, dependencies and
acceptance mappings are unchanged. This is implementation progress, not closure.
