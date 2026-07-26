from __future__ import annotations

import time
from typing import Any

import requests

from .errors import ApiError


class Client:
    RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
    TRANSIENT_ERRORS = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.SSLError,
    )
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 0.5

    def __init__(self, builder: Any) -> None:
        self.builder = builder

    def call(self, *, max_output_tokens: int = 1024, tools: list[Any] | None = None) -> Any:
        url = self.builder.url
        headers = self.builder.headers
        payload = self.builder.to_api_payload(max_output_tokens=max_output_tokens, tools=tools)

        attempts = 0
        response: requests.Response | None = None

        while True:
            attempts += 1

            try:
                response = requests.post(url, json=payload, headers=headers)
            except self.TRANSIENT_ERRORS as e:
                if attempts > self.MAX_RETRIES:
                    raise ApiError(
                        f"API request failed after {attempts} attempts: {type(e).__name__}: {e}"
                    ) from e

                time.sleep(self._retry_delay(attempts))
                continue

            if self._retryable_response(response) and attempts <= self.MAX_RETRIES:
                time.sleep(self._retry_delay(attempts))
                continue

            break

        if not response.ok:
            if response.status_code == 401:
                raise ApiError("authentication failed (401) — check your API key")

            suffix = "" if attempts == 1 else "s"
            raise ApiError(
                f"API request failed after {attempts} attempt{suffix} ({response.status_code}): {response.text}"
            )

        return response.json()

    def _retryable_response(self, response: requests.Response) -> bool:
        return response.status_code in self.RETRYABLE_STATUS_CODES

    def _retry_delay(self, attempt: int) -> float:
        return self.BASE_RETRY_DELAY * (2 ** (attempt - 1))
