"""FileSystem registers the standard set of file-oriented tools against a
registry, all sandboxed to a single root directory.

Tools registered:
  pwd              -- return the working directory
  read_file        -- read the full contents of a file
  write_file       -- write (or overwrite) a file
  delete_file      -- delete a file

list_directory and search_files are currently disabled (commented out
below) -- leftover from when this app was a coding harness; the player
agent has no use for them yet.

Every path argument the agent supplies is resolved relative to that root.
If the resolved path would escape the root (path traversal) the tool
returns an error string rather than raising -- so the agent sees it and
can try something sensible instead.

Usage (handled automatically by run()/repl() when working_dir= is set, but
you can call it directly too):

    from boukensha.tools import file_system
    file_system.register(registry, working_dir="/my/project")
"""

from __future__ import annotations

import os
from typing import Any


def register(registry: Any, *, working_dir: str) -> None:
    root = os.path.abspath(working_dir)

    def resolve(path: str) -> str:
        absolute = os.path.normpath(os.path.join(root, str(path)))
        if absolute == root or absolute.startswith(root + os.sep):
            return absolute
        return f"error: path '{path}' escapes the working directory"

    def oops(msg: str) -> str:
        return f"error: {msg}"

    registry.tool(
        "pwd",
        description="Return the working directory — the root that all file paths are relative to.",
        parameters={},
        block=lambda: root,
    )

    # list_directory: disabled for now -- leftover from when this app was a
    # coding harness; the current player agent has no use for it. Kept here
    # so it can be re-registered later if a task needs it.
    #
    # def _list_directory(*, path: str = ".") -> str:
    #     target = resolve(path)
    #     if target.startswith("error:"):
    #         return target
    #     if not os.path.isdir(target):
    #         return oops(f"'{path}' is not a directory")
    #
    #     entries = sorted(os.listdir(target))
    #     entries = [
    #         f"{name}/" if os.path.isdir(os.path.join(target, name)) else name for name in entries
    #     ]
    #     return "(empty)" if not entries else "\n".join(entries)
    #
    # registry.tool(
    #     "list_directory",
    #     description=(
    #         "List files and subdirectories at a path relative to the working directory. "
    #         "Defaults to the working directory itself."
    #     ),
    #     parameters={"path": {"type": "string", "description": "Relative path to list (default '.')"}},
    #     block=_list_directory,
    # )

    def _read_file(*, path: str) -> str:
        target = resolve(path)
        if target.startswith("error:"):
            return target
        if not os.path.isfile(target):
            return oops(f"'{path}' is not a file")
        try:
            with open(target, "r") as f:
                return f.read()
        except Exception as e:
            return oops(str(e))

    registry.tool(
        "read_file",
        description="Read and return the full contents of a file. Path is relative to the working directory.",
        parameters={"path": {"type": "string", "description": "Relative path to the file"}},
        block=_read_file,
    )

    def _write_file(*, path: str, content: str) -> str:
        target = resolve(path)
        if target.startswith("error:"):
            return target
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(content)
            rel = target[len(root) + 1 :] if target.startswith(root + os.sep) else target
            return f"ok: wrote {len(content.encode('utf-8'))} bytes to {rel}"
        except Exception as e:
            return oops(str(e))

    registry.tool(
        "write_file",
        description=(
            "Write content to a file, creating it (and any missing parent directories) if needed, "
            "overwriting if it exists. Path is relative to the working directory."
        ),
        parameters={
            "path": {"type": "string", "description": "Relative path to the file"},
            "content": {"type": "string", "description": "Text content to write"},
        },
        block=_write_file,
    )

    def _delete_file(*, path: str) -> str:
        target = resolve(path)
        if target.startswith("error:"):
            return target
        if not os.path.isfile(target):
            return oops(f"'{path}' is not a file")
        try:
            os.remove(target)
            return f"ok: deleted {path}"
        except Exception as e:
            return oops(str(e))

    registry.tool(
        "delete_file",
        description="Delete a file. Directories are not deleted. Path is relative to the working directory.",
        parameters={"path": {"type": "string", "description": "Relative path to the file to delete"}},
        block=_delete_file,
    )

    # search_files: disabled for now -- same reason as list_directory above.
    #
    # def _search_files(*, pattern: str, path: str = ".", glob: str = "*") -> str:
    #     target = resolve(path)
    #     if target.startswith("error:"):
    #         return target
    #
    #     file_glob = target if os.path.isfile(target) else os.path.join(target, "**", glob)
    #
    #     try:
    #         regex = re.compile(pattern)
    #     except re.error as e:
    #         return oops(f"invalid pattern: {e}")
    #
    #     matches: list[str] = []
    #     for file in sorted(glob_module.glob(file_glob, recursive=True)):
    #         if not os.path.isfile(file):
    #             continue
    #         rel = file[len(root) + 1 :] if file.startswith(root + os.sep) else file
    #         try:
    #             with open(file, "r") as f:
    #                 for lineno, line in enumerate(f, start=1):
    #                     if regex.search(line):
    #                         matches.append(f"{rel}:{lineno}:{line.rstrip(chr(13) + chr(10))}")
    #         except Exception as e:
    #             matches.append(f"{rel}: error reading file: {e}")
    #
    #     return "no matches" if not matches else "\n".join(matches)
    #
    # registry.tool(
    #     "search_files",
    #     description=(
    #         "Search for a text pattern (literal string or regex) across all files in the working "
    #         "directory tree. Returns matching lines in 'path:line_number:content' format."
    #     ),
    #     parameters={
    #         "pattern": {"type": "string", "description": "The text or regex pattern to search for"},
    #         "path": {
    #             "type": "string",
    #             "description": "Subdirectory or file to search within (default '.' = entire working directory)",
    #         },
    #         "glob": {
    #             "type": "string",
    #             "description": "File glob to restrict which files are searched, e.g. '*.py' (default '*')",
    #         },
    #     },
    #     block=_search_files,
    # )
