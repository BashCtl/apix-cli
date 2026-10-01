from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ApiResponse:
    status_code: int
    headers: dict[str, str]
    body: Any
    elapsed_ms: float
    size_bytes: int = 0

    @classmethod
    def from_httpx(cls, response: httpx.Response) -> "ApiResponse":
        try:
            body = response.json()
        except ValueError:  # empty body or not JSON
            body = response.text
        return cls(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=body,
            elapsed_ms=response.elapsed.total_seconds() * 1000,
            size_bytes=len(response.content),
        )
