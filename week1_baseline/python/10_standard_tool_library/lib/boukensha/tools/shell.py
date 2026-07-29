"""Shell registers command-execution tools against a registry.

Tools registered:
  run_command  -- run an arbitrary shell command inside the working directory

Options:
  working_dir:  (required) all commands run with this as their cwd
  timeout:      seconds before a command is killed (default 30)
  allowed_commands: optional list of allowed executable names (e.g. ["python", "git"]).
                When None (the default) all commands are permitted.
                When set, any command whose first token is not in the list
                is rejected before execution.

Usage (handled automatically by run()/repl() when working_dir= is set):

    from boukensha.tools import shell
    shell.register(registry, working_dir="/my/project", allowed_commands=["python", "git"])
"""

from __future__ import annotations

import os
import subprocess
from typing import Any


def register(
    registry: Any,
    *,
    working_dir: str,
    timeout: float = 30,
    allowed_commands: list[str] | None = None,
) -> None:
    root = os.path.abspath(working_dir)

    def oops(msg: str) -> str:
        return f"error: {msg}"

    allowed_note = f" Allowed executables: {', '.join(allowed_commands)}." if allowed_commands else ""

    def _run_command(*, command: str) -> str:
        if allowed_commands:
            executable = command.strip().split()[0] if command.strip() else ""
            if executable not in [str(c) for c in allowed_commands]:
                return oops(
                    f"'{executable}' is not in the allowed-commands list ({', '.join(allowed_commands)})"
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return oops(f"command timed out after {timeout}s: {command}")
        except OSError as e:
            return oops(f"command not found: {e}")
        except Exception as e:
            return oops(str(e))

        exit_note = "" if result.returncode == 0 else f"\n[exit {result.returncode}]"
        output = (result.stdout + result.stderr).strip()
        return f"(no output){exit_note}" if not output else f"{output}{exit_note}"

    registry.tool(
        "run_command",
        description=(
            "Run a shell command inside the working directory and return its combined "
            f"stdout+stderr output. Commands run with a {timeout}-second timeout.{allowed_note}"
        ),
        parameters={
            "command": {
                "type": "string",
                "description": "The shell command to execute (e.g. 'python script.py', 'ls -la', 'git status')",
            }
        },
        block=_run_command,
    )
