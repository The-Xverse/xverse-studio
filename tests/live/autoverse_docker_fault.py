"""Pinned native test transport: lose one acknowledgement after real Docker success.

The closed native fixture copies this source into its private enrolled tool path.
All ordinary commands exec the original pinned Docker executable unchanged. Faults
apply only to the exact Android container claimed by that fixture's actual worker.
No container, lifecycle state, observation or cleanup result is fabricated.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    config_path = Path(sys.argv[0]).parent / "fault.private.json"
    assert config_path.stat().st_size <= 4096
    config = json.loads(config_path.read_bytes())
    docker = config["docker"]
    assert Path(docker).is_absolute()
    argv = sys.argv[1:]
    directory = Path.cwd()
    owned = directory.parent == Path(config["dataRoot"]) / "runs"
    observation = directory / "cleanup-fault.observation.json"
    kind = config["mode"]
    matches = (
        kind == "stop-timeout"
        and argv[:1] == ["stop"]
        or kind == "android-timeout"
        and argv[:1] == ["exec"]
        and argv[-1:] == ["./bin/stop_cvd"]
    )
    cid = config["androidId"]
    if owned and matches and cid in argv and not observation.exists():
        claims = directory / "containers.private.json"
        assert claims.stat().st_size <= 64 * 1024
        claim = json.loads(claims.read_bytes())["android"]
        assert claim["identity"]["id"] == cid and claim["startedAt"]
        result = subprocess.run([docker, *argv], check=False)
        if result.returncode == 0:
            with observation.open("x") as output:
                os.fchmod(output.fileno(), 0o600)
                json.dump(
                    {
                        "mode": kind,
                        "actualDockerExit": 0,
                        "effect": "original command executed once; acknowledgement withheld",
                        "workerOwnsExactClaim": True,
                    },
                    output,
                )
                output.flush()
                os.fsync(output.fileno())
            # The provider's existing20s bound kills this original CLI handle.
            # There is no replay, fake result or longer product cleanup budget.
            time.sleep(30)
        return result.returncode
    os.execv(docker, [docker, *argv])


if __name__ == "__main__":
    raise SystemExit(main())
