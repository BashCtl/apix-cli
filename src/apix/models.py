from dataclasses import dataclass
from typing import Any


@dataclass
class ApiResponse:
    status_code: int
    headers: dict[str, str]
    body: Any
    elapsed_ms: float
    size_bytes: int = 0
