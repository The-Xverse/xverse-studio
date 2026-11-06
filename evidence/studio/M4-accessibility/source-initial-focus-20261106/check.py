from pathlib import Path
import hashlib
import io
import json
import subprocess
import sys
import tarfile

root=Path.cwd();local=Path(__file__).resolve().parent;prefix=root.parents[3]
node=prefix/'.xverse-studio-cache/node-v24.22.1-linux-x64/bin/node'
sha=lambda data:hashlib.sha256(data).hexdigest()
commands=[]
def run(name,argv,cwd=root):
    r=subprocess.run([str(a) for a in argv],cwd=cwd,capture_output=True,timeout=90)
    (local/(name+'.log')).write_bytes(r.stdout+r.stderr)
    commands.append({'name':name,'argv':[str(a) for a in argv],'cwd':str(cwd),'exit':r.returncode})
    assert r.returncode==0,name
run('ui-reproduction',[node,'[MAIN_CHECKOUT]/node_modules/vite/bin/vite.js','build','--outDir',local/'ui-reproduced'],root/'apps/studio-web')
def assets(folder):return {f.relative_to(folder).as_posix():sha(f.read_bytes()) for f in folder.rglob('*') if f.is_file()}
assert assets(local/'ui2')==assets(local/'ui-reproduced') and len(assets(local/'ui2'))==6
(local/'ui-reproduction.json').write_text(json.dumps({'exact':True,'files':assets(local/'ui2')},indent=2)+'\n')
run('architecture',[sys.executable,'-I','scripts/check_architecture.py'])
baseline='ad87ebe99186f9159c0e838dc1bef6a7f5c26344'
previous=json.loads((root/'.studio-local/t097-orca-observers-20261106/final-observers-1024/source-inputs.json').read_bytes())
candidate=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',candidate,'--','apps','services','packages','tests','config','scripts','package.json','package-lock.json','pyproject.toml','uv.lock']))) as archive:
    current={m.name:sha(archive.extractfile(m).read()) for m in archive if m.isfile()}
assert set(current)==set(previous) and len(current)==601
changed={name for name in current if current[name]!=previous[name]}
assert changed=={'apps/studio-web/src/features/model/Views.tsx','tests/live/autoverse-authoring-keyboard.spec.ts'}
path='apps/studio-web/src/features/model/Views.tsx'
before=subprocess.check_output(['git','show',baseline+':'+path]).decode()
after=(root/path).read_text()
start=before.index('  useEffect(() => {\n    if (!anchored.current && content && (target?.elementId || target?.ref)) {')
end=before.index('  const externalSource',start)
assert after.startswith(before[:start]) and after.endswith(before[end:])
(local/'source-comparison.json').write_text(json.dumps({'candidate':candidate,'baseline':baseline,'sourceInputs':len(current),'changedInputs':sorted(changed),'allOtherInputsIdentical':True,'sourceEditorOnlyInitialEffectChanged':True,'backendInputsUnchanged':sum(n.startswith('services/') for n in current),'beforeViewSha256':sha(before.encode()),'afterViewSha256':sha(after.encode())},indent=2)+'\n')
commands.append({'name':'typecheck','argv':[str(node),'[MAIN_CHECKOUT]/node_modules/typescript/bin/tsc','--noEmit','-p','apps/studio-web/tsconfig.json'],'exit':0,'provenance':'Actual tool result96032 before commit2391af4; source bytes unchanged; no additional typecheck execution claimed.'})
(local/'checks.private.json').write_text(json.dumps(commands,indent=2)+'\n')
print(json.dumps({'candidate':candidate,'reproducedAssets':6,'changedInputs':sorted(changed),'architectureExit':0}))
