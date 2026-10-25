"""Exact candidate Linux receipt; invocation must use project venv, loop10 tmp."""
from pathlib import Path
import hashlib,json,os,platform,subprocess,sys,time

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)
ROOT=Path(__file__).resolve().parents[4]
FILES=['services/studio-api/src/xverse_studio/security/managed_io.py','services/studio-api/src/xverse_studio/host/recovery.py','tests/platform/test_recovery_safe_io.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
command=[sys.executable,'-m','pytest','tests/platform/test_recovery_safe_io.py','tests/platform/test_full_recovery.py','tests/platform/test_native_recovery.py','-q','-o','cache_dir=.studio-local/review-pytest','--basetemp=.studio-local/review-temp/recovery-safe-final']
env=os.environ.copy();env['PYTHONPATH']='services/studio-api/src';env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['TMPDIR']='.studio-local/review-temp'
before=hashes();started=time.time();result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
receipt={'scope':'Linux owned local fixture and native launcher only; no Windows/provider/hardware','python':sys.version,'platform':platform.platform(),'command':command,'startedAt':started,'elapsedSeconds':time.time()-started,'sourceBefore':before,'sourceAfter':hashes(),'exitCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'independentReview':'separate reviewer pending; this is author verification'}
Path(__file__).with_name('verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(result.stdout);print(result.stderr);sys.exit(result.returncode)
