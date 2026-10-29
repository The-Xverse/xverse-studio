import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import xverse_studio.api.advanced as advanced
assert Path(advanced.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
import pytest
raise SystemExit(pytest.main(sys.argv[2:]))
