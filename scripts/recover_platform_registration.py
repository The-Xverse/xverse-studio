"""Explicit host maintenance of an existing released simulation registration.

Default is read-only inspection. No HTTP endpoint, imported command, process
signal, container action or ownership-handle reconstruction is involved.
"""
import argparse
import json
from pathlib import Path
import time
import uuid

from xverse.maestro.execution import HostRecoveryPermit, PublicExecutionService, RecoveryProviderBinding
from xverse_studio.host.ownership import own_root
from xverse_studio.providers.autoverse.platform_adapter import PlatformProvider
from xverse_studio.providers.autoverse.platform_installation import enroll_platform
from xverse_studio.providers.autoverse.platform_owner import RuntimeRouter
from xverse_studio.providers.autoverse.preparation import inspection_host


def recover(installation, run_ids, *, approval_reference=None):
    """Trusted host arguments only; no browser/project grant is accepted."""
    if (not 1 <= len(run_ids) <= 128 or len(set(run_ids)) != len(run_ids)
            or (approval_reference is not None and not 1 <= len(approval_reference) <= 512)):
        raise ValueError("AUTOVERSE_RECOVERY_ARGUMENTS_INVALID")
    adapter = PlatformProvider(installation)
    router = RuntimeRouter(installation, adapter)
    service = PublicExecutionService(
        Path(installation["nativeBridge"]["runtimeRoot"]),
        inspection_host(router, installation["nativeBridge"]["hostId"]), (router,),
        max_runtime_seconds=2700, cleanup_budget_seconds=60,
        recovery_bindings=(RecoveryProviderBinding(router.provider_id, installation["identityDigest"]),),
    )
    try:
        inspections = [service.inspect_recovery(rid) for rid in run_ids]
        if approval_reference is not None:
            if any(not item.to_data()["eligible"] for item in inspections):
                raise ValueError("AUTOVERSE_RECOVERY_INELIGIBLE")
            for item in inspections:
                data = item.to_data()
                now = time.time()
                permit = HostRecoveryPermit(
                    "recovery-" + uuid.uuid4().hex, item.inspection_digest,
                    data["hostBindingDigest"], data["runtimeBindingDigest"],
                    data["recoveryBindingDigest"], installation["nativeBridge"]["hostId"],
                    approval_reference, now - 1, now + 60,
                )
                service.retire_released(item, permit)
        return {"inspections": [item.to_data() for item in inspections],
                "retirements": [service.recovery_status(rid) for rid in run_ids]}
    finally:
        service.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--autoverse-root", type=Path, required=True)
    parser.add_argument("--autoverse-native-bridge", type=Path, required=True)
    parser.add_argument("--run-id", action="append", required=True)
    parser.add_argument("--retire", action="store_true", help="Issue a finite host grant for the exact inspected sources.")
    parser.add_argument("--approval-reference", help="Required host authorization reference when --retire is used.")
    args = parser.parse_args()
    if bool(args.approval_reference) != args.retire:
        parser.error("--retire and --approval-reference must be supplied together.")
    root = args.data_dir.resolve(strict=True)
    runtime = root / "platform-runtime" / "autoverse"
    if not runtime.is_dir():
        parser.error("Select the existing registration; no new runtime root is created for recovery.")
    # The same lock as the native launcher, then the SDK's actual root lock.
    with own_root(root):
        installation = enroll_platform(args.autoverse_root, args.autoverse_native_bridge, runtime)
        result = recover(installation, args.run_id, approval_reference=args.approval_reference)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
