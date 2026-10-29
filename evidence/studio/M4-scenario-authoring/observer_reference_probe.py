"""Read-only fixture-source probe for typed removal reference integrity."""
from pathlib import Path
from io import StringIO
from copy import deepcopy
import hashlib
import json
from ruamel.yaml import YAML
from xverse_studio.xdl import examples, XDLAdapter
from xverse_studio.xdl.edits import semantic_edits
from xverse_studio.assertions.snapshot import snapshot_definitions, definition_digest

sources=deepcopy(examples()[0]['documents']);yaml=YAML();resource=yaml.load(sources['scenario.xdl.yaml'])
observer=deepcopy(resource['spec']['observers'][0]);observer['id']='other-observer';resource['spec']['observers'].append(observer)
resource['extensions']['io.xverse.studio.experiments']['definitions'][0]['expression']['left']['input']['observerRef']='other-observer'
stream=StringIO();yaml.dump(resource,stream);sources['scenario.xdl.yaml']=stream.getvalue();adapter=XDLAdapter()
assert adapter.validate(sources)['valid']
def resolved(documents):
    snapshot={'documents':documents};snapshot['snapshotDigest']=definition_digest(snapshot)
    try:return {'result':'VALID','count':len(snapshot_definitions(snapshot,adapter))}
    except Exception as exc:return {'result':'ERROR','type':type(exc).__name__,'detail':str(exc)}
report={'sourceDigests':{path:'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in ['services/studio-api/src/xverse_studio/experiments/authoring.py','services/studio-api/src/xverse_studio/xdl/edits.py']},'beforeAdmittedDefinitions':resolved(sources)}
try:
    changed=semantic_edits(sources,[{'kind':'remove_scenario_item','documentId':'scenario.xdl.yaml','itemKind':'observer','itemId':'other-observer'}])
    report.update(editResult='ACCEPTED',afterPublicValid=adapter.validate(changed)['valid'],afterAdmittedDefinitions=resolved(changed))
except Exception as exc:report.update(editResult='REJECTED',errorType=type(exc).__name__,detail=str(exc))
print(json.dumps(report,indent=2))
