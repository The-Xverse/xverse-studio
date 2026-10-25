"""Profile fixtures with declared expected semantics; trusted test inputs, never executed."""

import io
import json

from ruamel.yaml import YAML

from xverse_studio.xdl import examples


def _dump(value):
    out = io.StringIO()
    YAML().dump(value, out)
    return out.getvalue()


def _with_profile(namespace, name="redefiner"):
    docs = dict(examples()[0]["documents"])
    profile = YAML(typ="safe").load(docs["profile.xdl.yaml"])
    profile["metadata"]["name"] = name
    profile["spec"]["extensionNamespace"] = namespace
    docs[f"{name}.xdl.yaml"] = _dump(profile)
    return docs


def redefined_admitted_profile(**changes):
    """The authored resource for an admitted namespace, with its semantics changed."""
    docs = dict(examples()[0]["documents"])
    profile = YAML(typ="safe").load(docs["profile.xdl.yaml"])
    for key, value in changes.items():
        if key == "version":
            profile["metadata"]["version"] = value
        else:
            profile["spec"][key] = value
    docs["profile.xdl.yaml"] = _dump(profile)
    return docs


def core_namespace_profile():
    """A project Profile claiming a core-looking namespace: XDL-valid but never admitted."""
    return _with_profile("xverse.io")


def duplicate_owner_profile():
    """A second owner of an admitted extension namespace: rejected by the validator."""
    return _with_profile("io.xverse.experiment", "second-owner")


# Presentation sidecar payloads that must never be accepted in place of admitted inert metadata.
MALICIOUS_PRESENTATIONS = {
    "script-label": {"name": "x", "labels": {"node": "<script>alert(1)</script>"}},
    "event-hook": {"name": "x", "onLoad": "fetch('https://example.invalid')"},
    "provider-dispatch": {"name": "x", "providerId": "studio.reference", "execute": True},
    "core-relabel": {"name": "x", "labels": {"componentInstances": "devices"}, "redefines": ["spec.flows"]},
}


def presentation_bytes(name):
    return json.dumps(MALICIOUS_PRESENTATIONS[name])
