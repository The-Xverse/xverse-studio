"""Versioned inert catalog/profile admission and authored deployment composition."""
from fastapi import Query, Request, Response
from pydantic import Field

from xverse_studio.api.models import Body
from xverse_studio.catalog import ArtifactRegistration, Catalog
from xverse_studio.deployments import Deployments
from xverse_studio.profiles import ProfileRegistry
from xverse_studio.storage.core import Problem


class ProfileLock(Body):
    profileId: str = Field(min_length=1, max_length=253)
    version: str = Field(min_length=1, max_length=64)
    schemaDigest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    presentationDigest: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")


class ProfileBindings(Body):
    baseRevision: int = Field(ge=1)
    profiles: list[ProfileLock] = Field(min_length=1, max_length=16)


class VariantCreate(Body):
    baseRevision: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    sourceDeploymentId: str | None = Field(default=None, max_length=100)
    sourceScenarioId: str | None = Field(default=None, max_length=100)


class BindingUpdate(Body):
    baseRevision: int = Field(ge=1)
    bindingId: str = Field(min_length=1, max_length=63)
    targetId: str | None = Field(default=None, max_length=63)
    realizationClass: str | None = Field(default=None, max_length=32)
    artifactIds: list[str] | None = Field(default=None, max_length=32)
    resourceIds: list[str] | None = Field(default=None, max_length=32)
    scenarioRef: str | None = Field(default=None, max_length=512)


def _expected(request, base_revision):
    value = request.headers.get("if-match")
    if value is None:
        raise Problem("REVISION_REQUIRED", "Supply If-Match for the current authored project revision.", 428)
    try:
        revision = int(value.strip('"'))
    except ValueError:
        raise Problem("REVISION_INVALID", "If-Match must identify the numeric project revision.") from None
    if revision != base_revision:
        raise Problem("REVISION_CONFLICT", "If-Match and baseRevision must agree.", 412)
    return revision


def install_composition(app, store, projects, runs, adapter):
    def configuration_for(provider_id, provider, documents, compiled):
        # Static source mapping only. This authoring preview cannot contact
        # readiness resources or acquire execution authority.
        from xverse_studio.xdl import reference_configuration, XDLRejected

        if provider.get("available") is not True or provider.get("hostCompatible") is not True:
            raise XDLRejected("The selected provider is unavailable for configuration inspection.", "PROVIDER_UNAVAILABLE")
        installed = runs.installed_providers.get(provider_id)
        if installed is None:
            return reference_configuration(documents, compiled)
        mapping = getattr(installed, "configuration", None)
        configuration = mapping(documents, compiled) if callable(mapping) else None
        if not isinstance(configuration, dict):
            raise XDLRejected("The selected provider does not admit these authored inputs.", "PROVIDER_SOURCE_UNSUPPORTED")
        return configuration

    catalog, profiles, deployments = Catalog(store), ProfileRegistry(adapter), Deployments(
        projects, adapter, descriptor_source=runs.provider_descriptors, configuration_for=configuration_for)
    app.state.studio.catalog = catalog
    app.state.studio.profiles = profiles
    app.state.studio.deployments = deployments

    from xverse_studio.experiments.admission import ScenarioAdmission
    scenario_admission = ScenarioAdmission(projects, adapter, runs.provider_descriptors, configuration_for)

    @app.get("/api/v1/projects/{projectId}/scenario-admission")
    def inspect_scenario(projectId: str, request: Request,
                         revision: int = Query(ge=1, le=9007199254740991),
                         providerId: str = Query(min_length=1, max_length=128),
                         scenarioRef: str | None = Query(None, min_length=1, max_length=512)):
        allowed = {"revision", "providerId", "scenarioRef"}
        if any(k not in allowed or len(request.query_params.getlist(k)) != 1 for k in request.query_params):
            raise Problem("SCENARIO_QUERY_INVALID", "Use each supported scenario-inspection query field once.", 422)
        return scenario_admission.inspect(projectId, revision, providerId, scenarioRef)

    @app.get("/api/v1/catalog")
    def catalog_entries(kind: str | None = None, role: str | None = None, profile: str | None = None,
                        interface: str | None = None, providerId: str | None = None, query: str | None = None,
                        cursor: str | None = None, limit: int = 200):
        return catalog.list(kind=kind, role=role, profile=profile, interface=interface, providerId=providerId, query=query, cursor=cursor, limit=limit)

    @app.post("/api/v1/catalog/artifacts", status_code=201)
    def register_artifact(body: ArtifactRegistration, request: Request):
        return catalog.register(body.model_dump(), request.state.principal, request.headers.get("idempotency-key"))

    @app.get("/api/v1/catalog/{entryId}")
    def catalog_entry(entryId: str):
        return catalog.get(entryId)

    @app.get("/api/v1/profiles")
    def profile_entries():
        return profiles.list()

    @app.get("/api/v1/profiles/{profileId}")
    def profile_entry(profileId: str):
        return {k: v for k, v in profiles.get(profileId).items() if k != "schemaText"}

    @app.post("/api/v1/projects/{projectId}/profile-bindings")
    def profile_bindings(projectId: str, body: ProfileBindings, request: Request, response: Response):
        project = profiles.bind(projects, projectId, _expected(request, body.baseRevision), [lock.model_dump() for lock in body.profiles])
        response.headers["ETag"] = f'"{project["revision"]}"'
        return project

    @app.get("/api/v1/projects/{projectId}/deployment-variants")
    def list_variants(projectId: str):
        return deployments.list(projectId)

    @app.get("/api/v1/projects/{projectId}/deployment-variants/{documentId}/resolution")
    def variant_resolution(projectId: str, documentId: str, providerId: str = Query("studio.reference", max_length=128),
                           revision: int | None = Query(None, ge=1, le=9007199254740991)):
        return deployments.resolution(projectId, documentId, providerId, revision=revision)

    @app.get("/api/v1/projects/{projectId}/deployment-variants/{documentId}/comparison")
    def variant_comparison(projectId: str, documentId: str,
                           otherDocumentId: str = Query(min_length=1, max_length=128),
                           revision: int = Query(ge=1, le=9007199254740991),
                           providerId: str = Query("studio.reference", max_length=128)):
        return deployments.comparison(projectId, documentId, otherDocumentId, revision, providerId)

    @app.post("/api/v1/projects/{projectId}/deployment-variants", status_code=201)
    def create_variant(projectId: str, body: VariantCreate, request: Request, response: Response):
        result = deployments.create(projectId, _expected(request, body.baseRevision), body.model_dump(exclude={"baseRevision"}, exclude_none=True))
        response.headers["ETag"] = f'"{result["project"]["revision"]}"'
        return result

    @app.patch("/api/v1/projects/{projectId}/deployment-variants/{documentId}")
    def update_binding(projectId: str, documentId: str, body: BindingUpdate, request: Request, response: Response,
                       providerId: str = Query("studio.reference", max_length=128)):
        result = deployments.update_binding(projectId, _expected(request, body.baseRevision), documentId,
                                            body.model_dump(exclude={"baseRevision"}, exclude_none=True), providerId)
        response.headers["ETag"] = f'"{result["project"]["revision"]}"'
        return result
