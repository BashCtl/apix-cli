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


class RequestType(StrEnum):
    GET = auto()
    POST = auto()
    PUT = auto()
    PATCH = auto()
    DELETE = auto()


class ApiClient:
    def __init__(self):
        self.client = httpx.Client()

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: dict | None = None,
        timeout: float = 10.0,
    ) -> ApiResponse:
        method = method.upper()
        try:
            method = RequestType(method.upper())
        except ValueError:
            raise UnsupportedHttpMethodError(
                f"Unsupported HTTP method: {method}"
            ) from None

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

    def parse_body(self, response: httpx.Response) -> Any | None:
        if not response.content:
            return None

        try:
            return response.json()
        except ValueError:
            return response.text
