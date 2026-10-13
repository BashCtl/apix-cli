import pytest

from apix.errors import ApiError
from apix.models import TestSuite
from apix.parser import parse_test_suite
from apix.parser import parse_vars

def test_parse_data_to_test_suite():
    data = {
        "name": "Users",
        "tests": [
            {
                "name": "Get user",
                "method": "GET",
                "url": "https://example.com",
                "expect": {"expected_status": 200},
            }
        ],
    }

    test_suite = parse_test_suite(data)

    assert isinstance(test_suite, TestSuite)
    assert test_suite.name == "Users"
    assert test_suite.tests[0].expect is not None
    assert test_suite.tests[0].expect["expected_status"] == 200
    assert isinstance(test_suite.tests[0].extract, dict)


def test_parse_data_missing_key():
    data = {
        "name": "Users",
        "tests": [
            {
                "title": "Get user",
                "method": "GET",
                "url": "https://example.com",
                "expect": {"expected_status": 200},
            }
        ],
    }
    with pytest.raises(ApiError) as excinfo:
        parse_test_suite(data)

    assert "Missing required key" in str(excinfo.value)


def test_parse_empty_data_dict():
    data = {}
    with pytest.raises(ApiError) as excinfo:
        parse_test_suite(data)

    assert "'tests' must be a list" in str(excinfo.value)


def test_parse_string_data():
    data = ""
    with pytest.raises(ApiError) as excinfo:
        parse_test_suite(data)

    assert "Test suite must be a YAML mapping" in str(excinfo.value)


def test_parse_data_to_test_suite_with_valid_extract():
    data = {
        "name": "Users",
        "tests": [
            {
                "name": "Get user",
                "method": "GET",
                "url": "https://example.com",
                "expect": {"expected_status": 200},
                "extract": {"token": "access_token"},
            }
        ],
    }

    test_suite = parse_test_suite(data)

    assert isinstance(test_suite, TestSuite)
    assert test_suite.name == "Users"
    assert test_suite.tests[0].expect is not None
    assert test_suite.tests[0].expect["expected_status"] == 200
    assert test_suite.tests[0].extract is not None
    assert test_suite.tests[0].extract["token"] == "access_token"


def test_parse_data_to_test_suite_with_invalid_extract():
    data = {
        "name": "Users",
        "tests": [
            {
                "name": "Get user",
                "method": "GET",
                "url": "https://example.com",
                "expect": {"expected_status": 200},
                "extract": ["Mad", "Max"],
            }
        ],
    }

    with pytest.raises(ApiError) as excinfo:
        parse_test_suite(data)

    assert "'extract' must be a YAML mapping" in str(excinfo.value)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("expect", ["expected_status", 200], "'expect' must be a YAML mapping"),
        ("headers", "Authorization: token", "'headers' must be a YAML mapping"),
        ("timeout", "soon", "Invalid timeout value"),
    ],
)
def test_parse_rejects_invalid_field_values(field, value, message):
    test_case = {
        "name": "Get user",
        "method": "GET",
        "url": "https://example.com",
        field: value,
    }

    with pytest.raises(ApiError, match=message):
        parse_test_suite({"name": "Users", "tests": [test_case]})


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "  ", "'name' must be a nonempty string"),
        ("method", 42, "'method' must be a nonempty string"),
        ("url", None, "'url' must be a nonempty string"),
        ("headers", {"Authorization": 123}, "'headers' must contain"),
        ("json", {1: "not a JSON object key"}, "'json' must contain"),
        ("json_file", 42, "'json_file' must be a nonempty string"),
        ("extract", {"token": "user..token"}, "'extract' must map"),
        ("expect", {"unknown": True}, "Unsupported expect key"),
        ("expect", {"expected_status": True}, "'expected_status' must be"),
        ("expect", {"expected_status": 99}, "between 100 and 599"),
        ("expect", {"max_time": -1}, "finite number >= 0"),
        ("expect", {"expected_header": None}, "'expected_header' must be a string"),
    ],
)
def test_parse_rejects_invalid_suite_field_values(field, value, message):
    test_case = {
        "name": "Get user",
        "method": "GET",
        "url": "https://example.com",
        field: value,
    }

    with pytest.raises(ApiError, match=message):
        parse_test_suite({"name": "Users", "tests": [test_case]})


def test_parse_rejects_both_request_body_sources():
    test_case = {
        "name": "Create user",
        "method": "POST",
        "url": "https://example.com",
        "json": {"name": "Ada"},
        "json_file": "payload.json",
    }

    with pytest.raises(ApiError, match="only one of 'json' and 'json_file'"):
        parse_test_suite({"name": "Users", "tests": [test_case]})


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_parse_rejects_nonpositive_or_nonfinite_timeout(timeout):
    test_case = {
        "name": "Get user",
        "method": "GET",
        "url": "https://example.com",
        "timeout": timeout,
    }

    with pytest.raises(ApiError, match="finite number greater than zero"):
        parse_test_suite({"name": "Users", "tests": [test_case]})


@pytest.mark.parametrize(
    "items, expected",
    [
        ([], {}),
        (["a=1"], {"a": "1"}),
        (["a=1", "b=2"], {"a": "1", "b": "2"}),
        (["a=1", "a=2"], {"a": "2"}),
        (["a="], {"a": ""}),                           
        (["a=b=c"], {"a": "b=c"}),                     
        ([" a =1"], {"a": "1"}),                       
        (["a= spaced "], {"a": " spaced "}),           
        (["url=https://x.com?q=1"], {"url": "https://x.com?q=1"}),
    ],
)
def test_parse_vars(items, expected):
    assert parse_vars(items) == expected
 
 
@pytest.mark.parametrize("bad", ["oops", "=x", "  =x", ""])
def test_parse_vars_rejects_malformed_items(bad):
    with pytest.raises(ApiError):
        parse_vars([bad])
