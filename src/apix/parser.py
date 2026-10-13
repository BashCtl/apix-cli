import math
import re

from typing import Any

from apix.errors import ApiError
from apix.models import TestCase, TestSuite
from functools import reduce

VARIABLE_PATTERN = re.compile(r"\$\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
EXPECT_KEYS = {"expected_status", "expected_header", "max_time", "expected_json"}


def _is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return not isinstance(value, float) or math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_value(item)
            for key, item in value.items()
        )
    return False


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ApiError(f"'{field}' must be a nonempty string")
    return value


def parse_test_suite(data: dict) -> TestSuite:
    if not isinstance(data, dict):
        raise ApiError("Test suite must be a YAML mapping")

    tests = data.get("tests")

    if not isinstance(tests, list):
        raise ApiError("'tests' must be a list")

    try:
        test_cases = []
        for test in tests:
            if not isinstance(test, dict):
                raise ApiError("Each test case must be a YAML mapping")

            name = _require_nonempty_string(test["name"], "name")
            method = _require_nonempty_string(test["method"], "method")
            url = _require_nonempty_string(test["url"], "url")

            raw_expect = test.get("expect", {})
            if not isinstance(raw_expect, dict):
                raise ApiError(
                    f"'expect' must be a YAML mapping, got {type(raw_expect).__name__}"
                )
            expect = dict(raw_expect)

            headers = test.get("headers", {})
            if not isinstance(headers, dict):
                raise ApiError(
                    f"'headers' must be a YAML mapping, got {type(headers).__name__}"
                )
            if any(
                not isinstance(key, str)
                or not key.strip()
                or not isinstance(value, str)
                for key, value in headers.items()
            ):
                raise ApiError("'headers' must contain nonempty string names and string values")

            unknown_expect_keys = set(expect) - EXPECT_KEYS
            if unknown_expect_keys:
                unknown = ", ".join(sorted(map(str, unknown_expect_keys)))
                raise ApiError(f"Unsupported expect key(s): {unknown}")
            if "expected_status" in expect:
                status = expect["expected_status"]
                if isinstance(status, bool) or not isinstance(status, (int, str)):
                    raise ApiError("'expected_status' must be an integer or variable string")
                if isinstance(status, int) and not 100 <= status <= 599:
                    raise ApiError("'expected_status' must be between 100 and 599")
                if isinstance(status, str) and not status.strip():
                    raise ApiError("'expected_status' must not be empty")
            if "expected_header" in expect and not isinstance(
                expect["expected_header"], str
            ):
                raise ApiError("'expected_header' must be a string")
            if "max_time" in expect:
                max_time = expect["max_time"]
                if isinstance(max_time, bool) or not isinstance(
                    max_time, (int, float, str)
                ):
                    raise ApiError("'max_time' must be a number or variable string")
                if isinstance(max_time, (int, float)) and (
                    not math.isfinite(max_time) or max_time < 0
                ):
                    raise ApiError("'max_time' must be a finite number >= 0")
                if isinstance(max_time, str) and not max_time.strip():
                    raise ApiError("'max_time' must not be empty")
            if "expected_json" in expect and not _is_json_value(expect["expected_json"]):
                raise ApiError("'expected_json' must contain only JSON-compatible values")

            body = test.get("json")
            json_file = test.get("json_file")
            if body is not None and not _is_json_value(body):
                raise ApiError("'json' must contain only JSON-compatible values")
            if json_file is not None and (
                not isinstance(json_file, str) or not json_file.strip()
            ):
                raise ApiError("'json_file' must be a nonempty string")
            if body is not None and json_file is not None:
                raise ApiError("Specify only one of 'json' and 'json_file'")

            try:
                timeout = float(test.get("timeout", 10))
            except (TypeError, ValueError, OverflowError) as exc:
                raise ApiError(f"Invalid timeout value: {test.get('timeout')!r}") from exc
            if not math.isfinite(timeout) or timeout <= 0:
                raise ApiError("'timeout' must be a finite number greater than zero")

            extract = test.get("extract", {})

            if isinstance(extract, dict):
                extract = dict(extract)
            else:
                raise ApiError(
                    f"'extract' must be a YAML mapping, got {type(extract).__name__}"
                )
            if any(
                not isinstance(variable, str)
                or not variable.strip()
                or not isinstance(path, str)
                or not path.strip()
                or not all(path.split("."))
                for variable, path in extract.items()
            ):
                raise ApiError("'extract' must map nonempty variable names to valid paths")

            test_cases.append(
                TestCase(
                    name=name,
                    method=method,
                    url=url,
                    headers=headers,
                    json=test.get("json"),
                    json_file=json_file,
                    expect=expect,
                    timeout=timeout,
                    extract=extract,
                )
            )

        return TestSuite(
            name=_require_nonempty_string(data["name"], "suite name"),
            tests=test_cases,
        )

    except KeyError as exc:
        raise ApiError(f"Missing required key: {exc.args[0]!r}") from exc


def resolve_variables(
    value: Any,
    variables: dict[str, str | None],
) -> Any:
    if isinstance(value, dict):
        return {key: resolve_variables(item, variables) for key, item in value.items()}

    if isinstance(value, list):
        return [resolve_variables(item, variables) for item in value]

    if not isinstance(value, str):
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)

        if name not in variables or variables[name] is None:
            raise ApiError(f"Undefined environment variable: {name}")

        return str(variables[name])

    return VARIABLE_PATTERN.sub(replace, value)


def parse_vars(items: list[str]) -> dict[str, str]:
    variables = {}
    for item in items:
        key, sep, value = item.partition("=")
        key = key.strip()
        if not sep or not key:
            raise ApiError(f"{item} must be KEY=VAlUE format")
        variables[key] = value
    return variables


def _get_step(obj, key):
    if isinstance(obj, list):
        index = int(key)
        if index < 0:
            raise ValueError("Negative list indexes are not supported")
        return obj[index]
    return obj[key]


def extract_variables(body, extract):
    variables = {}

    if not isinstance(body, dict):
        raise ApiError("For extraction response body must be a dictionary")

    for variable, path in extract.items():
        if not isinstance(path, str):
            raise ApiError(f"path must be a string, got {type(path).__name__}")

        keys = path.split(".")
        if not all(keys):
            raise ApiError(f"'{path}' is not a valid path for extraction '{variable}'")

        try:
            value = reduce(_get_step, keys, body)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ApiError(
                f"'{path}' was not found in response for extraction '{variable}'"
            ) from exc

        if value is None:
            raise ApiError(f"Extracted value is None for '{variable}' variable")

        variables[variable] = value

    return variables
