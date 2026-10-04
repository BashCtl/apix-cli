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


def check_all_assetion(response: ApiResponse, **kwargs) -> list[AssertionResult]:
    assertions = []

    expected_status = kwargs.get("expected_status")
    if expected_status:
        assertions.append(StatusAssertion(expected_status))

    return [assertion.check(response) for assertion in assertions]
