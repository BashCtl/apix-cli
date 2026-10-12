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
    "items, expected",
    [
        ([], {}),
        (["a=1"], {"a": "1"}),
        (["a=1", "b=2"], {"a": "1", "b": "2"}),
        (["a=1", "a=2"], {"a": "2"}),
        (["a="], {"a": ""}),                           # empty value is allowed
        (["a=b=c"], {"a": "b=c"}),                     # first "=" splits
        ([" a =1"], {"a": "1"}),                       # key is stripped
        (["a= spaced "], {"a": " spaced "}),           # value is kept as given
        (["url=https://x.com?q=1"], {"url": "https://x.com?q=1"}),
    ],
)
def test_parse_vars(items, expected):
    assert parse_vars(items) == expected
 
 
@pytest.mark.parametrize("bad", ["oops", "=x", "  =x", ""])
def test_parse_vars_rejects_malformed_items(bad):
    with pytest.raises(ApiError):
        parse_vars([bad])