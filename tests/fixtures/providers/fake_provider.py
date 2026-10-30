"""Closed synthetic descriptor fixture. Never a native execution provider.

Its input is a captured real enrolled descriptor; no project can select this
class. Every case deliberately violates a v1 admission rule. It has no worker
module, native installation, task factory or process handle.
"""

from copy import deepcopy


CASES = {
    "contract-version": ("contractVersion", "2.0", "PROVIDER_VERSION_INCOMPATIBLE"),
    "implementation": ("implementationDigest", "sha256:invalid", "PROVIDER_DESCRIPTOR_INVALID"),
    "capabilities": ("capabilityRecords", None, "PROVIDER_DESCRIPTOR_INVALID"),
    "limits": ("limits", [], "PROVIDER_DESCRIPTOR_INVALID"),
    "availability": ("available", "false", "PROVIDER_DESCRIPTOR_INVALID"),
    "operations": ("operations", ["stop"], "PROVIDER_DESCRIPTOR_INVALID"),
}


class ManualClock:
    """Synthetic integer ticks only; never host/simulator time or a mapping."""

    def __init__(self):
        self.tick = 0

    def advance(self, amount):
        if type(amount) is not int or not 0 <= amount <= 2**63 - 1 - self.tick:
            raise ValueError("Use a bounded non-negative synthetic tick increment")
        self.tick += amount
        return self.observation()

    def observation(self):
        return {"clockDomain": "synthetic-fixture-clock", "tick": str(self.tick),
                "mapping": "none", "synthetic": True, "executionAllowed": False}


class FakeProvider:
    """Negative admission data with an independently controlled fake clock."""

    execution_allowed = False

    def __init__(self, original_descriptor, case):
        field, value, self.expected_code = CASES[case]
        self.original = deepcopy(original_descriptor)
        self.value = deepcopy(original_descriptor)
        self.value[field] = deepcopy(value)
        self.value["fixtureMetadata"] = {
            "kind": "synthetic_descriptor", "executionAllowed": False,
            "nativeProcessOwnership": "none",
        }
        self.case = case
        self.clock = ManualClock()
        self.lifecycle_calls = 0

    def descriptor(self):
        value = deepcopy(self.value)
        value["fixtureMetadata"]["clock"] = self.clock.observation()
        return value

    def readiness(self, documents, compiled, provider_id, provider, active_count):
        self.lifecycle_calls += 1
        raise AssertionError("Synthetic negative fixture crossed the execution boundary")
