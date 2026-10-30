"""Private host declarations, independent of executable XDL and provider authority."""

from __future__ import annotations

import json
import platform
from pathlib import PurePosixPath
import re
from typing import Annotated, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from xverse_studio.security.files import check_portable_text, check_text, safe_name
from xverse_studio.security.managed_io import open_read, open_write, SafeIOError
from xverse_studio.security.models import Body
from xverse_studio.storage.core import Problem, canonical, digest, uid

MAX_BINDINGS = 32
MAX_BYTES = 64 * 1024
SHA256 = r"^sha256:[a-f0-9]{64}$"


def _text(value, portable=True):
    try:
        value.encode("utf-8")
        if value != value.strip() or any(ord(c) < 32 for c in value):
            raise ValueError()
        if portable and (value.startswith(("/", "\\")) or "\\" in value
                         or re.match(r"^[A-Za-z]:", value) or value.lower().startswith("file:")):
            raise ValueError()
        (check_portable_text if portable else check_text)(value)
    except (ValueError, Problem):
        raise ValueError("Use bounded credential-free UTF-8 text and external handles.") from None
    return value


class Binding(Body):
    bindingId: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    reference: str = Field(min_length=1, max_length=512)
    providerId: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

    @field_validator("reference")
    @classmethod
    def portable_reference(cls, value):
        return _text(value)


class ArtifactBinding(Binding):
    kind: Literal["artifact"]
    path: str = Field(min_length=1, max_length=4096)

    @field_validator("path")
    @classmethod
    def native_path(cls, value):
        _text(value, portable=False)
        if (not PurePosixPath(value).is_absolute() or value.startswith("//")
                or "\\" in value or any(p in (".", "..") for p in value.split("/"))):
            raise ValueError("Select an absolute Linux path without parent components; it will not be inspected.")
        return value


class AssetBinding(Binding):
    kind: Literal["asset"]
    assetId: str = Field(min_length=1, max_length=256)

    @field_validator("assetId")
    @classmethod
    def opaque_asset(cls, value):
        return _text(value)


class CredentialBinding(Binding):
    kind: Literal["credential"]
    credentialRef: str = Field(pattern=r"^(?:secret://[A-Za-z0-9][A-Za-z0-9._/-]{0,239}|urn:[A-Za-z0-9][A-Za-z0-9:._/-]{0,239})$")

    @field_validator("credentialRef")
    @classmethod
    def external_handle(cls, value):
        return _text(value)


LocalBinding = Annotated[ArtifactBinding | AssetBinding | CredentialBinding, Field(discriminator="kind")]


class LocalBindingsUpdate(Body):
    formatVersion: Literal["1.0"] = "1.0"
    bindings: list[LocalBinding] = Field(max_length=MAX_BINDINGS)

    @model_validator(mode="after")
    def unique_references(self):
        ids = [item.bindingId for item in self.bindings]
        references = [(item.providerId, item.reference) for item in self.bindings]
        if len(set(ids)) != len(ids) or len(set(references)) != len(references):
            raise ValueError("Binding IDs and provider/reference pairs must be unique.")
        return self


class LocalBindingsView(LocalBindingsUpdate):
    projectId: str = Field(min_length=1, max_length=80)
    bindingRevision: int = Field(ge=0)
    state: Literal["empty", "declared", "needs_review"]
    environmentChanged: bool
    validation: Literal["unverified"] = "unverified"
    executionAllowed: Literal[False] = False


class BindingDocument(LocalBindingsUpdate):
    projectId: str = Field(min_length=1, max_length=80)
    bindingRevision: int = Field(ge=1)
    contextDigest: str = Field(pattern=SHA256)


class BindingHead(Body):
    formatVersion: Literal["1.0"]
    projectId: str = Field(min_length=1, max_length=80)
    bindingRevision: int = Field(ge=1)
    sidecar: str = Field(min_length=1, max_length=240)
    digest: str = Field(pattern=SHA256)


