"""Bounded original-owner container release and readback; never replay a Stop."""

import subprocess
import time

from .installation import InstallationError, container_fact, inspect


def cleanup_container(installation, role, claim, *, deadline=None):
    codes = []
    # Preserve the previous sum of command/inspection caps per resource.
    end = time.monotonic() + (70 if role == "android" else 50)
    if deadline is not None:
        end = min(end, deadline)

    def code(value):
        if value not in codes and len(codes) < 4:
            codes.append(value)

    def budget(maximum):
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise InstallationError("AUTOVERSE_CLEANUP_DEADLINE")
        return min(maximum, remaining)

    def owned():
        row = inspect(
            installation["docker"], claim["identity"]["id"], timeout=budget(15)
        )
        if (
            container_fact(row) != claim["identity"]
            or not claim.get("startedAt")
            or row["State"]["StartedAt"] != claim["startedAt"]
            or type(row["State"]["Running"]) is not bool
        ):
            raise InstallationError("AUTOVERSE_CONTAINER_OWNERSHIP_UNKNOWN")
        return row

    status = "unknown"
    try:
        row = owned()
        if row["State"]["Running"]:
            if role == "android":
                try:
                    result = subprocess.run(
                        [
                            installation["docker"],
                            "exec",
                            "--env",
                            "ANDROID_HOST_OUT=/root/runtime",
                            "--env",
                            "CUTTLEFISH_CONFIG_FILE=/root/runtime/cvd-assembly/cuttlefish_config.json",
                            "--workdir",
                            "/root/runtime",
                            claim["identity"]["id"],
                            "./bin/stop_cvd",
                        ],
                        capture_output=True,
                        timeout=budget(20),
                        check=False,
                    )
                    if result.returncode:
                        code("AUTOVERSE_ANDROID_STOP_FAILED")
                except subprocess.TimeoutExpired:
                    code("AUTOVERSE_ANDROID_STOP_TIMEOUT")
                except (OSError, subprocess.SubprocessError):
                    code("AUTOVERSE_ANDROID_STOP_UNAVAILABLE")
                # The optional command can outlive its acknowledgement or the
                # original container start. Verify again before container Stop.
                row = owned()
            if row["State"]["Running"]:
                try:
                    subprocess.run(
                        [
                            installation["docker"],
                            "stop",
                            "--time",
                            "10",
                            claim["identity"]["id"],
                        ],
                        capture_output=True,
                        timeout=budget(20),
                        check=True,
                    )
                except subprocess.TimeoutExpired:
                    code("AUTOVERSE_CONTAINER_STOP_TIMEOUT")
                except subprocess.CalledProcessError:
                    code("AUTOVERSE_CONTAINER_STOP_FAILED")
                except (OSError, subprocess.SubprocessError):
                    code("AUTOVERSE_CONTAINER_STOP_UNAVAILABLE")
        # A missing command acknowledgement is not proof of release or failure.
        # Inspect the original identity once; never repeat the mutation here.
        row = owned()
        if row["State"]["Running"]:
            raise InstallationError("AUTOVERSE_CONTAINER_STOP_UNCONFIRMED")
        status = "released"
    except InstallationError as error:
        value = str(error)
        code(
            value
            if value
            in {
                "AUTOVERSE_CLEANUP_DEADLINE",
                "AUTOVERSE_CONTAINER_OWNERSHIP_UNKNOWN",
                "AUTOVERSE_CONTAINER_STOP_UNCONFIRMED",
            }
            else "AUTOVERSE_CONTAINER_INSPECTION_UNAVAILABLE"
        )
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError):
        code("AUTOVERSE_CONTAINER_INSPECTION_UNAVAILABLE")
    result = {"resourceId": role, "kind": "container", "status": status}
    if codes:
        result["diagnostics"] = codes
    return result
