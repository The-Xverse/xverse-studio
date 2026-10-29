"""In-memory physical-contract double. No IO, discovery, driver or admission."""

from copy import deepcopy
import json
from pathlib import Path

from xverse_studio.lab import LabError


class PhysicalContractFixture:
    provider_id = "physical-contract-fixture"
    asset_id = "fixture:bench-sensor"

    def __init__(self, clock):
        self.clock = clock
        self.assets = json.loads(Path(__file__).with_name("assets.json").read_text())
        self.online = True
        self.held = {}
        self.sequence = 0
        self.calls = []
        self.lose_reserve_ack = False
        self.lose_renew_ack = False
        self.release_observation = {"status": "released"}
        self.stop_observation = {"acknowledged": True}

    def _contact(self, operation):
        self.calls.append(operation)
        if not self.online:
            raise ConnectionError("fixture disconnected")

    def inventory(self):
        self._contact("inventory")
        return deepcopy(self.assets)

    def reserve(self, asset, scope, owner, deadline):
        self._contact("reserve")
        current = self.held.get(asset["assetId"])
        if current and current["expiry"] > self.clock():
            raise LabError("RESOURCE_BUSY")
        self.sequence += 1
        observed = {
            "owner": owner,
            "scope": scope,
            "expiry": deadline,
            "fencingIdentity": f"fixture-fence-{self.sequence}",
            "status": "owned",
        }
        self.held[asset["assetId"]] = observed
        if self.lose_reserve_ack:
            raise ConnectionError("fixture reservation acknowledgement lost")
        return deepcopy(observed)

    def renew(self, reservation, fence, deadline, authority):
        self._contact("renew")
        current = self.held.get(reservation["assetId"])
        if not current or fence != current["fencingIdentity"]:
            raise LabError("STALE_FENCING_IDENTITY")
        current["expiry"] = deadline
        if self.lose_renew_ack:
            raise ConnectionError("fixture renewal acknowledgement lost")
        return deepcopy(current)

    def release(self, reservation, authority):
        self._contact("release")
        current = self.held.get(reservation["assetId"])
        if current and current["fencingIdentity"] != reservation["fencingIdentity"]:
            raise LabError("STALE_FENCING_IDENTITY")
        if self.release_observation.get("status") == "released":
            self.held.pop(reservation["assetId"], None)
        return deepcopy(self.release_observation)

    def inspect_reservation(self, reservation):
        self._contact("inspect")
        return deepcopy(self.held.get(reservation["assetId"], {"status": "unknown"}))

    def stop(self):
        self._contact("stop")
        return deepcopy(self.stop_observation)
