import base64
import hashlib
import io
import json
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import tarfile

root=Path.cwd();local=Path(__file__).resolve().parent
target=root/'evidence/studio/M4-accessibility/source-initial-focus-20261106'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
final=[f'final-{mode}-{w}' for mode in ('escape','close-button') for w in (1024,1440)]
baseline='baseline-current-tools-1440';at_phases=['probe-1',baseline]+final
native_phases=['native-probe-1','final-native'];phases=at_phases+native_phases
candidate=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',candidate,'--','apps','services','packages','tests','config','scripts','package.json','package-lock.json','pyproject.toml','uv.lock']))) as archive:
    source={m.name:sha(archive.extractfile(m).read()) for m in archive if m.isfile()}
assert len(source)==601
ui=json.loads((local/'ui-reproduction.json').read_bytes())['files'];assert len(ui)==6
old_ui=json.loads((root/'.studio-local/t097-orca-20261105/checks-final/ui-reproduction.json').read_bytes())['files']
results={}
for phase in final:
    p=local/phase;v=json.loads((p/'verification.private.json').read_bytes());b=json.loads((p/'browser-result.json').read_bytes())
    assert v['isolatedExit']==0 and v['before']==v['after'] and v['copyMutationReadbackError'] is None
    assert v['copyMutationReadback']['acceptedSemanticEdits']==3 and b['toRevision']==b['fromRevision']+3 and len(b['writes'])==3
    assert all(v[k] for k in ('originalRecordingUnchanged','copiedCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged','originalRootReleased'))
    assert source==json.loads((p/'source-inputs.json').read_bytes()) and ui==json.loads((p/'ui-inputs.json').read_bytes())
    snapshots=[json.loads(f.read_bytes()) for f in p.glob('*.atspi.private.json')]
    assert all(not any(s[k] for k in ('errors','truncated','eventErrors','droppedEvents')) for s in snapshots)
    inputs=[json.loads(l) for l in (p/'native-input.private.jsonl').read_text().splitlines()]
    assert inputs[-1]['keyPresses']==inputs[-1]['keyReleases']
    results[phase]={'width':b['width'],'sourceExit':b['sourceExit'],'commands':b['commands'],'keyPresses':inputs[-1]['keyPresses'],'keyReleases':inputs[-1]['keyReleases'],'textCharacters':inputs[-1]['totalTextCharacters'],'snapshots':len(snapshots),'events':max(s['events'] for s in snapshots),'capturedProcessesExited':v['observedProcessesExited'],'captureFailures':v['failedProcessCaptureAttempts'],'mutation':v['copyMutationReadback']}
p=local/baseline;control=json.loads((p/'verification.private.json').read_bytes())
assert control['isolatedExit']==1 and control['before']==control['after'] and control['copyMutationReadbackError'] is None and control['copyMutationReadback']['acceptedSemanticEdits']==1
assert all(control[k] for k in ('originalRecordingUnchanged','copiedCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged','originalRootReleased'))
assert source==json.loads((p/'source-inputs.json').read_bytes()) and old_ui==json.loads((p/'ui-inputs.json').read_bytes())
assert 'Actual Orca SSIP utterance deadline: View source for step' in (p/'browser.log').read_text()
events=[json.loads(l) for l in (p/'atspi-events.private.jsonl').read_text().splitlines()]
last=next(e for e in reversed(events) if e.get('type')=='object:state-changed:focused' and e.get('detail1'));assert last['name']=='View source for step orca-step-1440'
native_results={}
def attachments(v):
    if isinstance(v,dict):
        if v.get('contentType')=='application/json' and isinstance(v.get('body'),str):yield v,json.loads(base64.b64decode(v['body']))
        for x in v.values():yield from attachments(x)
    elif isinstance(v,list):
        for x in v:yield from attachments(x)
for phase in native_phases:
    p=local/phase;v=json.loads((p/'verification.json').read_bytes());report=json.loads((p/'browser.json').read_bytes());stats=report['stats']
    assert v['browserExit']==0 and v['originalBrowserExited'] and v['before']==v['after']==v['expectedExecutionCounts']
    assert all(v[k] for k in ('originalRootReleased','originalRecordingUnchanged','copiedOriginalCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged'))
    assert all(s['originalIdentityVerified'] and s['termination']=='original-handle SIGTERM' and s['exit'] in (0,-signal.SIGTERM) for s in v['backendShutdown'])
    assert stats['expected']==14 and all(stats[k]==0 for k in ('unexpected','skipped','flaky'))
    assert source==json.loads((p/'source-inputs.json').read_bytes()) and ui==json.loads((p/'ui-inputs.json').read_bytes())
    checks=[a for metadata,a in attachments(report) if metadata.get('name')=='source-initial-focus-countercheck.json']
    assert len(checks)==6 and {(a['width'],a['mode']) for a in checks}=={(w,m) for w in (1024,1440) for m in ('resource','caret','escape')}
    assert all(a['mounted'] and a['fired'] and a['projectUnchanged'] and a['writes']==[] and (a['mode']!='escape' or a['prevented']) for a in checks)
    native_results[phase]={'cases':14,'originalAuthoringCases':8,'instrumentedInitialFocusCounterchecks':checks,'stats':stats,'originalBrowserHandleExited':v['originalBrowserExited'],'backendShutdown':v['backendShutdown'],'reportedCandidate':v['sourceCandidate'],'actualSourceHashesMatchFinalCandidate':True,'rootReleased':v['originalRootReleased']}
