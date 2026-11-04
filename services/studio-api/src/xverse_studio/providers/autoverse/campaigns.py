"""Only the existing applied native-runtime duration may vary between runs."""

from copy import deepcopy

from ruamel.yaml import YAML
from xverse_studio.storage.core import Problem
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml
from xverse_studio.blueprints.autoverse import NAMESPACE

CONTRACT = {
    "contractVersion": "1.0",
    "parameters": {
        "durationSeconds": {
            "type": "integer",
            "minimum": 30,
            "maximum": 1800,
            "unit": "s",
        }
    },
    "durationParameter": "durationSeconds",
    "maxConcurrency": 1,
    "seedPolicy": "unsupported",
}


def documents(provider, sources, parameters):
    if (
        not isinstance(parameters, dict)
        or set(parameters) != {"durationSeconds"}
        or type(parameters["durationSeconds"]) is not int
        or not 30 <= parameters["durationSeconds"] <= 1800
    ):
        raise Problem(
            "INVALID_PARAMETER",
            "Only an integer durationSeconds between 30 and 1800 is admitted; applied seeds are unavailable.",
        )
    compiled = XDLAdapter().compile(sources)
    if provider.configuration(sources, compiled) is None:
        raise Problem(
            "ADMISSION_REJECTED",
            "Unsupported source semantics cannot acquire campaign authority.",
        )
    changed = deepcopy(sources)
    scenario_name = next(
        name for name in sources if name.rsplit("/", 1)[-1] == "scenario.xdl.yaml"
    )
    scenario = YAML(typ="safe").load(sources[scenario_name])
    scenario["extensions"][NAMESPACE]["durationSeconds"] = parameters["durationSeconds"]
    changed[scenario_name] = dump_yaml(scenario)
    updated = XDLAdapter().compile(changed)
    if provider.configuration(changed, updated) is None:
        raise Problem(
            "ADMISSION_REJECTED",
            "The mapped campaign source is outside the admitted complete-demo contract.",
        )
    return changed
