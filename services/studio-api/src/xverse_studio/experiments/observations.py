"""Pure selected-provider observation declarations and exact-unit budget checks."""

from copy import deepcopy
from decimal import Decimal

from pydantic import Field, ValidationError, model_validator
from ruamel.yaml import YAML

from xverse_studio.security.models import Body
from xverse_studio.lab.assets import public_text

MAX_ROWS = 32
MAX_QUANTITY = 10**15


class Quantity(Body):
    value: int | float = Field(ge=0, le=MAX_QUANTITY)
    unit: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9._/-]{0,63}$")


class Budget(Body):
    maximum: int | float = Field(ge=0, le=MAX_QUANTITY)
    unit: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9._/-]{0,63}$")


class Observer(Body):
    observerId: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", max_length=63)
    costs: list[Quantity] | None = Field(default=None, max_length=8)
    intrusiveness: str | None = Field(default=None, min_length=1, max_length=256)
    retention: str | None = Field(default=None, min_length=1, max_length=256)

    @model_validator(mode="after")
    def unique_units(self):
        units = [c.unit for c in self.costs or []]
        if len(units) != len(set(units)):
            raise ValueError("Ambiguous cost units")
        return self


class Contract(Body):
    contractVersion: str = Field(pattern=r"^1\.0$")
    observers: list[Observer] = Field(max_length=32)
    budgets: list[Budget] = Field(max_length=8)

    @model_validator(mode="after")
    def unique_names(self):
        ids = [v.observerId for v in self.observers]
        units = [v.unit for v in self.budgets]
        if len(ids) != len(set(ids)) or len(units) != len(set(units)):
            raise ValueError("Ambiguous observation declarations")
        return self


def text(value):
    if value is None:
        return {"status": "not_declared", "value": None}
    shown = public_text(value)
    return {"status": "declared" if shown is not None else "withheld", "value": shown}


def selected_scenario(documents, compiled):
    if compiled.get("valid") is not True:
        return None
    selected = compiled["selection"]["scenarioRef"]
    for raw in documents.values():
        value = YAML(typ="safe").load(raw)
        if value["kind"] == "Scenario":
            ref = f"xdl://{value['metadata']['namespace']}/scenario/{value['metadata']['name']}"
            if ref == selected:
                return value
    return None


def observation_admission(scenario, provider):
    if scenario is None:
        return {
            "observationAdmissionVersion": "1.0",
            "status": "unavailable",
            "items": [],
            "itemsComplete": False,
            "observerCount": None,
            "maxObservers": (provider or {}).get("limits", {}).get("maxObservers"),
            "budgets": [],
            "diagnostics": [
                {
                    "code": "OBSERVATION_SOURCE_UNAVAILABLE",
                    "severity": "error",
                    "message": "No validated selected Scenario is available for observation admission; no zero-cost assumption is made.",
                }
            ],
            "limitations": [
                "Unknown source cannot establish observation counts, costs or budgets."
            ],
        }
    observers = (scenario or {}).get("spec", {}).get("observers", [])
    diagnostics = []
    contract = None

    def reject(code, message):
        diagnostics.append({"code": code, "severity": "error", "message": message})

    declared = (provider or {}).get("observationContracts")
    if declared is not None:
        try:
            contract = Contract.model_validate(declared)
        except (ValidationError, ValueError, TypeError):
            reject(
                "OBSERVATION_CONTRACT_UNSUPPORTED",
                "The provider observation contract is invalid, ambiguous or unsupported.",
            )
    limit = (provider or {}).get("limits", {}).get("maxObservers")
    if limit is not None:
        if type(limit) is not int or limit < 0:
            reject(
                "OBSERVATION_CONTRACT_UNSUPPORTED",
                "The provider observation-count bound must be a nonnegative integer.",
            )
        elif len(observers) > limit:
            reject(
                "OBSERVATION_LIMIT",
                "The selected Scenario exceeds the provider observation-count bound.",
            )
    entries = {v.observerId: v for v in contract.observers} if contract else {}
    budgets = []
    for budget in contract.budgets if contract else []:
        quantities = []
        missing = False
        for observer in observers:
            entry = entries.get(observer["id"])
            cost = (
                next((v for v in entry.costs or [] if v.unit == budget.unit), None)
                if entry
                else None
            )
            if cost is None:
                missing = True
            else:
                quantities.append(Decimal(str(cost.value)))
        total = None if missing else sum(quantities, Decimal(0))
        status = (
            "unknown"
            if missing
            else "exceeded"
            if total > Decimal(str(budget.maximum))
            else "satisfied"
        )
        budgets.append(
            {
                "unit": budget.unit,
                "maximum": budget.maximum,
                "total": None
                if total is None
                else int(total)
                if total == int(total)
                else float(total),
                "status": status,
            }
        )
        if status == "unknown":
            reject(
                "OBSERVATION_COST_UNRESOLVED",
                "A selected observer has no declared cost in a budgeted unit; missing cost is not zero.",
            )
        elif status == "exceeded":
            reject(
                "OBSERVATION_BUDGET_EXCEEDED",
                "The selected observers exceed a declared provider cost budget.",
            )
    items = []
    for observer in observers[:MAX_ROWS]:
        entry = entries.get(observer["id"])
        items.append(
            {
                "observerId": observer["id"],
                "targetRef": deepcopy(observer.get("targetRef")),
                "clockDomain": observer.get("timeDomainId"),
                "sampling": text(observer.get("samplingIntent")),
                "units": text(observer.get("unitSemantics")),
                "payloadSchema": text(observer.get("payloadSchema")),
                "evidenceSink": text(observer.get("evidenceSinkRef")),
                "intrusiveness": text(entry.intrusiveness if entry else None),
                "retention": text(entry.retention if entry else None),
                "resourceCost": {
                    "status": "declared" if entry and entry.costs else "not_declared",
                    "quantities": [c.model_dump() for c in entry.costs or []]
                    if entry
                    else [],
                },
            }
        )
    return {
        "observationAdmissionVersion": "1.0",
        "status": "blocked"
        if diagnostics
        else "checked"
        if contract
        else "not_declared",
        "items": items,
        "itemsComplete": len(observers) <= MAX_ROWS,
        "observerCount": len(observers),
        "maxObservers": limit,
        "budgets": budgets,
        "diagnostics": diagnostics,
        "limitations": [
            "Only declared cost dimensions are counted; undeclared CPU, memory, retention and timing costs remain unknown.",
            "Costs and intrusiveness are provider declarations, not measured effects or execution authority. No unit conversion is inferred.",
        ],
    }
