import json as jsonlib
import httpx
from unittest.mock import MagicMock

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

def make_fake_response(**kwargs):
    response = MagicMock()
    for name, value in kwargs.items():
        setattr(response, name, value)
    return response

def make_fake_client(monkeypatch, response=None):
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.request.return_value = response
    monkeypatch.setattr("apix.cli.ApiClient", lambda: fake_client)
    return fake_client