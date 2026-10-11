import json as jsonlib
import httpx
from unittest.mock import MagicMock
import pytest
from types import SimpleNamespace


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


@pytest.fixture
def mocks(monkeypatch):
    m = SimpleNamespace(
        load_yaml=MagicMock(return_value={"raw": True}),
        load_env=MagicMock(return_value={"token": "abc"}),
        resolve_variables=MagicMock(return_value={"resolved": True}),
        parse_test_suite=MagicMock(return_value="suite"),
        run_test_suite=MagicMock(return_value=True),
        formatter=MagicMock(),
    )
    for name in (
        "load_yaml",
        "load_env",
        "resolve_variables",
        "parse_test_suite",
        "run_test_suite",
    ):
        monkeypatch.setattr(f"apix.cli.{name}", getattr(m, name))
    monkeypatch.setattr("apix.cli.Formatter", lambda: m.formatter)
    return m
