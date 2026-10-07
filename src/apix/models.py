from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ApiResponse:
    method: str
    url: str
    status_code: int
    headers: dict[str, str]
    body: Any | None
    elapsed_ms: float
    size_bytes: int = 0

    @classmethod
    def from_httpx(cls, response: httpx.Response) -> "ApiResponse":
        if not response.content:
            body = None
        else:
            try:
                body = response.json()
            except ValueError:
                body = response.text

        return cls(
            method=response.request.method,
            url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            body=body,
            elapsed_ms=response.elapsed.total_seconds() * 1000,
            size_bytes=len(response.content),
        )


@dataclass
class TestCase:
    name: str
    method: str
    url: str
    headers: dict[str, str]
    json: str | None
    json_file: str | None
    expect: dict[str, Any] | None
    timeout: float 


@dataclass
class TestSuite:
    name: str
    tests: list[TestCase]
