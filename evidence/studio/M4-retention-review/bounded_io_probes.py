"""Independent bounded-descriptor probes; only sparse owned temporary files are used."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
from xverse_studio.retention.files import read_bounded, inspect_tree, ProofBudget, ProofLimit, MAX_PROOF_BYTES

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

report={"sourceDigest":"sha256:"+hashlib.sha256(Path('services/studio-api/src/xverse_studio/retention/files.py').read_bytes()).hexdigest(),"cases":{}}
with TemporaryDirectory(dir='.studio-local/review-temp',prefix='retention-budget-review-') as directory:
    root=Path(directory);path=root/'owned-source'
    with path.open('wb') as stream:stream.truncate(16*1024*1024+1)
    with patch.object(os,'read',side_effect=AssertionError('oversized input read before refusal')) as spy:
        try:read_bounded(root,path,ProofBudget());raise AssertionError('oversized input admitted')
        except ProofLimit:pass
        assert spy.call_count==0
    report['cases']['oversized_source_refuses_before_read']='PASS'
    path.write_bytes(b'abcd');budget=ProofBudget();budget.read(MAX_PROOF_BYTES-3)
    with patch.object(os,'read',side_effect=AssertionError('aggregate proof budget exceeded before refusal')) as spy:
        try:read_bounded(root,path,budget);raise AssertionError('overbudget input admitted')
        except ProofLimit:pass
        assert spy.call_count==0
    report['cases']['aggregate_budget_refuses_before_read']='PASS'
    with path.open('wb') as stream:stream.truncate(MAX_PROOF_BYTES+1)
    with patch.object(os,'read',side_effect=AssertionError('oversized tree file read before refusal')) as spy:
        try:inspect_tree(root,path,ProofBudget());raise AssertionError('overbudget tree admitted')
        except ProofLimit:pass
        assert spy.call_count==0
    report['cases']['tree_proof_precharges_bytes']='PASS'
    path.write_bytes(b'abcd');original_read=os.read;requests=[]
    def grow(descriptor,count):
        requests.append(count)
        if len(requests)==1:
            with path.open('ab') as stream:stream.write(b'e')
        return original_read(descriptor,count)
    with patch.object(os,'read',side_effect=grow):
        try:read_bounded(root,path,ProofBudget());raise AssertionError('growing file admitted')
        except ValueError as exc:assert str(exc)=='FILES_CHANGED_DURING_PROOF'
    assert requests==[4]
    report['cases']['growth_refused_without_reading_beyond_reserved_size']='PASS'
print(json.dumps(report,indent=2))
