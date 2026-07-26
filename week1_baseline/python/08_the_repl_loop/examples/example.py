import os
import sys
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(_LIB_DIR))

import boukensha  # noqa: E402

# Config is loaded automatically inside boukensha.repl — system prompt, model,
# and API key all come from ~/.boukensha (or BOUKENSHA_DIR) by default.

_REPO_ROOT = Path(__file__).resolve().parents[4]
os.environ.setdefault("BOUKENSHA_DIR", str(_REPO_ROOT / ".boukensha"))

print(f"Config: {boukensha.config()}")
print()

# The base directory tools will operate relative to -- the step 7 folder makes
# a good playground since it already has source files to read.
base_dir = Path(__file__).resolve().parent.parent.parent / "07_the_run_dsl"


def register_tools(dsl: boukensha.RunDSL) -> None:
    dsl.tool(
        "read_file",
        description="Read the contents of a file from disk",
        parameters={
            "path": {"type": "string", "description": "File path (relative to the working directory)"}
        },
        block=lambda *, path: (base_dir / path).read_text(),
    )

    dsl.tool(
        "list_directory",
        description="List the files in a directory",
        parameters={
            "path": {
                "type": "string",
                "description": "Directory path (relative to the working directory, or '.' for root)",
            }
        },
        block=lambda *, path: ", ".join(
            sorted(f for f in os.listdir(base_dir / path) if not f.startswith("."))
        ),
    )


boukensha.repl(setup=register_tools)
