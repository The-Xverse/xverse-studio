"""Read-only independent malformed-dependency probes; emits JSON, changes no records/files."""
import hashlib
import json
from pathlib import Path

from xverse_studio.retention import plan_retention

artifact = {"entryId": "a", "digest": "sha256:example", "originRef": "urn:example:asset"}
cases = {
    "malformed_snapshot_project_link": ({"projects": [{"projectId": "p"}], "snapshots": [{"snapshotId": "s", "projectId": ["p"]}]}, {"project_ids": ["p"]}),
    "malformed_campaign_base_snapshot": ({"projects": [{"projectId": "p"}], "campaigns": [{"campaignId": "c", "baseSnapshot": []}]}, {"project_ids": ["p"]}),
}
for name, content in (("null", "null\n"), ("scalar", "opaque scalar source\n"), ("list", "- unknown\n")):
    cases["invalid_xdl_" + name] = ({"projects": [{"projectId": "p", "documents": {"d.xdl.yaml": content}}], "artifacts": [artifact]}, {"artifact_ids": ["a"]})
cases["unsupported_supporting_file"] = ({"projects": [{"projectId": "p", "supportingFiles": {"opaque.bin": "opaque"}}], "artifacts": [artifact]}, {"artifact_ids": ["a"]})
source = Path("services/studio-api/src/xverse_studio/retention/__init__.py")
report = {"sourceDigest": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(), "cases": {}}
for name, (state, selection) in cases.items():
    try:
        plan = plan_retention([], state, **selection)
        report["cases"][name] = {"result": "PLANNED", "removals": plan["removals"], "protected": plan["protected"]}
    except Exception as exc:
        report["cases"][name] = {"result": "exception", "type": type(exc).__name__, "detail": str(exc)}
print(json.dumps(report, indent=2))
