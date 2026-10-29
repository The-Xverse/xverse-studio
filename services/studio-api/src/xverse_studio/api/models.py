from typing import Any, Literal
import json

from pydantic import Field, field_validator

from xverse_studio.security.models import Body  # The strict base lives below the API layer.


class Login(Body):
    bootstrapToken: str = Field(min_length=1, max_length=256)


class ProbeRequest(Body):
    expectedBindingDigest: str = Field(pattern=r'^sha256:[a-f0-9]{64}$')
    scope: Literal['observe'] = 'observe'


class NewProject(Body):
    name: str = Field(min_length=1, max_length=120)
    blueprintRef: str | None = None


class Document(Body):
    content: str = Field(max_length=1024 * 1024)
    format: Literal["yaml", "json"] = "yaml"


class Selection(Body):
    systemRef: str | None = None
    revision: int = Field(ge=1)
    deploymentRef: str | None = None
    scenarioRef: str | None = None
    providerId: str = "studio.reference"


class Start(Body):
    snapshotId: str = Field(max_length=80)
    preflightId: str = Field(max_length=80)


class Command(Body):
    kind: Literal[
        "stop",
        "cancel",
        "pause",
        "resume",
        "step",
        "reset",
        "set_parameter",
        "activate_fault",
        "recover_fault",
    ]
    expectedStateVersion: int = Field(ge=0)
    parameters: dict[str, Any] = Field(default_factory=dict, max_length=32)

    @field_validator("parameters")
    @classmethod
    def canonical_parameters(cls, value):
        # allow_inf_nan=False does not inspect Any-valued nested parameters.
        # Validate before run lookup/idempotency hashing without normalizing
        # opaque, otherwise valid JSON or accepting a nonfinite fingerprint.
        try:
            json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, RecursionError) as error:
            raise ValueError("Command parameters require finite UTF-8 JSON values.") from error
        return value


class Import(Body):
    archiveBase64: str = Field(max_length=12 * 1024 * 1024)


class Layout(Body):
    positions: dict[str, dict[str, float]] = Field(default_factory=dict, max_length=200)
    viewport: dict[str, float] | None = None


class Edits(Body):
    baseRevision: int
    edits: list[dict[str, Any]] = Field(min_length=1, max_length=128)


class Recovery(Body):
    expectedRevision: int
    action: Literal["adopt_external", "restore_revision"]
    revision: int | None = Field(default=None, ge=1)


class Export(Body):
    revision: int
    inclusionPolicy: Literal["project"] = "project"


class Campaign(Body):
    snapshotId: str
    matrix: dict[str, list[Any]] = Field(max_length=16)
    budget: dict[str, Any]
    concurrency: int = 1
    stopPolicy: Literal["continue", "stop_on_failure"] = "continue"


class Evaluation(Body):
    snapshotId: str
    definitionRef: str
    definitionDigest: str
    evidenceRefs: list[str] = Field(max_length=32)


class Annotation(Body):
    kind: Literal["comment", "trace_link"] = "comment"
    text: str = Field(default="", max_length=4096)
    target: dict[str, Any] | None = None
    elementRefs: list[str] = Field(default_factory=list, max_length=32)
    evidenceRefs: list[str] = Field(default_factory=list, max_length=32)
    definitionRefs: list[dict[str, str]] = Field(default_factory=list, max_length=32)


class AnnotationUpdate(Annotation):
    revision: int


class Retention(Body):
    runIds: list[str] = Field(default_factory=list, max_length=128)
    projectIds: list[str] = Field(default_factory=list, max_length=128)
    artifactIds: list[str] = Field(default_factory=list, max_length=128)
    rule: Literal["explicit"] = "explicit"


class RetentionApply(Body):
    fingerprint: str


class Reservation(Body):
    scope: Literal["observe", "stimulate", "destructive"] = "observe"
    durationSeconds: int = Field(default=30, ge=1, le=300)


class Renewal(Body):
    fencingIdentity: str = Field(min_length=1, max_length=256)
    durationSeconds: int = Field(default=30, ge=1, le=300)
