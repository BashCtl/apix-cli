from dataclasses import dataclass
from typing import Protocol

from pathvalidate import is_valid_filepath

from apix.errors import ApiError
from apix.models import ApiResponse
from apix.utils import JsonUtil


@dataclass
class AssertionResult:
    passed: bool
    expected: object
    actual: object
    message: str


class Assertion(Protocol):
    def check(self, response: ApiResponse) -> AssertionResult: ...


class StatusAssertion:
    def __init__(self, expected: int):
        self.expected = expected

    def check(self, response: ApiResponse) -> AssertionResult:
        passed = response.status_code == self.expected
        return AssertionResult(
            passed=passed,
            expected=self.expected,
            actual=response.status_code,
            message=f"status == {self.expected}",
        )


class HeaderAssertion:
    def __init__(self, expected: str):
        self.expected = expected

    def check(self, response: ApiResponse) -> AssertionResult:
        return AssertionResult(
            passed=response.headers == self.expected,
            expected=self.expected,
            actual=response.headers,
            message=f"Expected header: {self.expected}, got {response.headers}",
        )


class JsonValueAssertion:
    def __init__(self, expected: str):
        self.expected = self.load_expected(expected)

    def load_expected(self, expected):
        if is_valid_filepath(expected):
            return JsonUtil.load_json_file(expected)
        if JsonUtil.is_json(expected):
            return JsonUtil.load_json_str(expected)
        raise ApiError(f"{expected} is invalid JSON")

    def check(self, response: ApiResponse) -> AssertionResult:
        return AssertionResult(
            passed=response.body == self.expected,
            expected=self.expected,
            actual=response.body,
            message="Expected response body to match JSON",
        )


class ResponseTimeAssertion:
    def __init__(self, expected: int):
        self.expected = expected

    def check(self, response: ApiResponse) -> AssertionResult:
        return AssertionResult(
            passed=response.elapsed_ms <= self.expected,
            expected=self.expected,
            actual=response.elapsed_ms,
            message=f"Expected elapsed time < {self.expected} ms, got {response.elapsed_ms:.2f} ms",
        )


def check_all_assetion(response: ApiResponse, **kwargs) -> list[AssertionResult]:
    assertions = []

    expected_status = kwargs.get("expected_status", None)
    expected_header = kwargs.get("expected_header", None)
    max_time = kwargs.get("max_time", None)
    expected_json = kwargs.get("expected_json", None)
    if expected_status:
        assertions.append(StatusAssertion(expected_status))
    if expected_header:
        assertions.append(HeaderAssertion(expected_header))
    if max_time:
        assertions.append(ResponseTimeAssertion(max_time))
    if expected_json:
        assertions.append(JsonValueAssertion(expected_json))

    return [assertion.check(response) for assertion in assertions]
