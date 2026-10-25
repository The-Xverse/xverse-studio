from __future__ import annotations
import asyncio
import base64
from contextlib import asynccontextmanager
import hashlib
import hmac
import io
import json
from pathlib import Path
import secrets
import time
from types import SimpleNamespace
from typing import Annotated
import zipfile
from fastapi import FastAPI, Request, Response, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from starlette.exceptions import HTTPException
from xverse_studio import __version__
from xverse_studio.api.models import *
from xverse_studio.storage.core import Store, Problem, atomic, canonical, digest, uid
from xverse_studio.security.files import MAX_BYTES, check_text
from xverse_studio.projects.service import Projects
from xverse_studio.runs.service import Runs, ACTIVE
from xverse_studio.providers.registry import (
    capabilities,
    capability_digest,
    descriptors,
)
from xverse_studio.diagnostics import explain_preflight, explain_run
from xverse_studio.evidence.reader import read_journal
from xverse_studio.events import EventStreams
from xverse_studio.evidence.query import (
    HistoryQuery,
    ObservationQuery,
    project_evidence,
)
from xverse_studio.xdl import XDLAdapter, XDLRejected, examples


class EventStreamingResponse(StreamingResponse):
    """Release admission even if ASGI startup fails before iterator entry."""

    def __init__(self, content, *, release, **options):
        super().__init__(content, **options)
        self.release_subscription = release

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.release_subscription()


def revision(request):
    value = request.headers.get("if-match")
    if value is None:
        return None
    try:
        return int(value.strip('"'))
    except ValueError:
        raise Problem(
            "REVISION_INVALID", "If-Match must identify the current numeric revision."
        ) from None


def page(items, cursor, limit):
    try:
        offset = int(cursor or "0")
    except ValueError:
        raise Problem("CURSOR_INVALID", "The page cursor is invalid.") from None
    if offset < 0 or not 1 <= limit <= 200:
        raise Problem("LIMIT_EXCEEDED", "Choose a page of 1–200 records.")
    return {
        "items": items[offset : offset + limit],
        "nextCursor": str(offset + limit) if len(items) > offset + limit else None,
    }