secrets=set();bootstrap=set();consumed=0;xauth=0;native_roots={}
def collect(v):
    if isinstance(v,str) and len(v)>=20:secrets.add(v)
    elif isinstance(v,dict):
        for x in v.values():collect(x)
    elif isinstance(v,list):
        for x in v:collect(x)
for phase in phases:
    p=local/phase
    data=p/'data' if phase in at_phases else Path(json.loads((p/'data-root.private.json').read_bytes())['dataRoot'])
    if phase in native_phases:native_roots[str(data)]=f'[NATIVE_DATA_ROOT:{phase}]'
    session=p/'browser-session.private.json' if phase in at_phases else data/'browser-session.private.json'
    secrets.update(c['value'] for c in json.loads(session.read_bytes())['cookies'])
    with sqlite3.connect((data/'studio.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        for (body,) in db.execute("SELECT body FROM records WHERE kind='session'"):collect(json.loads(body))
    if phase in at_phases:
        address=json.loads((p/'isolation.private.json').read_bytes()).get('ownSessionBus')
        if address:secrets.add(address)
        for record in json.loads((p/'observed-processes.private.json').read_bytes()):
            argv=record.get('argv',[])
            if 'MIT-MAGIC-COOKIE-1' in argv:secrets.add(argv[argv.index('MIT-MAGIC-COOKIE-1')+1]);xauth+=1
    if (data/'bootstrap.json').exists():bootstrap.add(json.loads((data/'bootstrap.json').read_bytes())['bootstrapToken'])
    else:consumed+=1
secrets|=bootstrap
def clean(text):
    for value in secrets:text=text.replace(value,'[PRIVATE_SESSION_VALUE]')
    for old,new in native_roots.items():text=text.replace(old,new)
    for old,new in [(str(root),'[WORKTREE]'),('[MAIN_CHECKOUT]','[MAIN_CHECKOUT]'),('[PYTHON_INSTALL]','[PYTHON_INSTALL]'),('[WORKSPACE_VOLUME]','[WORKSPACE_VOLUME]'),('[OPERATOR_HOME]','[OPERATOR_HOME]')]:text=text.replace(old,new)
    text=re.sub(r'[TRUNCATED_PRIVATE_PATH](?:/[^\s\"\)]*)?','[TRUNCATED_PRIVATE_PATH]',text)
    return re.sub(r'(?:http://)?127\.0\.0\.1:\d+','[LOOPBACK_ORIGIN]',text)
def convert(v):
    if isinstance(v,dict):
        result={clean(k):convert(x) for k,x in v.items()}
        if v.get('contentType')=='application/json' and isinstance(v.get('body'),str):result['body']=base64.b64encode((json.dumps(convert(json.loads(base64.b64decode(v['body']))))+'\n').encode()).decode()
        return result
    if isinstance(v,list):return [convert(x) for x in v]
    return clean(v) if isinstance(v,str) else v
target.mkdir(parents=True,exist_ok=False);manifest=[]
def retain(p,name,mode='complete'):
    raw=p.read_bytes();text=raw.decode('utf-8',errors='replace');replacements=text.count('\ufffd')
    if mode=='snapshot-summary':
        v=json.loads(raw);rows=v.pop('rows');v.update(sourceRows=len(rows),focusedRows=[r for r in rows if r['focused']],editableValues=[r for r in rows if 'editableTextPrefix' in r],fullSourceRetainedPrivately=True);text=json.dumps(convert(v),indent=2)
    elif mode=='orca-speech':text='\n'.join(l for l in text.splitlines() if 'SPEECH OUTPUT:' in l or 'ORCA: Launching version' in l or 'ORCA: Shutdown complete' in l)
    elif mode=='orca-focus':text='\n'.join(l for l in text.splitlines() if any(s in l for s in ('EVENT MANAGER: Dequeued object:state-changed:focused','EVENT MANAGER: Dequeued object:selection-changed','ORCA: Changing locusOfFocus','ORCA: Setting locusOfFocus to existing locusOfFocus','WEB: Updating focus and context','SPEECH OUTPUT:')))
    elif mode=='orca-restoration':
        lines=text.splitlines();indexes=[i for i,l in enumerate(lines) if 'EVENT MANAGER: Dequeued object:state-changed:focused [push button | View source for step' in l and '(1,0,0)' in l];assert indexes;text='\n'.join(lines[indexes[-1]:])
    elif mode=='ssip-speech':text='\n'.join(l for l in text.splitlines() if any(s in l for s in ('DATA:|<speak>','CLIENT_NAME unknown:Orca:','200 OK SPEAKING','audio_output_method=','audio_alsa_device=')))
    elif p.suffix=='.json':text=json.dumps(convert(json.loads(raw)),indent=2)
    text='\n'.join(l.rstrip() for l in clean(text).splitlines()).rstrip();cooked=(text+'\n').encode() if text else b'';(target/name).write_bytes(cooked)
    manifest.append({'source':str(p.relative_to(root)),'artifact':name,'sourceSha256':sha(raw),'retainedSha256':sha(cooked),'transformation':mode,'sourceBytes':len(raw),'retainedBytes':len(cooked),'utf8ReplacementCharactersOnDecode':replacements})
for phase in at_phases:
    p=local/phase
    for name in ('source-inputs.json','ui-inputs.json','verification.private.json','observed-processes.private.json','command.private.json','isolation.private.json','browser-result.json','driver.log','orca.log','browser.log','inspector.log','host-1.log','native-input.private.jsonl','atspi-events.private.jsonl'):
        if (p/name).exists():retain(p/name,phase+'-'+name.replace('.private',''))
    for f in sorted(p.glob('*.atspi.private.json')):
        full=phase in final and any(s in f.name for s in ('selected-source-observation','source-return','edited-schedule-value','validation-error','created-focus','updated-focus','removed-focus','keep-focus'))
        retain(f,phase+'-'+f.name.replace('.private',''),'complete' if full else 'snapshot-summary')
    retain(p/'orca-debug.private.log',phase+'-orca-speech.log','orca-speech');retain(p/'orca-debug.private.log',phase+'-orca-focus.log','orca-focus')
    retain(p/'speech-logs/speech-dispatcher.log',phase+'-ssip-speech.log','ssip-speech')
    if phase==baseline:retain(p/'orca-debug.private.log',phase+'-orca-restoration.log','orca-restoration')
for phase in native_phases:
    p=local/phase
    for name in ('verification.json','source-inputs.json','ui-inputs.json','command.private.json','browser-owner.private.json','browser-device-proof.private.json','browser.json','browser.log','host-1.log','host-1-command.private.json','host-1-identity.private.json'):
        if (p/name).exists():retain(p/name,phase+'-'+name.replace('.private',''))
for name in ('checks.private.json','source-comparison.json','ui-reproduction.json','ui-reproduction.log','architecture.log','versions.json','run.py','run-baseline.py','native.py','final-matrix.py','check.py','retention-probe.json','retain-initial.py'):
    retain(local/name,name.replace('.private',''))
(target/'verification.json').write_text(json.dumps(convert({'candidate':candidate,'sourceInputs':601,'finalSourceAndGitMatch':True,'uiAssetsReproduced':6,'actualAtJourneysPassed':4,'actualBaselineFailure':{'phase':baseline,'oldUiCandidate':'240778b','sameCurrent601InputSupervisionAndBackend':True,'outcome':'failed actual return-button speech; correct DOM/AT focus','finalAtFocus':last,'mutation':control['copyMutationReadback'],'capturedProcessesExited':control['observedProcessesExited'],'captureFailures':control['failedProcessCaptureAttempts']},'atResults':results,'nativeResults':native_results,'sourceInitialFocusGapResolvedForCandidateAtBothSizes':True,'taskStatusChanges':[],'counts':{'completed':72,'in_progress':18,'blocked':10},'windows':'independently frozen','goal':'active'}),indent=2)+'\n')
(target/'retention-manifest.json').write_text(json.dumps({'files':manifest,'privateSessionControlStringsExcluded':len(secrets),'sessionDatabasesChecked':len(phases),'nativeSessionDatabasesChecked':len(native_phases),'capturedXauthorityArgumentsExcluded':xauth,'consumedBootstrapFilesAbsent':consumed,'remainingBootstrapValuesChecked':len(bootstrap),'consumedBootstrapValuesRecoveredOrScanned':0,'transformations':'Known session/control values and machine paths removed; nested JSON attachments decoded, sanitized and re-encoded. LF/trailing-whitespace normalization and zero-byte empty logs. Critical final AT trees complete, other trees labelled summaries. Orca/SSIP speech/focus/protocol subsets and one labelled post-restoration excerpt; raw source hashes retained. Raw databases, authentication, full API/project/SQL baselines and native data locators remain private.'},indent=2)+'\n')
def privacy(text):assert all(s not in text for s in secrets) and '[OPERATOR_HOME]' not in text and '[TRUNCATED_PRIVATE_PATH]' not in text
for p in target.iterdir():privacy(p.read_text())
print(json.dumps({'sourceDerivativePairs':len(manifest),'privateStrings':len(secrets),'sessionDatabases':len(phases),'actualAtJourneysPassed':4,'nativeCases':14,'candidate':candidate}))
