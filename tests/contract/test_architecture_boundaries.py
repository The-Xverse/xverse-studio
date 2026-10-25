import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[2] / "scripts/check_architecture.py"
spec = importlib.util.spec_from_file_location("studio_architecture_check", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize(
    "source",
    [
        "from xverse_blueprints.automotive import run",
        "import provider.carla",
        "from runtime import _OriginalRuntimeRun",
        'if profile == "automotive":\n    start()',
        "eval(expression)",
        "builtins.exec(expression)",
        "subprocess.run(argv,shell=True)",
    ],
)
def test_forbidden_core_boundaries_detected(source):
    assert module.inspect_source(source, "fixture.py")


def test_declarative_domain_metadata_and_neutral_control_allowed():
    assert (
        module.inspect_source(
            'catalog=[{"profile":"automotive"}]\nif capability == "pause":\n    command()',
            "fixture.py",
        )
        == []
    )
    assert module.main() == 0
