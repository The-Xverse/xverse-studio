from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Login(Body):
    bootstrapToken: str = Field(min_length=1, max_length=256)


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


class Import(Body):
    archiveBase64: str = Field(max_length=12 * 1024 * 1024)


class Layout(Body):
    positions: dict[str, dict[str, float]] = Field(default_factory=dict, max_length=200)
    viewport: dict[str, float] | None = None


class Edits(Body):
    baseRevision: int
    edits: list[dict[str, Any]] = Field(min_length=1, max_length=128)


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
    scope: Literal["observe", "stimulate"] = "observe"
    durationSeconds: int = Field(default=30, ge=1, le=300)


class Renewal(Body):
    fencingIdentity: str
    durationSeconds: int = Field(default=30, ge=1, le=300)
