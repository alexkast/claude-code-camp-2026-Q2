from __future__ import annotations

from .config import Config

_quiet = False
_debug = False
_config: Config | None = None


def config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def enable_quiet() -> None:
    global _quiet
    _quiet = True


def disable_quiet() -> None:
    global _quiet
    _quiet = False


def is_quiet() -> bool:
    return _quiet


def enable_debug() -> None:
    global _debug
    _debug = True


def is_debug() -> bool:
    return _debug
