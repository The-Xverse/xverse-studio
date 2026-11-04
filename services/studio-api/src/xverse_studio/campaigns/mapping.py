"""Closed installed campaign parameters; pure source callbacks grant no authority."""

from copy import deepcopy

from xverse_studio.storage.core import Problem
from .planner import CampaignPlanner, _finite_number


def rejected(message):
    return Problem("ADMISSION_REJECTED", message)


class InstalledCampaign:
    def __init__(self, snapshot, provider, descriptor):
        frozen = snapshot.get("providerIdentity", {})
        contract = frozen.get("campaignContract")
        if (
            not isinstance(contract, dict)
            or descriptor.get("available") is not True
            or descriptor.get("hostCompatible") is not True
            or frozen != descriptor
            or snapshot.get("providerId") != descriptor.get("providerId")
            or not callable(getattr(provider, "campaign_documents", None))
        ):
            raise rejected(
                "This frozen provider has no current admitted campaign mapping; obtain a new ready preflight for a supported provider."
            )
        expected = {
            "contractVersion",
            "parameters",
            "durationParameter",
            "maxConcurrency",
            "seedPolicy",
        }
        parameters = contract.get("parameters")
        if (
            set(contract) != expected
            or contract["contractVersion"] != "1.0"
            or contract["seedPolicy"] != "unsupported"
            or not isinstance(parameters, dict)
            or not 1 <= len(parameters) <= 8
            or type(contract["maxConcurrency"]) is not int
            or contract["maxConcurrency"] != 1
            or descriptor["limits"]["maxConcurrentRuns"] < 1
            or not isinstance(contract["durationParameter"], str)
            or contract["durationParameter"] not in parameters
        ):
            raise rejected("The installed campaign contract is unsupported.")
        for name, rule in parameters.items():
            if (
                not isinstance(name, str)
                or not isinstance(rule, dict)
                or set(rule) != {"type", "minimum", "maximum", "unit"}
                or not isinstance(rule["type"], str)
                or rule["type"] not in {"integer", "number"}
                or not _finite_number(rule["minimum"])
                or not _finite_number(rule["maximum"])
                or rule["minimum"] > rule["maximum"]
                or not isinstance(rule["unit"], str)
            ):
                raise rejected(
                    "The installed campaign parameter schema is unsupported."
                )
        duration = parameters[contract["durationParameter"]]
        if (
            duration["unit"] != "s"
            or duration["minimum"] <= 0
            or duration["maximum"] > descriptor["limits"]["maxDurationSeconds"]
        ):
            raise rejected(
                "The campaign duration must fit the admitted provider limit in seconds."
            )
        self.provider = provider
        self.contract = deepcopy(contract)
        self.snapshot = deepcopy(snapshot)
        self.value(
            contract["durationParameter"],
            snapshot.get("configuration", {}).get(contract["durationParameter"]),
        )

    def value(self, name, value):
        rule = self.contract["parameters"].get(name)
        if (
            rule is None
            or not _finite_number(value)
            or (rule["type"] == "integer" and type(value) is not int)
            or not rule["minimum"] <= value <= rule["maximum"]
        ):
            raise Problem(
                "INVALID_PARAMETER",
                "Campaign axes and values must fit the frozen provider parameter contract; unsupported seeds cannot be applied.",
            )

    def preview(self, matrix, *, budget, concurrency, stop_policy):
        for name, values in matrix.items():
            if name not in self.contract["parameters"]:
                raise Problem(
                    "INVALID_MATRIX",
                    "This parameter or seed is not admitted by the frozen provider campaign contract.",
                )
            for value in values:
                self.value(name, value)
        duration = self.contract["durationParameter"]
        maximum = max(matrix.get(duration, [self.snapshot["configuration"][duration]]))
        return CampaignPlanner(
            max_children=32,
            max_concurrency=self.contract["maxConcurrency"],
            allowed_parameters=set(self.contract["parameters"]),
        ).preview(
            self.snapshot,
            matrix,
            budget=budget,
            concurrency=concurrency,
            duration_seconds=maximum,
            stop_policy=stop_policy,
        )

    def documents(self, parameters):
        for name, value in parameters.items():
            self.value(name, value)
        sources = self.provider.campaign_documents(
            deepcopy(self.snapshot["documents"]), deepcopy(parameters)
        )
        if (
            not isinstance(sources, dict)
            or set(sources) != set(self.snapshot["documents"])
            or any(not isinstance(value, str) for value in sources.values())
        ):
            raise rejected(
                "The installed campaign mapping changed the source document set."
            )
        return sources
