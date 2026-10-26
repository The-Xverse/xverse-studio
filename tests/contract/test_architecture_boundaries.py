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


CORE = "services/studio-api/src/xverse_studio/{}/module.py"


@pytest.mark.parametrize(
    "source,filename",
    [
        # Domain dispatch hidden in expressions, filters and match cases.
        ('ref = "io.a.automotive" if identifier == "reference-automotive" else "io.a.other"', "fixture.py"),
        ('supported = kind in ("process-control", "other")', "fixture.py"),
        ('match profile:\n    case "automotive":\n        start()', "fixture.py"),
        ('chosen = [x for x in items if x.domain == "ecu"]', "fixture.py"),
        ('while mode != "carla":\n    step()', "fixture.py"),
        # Dependency direction.
        ("from xverse_studio.profiles.presentation import DOMAIN_PROFILES", CORE.format("xdl")),
        ("from xverse_studio.runs.service import Runs", CORE.format("storage")),
        ("from xverse_studio.api.models import Body", CORE.format("catalog")),
        # Relative and dynamic imports resolve to the same packages.
        ("from ..profiles import presentation", CORE.format("xdl")),
        ("from .. import profiles", CORE.format("xdl")),
        ("from ..api import app", CORE.format("runs")),
        ('importlib.import_module("xverse_studio.profiles")', CORE.format("xdl")),
        ("from ..experiments import authoring", CORE.format("storage")),
        # Domain literals used to select behaviour.
        ('handlers["automotive"]()', "fixture.py"),
        ('handler = HANDLERS.get("process-control")', "fixture.py"),
        ('run = getattr(module, "automotive")', "fixture.py"),
        ('special = name.startswith("carla")', "fixture.py"),
        ('HANDLERS = {"automotive": start_vehicle}', CORE.format("runs")),
    ],
)
def test_hidden_domain_dispatch_and_reversed_dependencies_are_detected(source, filename):
    assert module.inspect_source(source, filename)


def test_feature_layers_may_depend_downward_and_data_may_name_domains():
    assert module.inspect_source("from xverse_studio.xdl.examples import DOMAIN_PROFILES", CORE.format("profiles")) == []
    assert module.inspect_source("from xverse_studio.security.models import Body", CORE.format("catalog")) == []
    assert module.inspect_source('DOMAINS = [{"namespace": "io.xverse.studio.domain.automotive"}]', CORE.format("xdl")) == []
    # Declarative domain data belongs to the owned blueprint module, where keyed data is allowed.
    assert module.inspect_source('PRESENTATION = {"automotive": {"Element": "ECU"}}', "services/studio-api/src/xverse_studio/xdl/examples.py") == []
    # Package-internal relative imports and the documented XDL semantic helpers stay allowed.
    assert module.inspect_source("from .edits import semantic_edits", CORE.format("xdl")) == []
    assert module.inspect_source("from xverse_studio.experiments.authoring import edit_scenario", CORE.format("xdl")) == []


@pytest.mark.parametrize("source", [
    "<div dangerouslySetInnerHTML={{ __html: html }} />",
    "element.innerHTML = text;",
    "const run = new Function(body);",
    "eval(code);",
    "node.outerHTML = text;",
    "node.insertAdjacentHTML('beforeend', text);",
    "document.write(text);",
    "<iframe srcdoc={html} />",
    '<a href={"javascript:run()"}>x</a>',
    "const run = Function(body);",
    "setTimeout('run()', 10);",
])

def test_browser_executable_hooks_are_detected(source):
    assert module.inspect_web(source, "apps/studio-web/src/x.tsx")


def test_ordinary_browser_code_is_not_flagged():
    assert module.inspect_web("setTimeout(() => refresh(), 2000); const isFunction = typeof x === 'function';", "x.tsx") == []
