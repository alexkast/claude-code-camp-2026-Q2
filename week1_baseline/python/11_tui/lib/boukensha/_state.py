from __future__ import annotations

from .config import Config

_debug = False
_config: Config | None = None


def config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def enable_debug() -> None:
    global _debug
    _debug = True


def is_debug() -> bool:
    return _debug
