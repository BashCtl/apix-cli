import json as jsonlib
import httpx


def make_response(
    status_code: int = 200, *, json=None, content: bytes = b"", headers=None
) -> httpx.Response:
    headers = dict(headers or {})
    if json is not None:
        content = jsonlib.dumps(json).encode()
        headers.setdefault("content-type", "application/json")
    return httpx.Response(
        status_code,
        headers=headers,
        stream=httpx.ByteStream(content),
    )
