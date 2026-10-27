import importlib.util,sys
from pathlib import Path
p=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location("comparison_window_proposal",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import xverse_studio.comparison
xverse_studio.comparison.compare_runs=m.compare_runs
assert Path(m.__file__).resolve()==p.resolve()
import pytest
raise SystemExit(pytest.main(sys.argv[2:]))
