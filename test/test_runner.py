from types import SimpleNamespace
from unittest.mock import MagicMock
from apix.errors import ApiError
from apix.models import TestCase, TestSuite
import pytest

from apix.runner import run_test_suite


def make_case(**overrides):
    values = dict(
        name="User Test",
        method="GET",
        url="https://api.example.com/users",
        headers={},
        json=None,
        json_file=None,
        timeout=10,
        expect={"expected_status": 200},
    )
    values.update(overrides)
    return TestCase(**values)


@pytest.fixture
def mocks(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client  # for `with ApiClient() as client`
    client.request.return_value = "response"

    formatter = MagicMock()
    formatter.print_assertions.return_value = True

    check = MagicMock(return_value=["r1", "r2"])

    monkeypatch.setattr("apix.runner.ApiClient", lambda: client)
    monkeypatch.setattr("apix.runner.Formatter", lambda: formatter)
    monkeypatch.setattr("apix.runner.check_all_assertions", check)
    return SimpleNamespace(client=client, formatter=formatter, check=check)


def test_builds_request_runs_assertions_and_returns_true(mocks):
    case = make_case(
        name="User Authorizaiton",
        method="POST",
        headers={"Authorization": "Bearer abc", "Accept": "application/json"},
        json='{"name": "Dude"}',
        timeout=5,
        expect={"expected_status": 201, "max_time": 500},
    )

    assert run_test_suite(TestSuite(name="Users Suite", tests=[case])) is True

    mocks.client.request.assert_called_once_with(
        method="POST",
        url="https://api.example.com/users",
        header=["Authorization: Bearer abc", "Accept: application/json"],
        json='{"name": "Dude"}',
        json_file=None,
        timeout=5,
    )
    mocks.check.assert_called_once_with("response", expected_status=201, max_time=500)
    mocks.formatter.print_assertions.assert_called_once_with("r1", "r2")


def test_returns_false_if_any_test_fails_but_still_runs_all(mocks):
    mocks.formatter.print_assertions.side_effect = [True, False, True]
    suite = TestSuite(name="Users Suite", tests=[make_case(), make_case(), make_case()])

    assert run_test_suite(suite) is False
    assert mocks.client.request.call_count == 3
    assert mocks.check.call_count == 3
    assert mocks.formatter.print_assertions.call_count == 3


def test_empty_suite_returns_true(mocks):
    suite = TestSuite(name="Empty Suite", tests=[])

    assert run_test_suite(suite) is True
    mocks.client.request.assert_not_called()
    mocks.check.assert_not_called()
    mocks.formatter.print_assertions.assert_not_called()


def test_case_without_http_method(mocks):
    case = make_case(
        name="User Authorizaiton",
        method="POST",
        headers={"Authorization": "Bearer abc", "Accept": "application/json"},
        json='{"name": "Dude"}',
        timeout=5,
        expect={"expected_status": 201, "max_time": 500},
    )

    del case.method

    run_test_suite(TestSuite(name="Users  Suite", tests=[case]))

    mocks.formatter.print_error.assert_called_once()
    error = mocks.formatter.print_error.call_args.args[0]
    assert isinstance(error, ApiError)
    assert str(error) == "TestCase must have method attribute"


def test_case_with_expect_none(mocks):
    case = make_case(
        name="User Authorizaiton",
        method="POST",
        headers={"Authorization": "Bearer abc", "Accept": "application/json"},
        json='{"name": "Dude"}',
        timeout=5,
        expect=None,
    )

    assert run_test_suite(TestSuite(name="Users Suite", tests=[case])) is True

    mocks.client.request.assert_called_once_with(
        method="POST",
        url="https://api.example.com/users",
        header=["Authorization: Bearer abc", "Accept: application/json"],
        json='{"name": "Dude"}',
        json_file=None,
        timeout=5,
    )
    mocks.check.assert_called_once_with("response")


def test_case_with_json_file(mocks, tmp_path):
    data_file = tmp_path / "user.json"
    data_file.write_text('{"name": "Dude"}')

    case = make_case(
        name="User Authorization",
        method="POST",
        headers={
            "Authorization": "Bearer abc",
            "Accept": "application/json",
        },
        json_file=data_file,
        timeout=5,
        expect={"expected_json": {"name": "Dude"}},
    )

    assert run_test_suite(TestSuite(name="Users Suite", tests=[case])) is True

    mocks.client.request.assert_called_once_with(
        method="POST",
        url="https://api.example.com/users",
        header=[
            "Authorization: Bearer abc",
            "Accept: application/json",
        ],
        json=None,
        json_file=data_file,
        timeout=5,
    )

    mocks.check.assert_called_once_with(
        "response",
        expected_json={"name": "Dude"},
    )
