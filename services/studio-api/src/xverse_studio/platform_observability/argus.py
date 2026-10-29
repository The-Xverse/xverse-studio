"""Host-bound read-only adapter to the pinned public Argus API.

This adapter returns internal original evidence, not a redacted browser projection.
Only trusted host code supplies roots and expected identities. HTTP views must
apply their own payload/log policy before exposing records. No writer is opened.
"""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re
import json
import hashlib
import stat
import sys

from xverse.argus import ARGUS_VERSION, EvidenceLimits, EvidenceStore
from xverse_studio.storage.core import Problem, digest
from xverse_studio.security.managed_io import SafeIOError, open_read

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")


@dataclass(frozen=True)
class ArgusBinding:
    """A trusted-host registration; never constructed from an imported project."""
    source_id: str
    root: Path
    run_id: str
    plan_digest: str

    def __post_init__(self):
        if (not _ID.fullmatch(self.source_id) or not _ID.fullmatch(self.run_id)
                or not _DIGEST.fullmatch(self.plan_digest)):
            raise ValueError("ARGUS_BINDING_INVALID")
        root = Path(self.root).absolute()
        if root.resolve(strict=True) != root or not stat.S_ISDIR(root.lstat().st_mode):
            raise ValueError("ARGUS_BINDING_ROOT_INVALID")
        object.__setattr__(self, 'root', root)


def _identity(path):
    st = path.lstat()
    if not stat.S_ISDIR(st.st_mode):
        raise Problem("ARGUS_SOURCE_CHANGED", "The registered evidence root changed.", 409)
    return st.st_dev, st.st_ino


def _manifest_budget(root):
    # Resource admission only. The actual Argus reader remains authoritative for
    # schemas, digests, record validity, artifacts and evidence assessment.
    try:
        with open_read(root,root/'manifest.json') as stream:
            raw=stream.read(1024*1024+1)
    except SafeIOError as error:
        if error.code == "FILE_MISSING":
            return None
        raise Problem("ARGUS_SOURCE_UNAVAILABLE","The registered manifest cannot be read.",503) from None
    except OSError:
        raise Problem("ARGUS_SOURCE_UNAVAILABLE","The registered manifest cannot be read.",503) from None
    if len(raw)>1024*1024:
        raise Problem("ARGUS_SOURCE_LIMIT","The Argus manifest exceeds the reader byte budget.",413)
    try:
        manifest=json.loads(raw)
    except (ValueError,UnicodeError,RecursionError):
        return hashlib.sha256(raw).hexdigest()  # Let Argus retain its diagnostic.
    if isinstance(manifest,dict):
        stream=manifest.get('eventStream')
        artifacts=manifest.get('artifacts')
        entries=([stream] if isinstance(stream,dict) else [])+(artifacts if isinstance(artifacts,list) else [])
        total=0
        for entry in entries:
            if isinstance(entry,dict) and type(entry.get('bytes')) is int:
                total+=max(0,entry['bytes'])
        if len(entries)>65 or total>64*1024*1024:
            raise Problem("ARGUS_SOURCE_LIMIT","The Argus source exceeds the reader byte budget.",413)
    return hashlib.sha256(raw).hexdigest()


