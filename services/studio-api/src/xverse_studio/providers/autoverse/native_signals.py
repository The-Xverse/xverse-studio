"""Fixed public VCU boundary vocabulary; no executable project instructions."""
# Public VCU interfaces in the existing admitted installation. These are host
# implementation constants, never imported project endpoint/command instructions.
SIGNALS = (
    ("driver-throttle", "vehicle/command/acc_pedal_sts", "to-vcu"),
    ("driver-brake", "vehicle/command/brake_pedal_sts", "to-vcu"),
    ("driver-cruise", "vehicle/control/cc_engage_req", "to-vcu"),
    ("driver-reverse", "vehicle/control/reverse_req", "to-vcu"),
    ("vehicle-speed", "vehicle/status/velocity_status", "to-vcu"),
    ("cruise-throttle", "adas/cruise_control/thruttle_req", "to-vcu"),
    ("vcu-cruise-status", "vcu/control/cc_engage_sts", "from-vcu"),
    ("vcu-throttle", "vcu/control/throttle_cmd", "from-vcu"),
    ("vcu-brake", "vcu/control/brake_cmd", "from-vcu"),
    ("vcu-reverse-status", "vcu/control/reverse_sts", "from-vcu"),
    ("vcu-brake-status", "vcu/control/brake_sts", "from-vcu"),
)
OBSERVED = frozenset(("vehicle-speed", "vcu-throttle", "vcu-brake"))
