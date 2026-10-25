"""Revisioned annotations are derived metadata, never canonical evidence edits."""
from copy import deepcopy
import time
from urllib.parse import urlsplit
import uuid


class AnnotationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _content(body):
    if not isinstance(body, dict) or body.keys() - {"kind", "text", "target", "elementRefs", "evidenceRefs"}:
        raise AnnotationError("ANNOTATION_INVALID")
    kind = body.get("kind", "comment")
    text = body.get("text", "")
    if kind not in {"comment", "trace_link"} or not isinstance(text, str) or len(text) > 4096:
        raise AnnotationError("ANNOTATION_INVALID")
    target = body.get("target")
    if kind == "comment":
        if not text.strip() or target is not None:
            raise AnnotationError("ANNOTATION_INVALID")
    else:
        if not isinstance(target, dict) or target.keys() != {"uri", "revision"} or not isinstance(target["uri"], str) or len(target["uri"]) > 2048 or not isinstance(target["revision"], str) or not 0 < len(target["revision"]) <= 256:
            raise AnnotationError("TRACE_TARGET_INVALID")
        if any(ord(c) < 32 for c in target["uri"]):
            raise AnnotationError("TRACE_TARGET_INVALID")
        try:
            parsed = urlsplit(target["uri"])
        except ValueError:
            raise AnnotationError("TRACE_TARGET_INVALID") from None
        if parsed.scheme not in {"https", "http", "urn"} or parsed.username or parsed.password or parsed.query:
            raise AnnotationError("TRACE_TARGET_INVALID")
    for key in ("elementRefs", "evidenceRefs"):
        values = body.get(key, [])
        if not isinstance(values, list) or len(values) > 32 or any(not isinstance(v, str) or not 0 < len(v) <= 512 for v in values):
            raise AnnotationError("ANNOTATION_INVALID")
    return {"kind": kind, "text": text, "target": deepcopy(target), "elementRefs": deepcopy(body.get("elementRefs", [])), "evidenceRefs": deepcopy(body.get("evidenceRefs", []))}


def create_annotation(run_id, body, *, author):
    return {"annotationId": "ann-" + str(uuid.uuid4()), "runId": run_id, "revision": 1, "author": author, "createdAt": time.time(), "updatedAt": time.time(), "deleted": False, "history": [], **_content(body)}


def revise_annotation(record, body, *, expected_revision, author, delete=False):
    if expected_revision is None:
        raise AnnotationError("REVISION_REQUIRED")
    if expected_revision != record["revision"]:
        raise AnnotationError("REVISION_CONFLICT")
    if record.get("deleted"):
        raise AnnotationError("ANNOTATION_DELETED")
    if len(record.get("history", [])) >= 100:
        raise AnnotationError("ANNOTATION_HISTORY_LIMIT")
    old = {k: deepcopy(v) for k, v in record.items() if k != "history"}
    out = deepcopy(record)
    out["history"].append(old)
    if not delete:
        out.update(_content(body))
    out.update(revision=record["revision"] + 1, author=author, updatedAt=time.time(), deleted=delete)
    return out
