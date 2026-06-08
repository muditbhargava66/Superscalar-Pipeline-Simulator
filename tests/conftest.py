"""
Pytest configuration for the Superscalar Pipeline Simulator test suite.

Adds the ``src/`` directory to ``sys.path`` so that source modules which use
``from utils.X import Y`` style imports (inside fallback ``except`` blocks or
function bodies) resolve correctly under pytest.

Without this, tests that import ``src.pipeline.hazard_controller`` or
``src.register_file.enhanced_register_renaming`` trigger ``ModuleNotFoundError``
when those modules call ``from utils.instruction_parser import parse_register``
internally — because ``src/`` is not on ``sys.path`` when pytest collects tests.
"""

from pathlib import Path
import sys

_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
