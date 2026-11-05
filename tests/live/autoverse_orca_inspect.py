"""Bounded actual AT-SPI events/snapshots and XTest keys inside the private session."""

from collections import deque
import faulthandler
import ctypes
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
    "object:text-changed",
    "object:property-change:accessible-name",
    "object:children-changed",
    "object:announcement",
    "window:activate",
    "document:load-complete",
)
seen = set()
last_key = None


def tick():
    global last_key
    key_request = out / "key-request.json"
    if key_request.exists():
        command = json.loads(key_request.read_text())
        if command["id"] != last_key:
            assert type(command["id"]) is int and 1 <= command["id"] <= 1000
            assert command["id"] == (last_key or 0) + 1
            assert command["key"] in ("Tab", "Return", "Down", "Up", "Escape", "space")
            sym = x11.XStringToKeysym(command["key"].encode())
            code = x11.XKeysymToKeycode(display, sym)
            assert code
            assert xtst.XTestFakeKeyEvent(display, code, 1, 0)
            assert xtst.XTestFakeKeyEvent(display, code, 0, 0)
            x11.XFlush(display)
            last_key = command["id"]
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
                    "selected": state.contains(pyatspi.STATE_SELECTED),
                    "showing": state.contains(pyatspi.STATE_SHOWING),
                    "attributes": node.getAttributes(),
                }
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
