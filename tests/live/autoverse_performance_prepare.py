"""Prepare explicit inert Autoverse load inputs in a new contributor workspace."""

import argparse
import importlib.util
import json
from pathlib import Path
import uuid

from xverse_studio.host.ownership import own_root
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store
from xverse_studio.xdl import XDLAdapter


_spec = importlib.util.spec_from_file_location(
    "autoverse_performance_inputs", Path(__file__).with_name("autoverse_performance.py")
)
benchmark = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(benchmark)


def main():
    p = argparse.ArgumentParser()
    for name in ("recording", "project-archive", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    result = json.loads((args.recording / "native-result.json").read_bytes())
    assert result["outcome"] == "passed" and result["fullAndroidAndSpeedObserved"]
    original = Path(
        json.loads((args.recording / "data-root.private.json").read_bytes())["dataRoot"]
    )
    source_hashes = benchmark.protected_files(original)
    import hashlib

    database = hashlib.sha256((original / "studio.sqlite").read_bytes()).hexdigest()
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    data = (
        benchmark.native.ROOT
        / ".studio-local/browser-tests"
        / ("autoverse-performance-prepared-" + uuid.uuid4().hex)
    )
    benchmark.exchange.clone(original, data)
    (args.output / "data-root.private.json").write_text(
        json.dumps({"dataRoot": str(data), "original": str(original)}, indent=2) + "\n"
    )
    with own_root(data):
        store = Store(data)
        projects = Projects(store, XDLAdapter())
        _, model = benchmark.model_fixture(projects, args.project_archive.read_bytes())
        history = benchmark.history_fixture(store, projects, result["runId"])
    assert benchmark.protected_files(original) == source_hashes
    assert (
        hashlib.sha256((original / "studio.sqlite").read_bytes()).hexdigest()
        == database
    )
    (args.output / "fixtures.json").write_text(
        json.dumps({"model": model, "history": history}, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "model": model,
                "history": history,
                "originalUnchanged": True,
                "generatedFixtureRunRecords": 1,
                "generatedFixtureOperationRecords": 1,
                "preflightOrProviderExecution": False,
            }
        )
    )


if __name__ == "__main__":
    main()
