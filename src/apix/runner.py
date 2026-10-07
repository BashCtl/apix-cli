from apix.models import TestSuite
from apix.client import ApiClient
from apix.assertions import AssertionResult, check_all_assetions
from apix.formatter import Formatter


def run_test_suite(suite: TestSuite) -> bool:
    all_passed = True
    formatter = Formatter()
    for test in suite.tests:
        with ApiClient() as client:
            response = client.request(
                method=test.method,
                url=test.url,
                header=[f"{name}: {value}" for name, value in test.headers.items()],
                json=test.json,
                json_file=test.json_file,
                timeout=test.timeout,
            )
        result: list[AssertionResult] = check_all_assetions(response, **(test.expect or {}))
        passed: bool = formatter.print_assertions(*result)
        if not passed:
            all_passed = False
    return all_passed