def create_app(
    data_dir: Path,
    *,
    allowed_hosts=None,
    bootstrap_token=None,
    static_dir: Path | None = None,
):
    store = Store(Path(data_dir))
    adapter = XDLAdapter()
    projects = Projects(store, adapter)
    runs = Runs(store, projects, adapter)
    event_streams = EventStreams(store, runs)
    hosts = allowed_hosts or ["127.0.0.1:8765", "localhost:8765"]
    token = bootstrap_token or secrets.token_urlsafe(32)
    bootstrap = {
        "digest": hashlib.sha256(token.encode()).hexdigest(),
        "expiresAt": time.time() + 300,
        "used": False,
    }
    atomic(
        store.root / "bootstrap.json",
        canonical(
            {
                "bootstrapToken": token,
                "expiresAt": bootstrap["expiresAt"],
                "instruction": "Enter this one-use token in the local Studio browser. It expires after five minutes.",
            }
        ).encode(),
    )
    try:
        (store.root / "bootstrap.json").chmod(0o600)
    except OSError:
        pass
    for run in store.all("run"):
        if run["state"] in ACTIVE:
            run["state"] = "reconciling"
            store.put("run", run["runId"], run)
            runs.read(run["runId"])

    @asynccontextmanager
    async def lifespan(app):
        async def campaigns_loop():
            while True:
                tick = getattr(app.state.studio, "campaign_tick", None)
                if tick:
                    try:
                        await asyncio.to_thread(tick)
                    except Exception:
                        # A scheduler failure never replays an uncertain dispatch. Its service retains child state.
                        app.state.studio.campaign_error = "CAMPAIGN_SCHEDULER_ERROR"
                await asyncio.sleep(0.5)

        scheduler = asyncio.create_task(campaigns_loop())
        try:
            yield
        finally:
            event_streams.close()
            scheduler.cancel()
            try:
                await scheduler
            except asyncio.CancelledError:
                pass
            await asyncio.to_thread(runs.shutdown)

    app = FastAPI(
        title="X-Verse Studio",
        version=__version__,
        openapi_url="/api/v1/openapi.json",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.studio = SimpleNamespace(
        store=store, projects=projects, runs=runs, adapter=adapter, events=event_streams
    )

    def error(code, message, status, request, **details):
        return JSONResponse(
            {
                "code": code,
                "message": message,
                "requestId": getattr(request.state, "requestId", uid("req-")),
                "retryable": False,
                **details,
            },
            status_code=status,
        )

    @app.middleware("http")
    async def boundary(request, call_next):
        request.state.requestId = uid("req-")
        host = request.headers.get("host", "")
        origin = request.headers.get("origin")
        if host not in hosts or origin is not None and origin != "http://" + host:
            return error(
                "FORBIDDEN",
                "The request Host or Origin is not admitted for this local service.",
                403,
                request,
            )
        mutation = request.method not in ("GET", "HEAD", "OPTIONS")
        if mutation and origin != "http://" + host:
            return error(
                "FORBIDDEN", "Mutations require the exact local Origin.", 403, request
            )
        if request.url.path.startswith("/api/"):
            if request.headers.get("x-studio-contract-version", "1.0") != "1.0":
                return error(
                    "API_VERSION_INCOMPATIBLE",
                    "This service requires Studio HTTP contract 1.0.",
                    426,
                    request,
                )
            if not (request.url.path == "/api/v1/session" and request.method == "POST"):
                session_token = request.cookies.get("studio_session", "")
                try:
                    session = store.get(
                        "session", hashlib.sha256(session_token.encode()).hexdigest()
                    )
                except Problem:
                    return error(
                        "UNAUTHORIZED",
                        "Sign in using the native launcher bootstrap file.",
                        401,
                        request,
                    )
                if session["expiresAt"] < time.time():
                    return error(
                        "UNAUTHORIZED",
                        "The local session expired. Restart the native launcher to obtain a new bootstrap.",
                        401,
                        request,
                    )
                request.state.principal = "local-operator"
                request.state.session = session
                if mutation and not hmac.compare_digest(
                    request.headers.get("x-csrf-token", ""), session["csrfToken"]
                ):
                    return error(
                        "FORBIDDEN", "The CSRF token is invalid.", 403, request
                    )
        if mutation:
            chunks = []
            size = 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > MAX_BYTES:
                    return error(
                        "LIMIT_EXCEEDED", "Request byte limit exceeded.", 413, request
                    )
                chunks.append(chunk)
            request._body = b"".join(chunks)
        result = await call_next(request)
        result.headers["X-Content-Type-Options"] = "nosniff"
        result.headers["Referrer-Policy"] = "no-referrer"
        result.headers["X-Frame-Options"] = "DENY"
        result.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
        )
        result.headers["X-Request-ID"] = request.state.requestId
        if request.url.path.startswith("/api/"):
            result.headers["Cache-Control"] = "no-store"
        return result

    @app.exception_handler(Problem)
    async def problem_handler(request, e):
        return error(e.code, e.message, e.status, request, **e.details)

    @app.exception_handler(XDLRejected)
    async def xdl_handler(request, e):
        return error(e.code, str(e), 422, request)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, e):
        return error(
            "REQUEST_INVALID",
            "The request does not match the versioned schema.",
            422,
            request,
            diagnostics=[
                {
                    "code": "SCHEMA_INVALID",
                    "severity": "error",
                    "location": {"pointer": "/".join(map(str, x["loc"]))},
                    "message": x["msg"],
                }
                for x in e.errors()[:20]
            ],
        )

    @app.exception_handler(Exception)
    async def internal_handler(request, e):
        return error(
            "INTERNAL_ERROR",
            "The operation failed. Preserve inputs and use the request identifier for diagnosis.",
            500,
            request,
        )

    @app.exception_handler(HTTPException)
    async def http_handler(request, e):
        return error(
            "NOT_FOUND" if e.status_code == 404 else "HTTP_ERROR",
            "The route or operation is unavailable.",
            e.status_code,
            request,
        )

    @app.post("/api/v1/session")
    def login(body: Login, response: Response, request: Request):
        with store.lock:
            if (
                bootstrap["used"]
                or bootstrap["expiresAt"] < time.time()
                or not hmac.compare_digest(
                    hashlib.sha256(body.bootstrapToken.encode()).hexdigest(),
                    bootstrap["digest"],
                )
            ):
                raise Problem(
                    "UNAUTHORIZED",
                    "The bootstrap is invalid, expired or already used.",
                    401,
                )
            bootstrap["used"] = True
            (store.root / "bootstrap.json").unlink(missing_ok=True)
            session_token = secrets.token_urlsafe(32)
            session = {
                "csrfToken": secrets.token_urlsafe(32),
                "expiresAt": time.time() + 86400,
            }
            store.put(
                "session", hashlib.sha256(session_token.encode()).hexdigest(), session
            )
            response.set_cookie(
                "studio_session",
                session_token,
                httponly=True,
                samesite="strict",
                max_age=86400,
                path="/",
            )
            return session

    @app.get("/api/v1/session")
    def session(request: Request):
        return request.state.session

    @app.get("/api/v1/capabilities")
    def caps():
        return capabilities()

    @app.get("/api/v1/providers")
    def providers():
        return {"items": descriptors(), "nextCursor": None}

    @app.get("/api/v1/projects")
    def list_projects(cursor: str | None = None, limit: int = 200):
        return page(
            [
                {k: v for k, v in p.items() if k not in ("documents", "manifest")}
                for p in store.all("project")
            ],
            cursor,
            limit,
        )

    @app.post("/api/v1/projects", status_code=201)
    def new_project(body: NewProject, response: Response):
        p = projects.create(body.name, body.blueprintRef)
        response.headers["ETag"] = f'"{p["revision"]}"'
        return p

    @app.get("/api/v1/projects/{projectId}")
    def get_project(projectId: str, response: Response):
        p = projects.read(projectId)
        response.headers["ETag"] = f'"{p["revision"]}"'
        return p

    @app.put("/api/v1/projects/{projectId}/documents/{documentId}")
    def put_document(
        projectId: str,
        documentId: str,
        body: Document,
        request: Request,
        response: Response,
    ):
        p = projects.save(
            projectId, documentId, revision(request), body.content, body.format
        )
        response.headers["ETag"] = f'"{p["revision"]}"'
        return p

    @app.put("/api/v1/projects/{projectId}/layout")
    def layout(projectId: str, body: Layout, request: Request):
        return projects.layout(
            projectId, revision(request), body.model_dump(exclude_none=True)
        )

    @app.post("/api/v1/projects/imports", status_code=201)
    def imports(body: Import):
        return projects.import_archive(body.archiveBase64)

    @app.get("/api/v1/projects/{projectId}/graph")
    def graph(projectId: str):
        p = projects.read(projectId)
        result = adapter.project(projects.sources(p))
        result["revision"] = p["revision"]
        result["layout"] = p["layout"]
        return result

    @app.post("/api/v1/projects/{projectId}/validations")
    def validate(projectId: str, body: Selection):
        p = projects.read(projectId)
        if p["revision"] != body.revision:
            raise Problem(
                "REVISION_CONFLICT",
                "Validate the current revision.",
                412,
                currentRevision=p["revision"],
            )
        projects.assert_intact(p)
        return {**adapter.validate(projects.sources(p)), "revision": p["revision"]}

    @app.post("/api/v1/projects/{projectId}/compilations")
    def compile(projectId: str, body: Selection):
        p = projects.read(projectId)
        if p["revision"] != body.revision:
            raise Problem(
                "REVISION_CONFLICT",
                "Compile the current revision.",
                412,
                currentRevision=p["revision"],
            )
        projects.assert_intact(p)
        from xverse_studio.profiles import ProfileRegistry

        ProfileRegistry(adapter).validate_project(p)
        return {
            **runs.compilation(projects.sources(p), body.model_dump()),
            "revision": p["revision"],
        }

    @app.post("/api/v1/projects/{projectId}/edits")
    def edits(projectId: str, body: Edits, request: Request):
        from xverse_studio.xdl.edits import semantic_edits

        expected = revision(request)
        if expected != body.baseRevision:
            raise Problem(
                "REVISION_CONFLICT", "If-Match and baseRevision must agree.", 412
            )

        def change(p):
            by_path = {d["path"]: id for id, d in p["documents"].items()}
            commands = json.loads(canonical(body.edits))
            for c in commands:
                if c.get("documentId") in p["documents"]:
                    c["documentId"] = p["documents"][c["documentId"]]["path"]
            updated = semantic_edits(projects.sources(p), commands)
            return {
                by_path.get(path, uid("doc-")): {
                    "path": path,
                    "content": content,
                    "format": "json" if path.endswith(".json") else "yaml",
                }
                for path, content in updated.items()
            }

        return projects.mutate(projectId, expected, change)

    @app.post("/api/v1/projects/{projectId}/preflights")
    def preflight(projectId: str, body: Selection):
        return runs.preflight(projectId, body.model_dump())

    @app.post("/api/v1/runs", status_code=202)
    def start(body: Start, request: Request):
        return runs.start(
            request.state.principal,
            request.headers.get("idempotency-key"),
            body.model_dump(),
        )

    @app.get("/api/v1/runs")
    def list_runs(
        projectId: str | None = None, cursor: str | None = None, limit: int = 200
    ):
        items = [
            runs.read(r["runId"])
            for r in store.all("run")
            if not projectId or r["projectId"] == projectId
        ]
        return page(
            [
                {
                    k: v
                    for k, v in r.items()
                    if k not in ("pid", "createTime", "ownerDigest")
                }
                for r in items
            ],
            cursor,
            limit,
        )

    @app.get("/api/v1/runs/{runId}")
    def run(runId: str):
        return {
            k: v
            for k, v in runs.read(runId).items()
            if k not in ("pid", "createTime", "ownerDigest")
        }

    @app.get("/api/v1/runs/{runId}/snapshot")
    def frozen_snapshot(runId: str):
        run = store.get("run", runId)
        snapshot = store.get("snapshot", run["snapshotId"])
        runs.verify_snapshot(snapshot)
        return {"snapshot": snapshot, "integrity": "valid", "readOnly": True}

    @app.post("/api/v1/runs/{runId}/commands", status_code=202)
    def command(runId: str, body: Command, request: Request):
        return runs.command(
            runId,
            request.state.principal,
            request.headers.get("idempotency-key"),
            body.model_dump(),
        )

    @app.get("/api/v1/operations/{operationId}")
    def operation(operationId: str):
        op = store.get("operation", operationId)
        if op.get("kind") == "rerun":
            app.state.studio.reruns.reconcile_operation(operationId)
        if op.get("runId"):
            runs.read(op["runId"])
        return store.get("operation", operationId)

    @app.get("/api/v1/runs/{runId}/evidence")
    def evidence(runId: str):
        r = runs.read(runId)
        records, integrity = read_journal(runs.directory(runId), r)
        return {
            "items": [
                {
                    "evidenceId": runId + ":reference-journal",
                    "digest": r.get("journalDigest"),
                    "integrity": integrity,
                    "status": r["evidence"],
                    "recordCount": len(records),
                    "reader": "studio.reference.hash-chain-v1",
                    "evidenceScope": r.get("evidenceScope", "unknown"),
                }
            ],
            "nextCursor": None,
            "integrity": integrity,
            "status": r["evidence"],
        }

    @app.get("/api/v1/runs/{runId}/observations")
    def observations(
        runId: str,
        query: Annotated[ObservationQuery, Query()],
        request: Request,
    ):
        if len(request.query_params.multi_items()) != len(request.query_params):
            raise Problem(
                "EVIDENCE_FILTER_INVALID", "Each evidence selector may occur only once."
            )
        r = runs.read(runId)
        records, integrity = read_journal(runs.directory(runId), r)
        return project_evidence(
            records,
            integrity,
            query,
            runId,
            "observations",
            evidence_scope=r.get("evidenceScope", "unknown"),
        )

    @app.get("/api/v1/runs/{runId}/history")
    def history(
        runId: str,
        query: Annotated[HistoryQuery, Query()],
        request: Request,
    ):
        if len(request.query_params.multi_items()) != len(request.query_params):
            raise Problem(
                "EVIDENCE_FILTER_INVALID", "Each evidence selector may occur only once."
            )
        r = runs.read(runId)
        records, integrity = read_journal(runs.directory(runId), r)
        return project_evidence(
            records,
            integrity,
            query,
            runId,
            "history",
            evidence_scope=r.get("evidenceScope", "unknown"),
        )

    @app.get("/api/v1/runs/{runId}/diagnostics")
    def run_diagnostics(runId: str):
        r = runs.read(runId)
        records, integrity = read_journal(runs.directory(runId), r)
        try:
            configuration = store.get("snapshot", r["snapshotId"]).get("configuration")
        except Problem:
            configuration = None
        configuration = configuration or {}
        observer = configuration.get("observerRef")
        element_refs = configuration.get("elementRefs")
        return explain_run(
            r,
            records,
            integrity,
            expected_observers=[observer] if isinstance(observer, str) else [],
            operations=store.find("operation", "runId", runId),
            element_refs=[ref for ref in element_refs if isinstance(ref, str)]
            if isinstance(element_refs, list)
            else [],
        )

    @app.get("/api/v1/projects/{projectId}/preflights/{preflightId}/diagnostics")
    def preflight_diagnostics(projectId: str, preflightId: str):
        pf = store.get("preflight", preflightId)
        if store.get("snapshot", pf["snapshotId"]).get("projectId") != projectId:
            raise Problem("NOT_FOUND", "Requested record was not found.", 404)
        return explain_preflight(
            pf,
            current_revision=projects.read(projectId)["revision"],
            capability_digest=capability_digest(),
        )

    @app.get("/api/v1/runs/{runId}/resync")
    def resynchronize(runId: str, request: Request):
        if request.query_params:
            raise Problem(
                "CURSOR_INVALID",
                "Recovery uses the unfiltered original stream watermark.",
            )
        return event_streams.resync(runId)

    @app.get("/api/v1/runs/{runId}/events")
    async def events(
        runId: str,
        request: Request,
        after: str | None = None,
        streamVersion: str = "1.0",
    ):
        if set(request.query_params) - {"after", "streamVersion"} or len(
            request.query_params.multi_items()
        ) != len(request.query_params):
            raise Problem(
                "CURSOR_INVALID", "Event selectors must be supported and unambiguous."
            )
        header = request.headers.get("last-event-id")
        if len(request.headers.getlist("last-event-id")) > 1 or (
            header is not None and after is not None and header != after
        ):
            raise Problem(
                "CURSOR_INVALID", "The query and Last-Event-ID cursors must agree."
            )
        cursor = after if after is not None else header
        if cursor is not None and (not cursor or len(cursor) > 2048):
            raise Problem(
                "CURSOR_INVALID", "The event cursor exceeds its supported shape."
            )
        lease = event_streams.reserve(runId)
        try:
            prepared = await asyncio.to_thread(
                event_streams.prepare, runId, cursor, streamVersion
            )
        except BaseException:
            event_streams.release(lease)
            raise
        return EventStreamingResponse(
            event_streams.iterate(runId, prepared, lease, request),
            release=lambda: event_streams.release(lease),
            media_type="text/event-stream",
            headers={
                "X-Accel-Buffering": "no",
                "Cache-Control": "no-store",
                "X-Studio-Stream-Version": streamVersion,
            },
        )

    from xverse_studio.api.composition import install_composition

    install_composition(app, store, projects, runs, adapter)
    from xverse_studio.api.reruns import install_reruns

    install_reruns(app, store, projects, runs, adapter)
    from xverse_studio.api.exchange import install_exchange

    install_exchange(app, store, projects, runs)
    from xverse_studio.api.evidence_exchange import install_evidence_exchange

    install_evidence_exchange(app, store, projects, runs)

    # Later feature facades are installed only when their implementations exist.
    from xverse_studio.api.advanced import install_advanced

    install_advanced(app, store, projects, runs, adapter)

    webroot = static_dir or Path(__file__).resolve().parents[5] / "apps/studio-web/dist"

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str):
        if path.startswith("api/"):
            raise Problem("NOT_FOUND", "This API version or route is unsupported.", 404)
        target = (webroot / path).resolve()
        if not target.is_relative_to(webroot.resolve()):
            raise Problem("NOT_FOUND", "File not found.", 404)
        if target.is_file():
            return FileResponse(target)
        if "." not in path and (webroot / "index.html").exists():
            return FileResponse(webroot / "index.html")
        raise Problem(
            "NOT_FOUND",
            "Build the frontend with npm run build before launching Studio.",
            404,
        )

    return app
