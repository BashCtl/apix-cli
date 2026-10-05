from dataclasses import dataclass
from typing import Protocol

from apix.models import ApiResponse


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


class ResponseTimeAssertion:
    def __init__(self, expected: int):
        self.expected = expected

    def check(self, response: ApiResponse) -> AssertionResult:
        return AssertionResult(
            passed=response.elapsed_ms <= self.expected,
            expected=self.expected,
            actual=response.elapsed_ms,
            message=f"Expected elapsed time is below{self.expected}, got {response.elapsed_ms}",
        )


def check_all_assetion(response: ApiResponse, **kwargs) -> list[AssertionResult]:
    assertions = []

    expected_status = kwargs.get("expected_status", None)
    expected_header = kwargs.get("expected_header", None)
    max_time = kwargs.get("max_time", None)
    if expected_status:
        assertions.append(StatusAssertion(expected_status))
    if expected_header:
        assertions.append(HeaderAssertion(expected_header))
    if max_time:
        assertions.append(ResponseTimeAssertion(max_time))

    return [assertion.check(response) for assertion in assertions]
