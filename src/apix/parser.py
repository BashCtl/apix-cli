from apix.models import TestSuite, TestCase
from apix.errors import ApiError
from apix.yaml_loader import load_yaml


def parse_test_suite(data: dict) -> TestSuite:
    try:
        tests: list[TestCase] = [
            TestCase(
                name=test["name"],
                method=test["method"],
                url=test["url"],
                headers=test.get("headers", {}),
                json=test.get("json"),
                json_file=test.get("json_file"),
                expect=test.get("expect"),
                timeout=test.get("timeout", 10)
            )
            for test in data["tests"]
        ]
        return TestSuite(name=data["name"], tests=tests)
    except KeyError as exc:
        raise ApiError(f"Missing required key: {exc.args[0]!r}") from exc

data = load_yaml("src/apix/temp.yaml")
print(parse_test_suite(data))