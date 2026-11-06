"""Bounded actual AT-SPI events/snapshots and XTest keys inside the private session."""

from collections import deque
import faulthandler
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

out = Path(sys.argv[1])
context = json.loads((out / "context.private.json").read_bytes())
assert all(
    os.readlink("/proc/self/ns/" + name) != context[field]
    for name, field in (("mnt", "hostMount"), ("pid", "hostPid"), ("ipc", "hostIpc"))
)
assert os.environ["XDG_RUNTIME_DIR"] == "/run/user/" + str(os.getuid())
assert os.environ["DISPLAY"] == ":71"

# Verify isolation before importing a library that can connect to AT-SPI.
import gi  # noqa: E402
import pyatspi  # noqa: E402

gi.require_version("GLib", "2.0")
from gi.repository import GLib  # noqa: E402 — select GI version before import.

desktop = pyatspi.Registry.getDesktop(0)
web_roots = {}
last_focus = None
x11 = ctypes.CDLL("libX11.so.6")
xtst = ctypes.CDLL("libXtst.so.6")
x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
x11.XOpenDisplay.restype = ctypes.c_void_p
x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
x11.XStringToKeysym.restype = ctypes.c_ulong
x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
x11.XKeysymToKeycode.restype = ctypes.c_uint
x11.XFlush.argtypes = [ctypes.c_void_p]
x11.XkbKeycodeToKeysym.argtypes = [
    ctypes.c_void_p,
    ctypes.c_ubyte,
    ctypes.c_int,
    ctypes.c_int,
]
x11.XkbKeycodeToKeysym.restype = ctypes.c_ulong
xtst.XTestFakeKeyEvent.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_int,
    ctypes.c_ulong,
]
display = x11.XOpenDisplay(None)
assert display
log = (out / "atspi-events.private.jsonl").open("x", buffering=1)
count = 0
dropped = 0
event_errors = 0


def remember_web_root(node):
    name = str(node)
    assert name in web_roots or len(web_roots) < 8
    web_roots[name] = node


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def event(e):
    global count, last_focus, dropped, event_errors
    if count >= 2000:
        dropped += 1
        return
    count += 1
    try:
        row = {
            "type": e.type,
            "name": e.source.name,
            "role": e.source.getRoleName(),
            "detail1": e.detail1,
            "detail2": e.detail2,
            "time": time.monotonic(),
        }
        if row["role"] == "document web":
            remember_web_root(e.source)
        if e.type == "object:state-changed:focused" and e.detail1:
            last_focus = dict(row)
            ancestor = e.source
            for _ in range(30):
                if ancestor is None:
                    break
                if ancestor.getRoleName() == "document web":
                    remember_web_root(ancestor)
                    break
                ancestor = ancestor.parent
        if isinstance(e.any_data, str):
            row["text"] = e.any_data[:2048]
        log.write(json.dumps(row) + "\n")
    except Exception as exc:
        event_errors += 1
        log.write(json.dumps({"error": type(exc).__name__}) + "\n")


pyatspi.Registry.registerEventListener(
    event,
    "object:state-changed:focused",
    "object:state-changed:selected",
    "object:state-changed:checked",
    "object:text-changed",
    "object:property-change:accessible-name",
    "object:children-changed",
    "object:announcement",
    "window:activate",
    "document:load-complete",
)
seen = set()
last_key = None
typed_characters = 0
key_presses = 0
key_releases = 0
input_log = (out / "native-input.private.jsonl").open("x", buffering=1)


def emit(code, pressed):
    global key_presses, key_releases
    assert xtst.XTestFakeKeyEvent(display, code, int(pressed), 0)
    if pressed:
        key_presses += 1
    else:
        key_releases += 1


def named_code(name):
    code = x11.XKeysymToKeycode(display, x11.XStringToKeysym(name.encode()))
    assert code
    return code


def type_ascii(text):
    global typed_characters
    assert isinstance(text, str) and 1 <= len(text) <= 2048
    assert typed_characters + len(text) <= 4096 and all(
        32 <= ord(c) <= 126 for c in text
    )
    strokes = []
    # Inspect only this private X server's existing map. Never remap a key or
    # touch the host keymap; unsupported layouts fail before emitting text.
    for char in text:
        symbol = ord(char)
        code = x11.XKeysymToKeycode(display, symbol)
        assert code
        levels = [x11.XkbKeycodeToKeysym(display, code, 0, n) for n in (0, 1)]
        assert symbol in levels
        strokes.append((code, levels.index(symbol) == 1))
    shift = named_code("Shift_L")
    for code, shifted in strokes:
        if shifted:
            emit(shift, True)
        try:
            emit(code, True)
            emit(code, False)
        finally:
            if shifted:
                emit(shift, False)
        x11.XFlush(display)
        time.sleep(0.002)
    typed_characters += len(text)


