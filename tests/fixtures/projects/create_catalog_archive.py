"""Trusted neutral project archives for catalog/wizard verification; never executed."""

import argparse
import base64
import io
import json
import zipfile

from ruamel.yaml import YAML

from xverse_studio.xdl import XDLAdapter, examples


def _dump(value):
    out = io.StringIO()
    YAML().dump(value, out)
    return out.getvalue()


def documents(variant):
    yaml = YAML(typ="safe")
    docs = dict(examples()[0]["documents"])
    if variant == "unknown-extension":
        # An unresolved extension namespace: preserved and inspectable, never executable.
        system = yaml.load(docs["system.xdl.yaml"])
        system["extensions"] = {"org.example.unresolved": {"script": "rm -rf /", "opaque": [1, 2, 3]}}
        docs["system.xdl.yaml"] = _dump(system)
        assert not XDLAdapter().validate(docs)["valid"]
        return docs
    plant = yaml.load(docs["plant.xdl.yaml"])
    service = json.loads(json.dumps(plant))
    service["metadata"]["name"] = "telemetry-service"
    service["metadata"]["description"] = "Neutral fixture service definition."
    # Its own fixture provenance: not the owned executable reference.
    service["metadata"]["provenance"] = {
        "source": "urn:xverse:studio:test-fixture:telemetry-service",
        "revision": "1.0.0",
        "maturity": "architectural-target",
        "limitations": ["Test fixture definition only; no implementation or provider exists."],
    }
    service["spec"]["capabilities"] = ["telemetry-forwarding"]
    service["spec"]["endpoints"][0]["ownerId"] = "telemetry-service"
    service["spec"].pop("models", None)
    if variant == "unsupported":
        # A definition declared in a future, non-admitted XDL API version.
        service["apiVersion"] = "xverse.io/xdl/v9"
    docs["service.xdl.yaml"] = _dump(service)
    system = yaml.load(docs["system.xdl.yaml"])
    system["spec"]["nodes"].append({"id": "service-node", "roles": ["service"]})
    docs["system.xdl.yaml"] = _dump(system)
    valid = XDLAdapter().validate(docs)["valid"]
    assert valid == (variant == "service"), (variant, valid)
    return docs


def archive(variant):
    docs = documents(variant)
    manifest = {
        "formatVersion": "1.0",
        "name": f"Catalog fixture ({variant})",
        "resources": [{"path": "xdl/" + name, "format": "yaml"} for name in sorted(docs)],
        "profiles": [],
        "layoutFiles": [],
    }
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("project.studio.json", json.dumps(manifest))
        for name, content in sorted(docs.items()):
            z.writestr("xdl/" + name, content)
    return base64.b64encode(data.getvalue()).decode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["service", "unsupported", "unknown-extension"], required=True)
    print(archive(parser.parse_args().variant))
