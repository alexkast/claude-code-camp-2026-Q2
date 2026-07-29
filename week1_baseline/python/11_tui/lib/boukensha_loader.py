"""Resolves which step folder to load boukensha from, then boots the REPL.

Resolution order:
  1. BOUKENSHA_PATH environment variable (selects which *step* lib to load)
  2. ~/.boukensharc  (a file containing a single path)
  3. The lib/ directory bundled inside this package (the latest release)

Config directory (settings.yaml, .env, system.md) is separate:
  BOUKENSHA_DIR=~/.boukensha  (default, set in env to override)

MUD connection details come from settings.yaml (mud: block) by default.
The legacy MUD_NAME / MUD_HOST / MUD_PORT / MUD_PASSWORD env vars are still
honoured and take precedence over config when set.

Pass --no-tui to fall back to the plain terminal REPL instead of the
Textual-based TUI (the default).

Examples:
  boukensha                                                              # uses bundled lib + ~/.boukensha
  BOUKENSHA_PATH=~/Sites/boukensha/04_api_client boukensha               # loads step 4
  BOUKENSHA_DIR=~/projects/mybot/.boukensha boukensha                    # custom config dir
  boukensha --no-tui                                                    # plain REPL, no Textual
  echo ~/Sites/boukensha/11_tui > ~/.boukensharc && boukensha            # permanent step default
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

# Absolute path to this package's own bundled boukensha lib.
BUNDLED_LIB = Path(__file__).resolve().parent / "boukensha"


def resolve() -> Path:
    # 1. Env var wins.
    env_path = os.environ.get("BOUKENSHA_PATH")
    if env_path:
        step_dir = Path(env_path).expanduser().resolve()
        lib_dir = step_dir / "lib" / "boukensha"
        if (lib_dir / "__init__.py").exists():
            return lib_dir

        sys.exit(
            "boukensha: BOUKENSHA_PATH is set but no lib/boukensha found at:\n"
            f"       {step_dir}\n"
            "       Make sure BOUKENSHA_PATH points to a step folder, e.g.:\n"
            "       BOUKENSHA_PATH=~/Sites/boukensha/python/07_the_run_dsl boukensha"
        )

    # 2. ~/.boukensharc
    rc = Path("~/.boukensharc").expanduser()
    if rc.exists():
        dir_str = rc.read_text().strip()
        if dir_str:
            step_dir = Path(dir_str).expanduser().resolve()
            lib_dir = step_dir / "lib" / "boukensha"
            if (lib_dir / "__init__.py").exists():
                return lib_dir

            sys.exit(
                f"boukensha: ~/.boukensharc points to {dir_str}\n"
                "       but no lib/boukensha was found there.\n"
                "       Update ~/.boukensharc or remove it to use the bundled default."
            )

    # 3. Bundled default.
    return BUNDLED_LIB


def _load_boukensha_package(lib_dir: Path) -> ModuleType:
    # Load the target step's `boukensha` package under a fixed module name,
    # registering it in sys.modules *before* executing it so its own internal
    # relative imports (e.g. `from .config import Config`) resolve against
    # this lib_dir specifically -- not this package's own bundled/editable
    # install of a package with the same name.
    init_file = lib_dir / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "boukensha", init_file, submodule_search_locations=[str(lib_dir)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["boukensha"] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    lib_dir = resolve()
    step_dir = lib_dir.parent.parent

    if os.environ.get("BOUKENSHA_DEBUG"):
        print(f"[boukensha] loading from: {step_dir}")

    module = _load_boukensha_package(lib_dir)

    if not hasattr(module, "repl"):
        sys.exit(
            f"boukensha: the step at {step_dir}\n"
            "       does not support the interactive REPL (added in step 7).\n"
            "       Run its examples directly, e.g.:\n"
            f"         python {step_dir}/examples/example.py\n"
            "       Or point BOUKENSHA_PATH at step 7 or later."
        )

    # --no-tui falls back to the plain terminal REPL (no Textual).
    no_tui = "--no-tui" in sys.argv
    if no_tui:
        sys.argv.remove("--no-tui")

    repl_opts: dict[str, Any] = {"tui": not no_tui}

    if os.environ.get("MUD_NAME"):
        # Legacy env-var override still works and takes precedence over config.
        repl_opts["working_dir"] = False
        password = os.environ.get("MUD_PASSWORD")
        if password is None:
            sys.exit("boukensha: MUD_NAME is set but MUD_PASSWORD is missing.")
        repl_opts["mud"] = {
            "host": os.environ.get("MUD_HOST", "localhost"),
            "port": int(os.environ.get("MUD_PORT", "4000")),
            "name": os.environ["MUD_NAME"],
            "password": password,
        }
    # If MUD_NAME is not set, module.repl() falls back to config.mud_* values
    # automatically (via _mud_opts_from_config inside run_dsl.py).

    module.repl(**repl_opts)


if __name__ == "__main__":
    main()
