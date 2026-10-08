from apix.models import TestSuite, TestCase
from apix.errors import ApiError
from apix.yaml_loader import load_yaml


def parse_test_suite(data: dict) -> TestSuite:
    if not isinstance(data, dict):
        raise ApiError("Test suite must be a YAML mapping")

    tests = data.get("tests")

    if not isinstance(tests, list):
        raise ApiError("'tests' must be a list")

    try:
        test_cases = [
            TestCase(
                name=test["name"],
                method=test["method"],
                url=test["url"],
                headers=test.get("headers", {}),
                json=test.get("json"),
                json_file=test.get("json_file"),
                expect=test.get("expect"),
                timeout=test.get("timeout", 10),
            )
            for test in tests
        ]

        return TestSuite(
            name=data["name"],
            tests=test_cases,
        )

    except KeyError as exc:
        raise ApiError(f"Missing required key: {exc.args[0]!r}") from exc
