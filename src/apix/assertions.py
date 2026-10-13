from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from apix.errors import ApiError
from apix.models import ApiResponse
from apix.utils import JsonUtil


@dataclass
class AssertionResult:
    passed: bool
    expected: object
    actual: object
    message: str


def is_valid_filepath(filepath: str) -> bool:
    return Path(filepath).is_file()


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
            message=f"Expected status: {self.expected}, got {response.status_code}",
        )


class HeaderAssertion:
    def __init__(self, expected: str):
        self.expected = expected

        name, sep, value = expected.partition(":")
        self.name = name.strip().lower()

        if not self.name:
            raise ApiError(
                f"Invalid header assertion {expected!r}, use 'Name: value' or 'Name'"
            )

        self.value = value.strip() if sep else None

    def check(self, response: ApiResponse) -> AssertionResult:
        actual = response.headers.get(self.name)

        if actual is None:
            return AssertionResult(
                passed=False,
                expected=self.expected,
                actual=None,
                message=f"Expected header {self.name!r} is missing",
            )

        passed = self.value is None or self._value_matches(actual)

        if self.value is None:
            message = f"Header {self.name!r} is present"
        else:
            message = f"Expected header {self.name!r}: {self.value!r}, got {actual!r}"

        return AssertionResult(
            passed=passed,
            expected=self.expected,
            actual=actual,
            message=message,
        )

    def _value_matches(self, actual: str) -> bool:
        if self.name == "content-type" and self.value and ";" not in self.value:
            actual = actual.split(";", 1)[0].strip()
            return actual.lower() == self.value.lower()
        return actual == self.value


class JsonValueAssertion:
    def __init__(self, expected: object):
        self.expected = self.load_expected(expected)

    def load_expected(self, expected: object) -> object:
        if not isinstance(expected, str):
            return expected
        if is_valid_filepath(expected):
            return JsonUtil.load_json_file(expected)
        if JsonUtil.is_json(expected):
            return JsonUtil.load_json_str(expected)
        raise ApiError(f"{expected} is invalid JSON")

    def check(self, response: ApiResponse) -> AssertionResult:
        path = self._first_difference(self.expected, response.body)
        passed = path is None
        return AssertionResult(
            passed=passed,
            expected=self.expected,
            actual=response.body,
            message=(
                "JSON response matches expected value"
                if passed
                else f"JSON response differs at {path}"
            ),
        )

    def _first_difference(
        self, expected: object, actual: object, path: str = "$"
    ) -> str | None:
        both_numbers = (
            isinstance(expected, (int, float))
            and not isinstance(expected, bool)
            and isinstance(actual, (int, float))
            and not isinstance(actual, bool)
        )
        if type(expected) is not type(actual) and not both_numbers:
            return path
        if isinstance(expected, dict):
            for key in expected:
                child_path = (
                    f"{path}.{key}"
                    if isinstance(key, str)
                    else f"{path}[{key!r}]"
                )
                if key not in actual:
                    return child_path
                difference = self._first_difference(expected[key], actual[key], child_path)
                if difference is not None:
                    return difference
            for key in actual:
                if key not in expected:
                    return f"{path}.{key}" if isinstance(key, str) else f"{path}[{key!r}]"
            return None
        if isinstance(expected, list):
            for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
                difference = self._first_difference(
                    expected_item, actual_item, f"{path}[{index}]"
                )
                if difference is not None:
                    return difference
            if len(expected) != len(actual):
                return f"{path}[{min(len(expected), len(actual))}]"
            return None
        return None if expected == actual else path


class ResponseTimeAssertion:
    def __init__(self, expected: int):
        self.expected = expected

    def check(self, response: ApiResponse) -> AssertionResult:
        return AssertionResult(
            passed=response.elapsed_ms <= self.expected,
            expected=self.expected,
            actual=response.elapsed_ms,
            message=f"Expected elapsed time <= {self.expected} ms, got {response.elapsed_ms:.2f} ms",
        )


def check_all_assertions(response: ApiResponse, **kwargs) -> list[AssertionResult]:
    assertions = []

    expected_status = kwargs.get("expected_status", None)
    expected_header = kwargs.get("expected_header", None)
    max_time = kwargs.get("max_time", None)
    expected_json = kwargs.get("expected_json", None)
    if expected_status is not None:
        assertions.append(StatusAssertion(expected_status))
    if expected_header is not None:
        assertions.append(HeaderAssertion(expected_header))
    if max_time is not None:
        assertions.append(ResponseTimeAssertion(max_time))
    if expected_json is not None:
        assertions.append(JsonValueAssertion(expected_json))

    return [assertion.check(response) for assertion in assertions]
