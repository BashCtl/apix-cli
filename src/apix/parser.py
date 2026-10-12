import re
from typing import Any

from apix.errors import ApiError
from apix.models import TestCase, TestSuite

VARIABLE_PATTERN = re.compile(r"\$\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


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

            expect: dict = dict(test.get("expect", {}))

            if "expected_status" in expect:
                expect["expected_status"] = int(expect["expected_status"])
            if "max_time" in expect:
                expect["max_time"] = int(expect["max_time"])

            test_cases.append(
                TestCase(
                    name=test["name"],
                    method=test["method"],
                    url=test["url"],
                    headers=test.get("headers", {}),
                    json=test.get("json"),
                    json_file=test.get("json_file"),
                    expect=expect,
                    timeout=float(test.get("timeout", 10)),
                )
            )

        return TestSuite(
            name=data["name"],
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
            raise ApiError(f"{item:r} must be KEY=VAlUE format")
        variables[key] = value
    return variables