def tick():
    global last_key
    key_request = out / "key-request.json"
    if key_request.exists():
        command = json.loads(key_request.read_text())
        if command["id"] != last_key:
            assert type(command["id"]) is int and 1 <= command["id"] <= 1000
            assert command["id"] == (last_key or 0) + 1
            assert set(command) in ({"id", "key"}, {"id", "text"}, {"id", "chord"})
            observation = {"id": command["id"]}
            if "key" in command:
                assert command["key"] in (
                    "Tab",
                    "Return",
                    "Down",
                    "Up",
                    "Escape",
                    "space",
                    "Home",
                )
                code = named_code(command["key"])
                emit(code, True)
                emit(code, False)
                observation["key"] = command["key"]
            elif "chord" in command:
                assert command["chord"] == "Control+a"
                control = named_code("Control_L")
                letter = named_code("a")
                emit(control, True)
                try:
                    emit(letter, True)
                    emit(letter, False)
                finally:
                    emit(control, False)
                observation["chord"] = "Control+a"
            else:
                type_ascii(command["text"])
                observation.update(
                    textCharacters=len(command["text"]),
                    textSha256=hashlib.sha256(command["text"].encode()).hexdigest(),
                )
            x11.XFlush(display)
            last_key = command["id"]
            observation.update(
                keyPresses=key_presses,
                keyReleases=key_releases,
                totalTextCharacters=typed_characters,
            )
            input_log.write(json.dumps(observation) + "\n")
            write_json(out / "key-ack.json", {"id": last_key})
    request = out / "snapshot-request.json"
    if not request.exists():
        return True
    name = json.loads(request.read_text())["name"]
    if name in seen:
        return True
    assert re.fullmatch("[a-z][a-z0-9-]{0,50}", name) and len(seen) < 32
    seen.add(name)
    rows = []
    faulthandler.dump_traceback_later(5, repeat=True)
    # Include web roots received from the real AT-SPI event stream. Chromium's
    # separate renderer subtree is not necessarily present in its native UI
    # cache; these are actual accessible objects, never DOM/CDP substitutes.
    queue = deque([(desktop, 0), *((node, 0) for node in web_roots.values())])
    errors = 0
    limited = 0
    while queue and len(rows) < 5000:
        node, depth = queue.popleft()
        try:
            if len(rows) < 10 or len(rows) % 50 == 0:
                print("Snapshot step", name, len(rows), depth, flush=True)
            state = node.getState()
            rows.append(
                {
                    "name": node.name,
                    "description": node.description,
                    "role": node.getRoleName(),
                    "depth": depth,
                    "pid": node.get_process_id(),
                    "focused": state.contains(pyatspi.STATE_FOCUSED),
                    "editable": state.contains(pyatspi.STATE_EDITABLE),
                    "selected": state.contains(pyatspi.STATE_SELECTED),
                    "checked": state.contains(pyatspi.STATE_CHECKED),
                    "showing": state.contains(pyatspi.STATE_SHOWING),
                    "attributes": node.getAttributes(),
                }
            )
            if rows[-1]["editable"] and rows[-1]["name"] in (
                "Initial conditions (JSON object)",
                "Scenario acceptance intent",
                "Scenario item identifier",
                "Action payload (JSON object)",
                "Scheduled at",
                "XDL source",
                "Sampling intent",
                "Metric acceptance intent",
                "Activation intent",
                "Recovery intent",
                "Fault activation time",
                "Fault duration",
            ):
                text = node.queryText()
                length = text.characterCount
                rows[-1].update(
                    editableTextLength=length,
                    editableTextPrefix=text.getText(0, min(length, 2048)),
                    editableTextTruncated=length > 2048,
                )
                if rows[-1]["name"] == "XDL source" and text.getNSelections():
                    start, end = text.getSelection(0)
                    rows[-1].update(
                        selectedTextStart=start,
                        selectedTextEnd=end,
                        selectedTextPrefix=text.getText(start, min(end, start + 2048)),
                        selectedTextTruncated=end - start > 2048,
                    )
            children = node.childCount
            if depth >= 35 and children:
                limited += 1
            elif depth < 35:
                if children > 1000:
                    limited += 1
                for i in range(min(children, 1000)):
                    if len(rows) + len(queue) >= 5000:
                        limited += 1
                        break
                    queue.append((node.getChildAtIndex(i), depth + 1))
        except Exception:
            errors += 1
    write_json(
        out / (name + ".atspi.private.json"),
        {
            "rows": rows,
            "errors": errors,
            "truncated": bool(queue) or bool(limited),
            "events": count,
            "droppedEvents": dropped,
            "eventErrors": event_errors,
            "lastFocusEvent": last_focus,
            "eventWebRoots": len(web_roots),
        },
    )
    faulthandler.cancel_dump_traceback_later()
    return True


GLib.timeout_add(100, tick)
(out / "atspi-ready.json").write_text(
    json.dumps(
        {
            "desktopRole": desktop.getRoleName(),
            "desktopChildren": desktop.childCount,
            "pid": os.getpid(),
        }
    )
)
pyatspi.Registry.start()
