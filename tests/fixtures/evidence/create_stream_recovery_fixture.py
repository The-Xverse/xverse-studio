"""NEW inert unknown-state browser stream fixture, never a runtime admission."""

import argparse
import importlib.util
import json
from pathlib import Path

from xverse_studio.storage.core import Store
from xverse_studio.projects.service import Projects
from xverse_studio.runs.service import Runs
from xverse_studio.xdl import XDLAdapter


def create_stream_recovery_fixture(store, projects, runs, project_id, *, noise=1200):
    if type(noise) is not int or not 1000 <= noise <= 2000:
        raise ValueError("Fixture noise must be within 1000–2000 records")
    path = Path(__file__).with_name("create_recorded_evidence.py")
    spec = importlib.util.spec_from_file_location("new_stream_recorded_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    created = fixture.create_recorded_evidence(
        store, projects, runs, project_id, noise=noise
    )
    with store.tx() as db:
        run = store.get("run", created["runId"], db)
        # Set the new fixture's initial exposed state. No actual lifecycle took place.
        run["state"] = "unknown"
        run.pop("endedAt", None)
        run["limitations"].append(
            "Unknown nonterminal transport state is synthetic; no process or physical state is represented."
        )
        store.put("run", created["runId"], run, db)
    return {
        **created,
        "state": "unknown",
        "streamVersion": "1.1",
        "runtimeAuthority": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--noise", type=int, default=1200)
    args = parser.parse_args()
    root = args.data_dir.resolve()
    allowed = Path(__file__).resolve().parents[3] / ".studio-local/browser-tests"
    if (
        not root.is_relative_to(allowed.resolve())
        or not (root / "studio.sqlite").is_file()
    ):
        parser.error(
            "Only existing isolated .studio-local/browser-tests roots are allowed."
        )
    store = Store(root)
    adapter = XDLAdapter()
    projects = Projects(store, adapter)
    runs = Runs(store, projects, adapter)
    print(
        json.dumps(
            create_stream_recovery_fixture(
                store, projects, runs, args.project_id, noise=args.noise
            )
        )
    )


if __name__ == "__main__":
    main()
