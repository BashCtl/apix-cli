import httpx
import json
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
    assert result.elapsed_ms <= 0.65
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


def test_delete_sends_correct_request(make_api):
    def handler(request: httpx.Request) -> httpx.Response:
        return make_response(204)

    result = make_api(handler).request("DELETE", URL)
    assert result is not None
    assert isinstance(result, ApiResponse)
    assert result.status_code == 204


def test_delete_404_does_not_raise(make_api):
    api = make_api(lambda request: make_response(404, json={"detail": "not found"}))
    result = api.request("DELETE", URL)
    assert result is not None
    assert isinstance(result, ApiResponse)
    assert result.status_code == 404
    assert result.body == {"detail": "not found"}


@pytest.mark.parametrize("method", ["HEAD", "FOO", ""])
def test_unsupported_method(make_api, method):
    api = make_api(ok)
    with pytest.raises(UnsupportedHttpMethodError) as excinfo:
        api.request(method, URL)

    assert str(excinfo.value) == f"Unsupported HTTP method: {method}"

def test_put_200_returns_updated_resource(make_api):
    api = make_api(lambda request: make_response(200, json={"id": 42, "name": "Widget"}))
    result = api.request("PUT", URL, json='{"name": "Widget"}')
    assert result is not None
    assert isinstance(result, ApiResponse)
    assert result.status_code == 200
    assert result.body == {"id": 42, "name": "Widget"}


def test_json_text_is_sent_as_json_document(make_api):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return make_response(200, json={"ok": True})

    make_api(handler).request("POST", URL, json='{"name":"Ada"}')

    assert seen["body"] == {"name": "Ada"}


def test_invalid_json_text_raises_api_error(make_api):
    api = make_api(ok)

    with pytest.raises(ApiError, match="Invalid request JSON"):
        api.request("POST", URL, json='{"name":')


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (httpx.ReadTimeout("t"), RequestTimeoutError),
        (httpx.ConnectTimeout("t"), RequestTimeoutError),
        (httpx.ConnectError("c"), ConnectionFailedError),
        (httpx.UnsupportedProtocol("p"), InvalidUrlError),
        (httpx.InvalidURL("u"), InvalidUrlError),
        (httpx.ReadError("r"), ApiError),
        (httpx.RemoteProtocolError("r"), ApiError),
    ],
)
def test_exception_mapping(make_api, raised, expected):
    def handler(request):
        raise raised

    api = make_api(handler)
    with pytest.raises(expected) as exc_info:
        api.request("GET", URL)

    assert exc_info.value.__cause__ is raised


def test_context_manager_closes_client():
    client = httpx.Client(transport=httpx.MockTransport(ok))
    with ApiClient(client=client):
        pass
    assert client.is_closed
