"""Explicit owned native-window driving check for the platform browser live test."""

import argparse
import ctypes as C
import ctypes.util
import json
from pathlib import Path
import re
import time

import psutil
from xverse_studio.storage.core import canonical, digest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-dir", type=Path, required=True)
parser.add_argument("--run-id", required=True)
args = parser.parse_args()
assert re.fullmatch(r"run-[A-Za-z0-9-]{1,100}", args.run_id)
root = args.data_dir.resolve() / "runs" / args.run_id
assert root.resolve() == root and root.is_dir()
request = json.loads((root / "request.json").read_text())
assert request["runId"] == args.run_id
assert request["snapshot"]["providerIdentity"]["providerId"] == "autoverse.platform"
ready = json.loads((root / "manual-window.private.json").read_text())
owner = json.loads((root / "resources.private.json").read_text())["manual"]
proc = psutil.Process(ready["pid"])
assert ready["pid"] == owner["pid"] and ready["title"] == "Vehicle Manual Control"
x = C.CDLL(ctypes.util.find_library("X11"))
xt = C.CDLL(ctypes.util.find_library("Xtst"))
x.XOpenDisplay.restype = C.c_void_p
x.XOpenDisplay.argtypes = [C.c_char_p]
display = x.XOpenDisplay(None)
assert display
x.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
x.XRaiseWindow.argtypes = [C.c_void_p, C.c_ulong]
x.XGetInputFocus.argtypes = [C.c_void_p, C.POINTER(C.c_ulong), C.POINTER(C.c_int)]
x.XFlush.argtypes = [C.c_void_p]
x.XStringToKeysym.argtypes = [C.c_char_p]
x.XStringToKeysym.restype = C.c_ulong
x.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]
x.XKeysymToKeycode.restype = C.c_uint
xt.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
x.XCloseDisplay.argtypes = [C.c_void_p]


def key(name, pressed):
    assert (
        proc.create_time() == owner["createTime"]
        and digest(proc.cmdline()) == owner["argvDigest"]
    )
    x.XRaiseWindow(display, ready["windowId"])
    x.XSetInputFocus(display, ready["windowId"], 2, 0)
    x.XFlush(display)
    actual, revert = C.c_ulong(), C.c_int()
    x.XGetInputFocus(display, C.byref(actual), C.byref(revert))
    assert actual.value == ready["windowId"]
    code = x.XKeysymToKeycode(display, x.XStringToKeysym(name.encode()))
    assert code and xt.XTestFakeKeyEvent(display, code, int(pressed), 0)
    x.XFlush(display)


def state():
    return json.loads((root / "state.json").read_text())


report = {
    "scope": "actual owned native simulation window; source telemetry distinct from native Argus observations",
    "outcome": "failed",
}
try:
    key("w", True)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            time.sleep(0.3)
            speed = state()["inputTelemetry"]["items"]["speed"]["value"]
            if speed is not None and speed > 15:
                break
        assert speed > 12, speed
        report["actualKeyboardSpeed"] = speed
    finally:
        key("w", False)
    key("c", True)
    try:
        time.sleep(0.15)
    finally:
        key("c", False)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if state()["inputTelemetry"]["items"]["cruiseEngaged"]["value"] is True:
            break
        time.sleep(0.3)
    assert state()["inputTelemetry"]["items"]["cruiseEngaged"]["value"] is True
    report["cruiseEngaged"] = True
    key("s", True)
    try:
        time.sleep(2)
    finally:
        key("s", False)
    report["outcome"] = "passed"
    print("ACTUAL_OWNED_PYGAME_DRIVING_AND_CRUISE_PASS", flush=True)
finally:
    x.XCloseDisplay(display)
    (args.data_dir / "keyboard-verification.json").write_text(canonical(report))
