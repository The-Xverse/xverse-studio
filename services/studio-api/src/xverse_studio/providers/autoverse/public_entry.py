"""Diagnostic wrapper around an existing public Python CLI, preserving its argv.

Only the provider's fixed launch vector invokes this module. Thread dumps expose
stalled native dependencies without changing or importing their private classes.
"""
import faulthandler
from pathlib import Path
import runpy
import sys

faulthandler.enable()
faulthandler.dump_traceback_later(30, repeat=True)
entry = Path(sys.argv[1]).resolve(strict=True)
sys.argv = sys.argv[1:]
sys.path.insert(0, str(entry.parent))
runpy.run_path(str(entry), run_name="__main__")