class LocalBindings:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def discovery():
        return {"formatVersion": "1.0", "maxBindings": MAX_BINDINGS, "maxBytes": MAX_BYTES,
                "supportedHostOS": ["Linux"], "validation": "unverified", "executionAllowed": False}

    def _context(self):
        # Change detection only. This is neither attestation nor an execution permit.
        return digest({"root": str(self.store.root), "host": platform.node(),
                       "os": platform.system(), "architecture": platform.machine()})

    def _project(self, pid, db):
        self.store.get("project", pid, db)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", pid):
            raise Problem("LOCAL_BINDINGS_UNAVAILABLE", "The project has no safe private binding identity.", 409)

    def _raw(self, sidecar):
        try:
            with open_read(self.store.root, self.store.root / sidecar) as stream:
                raw = stream.read(MAX_BYTES + 1)
        except SafeIOError as error:
            if error.code == "SECURE_IO_UNAVAILABLE":
                raise Problem("PLATFORM_IO_UNAVAILABLE", "Secure native binding-file access is unavailable on this host.", 503) from None
            raise Problem("LOCAL_BINDINGS_UNAVAILABLE", "The private sidecar is missing or unsafe; preserve the root before recovery.", 409) from None
        except (OSError, ValueError):
            raise Problem("LOCAL_BINDINGS_UNAVAILABLE", "The private sidecar is missing or unsafe; preserve the root before recovery.", 409) from None
        if len(raw) > MAX_BYTES:
            raise Problem("LOCAL_BINDINGS_UNAVAILABLE", "The private sidecar exceeds its declared bound; preserve it before recovery.", 409)
        return raw

    def _read(self, pid, db):
        self._project(pid, db)
        try:
            saved = self.store.get("project_local_bindings", pid, db)
        except Problem as error:
            if error.code != "NOT_FOUND":
                raise
            return {"formatVersion": "1.0", "projectId": pid, "bindingRevision": 0, "bindings": [],
                    "state": "empty", "environmentChanged": False, "validation": "unverified", "executionAllowed": False}
        except (ValueError, TypeError, RecursionError):
            raise Problem("LOCAL_BINDINGS_UNAVAILABLE", "The private binding head cannot be decoded; preserve it before recovery.", 409) from None
        try:
            if not isinstance(saved, dict):
                raise ValueError()
            if saved.get("formatVersion") != "1.0":
                raise Problem("LOCAL_BINDINGS_VERSION_UNSUPPORTED", "The private binding head uses an unsupported format; no data was changed.", 409)
            head = BindingHead.model_validate(saved)
            try:
                safe_name(head.sidecar)
            except Problem:
                raise ValueError() from None
            prefix = f"projects/{pid}/local-bindings/{head.bindingRevision}-binding-"
            if head.projectId != pid or not head.sidecar.startswith(prefix) or not re.fullmatch(r"[a-f0-9-]{36}\.json", head.sidecar[len(prefix):]):
                raise ValueError()
            raw = self._raw(head.sidecar)
            if digest(raw) != head.digest:
                raise Problem("LOCAL_BINDINGS_CONFLICT", "The private sidecar differs from its committed digest; no data was changed.", 409)
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError()
            if data.get("formatVersion") != "1.0":
                raise Problem("LOCAL_BINDINGS_VERSION_UNSUPPORTED", "The private sidecar uses an unsupported format; no data was changed.", 409)
            document = BindingDocument.model_validate(data)
            if document.projectId != pid or document.bindingRevision != head.bindingRevision:
                raise ValueError()
        except (ValidationError, ValueError, TypeError, RecursionError):
            raise Problem("LOCAL_BINDINGS_UNAVAILABLE", "The private binding identity or format cannot be verified; preserve it before recovery.", 409) from None
        changed = document.contextDigest != self._context()
        return {**document.model_dump(exclude={"contextDigest"}), "state": "needs_review" if changed else "declared",
                "environmentChanged": changed, "validation": "unverified", "executionAllowed": False}

    def read(self, pid):
        with self.store.tx() as db:
            return self._read(pid, db)

    def save(self, pid, expected, update):
        if expected is None:
            raise Problem("REVISION_REQUIRED", "Supply If-Match for the current binding revision.", 428)
        if type(expected) is not int or expected < 0:
            raise Problem("REVISION_INVALID", "The binding revision must be a nonnegative integer.")
        try:
            with self.store.tx() as db:
                old = self._read(pid, db)
                if db.execute("SELECT 1 FROM records WHERE kind='retentionProjectStage' "
                              "AND json_extract(body,'$.resourceId')=? "
                              "AND (json_extract(body,'$.phase') IS NULL OR json_extract(body,'$.phase')!='aborted') LIMIT 1", (pid,)).fetchone():
                    raise Problem("LOCAL_BINDINGS_BUSY", "Project retirement is active or uncertain; reconcile it before publishing bindings.", 409)
                if expected != old["bindingRevision"]:
                    raise Problem("REVISION_CONFLICT", "Local bindings changed; reload their independent revision.", 412,
                                  currentBindingRevision=old["bindingRevision"])
                document = BindingDocument(**update.model_dump(), projectId=pid, bindingRevision=expected + 1,
                                           contextDigest=self._context())
                raw = canonical(document.model_dump()).encode("utf-8")
                if len(raw) > MAX_BYTES:
                    raise Problem("LIMIT_EXCEEDED", "The complete private binding sidecar limit is 64 KiB.", 413)
                sidecar = f"projects/{pid}/local-bindings/{expected + 1}-{uid('binding-')}.json"
                with open_write(self.store.root, self.store.root / sidecar, parents=True) as stream:
                    stream.write(raw)
                if self._raw(sidecar) != raw:
                    raise Problem("LOCAL_BINDINGS_CONFLICT", "The prepared private sidecar changed; its head was not advanced.", 409)
                self.store.put("project_local_bindings", pid, {"formatVersion": "1.0", "projectId": pid,
                    "bindingRevision": expected + 1, "sidecar": sidecar, "digest": digest(raw)}, db)
                result = self._read(pid, db)
            return result
        except SafeIOError as error:
            if error.code == "SECURE_IO_UNAVAILABLE":
                raise Problem("PLATFORM_IO_UNAVAILABLE", "Secure native binding-file persistence is unavailable on this host.", 503) from None
            raise Problem("LOCAL_BINDINGS_WRITE_FAILED", "Private binding persistence was not acknowledged; reload its current revision before retrying. Prepared files are retained.", 503) from None
        except OSError:
            raise Problem("LOCAL_BINDINGS_WRITE_FAILED", "Private binding persistence was not acknowledged; reload its current revision before retrying. Prepared files are retained.", 503) from None
