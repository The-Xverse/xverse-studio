"""Owned-fixture directory/leaf acquisition races with capability-preserving hooks."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
from xverse_studio.security.managed_io import open_read,open_write,SafeIOError

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

report={'sourceDigest':'sha256:'+hashlib.sha256(Path('services/studio-api/src/xverse_studio/security/managed_io.py').read_bytes()).hexdigest(),'cases':{}}
for mode in ('read_leaf','read_root_component','write_leaf'):
    with TemporaryDirectory(dir='.studio-local/review-temp',prefix='anchored-io-review-') as directory:
        base=Path(directory);root=base/'root';parent=root/'nested';parent.mkdir(parents=True)
        outside=base/'outside';outside.mkdir();target=parent/'value.bin';sentinel=b'OUTSIDE OWNED FIXTURE'
        outside_file=(outside/'nested'/target.name) if mode=='read_root_component' else outside/target.name
        if mode!='write_leaf':outside_file.parent.mkdir(parents=True,exist_ok=True);outside_file.write_bytes(sentinel)
        if mode!='write_leaf':target.write_bytes(b'OWNED ORIGINAL')
        attack_parent=root if mode=='read_root_component' else parent
        held=attack_parent.with_name(attack_parent.name+'-held');real_open=os.open;swaps=[]
        def race(path,flags,*args,**kwargs):
            descriptor=kwargs.get('dir_fd')
            desired=root.name if mode=='read_root_component' else target.name
            expected_parent=base if mode=='read_root_component' else parent
            hit=descriptor is not None and str(path)==desired and os.fstat(descriptor).st_ino==expected_parent.stat().st_ino
            if not hit:return real_open(path,flags,*args,**kwargs)
            attack_parent.rename(held);attack_parent.symlink_to(outside,target_is_directory=True);swaps.append(True)
            try:return real_open(path,flags,*args,**kwargs)
            finally:attack_parent.unlink();held.rename(attack_parent)
        try:
            with patch.object(os,'supports_dir_fd',set(os.supports_dir_fd)|{race}),patch.object(os,'open',race):
                if mode=='write_leaf':
                    with open_write(root,target) as stream:stream.write(b'OWNED WRITE')
                    result='WROTE_OWNED'
                else:
                    with open_read(root,target) as stream:content=stream.read()
                    assert content==b'OWNED ORIGINAL'
                    result='READ_OWNED'
        except SafeIOError as exc:result=exc.code
        assert swaps,'Capability guard must not bypass the instrumented acquisition'
        if mode=='read_root_component':assert result=='UNSAFE_PATH'
        elif mode=='write_leaf':
            assert result=='WROTE_OWNED' and target.read_bytes()==b'OWNED WRITE' and not outside_file.exists()
        else:assert result=='READ_OWNED' and outside_file.read_bytes()==sentinel
        report['cases'][mode]={'hookExecuted':True,'result':result,'outsideUnaffected':True}
print(json.dumps(report,indent=2))
