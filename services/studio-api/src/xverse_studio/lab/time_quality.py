from copy import deepcopy
import math


def assess_time_quality(observation: dict, *, target_clock: str, max_uncertainty_ticks: int = 0) -> dict:
    """Expose original timestamps; receipt time never stands in for source time."""
    result = {"clockDomainRef": observation.get("clockDomainRef"), "sourceTick": observation.get("sourceTick"), "recordedAt": observation.get("recordedAt"), "mapping": deepcopy(observation.get("mapping")), "correlation": "unknown", "preciseLatencyAvailable": False, "reasons": []}
    if result["sourceTick"] is None or result["clockDomainRef"] is None:
        result["reasons"] = ["SOURCE_TIME_UNAVAILABLE"]
        return result
    if result["clockDomainRef"] == target_clock:
        result["correlation"] = "same_domain"
        result["preciseLatencyAvailable"] = True
        return result
    mapping = observation.get("mapping")
    if not isinstance(mapping, dict) or mapping.get("admitted") is not True or not mapping.get("mappingId") or not mapping.get("digest") or mapping.get("targetClockDomainRef") != target_clock:
        result["reasons"] = ["CLOCK_MAPPING_UNAVAILABLE"]
        return result
    uncertainty = mapping.get("uncertaintyTicks")
    if not isinstance(uncertainty, (int, float)) or isinstance(uncertainty, bool) or not math.isfinite(uncertainty) or uncertainty < 0:
        result["reasons"] = ["CLOCK_UNCERTAINTY_UNKNOWN"]
        return result
    result["correlation"] = "mapped" if uncertainty <= max_uncertainty_ticks else "uncertain"
    result["preciseLatencyAvailable"] = uncertainty == 0
    if uncertainty > max_uncertainty_ticks:
        result["reasons"] = ["CLOCK_UNCERTAINTY_EXCEEDED"]
    return result
