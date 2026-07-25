from __future__ import annotations

from typing import Any


class PromptBuilder:
    def __init__(self, context: Any, backend: Any) -> None:
        self.context = context
        self.backend = backend

    def to_messages(self) -> Any:
        return self.backend.to_messages(self.context.system, self.context.messages)

    def to_tools(self) -> Any:
        return self.backend.to_tools(self.context.tools)

    def to_api_payload(self, *, max_output_tokens: int = 1024) -> dict[str, Any]:
        return self.backend.to_payload(self.context, max_output_tokens=max_output_tokens)

    @property
    def headers(self) -> dict[str, str]:
        return self.backend.headers

    @property
    def url(self) -> str:
        return self.backend.url
