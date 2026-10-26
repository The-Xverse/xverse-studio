"""Round-trip corpus over the admitted examples: each case derives a source set from a baseline and
declares the expected semantic relation, shared by Studio and the pinned CLI."""
from __future__ import annotations

import json

from ruamel.yaml import YAML

from xverse_studio.xdl.examples import dump_yaml, examples

SAFE = YAML(typ="safe")


def baseline(index=0):
    return {"xdl/" + name: content for name, content in examples()[index]["documents"].items()}


def _comments(documents):
    return {path: "# authored comment\n" + text.replace("\nspec:", "\n# inner comment\nspec:", 1) for path, text in documents.items()}


def _reordered(documents):
    out = {}
    for path, text in documents.items():
        resource = SAFE.load(text)
        out[path] = dump_yaml({key: resource[key] for key in reversed(list(resource))})
    return out


def _crlf(documents):
    return {path: text.replace("\n", "\r\n") for path, text in documents.items()}


def _json(documents):
    out = dict(documents)
    out["xdl/system.xdl.json"] = json.dumps(SAFE.load(out.pop("xdl/system.xdl.yaml")), ensure_ascii=False, indent=1)
    return out


def _display_label(documents):
    out = dict(documents)
    resource = SAFE.load(out["xdl/system.xdl.yaml"])
    resource["metadata"]["description"] = "Prüfstand – Ω 制御"
    out["xdl/system.xdl.yaml"] = dump_yaml(resource)
    return out


def _non_ascii_path(documents):
    out = dict(documents)
    out["xdl/Système de contrôle.xdl.yaml"] = out.pop("xdl/system.xdl.yaml")
    return out


def _parameter(documents):
    out = dict(documents)
    resource = SAFE.load(out["xdl/scenario.xdl.yaml"])
    for parameter in next(iter(resource["extensions"].values()))["parameters"]:
        if parameter["id"] == "duration":
            parameter["value"] = 6.0
    out["xdl/scenario.xdl.yaml"] = dump_yaml(resource)
    return out


def _unknown_extension(documents):
    out = dict(documents)
    resource = SAFE.load(out["xdl/system.xdl.yaml"])
    resource["extensions"] = {"org.example.unresolved": {"opaque": [1, 2, 3]}}
    out["xdl/system.xdl.yaml"] = dump_yaml(resource)
    return out


# (name, derive, expectation): "equal" keeps semantic and plan identity, "changed" alters both,
# "invalid" is rejected by both tools with the listed diagnostic code.
CASES = [
    ("comments", _comments, "equal", None),
    ("reordered-keys", _reordered, "equal", None),
    ("crlf-line-endings", _crlf, "equal", None),
    ("yaml-to-json", _json, "equal", None),
    ("display-label-non-ascii", _display_label, "equal", None),
    ("non-ascii-path-with-spaces", _non_ascii_path, "equal", None),
    ("parameter-value", _parameter, "changed", None),
    ("unknown-extension", _unknown_extension, "invalid", "XDL-SEMANTIC-PROFILE-MISSING"),
]
