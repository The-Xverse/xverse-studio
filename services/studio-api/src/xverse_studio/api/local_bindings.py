"""Authenticated project-local declaration routes; no provider operations."""

from fastapi import Request, Response

from xverse_studio.projects.local_bindings import LocalBindings, LocalBindingsUpdate, LocalBindingsView


def install_local_bindings(app, store, revision):
    service = LocalBindings(store)
    app.state.studio.local_bindings = service

    @app.get("/api/v1/projects/{projectId}/local-bindings", response_model=LocalBindingsView)
    def local_bindings(projectId: str, response: Response):
        result = service.read(projectId)
        response.headers["ETag"] = f'"{result["bindingRevision"]}"'
        return result

    @app.put("/api/v1/projects/{projectId}/local-bindings", response_model=LocalBindingsView)
    def save_local_bindings(projectId: str, body: LocalBindingsUpdate, request: Request, response: Response):
        result = service.save(projectId, revision(request), body)
        response.headers["ETag"] = f'"{result["bindingRevision"]}"'
        return result
