from __future__ import annotations

from typing import Any

# Static model -> capability table.
#
# context_window is a known *model* fact -- the physical input ceiling -- not
# a value the user sets. The agent looks it up from its configured model id;
# the user never configures it in settings.yaml. Unknown models fall back to
# a conservative default so an unrecognised id can't silently assume a huge
# window.
TABLE: dict[str, dict[str, Any]] = {
    "claude-opus-4-8": {"context_window": 200_000},
    "claude-sonnet-4-6": {"context_window": 200_000},
    "claude-haiku-4-5": {"context_window": 200_000},
}

DEFAULT_CONTEXT_WINDOW = 32_000


def context_window(model: str) -> int:
    info = TABLE.get(str(model))
    return info["context_window"] if info else DEFAULT_CONTEXT_WINDOW
