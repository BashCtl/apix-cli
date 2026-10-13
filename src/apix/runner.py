from typing import Any

from apix.assertions import AssertionResult, check_all_assertions
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

    with ApiClient() as client:
        for test in suite.tests:
            try:
                passed = run_test(client, test, context, formatter)
            except ApiError as exc:
                formatter.print_error(exc)
                passed = False
            except (TypeError, ValueError, OverflowError) as exc:
                name = getattr(test, "name", "<unnamed>")
                formatter.print_error(
                    ApiError(f"Test {name!r} has an invalid value: {exc}")
                )
                passed = False
            all_passed = all_passed and passed
    return all_passed


def run_test(client, test, context, formatter):
    method = getattr(test, "method", None)
    if method is None:
        raise ApiError("TestCase must have method attribute")

    method = resolve_variables(method, context)
    url = resolve_variables(test.url, context)
    headers = resolve_variables(test.headers, context)
    json_str = resolve_variables(test.json, context)
    json_file = resolve_variables(test.json_file, context)
    timeout = resolve_variables(test.timeout, context)
    expect = resolve_variables(test.expect or {}, context)

    if "expected_status" in expect:
        try:
            expect["expected_status"] = int(expect["expected_status"])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ApiError(
                f"Invalid expected_status: {expect['expected_status']!r}"
            ) from exc
    if "max_time" in expect:
        try:
            expect["max_time"] = int(expect["max_time"])
        except (TypeError, ValueError, OverflowError) as exc:
            raise ApiError(f"Invalid max_time: {expect['max_time']!r}") from exc

    try:
        request_timeout = float(timeout)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ApiError(f"Invalid timeout: {timeout!r}") from exc

    response = client.request(
        method=method,
        url=url,
        header=[f"{name}: {value}" for name, value in headers.items()],
        json=json_str,
        json_file=json_file,
        timeout=request_timeout,
    )

    formatter.print_response(response)
    result: list[AssertionResult] = check_all_assertions(
        response, **(expect or {})
    )
    passed: bool = formatter.print_assertions(*result)

    if passed and test.extract:
        context.update(extract_variables(response.body, test.extract))
    return passed
