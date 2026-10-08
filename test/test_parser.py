import pytest

from apix.errors import ApiError
from apix.models import TestSuite
from apix.parser import parse_test_suite


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