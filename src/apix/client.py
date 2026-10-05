from enum import StrEnum, auto

import httpx

from apix.errors import (
    ApiError,
    ConnectionFailedError,
    InvalidUrlError,
    RequestTimeoutError,
    UnsupportedHttpMethodError,
)
from apix.models import ApiResponse
from apix.utils import JsonUtil


class RequestType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ApiClient:
    def __init__(self, client: httpx.Client | None = None):
        self.client: httpx.Client = client or httpx.Client()

    def request(
        self,
        method: str,
        url: str,
        *,
        header: list[str] | None = None,
        json: str | None = None,
        json_file: str | None = None,
        timeout: float = 10.0,
    ) -> ApiResponse:
        method = method.upper()
        try:
            method = RequestType(method.upper())
        except ValueError:
            raise UnsupportedHttpMethodError(
                f"Unsupported HTTP method: {method}"
            ) from None

        headers = {}
        for h in header or []:
            key, _, value = h.partition(":")
            headers[key.strip()] = value.strip()

        if json or json_file:
            headers.setdefault("Content-Type", "application/json")

        if json is not None and json_file is not None:
            raise ApiError("Use either --json or --json-file, not both.")

        if json_file:
            json = JsonUtil.load_json_file(json_file)

        try:
            response: httpx.Response = self.client.request(
                method=method, url=url, headers=headers, json=json, timeout=timeout
            )
        except httpx.TimeoutException as e:
            raise RequestTimeoutError(
                f"Request to {url} timed out after {timeout}s"
            ) from e
        except httpx.ConnectError as e:
            raise ConnectionFailedError(
                f"Could not connect to {url}. Check the URL and your network."
            ) from e
        except httpx.UnsupportedProtocol as e:
            raise InvalidUrlError(
                f"Invalid URL '{url}'. Include the scheme, e.g. https://"
            ) from e
        except httpx.InvalidURL as e:
            raise InvalidUrlError(f"Invalid URL '{url}'") from e
        except httpx.HTTPError as e:
            raise ApiError(f"Request failed: {type(e).__name__}") from e

        return ApiResponse.from_httpx(response)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
