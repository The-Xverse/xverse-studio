from pathlib import Path
from tempfile import TemporaryDirectory
import json
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

nested = {"leaf": 1}
for _ in range(600): nested = {"nested": nested}
with TemporaryDirectory(dir=".studio-local/review-temp",prefix="scenario-depth-review-") as directory:
    app=create_app(Path(directory),allowed_hosts=["testserver"],bootstrap_token="review-fixture-bootstrap")
    with TestClient(app,base_url="http://testserver",raise_server_exceptions=False) as client:
        client.headers["Origin"]="http://testserver"
        session=client.post("/api/v1/session",json={"bootstrapToken":"review-fixture-bootstrap"})
        client.headers["X-CSRF-Token"]=session.json()["csrfToken"]
        project=client.post("/api/v1/projects",json={"name":"Depth review fixture"}).json()
        did=next(k for k,v in project["documents"].items() if "scenario" in v["path"])
        response=client.post(f"/api/v1/projects/{project['projectId']}/edits",headers={"If-Match":"1"},json={"baseRevision":1,"edits":[{"kind":"set_scenario_conditions","documentId":did,"properties":{"initialConditions":nested}}]})
        after=client.get(f"/api/v1/projects/{project['projectId']}").json()
        print(json.dumps({"depth":600,"status":response.status_code,"response":response.text[:500],"revisionAfter":after["revision"],"sourcePreserved":after["documents"]==project["documents"]},indent=2))
