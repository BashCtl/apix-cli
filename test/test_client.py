# tests/test_client.py
import json

import httpx
import pytest
from apix.models import ApiResponse
from conftest import make_response
from apix.client import ApiClient
from apix.errors import (
    ApiError,
    ConnectionFailedError,
    InvalidUrlError,
    RequestTimeoutError,
    UnsupportedHttpMethodError,
)

URL = "https://api.example.com/items"


@pytest.fixture
def make_api():
    """Build an ApiClient whose transport is the given handler."""
    created = []

    def _make(handler) -> ApiClient:
        api = ApiClient(client=httpx.Client(transport=httpx.MockTransport(handler)))
        created.append(api)
        return api

    yield _make
    for api in created:
        api.close()


def ok(request: httpx.Request) -> httpx.Response:
    return make_response(200, json={"ok": True})


def test_get_returns_api_response(make_api):
    api = make_api(ok)
    result = api.request("GET", URL)

    assert result is not None
    assert isinstance(result, ApiResponse)
    assert result.status_code == 200
    assert result.method == "GET"
    assert result.headers == {"content-type": "application/json"}
    assert result.elapsed_ms <=  0.65
    assert result.url == URL
    assert result.size_bytes == 12
    assert result.body == {"ok": True}


@pytest.mark.parametrize("method", ["get", "Get", "POST", "put", "patch", "delete"])
def test_method_is_normalised(make_api, method):
    seen = {}

    def handler(request):
        seen["method"] = request.method
        return make_response(200)

    make_api(handler).request(method, URL)
    assert seen["method"] == method.upper()


def test_post_returns_api_response(make_api):
    def post_handler(request: httpx.Request) -> httpx.Response:
        return make_response(201, json={"token": "adfadfa"})

    api = make_api(post_handler)
    result = api.request("post", URL, json={"user": "dude", "password": "querty"})

    assert result is not None
    assert isinstance(result, ApiResponse)
    assert result.status_code == 201
    assert result.body == {"token": "adfadfa"}
    assert result.elapsed_ms is not None
    assert result.size_bytes == 20


@pytest.mark.parametrize("method", ["HEAD", "FOO", ""])
def test_unsupported_method(make_api, method):
    api = make_api(ok)
    with pytest.raises(UnsupportedHttpMethodError) as excinfo:
        api.request(method, URL)

    assert str(excinfo.value) == f"Unsupported HTTP method: {method}"
