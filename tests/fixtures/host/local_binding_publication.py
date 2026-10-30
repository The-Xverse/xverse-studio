"""Owned native timing gate only; no replacement lifecycle or provider outcomes."""

import argparse
from pathlib import Path
import os
import sqlite3
import sys
import time

import psutil

from xverse_studio.storage.core import atomic, canonical, digest

parser = argparse.ArgumentParser()
parser.add_argument("--data-dir", type=Path, required=True)
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--witness", type=Path, required=True)
parser.add_argument("--lane", choices=["before-head", "after-commit"], required=True)
args = parser.parse_args()
if not args.data_dir.name.startswith("binding-owner-") or args.witness.parent != args.data_dir.parent:
    parser.error("An explicitly owned binding publication fixture root and sibling witness are required.")


def hold():
    process = psutil.Process()
    atomic(args.witness, canonical({"scope": "owned native SQLite binding publication; no provider contact",
        "pid": os.getpid(), "birth": process.create_time(), "uid": os.getuid(),
        "argvDigest": digest(process.cmdline()), "lane": args.lane}).encode())
    # The parent proves ownership then kills this original backend. Never
    # synthesize a commit or return a fake successful save after the gate.
    time.sleep(30)
    raise RuntimeError("Owned publication fault gate was not interrupted")


connect = sqlite3.connect


class PublicationConnection(sqlite3.Connection):
    binding_write = False

    def execute(self, sql, parameters=(), /):
        if sql.startswith("INSERT INTO records") and parameters and parameters[0] == "project_local_bindings":
            if args.lane == "before-head":
                hold()
            self.binding_write = True
        return super().execute(sql, parameters)

    def commit(self):
        result = super().commit()
        if self.binding_write and args.lane == "after-commit":
            hold()
        return result


sqlite3.connect = lambda *a, **kw: connect(*a, factory=PublicationConnection, **kw)
sys.argv = [sys.argv[0], "--data-dir", str(args.data_dir), "--port", str(args.port)]

def launch():
    # Install the timing gate before importing the native application.
    from xverse_studio.host.launcher import main
    main()


launch()