class ArgusSources:
    """Finite host registry with run/plan binding and source-bound pagination."""
    def __init__(self, bindings=()):
        if type(bindings) is not tuple or len(bindings) > 128:
            raise ValueError("ARGUS_REGISTRY_INVALID")
        self._sources = {}
        for binding in bindings:
            if type(binding) is not ArgusBinding or binding.source_id in self._sources:
                raise ValueError("ARGUS_REGISTRY_INVALID")
            self._sources[binding.source_id] = (binding, _identity(binding.root))
        self._limits = EvidenceLimits(max_event_bytes=16*1024, max_events=4096,
            max_id_length=128, max_text_length=2048, max_payload_bytes=4096,
            max_artifacts=64, max_obligations=64, max_diagnostic_count=128,
            max_manifest_bytes=1024*1024, max_causal_index_entries=4096,
            max_read_records=4096)

    def capture(self, source_id):
        """Capture one bounded original reader result for trusted host projection.

        A browser must never receive this raw result. A single capture avoids
        mixing pages read before/after an append to a live Argus manifest.
        """
        if not sys.platform.startswith("linux"):
            raise Problem("ARGUS_READER_OS_UNSUPPORTED", "This reader requires native Linux secure file access; use a supported host for this integration.", 422)
        if source_id not in self._sources:
            raise Problem("ARGUS_SOURCE_UNAVAILABLE", "Select a host-registered evidence source.", 404)
        binding, identity = self._sources[source_id]
        try:
            if _identity(binding.root) != identity:
                raise Problem("ARGUS_SOURCE_CHANGED", "The registered evidence root changed.", 409)
            manifest_witness = _manifest_budget(binding.root)
            reader = EvidenceStore.read_run(binding.root, limits=self._limits)
            if _manifest_budget(binding.root) != manifest_witness:
                raise Problem("ARGUS_SOURCE_CHANGED", "The evidence manifest changed during the read.", 409)
            if _identity(binding.root) != identity:
                raise Problem("ARGUS_SOURCE_CHANGED", "The registered evidence root changed during the read.", 409)
        except OSError:
            raise Problem("ARGUS_SOURCE_UNAVAILABLE", "The registered evidence source cannot be read.", 503) from None
        manifest = reader.manifest
        if manifest and manifest.get('runId') != binding.run_id:
            raise Problem("ARGUS_RUN_IDENTITY_MISMATCH", "Argus evidence belongs to another run.", 409)
        # Argus calls this manifest field semanticDigest, but it binds the
        # compiled plan. It is NOT Studio's separate inputSemanticDigest.
        plan = manifest.get('plan') or {}
        plan_identity = plan.get('semanticDigest') or {}
        actual_digest = 'sha256:' + str(plan_identity.get('value', ''))
        if manifest and (plan_identity.get('algorithm') != 'sha256' or actual_digest != binding.plan_digest):
            raise Problem("ARGUS_PLAN_IDENTITY_MISMATCH", "Argus evidence binds another compiled plan.", 409)
        records = reader.records()
        statuses = {'recorded': reader.recorded_evidence_status,
                    'assessed': reader.assessed_evidence_status,
                    'recordedReasons': reader.recorded_evidence_reasons,
                    'assessedReasons': reader.assessed_evidence_reasons}
        # Do not copy filesystem messages/paths into diagnostics. Codes preserve
        # the original Argus verdict; original evidence remains in Argus storage.
        diagnostics = [{key: getattr(item, key) for key in ('code','category','severity')}
                       for item in reader.diagnostics]
        witness = digest({'source':binding.source_id, 'run':binding.run_id,
            'plan':binding.plan_digest, 'manifest':manifest, 'records':records,
            'statuses':statuses, 'diagnostics':diagnostics, 'manifestBytes':manifest_witness})
        return {'projectionVersion':'1.0', 'sourceId':binding.source_id,
            'reader':{'service':'argus','version':ARGUS_VERSION},
            'expectedIdentity':{'runId':binding.run_id,'planDigest':binding.plan_digest},
            'runId':binding.run_id if manifest else None, 'planDigest':binding.plan_digest if manifest else None,
            'inputSemanticDigest':None,
            'identityVerified':bool(manifest), 'sourceWitness':witness,
            'evidence':deepcopy(statuses), 'diagnostics':diagnostics,
            'items':deepcopy(records), 'retainedRecordCount':len(records)}

    def read(self, source_id, *, limit=100, cursor=None):
        if type(limit) is not int or not 1 <= limit <= 200:
            raise Problem("LIMIT_EXCEEDED", "Select an evidence page of1–200 records.")
        captured = self.capture(source_id)
        records, witness = captured['items'], captured['sourceWitness']
        offset = 0
        if cursor is not None:
            if (type(cursor) is not dict or set(cursor) != {'witness','offset'}
                    or cursor['witness'] != witness or type(cursor['offset']) is not int
                    or not 0 < cursor['offset'] < len(records)):
                raise Problem("ARGUS_CURSOR_STALE", "The evidence or page identity changed; read the first page.", 409)
            offset = cursor['offset']
        following = offset + limit
        return {**captured,
            'items':deepcopy(records[offset:following]), 'retainedRecordCount':len(records),
            'nextCursor': {'witness':witness,'offset':following} if following < len(records) else None}
