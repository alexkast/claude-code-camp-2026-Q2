"""Step 10 -- A Standard Tool Library (MUD demo)

Demonstrates boukensha.tools.mud, which registers gameplay tools against a
live CircleMUD connection. Connection credentials come from
~/.boukensha/settings.yaml (mud: host/port/username/password) by default.
Set BOUKENSHA_DIR to point at a different config directory.

You can still override individual values as keyword arguments:

    python examples/example.py
    BOUKENSHA_DIR=iterations/.boukensha python examples/example.py
"""

import os
import sys
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(_LIB_DIR))

import boukensha  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault("BOUKENSHA_DIR", str(_REPO_ROOT / ".boukensha"))

cfg = boukensha.config()
print(f"Config: {cfg}")
print(f"API key set? {os.environ.get('ANTHROPIC_API_KEY') is not None}")
print()

boukensha.run(
    task=(
        "Connect to the MUD, look at your surroundings, check your score, "
        "then look at the available exits and tell me what you see."
    ),
    # system/model/api_key all come from config automatically
    working_dir=False,  # no filesystem tools needed for MUD play
    # mud: comes from config (settings.yaml mud: block) automatically
)
