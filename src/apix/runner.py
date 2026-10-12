from typing import Any

from apix.assertions import AssertionResult, check_all_assetions
from apix.client import ApiClient
from apix.errors import ApiError
from apix.formatter import Formatter
from apix.models import TestSuite
from apix.parser import resolve_variables, extract_variables


def run_test_suite(suite: TestSuite, variables: dict[str, Any] | None = None) -> bool:
    all_passed = True
    formatter = Formatter()
    context = dict(variables or {})
    if not hasattr(suite, "tests"):
        raise ApiError("Test suite doen't have 'tests' attribute")
    try:
        for test in suite.tests:
            method = resolve_variables(test.method, context)
            url = resolve_variables(test.url, context)
            headers = resolve_variables(test.headers, context)
            json_str = resolve_variables(test.json, context)
            json_file = resolve_variables(test.json_file, context)
            timeout = resolve_variables(test.timeout, context)

            with ApiClient() as client:
                response = client.request(
                    method=method,
                    url=url,
                    header=[f"{name}: {value}" for name, value in headers.items()],
                    json=json_str,
                    json_file=json_file,
                    timeout=timeout,
                )
            if test.extract:
                context.update(extract_variables(response.body, test.extract))
            formatter.print_response(response)
            result: list[AssertionResult] = check_all_assetions(
                response, **(test.expect or {})
            )
            passed: bool = formatter.print_assertions(*result)
            if not passed:
                all_passed = False
    except AttributeError as exc:
        raise ApiError(str(exc)) from exc
    return all_passed
