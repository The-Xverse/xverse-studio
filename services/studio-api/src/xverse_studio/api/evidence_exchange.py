"""Inert, bounded evidence-bundle inspection; this never creates runnable ownership."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import stat
import time
import unicodedata
import zipfile

from fastapi import Request
from pydantic import Field
from xverse_xdl import plan_matches_digest

from xverse_studio.api.models import Body
from xverse_studio.security.files import MAX_BYTES, MAX_EXPANDED, check_text, safe_name
from xverse_studio.storage.core import Problem, atomic, canonical, contained, digest, uid

ALLOWED_FILES = {"manifest.json", "snapshot.json", "run.json", "report.json", "evaluations.json", "annotations.json", "evidence/reference.jsonl"}
REQUIRED_FILES = {"manifest.json", "snapshot.json", "run.json", "report.json"}
INTEGRITIES = {"valid", "verified_prefix", "invalid", "unavailable"}
AVAILABILITIES = {"pending", "collecting", "complete", "partial", "invalid", "unavailable"}


class EvidenceImport(Body):
    archiveBase64: str = Field(max_length=12 * 1024 * 1024)


def _invalid(message="The evidence bundle violates its versioned identity or integrity contract."):
    raise Problem("EVIDENCE_BUNDLE_INVALID", message)


def _json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def finite(value):
        raise ValueError("non-finite JSON constant")
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite JSON number")
        return number
    try:
        value = json.loads(data, object_pairs_hook=unique, parse_constant=finite, parse_float=finite_float)
    except (ValueError, TypeError, RecursionError):
        _invalid("A declared evidence document is not bounded valid JSON.")
    return value


def _read_archive(encoded):
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        _invalid("Supply a base64 ZIP evidence bundle.")
    if len(data) > MAX_BYTES:
        raise Problem("LIMIT_EXCEEDED", "The compressed evidence bundle limit is 8 MiB.", 413)
    result, seen, total = {}, set(), 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as source:
            if len(source.infolist()) > 16:
                raise Problem("LIMIT_EXCEEDED", "The evidence bundle has too many entries.", 413)
            for info in source.infolist():
                name = safe_name(info.filename.rstrip("/") if info.is_dir() else info.filename)
                normalized = unicodedata.normalize("NFC", name).casefold()
                if normalized in seen:
                    raise Problem("UNSAFE_ARCHIVE", "Duplicate or colliding portable entry names are rejected.")
                seen.add(normalized)
                mode = stat.S_IFMT(info.external_attr >> 16)
                if info.flag_bits & 1 or mode not in {0, stat.S_IFREG, stat.S_IFDIR}:
                    raise Problem("UNSAFE_ARCHIVE", "Encrypted entries and non-regular files are rejected.")
                if info.is_dir():
                    if name != "evidence":
                        raise Problem("UNSAFE_ARCHIVE", "Only the declared evidence directory is permitted.")
                    continue
                if name not in ALLOWED_FILES:
                    raise Problem("UNSAFE_ARCHIVE", "Only versioned evidence-bundle document kinds are permitted.")
                total += info.file_size
                limit = MAX_EXPANDED if name == "evidence/reference.jsonl" else 1024 * 1024
                if total > MAX_EXPANDED or info.file_size > limit or info.file_size / max(1, info.compress_size) > 100:
                    raise Problem("LIMIT_EXCEEDED", "Evidence expanded-byte, file-size or compression-ratio limit exceeded.", 413)
                raw = source.read(info)
                if len(raw) != info.file_size:
                    _invalid("An evidence entry's expanded size disagrees with its archive header.")
                text = raw.decode("utf-8")
                # Canonical journals can exceed the per-document cap, but each
                # immutable envelope remains bounded and credential screened.
                if name.endswith(".jsonl"):
                    for line in text.splitlines():
                        check_text(line)
                else:
                    check_text(text)
                result[name] = raw
    except (zipfile.BadZipFile, UnicodeError, RuntimeError, NotImplementedError):
        _invalid("The evidence archive cannot be read safely.")
    if not REQUIRED_FILES <= result.keys():
        _invalid("The evidence bundle is missing a required source document.")
    return result, digest(data)


def _journal(data, run, snapshot):
    if data is None:
        return {"integrity": "unavailable", "recordCount": 0, "coverageComplete": False, "diagnostics": ["EVIDENCE_UNAVAILABLE"]}
    previous, count, coverage = "0" * 64, 0, False
    try:
        for line in data.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                if run.get("state") in {"stopped", "failed"}:
                    raise ValueError()
                break  # incomplete final write is a verified prefix, not a record
            record = _json(line)
            if not isinstance(record, dict):
                raise ValueError()
            recorded_digest = record.pop("digest")
            if record.get("schemaVersion") != "1.0" or record["runId"] != run["runId"] or record["snapshotId"] != snapshot["snapshotId"] or record["previousDigest"] != previous or int(record["sequence"]) != count + 1:
                raise ValueError()
            if not isinstance(recorded_digest, str) or hashlib.sha256(canonical(record).encode()).hexdigest() != recorded_digest:
                raise ValueError()
            previous = recorded_digest
            count += 1
            if count > 100_000:
                raise ValueError()
            if record.get("type") == "evidence.updated":
                coverage = record.get("payload", {}).get("coverage", {}).get("complete") is True
        expected = run.get("journalDigest")
        if expected and digest(data) != expected:
            raise ValueError()
        return {"integrity": "valid" if expected else "verified_prefix", "recordCount": count, "coverageComplete": coverage, "diagnostics": []}
    except (Problem, ValueError, KeyError, TypeError, OverflowError, AttributeError):
        return {"integrity": "invalid", "recordCount": count, "coverageComplete": False, "diagnostics": ["ORIGINAL_JOURNAL_INVALID"]}


def _degraded(declared, computed):
    if "invalid" in {declared, computed}:
        return "invalid"
    if "unavailable" in {declared, computed}:
        return "unavailable"
    if "verified_prefix" in {declared, computed}:
        return "verified_prefix"
    return "valid"


def _inspect(files, adapter):
    manifest, snapshot, run, report = (_json(files[name]) for name in ("manifest.json", "snapshot.json", "run.json", "report.json"))
    if not isinstance(manifest, dict) or manifest.keys() - {"formatVersion", "kind", "files", "integrity", "availability", "providerId"} or manifest.get("formatVersion") != "1.0" or manifest.get("kind") != "studio.evidence":
        _invalid("The evidence manifest version or fields are unsupported.")
    declared = manifest.get("files")
    if not isinstance(declared, dict) or set(declared) != set(files) - {"manifest.json"}:
        _invalid("The manifest must name every source file exactly once.")
    if any(not isinstance(expected, str) or digest(files[name]) != expected for name, expected in declared.items()):
        _invalid("An evidence source file is missing or its manifest digest is invalid.")
    if any(not isinstance(value, dict) for value in (snapshot, run, report)):
        _invalid()
    if report.get("schemaVersion") != "1.0":
        _invalid("The derived report schema version is unsupported.")
    if manifest.get("integrity") not in INTEGRITIES or report.get("integrity") not in INTEGRITIES or manifest.get("availability") not in AVAILABILITIES or report.get("evidenceStatus") not in AVAILABILITIES:
        _invalid("Evidence integrity and availability must use the versioned vocabularies.")
    if not isinstance(run.get("runId"), str) or not run["runId"] or len(run["runId"]) > 100 or not isinstance(snapshot.get("snapshotId"), str) or not snapshot["snapshotId"] or len(snapshot["snapshotId"]) > 100:
        _invalid()
    if snapshot["snapshotId"] != run.get("snapshotId") or snapshot["snapshotId"] != report.get("snapshotId") or run["runId"] != report.get("runId") or manifest.get("providerId") != run.get("providerId"):
        _invalid("Source run, snapshot, report and provider identities disagree.")
    expected_snapshot = snapshot.get("snapshotDigest")
    if expected_snapshot != digest({k: v for k, v in snapshot.items() if k != "snapshotDigest"}):
        _invalid("The frozen snapshot's original digest is invalid.")
    plan = snapshot.get("plan")
    try:
        if not isinstance(plan, dict) or not plan_matches_digest(plan) or "sha256:" + plan["digest"]["value"] != snapshot.get("planDigest") or snapshot.get("planDigest") != report.get("planDigest") or snapshot.get("planDigest") != run.get("planDigest") or "sha256:" + plan["provenance"]["inputSemanticDigest"]["value"] != snapshot.get("semanticDigest"):
            _invalid("The original compiled plan or input semantic identity is invalid.")
    except (KeyError, TypeError, ValueError, RecursionError, AttributeError):
        _invalid("The original compiled plan cannot be verified.")
    if not isinstance(snapshot.get("documents"), dict) or not 0 < len(snapshot["documents"]) <= 128 or any(not isinstance(name, str) or not isinstance(content, str) for name, content in snapshot["documents"].items()):
        _invalid("The frozen authored-input set is unavailable or exceeds its bound.")
    diagnostics = []
    compilation = "unavailable"
    # Reuse the installed public compiler only when its immutable identity agrees.
    # A different compiler/profile leaves inspection available but unresolved.
    compiler = snapshot.get("compiler")
    if isinstance(compiler, dict) and compiler.get("revision") == adapter.identity.get("revision"):
        try:
            compiled = adapter.compile(snapshot["documents"])
            if compiled["valid"]:
                if compiled["planDigest"] != snapshot["planDigest"] or compiled["semanticDigest"] != snapshot["semanticDigest"]:
                    _invalid("The frozen source inputs do not reproduce their declared compiled identity.")
                compilation = "verified"
            else:
                compilation = "unresolved"
                diagnostics.append("INPUT_COMPILATION_UNRESOLVED")
        except XDL_COMPILE_FAILURES:
            compilation = "unresolved"
            diagnostics.append("INPUT_COMPILATION_UNRESOLVED")
    else:
        diagnostics.append("COMPILER_IDENTITY_UNAVAILABLE")
    journal = _journal(files.get("evidence/reference.jsonl"), run, snapshot)
    if run.get("providerId") != "studio.reference":
        journal.update(integrity="unavailable", coverageComplete=False)
        journal["diagnostics"].append("SOURCE_PROVIDER_READER_UNSUPPORTED")
    declared_integrity = _degraded(manifest["integrity"], report["integrity"])
    integrity = _degraded(declared_integrity, journal["integrity"])
    diagnostics.extend(journal["diagnostics"])
    if declared_integrity != journal["integrity"]:
        diagnostics.append("DECLARED_AND_OBSERVED_INTEGRITY_DIFFER")
    if manifest["availability"] != report["evidenceStatus"]:
        diagnostics.append("DECLARED_AVAILABILITY_DISAGREEMENT")
    availability_order = {"complete": 0, "collecting": 1, "pending": 2, "partial": 3, "unavailable": 4, "invalid": 5}
    availability = max((report["evidenceStatus"], manifest["availability"]), key=availability_order.__getitem__)
    if availability == "complete" and (journal["integrity"] != "valid" or not journal["coverageComplete"]):
        availability = "unavailable" if journal["integrity"] == "unavailable" else "partial"
        diagnostics.append("COMPLETE_COVERAGE_UNPROVEN")
    if run.get("effectivePlanDigest") != snapshot["planDigest"] or run.get("effectiveSemanticDigest") != snapshot["semanticDigest"]:
        integrity = "invalid"
        diagnostics.append("EFFECTIVE_INPUT_IDENTITY_UNPROVEN")
    derived = {}
    for filename in ("evaluations.json", "annotations.json"):
        rows = _json(files[filename]) if filename in files else []
        if not isinstance(rows, list) or len(rows) > 256 or any(not isinstance(row, dict) or row.get("runId") != run["runId"] for row in rows):
            _invalid("Derived records must be bounded and refer to this source run.")
        if any(row.get("snapshotId", snapshot["snapshotId"]) != snapshot["snapshotId"] for row in rows):
            _invalid("A derived record references another frozen snapshot.")
        derived[filename.removesuffix(".json")] = rows
    inspection = {"sourceRunId": run["runId"], "sourceSnapshotId": snapshot["snapshotId"], "sourceProviderId": run["providerId"], "evidenceScope": "imported_recorded_evidence", "declaredEvidenceScope": report.get("evidenceScope", "unknown"), "providerAdmission": "not_conferred_by_import", "integrity": integrity, "declaredIntegrity": declared_integrity, "journalIntegrity": journal["integrity"], "availability": availability, "declaredAvailability": report["evidenceStatus"], "manifestAvailability": manifest["availability"], "recordCount": journal["recordCount"], "coverageComplete": journal["coverageComplete"], "snapshotIntegrity": "valid", "planIntegrity": "valid", "inputCompilation": compilation, "diagnostics": list(dict.fromkeys(diagnostics)), "executionAllowed": False, "limitations": ["Imported evidence is inert recorded data; it conveys no process, provider, device or execution authority.", "Internal digest consistency is not producer authentication or an external simulator/hardware admission claim.", "Original reports and derived verdicts are preserved; current import integrity is displayed separately."]}
    return {"manifest": manifest, "inspection": inspection, "report": report, **derived}


# Only typed authoritative compiler failures become unresolved inspection. A
# bundle identity failure remains an explicit rejection, never silently caught.
from xverse_studio.xdl import XDLRejected
XDL_COMPILE_FAILURES = (XDLRejected, ValueError, TypeError, KeyError)


def install_evidence_exchange(app, store, projects, runs):
    @app.post("/api/v1/evidence/imports", status_code=201)
    def evidence_import(body: EvidenceImport, request: Request):
        files, archive_digest = _read_archive(body.archiveBase64)
        inspected = _inspect(files, projects.adapter)
        with store.tx() as db:
            if len(store.all("importedEvidence", db)) >= 128:
                raise Problem("LIMIT_EXCEEDED", "This workspace has reached its retained evidence-import limit of 128.", 413)
            bundle_id = uid("bundle-")
            root = contained(store.root, store.root / "evidence-imports" / bundle_id)
            for name, raw in files.items():
                atomic(contained(root, root / name), raw)
            record = {"bundleId": bundle_id, "archiveDigest": archive_digest, "createdAt": time.time(), "importedBy": request.state.principal, **inspected}
            store.put("importedEvidence", bundle_id, record, db)
        return {k: v for k, v in record.items() if k != "importedBy"}

    @app.get("/api/v1/evidence/imports")
    def evidence_imports(cursor: str | None = None, limit: int = 100):
        try:
            offset = int(cursor or "0")
        except ValueError:
            raise Problem("CURSOR_INVALID", "Supply a valid evidence page cursor.") from None
        if offset < 0 or not 1 <= limit <= 200:
            raise Problem("LIMIT_EXCEEDED", "Choose an evidence page of one to 200 records.")
        rows = store.all("importedEvidence")
        return {"items": [{k: v for k, v in row.items() if k in {"bundleId", "createdAt", "archiveDigest", "inspection"}} for row in rows[offset:offset + limit]], "nextCursor": str(offset + limit) if offset + limit < len(rows) else None}

    @app.get("/api/v1/evidence/imports/{bundleId}")
    def evidence_import_detail(bundleId: str):
        record = store.get("importedEvidence", bundleId)
        root = contained(store.root, store.root / "evidence-imports" / bundleId)
        files = {}
        try:
            for name in {"manifest.json", *record["manifest"]["files"]}:
                path = contained(root, root / name)
                if path.is_symlink() or not path.is_file():
                    raise OSError()
                maximum = MAX_EXPANDED if name.endswith(".jsonl") else 1024 * 1024
                if path.stat().st_size > maximum:
                    raise OSError()
                files[name] = path.read_bytes()
            current = _inspect(files, projects.adapter)
            return {**{k: v for k, v in record.items() if k != "importedBy"}, **current}
        except (OSError, Problem):
            # Preserve original import report/history; report current availability
            # or integrity loss as a separate projection, never repair bytes.
            inspection = {**record["inspection"], "integrity": "invalid", "availability": "partial", "executionAllowed": False, "diagnostics": [*record["inspection"]["diagnostics"], "IMPORTED_FILES_CHANGED_OR_UNAVAILABLE"]}
            return {**{k: v for k, v in record.items() if k != "importedBy"}, "inspection": inspection}
