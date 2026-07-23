from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    # The .boukensha config directory is resolved in this order:
    #   1. BOUKENSHA_DIR environment variable (set before loading .env)
    #   2. ~/.boukensha  (default)
    DEFAULT_DIR: str = str(Path.home() / ".boukensha")

    def __init__(self) -> None:
        self.dir: str = self._resolve_dir()
        self._load_env()
        self.settings: dict[str, Any] = self._load_settings()

    # ---------- tasks -----------------------------------------------------

    # With no argument: returns the full tasks dict from settings.yaml.
    # With a name: returns that task's settings dict, e.g. tasks("player").
    def tasks(self, name: str | None = None) -> dict[str, Any] | None:
        all_tasks: dict[str, Any] = self.dig("tasks") or {}
        return all_tasks.get(name) if name is not None else all_tasks

    # The user's prompts directory for task prompt overrides.
    def user_prompts_dir(self) -> str:
        return str(Path(self.dir) / "prompts")

    # ---------- MUD connection --------------------------------------------

    def mud_host(self) -> str:
        return self.dig("mud", "host") or "localhost"

    def mud_port(self) -> int:
        return self.dig("mud", "port") or 4000

    def mud_username(self) -> str | None:
        return self.dig("mud", "username")

    def mud_password(self) -> str | None:
        return self.dig("mud", "password")

    # ---------- low-level helpers -----------------------------------------

    # Fetch a nested key path from settings, e.g. dig("mud", "host")
    def dig(self, *keys: str) -> Any:
        node: Any = self.settings
        for key in keys:
            if isinstance(node, dict):
                node = node.get(key)
            else:
                return None
        return node

    def __str__(self) -> str:
        return f"#<Boukensha::Config dir={self.dir} tasks={','.join(self.tasks().keys())}>"

    def __repr__(self) -> str:
        return str(self)

    def _resolve_dir(self) -> str:
        raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
        return str(Path(raw).expanduser().resolve())

    def _load_env(self) -> None:
        env_file = Path(self.dir) / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    def _load_settings(self) -> dict[str, Any]:
        settings_file = Path(self.dir) / "settings.yaml"
        if settings_file.exists():
            return yaml.safe_load(settings_file.read_text()) or {}
        return {}
