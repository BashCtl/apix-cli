from dataclasses import dataclass, field
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
    body_is_json: bool = False

    @classmethod
    def from_httpx(cls, response: httpx.Response) -> "ApiResponse":
        body_is_json = False
        if not response.content:
            body = None
        else:
            try:
                body = response.json()
                body_is_json = True
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
            body_is_json=body_is_json,
        )


@dataclass
class TestCase:
    __test__ = False

    name: str
    method: str
    url: str
    headers: dict[str, str]
    json: str | None
    json_file: str | None
    expect: dict[str, Any] | None
    timeout: float
    extract: dict[str, str] = field(default_factory=dict)


@dataclass
class TestSuite:
    __test__ = False

    name: str
    tests: list[TestCase]
