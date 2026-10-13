import pytest

from apix.assertions import (
    AssertionResult,
    HeaderAssertion,
    JsonValueAssertion,
    ResponseTimeAssertion,
    StatusAssertion,
    check_all_assertions,
)
from apix.errors import ApiError
from apix.models import ApiResponse


def make_response(
    status_code=200,
    headers=None,
    body=None,
    elapsed_ms=50.0,
    method="GET",
    url="https://api.example.com/users",
) -> ApiResponse:
    return ApiResponse(
        method=method,
        url=url,
        status_code=status_code,
        headers={} if headers is None else headers,
        body=body,
        elapsed_ms=elapsed_ms,
    )


@pytest.fixture
def fake_json_util(monkeypatch):

    from types import SimpleNamespace

    calls = SimpleNamespace(file=[], string=[])

    def load_json_file(path):
        calls.file.append(path)
        return {"from": "file"}

    def load_json_str(text):
        calls.string.append(text)
        return {"from": "string"}

    util = SimpleNamespace(
        load_json_file=load_json_file,
        load_json_str=load_json_str,
        is_json=lambda s: s.strip().startswith(("{", "[")),
    )
    monkeypatch.setattr("apix.assertions.JsonUtil", util)
    monkeypatch.setattr(
        "apix.assertions.is_valid_filepath", lambda s: s.endswith(".json")
    )
    return calls


class TestStatusAssertion:
    def test_pass(self):
        result = StatusAssertion(200).check(make_response(status_code=200))

        assert isinstance(result, AssertionResult)
        assert result.passed is True
        assert result.expected == 200
        assert result.actual == 200

    def test_fail(self):
        result = StatusAssertion(200).check(make_response(status_code=404))

        assert result.passed is False
        assert result.expected == 200
        assert result.actual == 404
        assert result.message == "Expected status: 200, got 404"

    @pytest.mark.parametrize(
        "expected, actual, passed",
        [(201, 201, True), (201, 200, False), (500, 500, True), (204, 404, False)],
    )
    def test_various_codes(self, expected, actual, passed):
        result = StatusAssertion(expected).check(make_response(status_code=actual))
        assert result.passed is passed


class TestHeaderAssertion:
    H = {"content-type": "application/json; charset=utf-8", "x-request-id": "abc"}

    @pytest.mark.parametrize(
        "expected, passed",
        [
            ("X-Request-Id: abc", True),
            ("x-request-id: abc", True),
            ("X-Request-Id: ABC", False),
            ("X-Request-Id", True),
            ("X-Missing", False),
            ("Content-Type: application/json", True),
            ("Content-Type: Application/JSON", True),
            ("Content-Type: application/json; charset=utf-8", True),
            ("Content-Type: application/json; charset=latin-1", False),
            ("Content-Type: text/html", False),
        ],
    )
    def test_header(self, expected, passed):
        assert (
            HeaderAssertion(expected).check(make_response(headers=self.H)).passed
            is passed
        )

    @pytest.mark.parametrize("bad", ["", ": value", "   "])
    def test_invalid_header_expression(self, bad):
        with pytest.raises(ApiError):
            HeaderAssertion(bad)


class TestJsonValueAssertion:
    def test_loads_from_file_when_path(self, fake_json_util):
        assertion = JsonValueAssertion("expected.json")

        assert assertion.expected == {"from": "file"}
        assert fake_json_util.file == ["expected.json"]
        assert fake_json_util.string == []

    def test_loads_from_string_when_json(self, fake_json_util):
        assertion = JsonValueAssertion('{"a": 1}')

        assert assertion.expected == {"from": "string"}
        assert fake_json_util.string == ['{"a": 1}']
        assert fake_json_util.file == []

    def test_invalid_input_raises_api_error(self, fake_json_util):
        with pytest.raises(ApiError, match="is invalid JSON"):
            JsonValueAssertion("not json and not a file")

    def test_check_pass(self, fake_json_util):
        result = JsonValueAssertion('{"a": 1}').check(
            make_response(body={"from": "string"})
        )

        assert result.passed is True
        assert result.expected == {"from": "string"}
        assert result.actual == {"from": "string"}

    def test_check_fail(self, fake_json_util):
        result = JsonValueAssertion('{"a": 1}').check(
            make_response(body={"other": True})
        )

        assert result.passed is False
        assert result.actual == {"other": True}
        assert result.message == "JSON response differs at $.from"

    def test_check_fail_reports_first_differing_json_path(self):
        assertion = JsonValueAssertion({"user": {"id": 1}})

        result = assertion.check(make_response(body={"user": {"id": 2}}))

        assert result.passed is False
        assert result.message == "JSON response differs at $.user.id"

    def test_empty_response_body_fails(self, fake_json_util):
        result = JsonValueAssertion('{"a": 1}').check(make_response(body=None))
        assert result.passed is False

    def test_text_body_fails(self, fake_json_util):
        result = JsonValueAssertion('{"a": 1}').check(make_response(body="oops"))
        assert result.passed is False


class TestResponseTimeAssertion:
    def test_pass_when_faster(self):
        result = ResponseTimeAssertion(500).check(make_response(elapsed_ms=120.5))

        assert result.passed is True
        assert result.expected == 500
        assert result.actual == 120.5

    def test_pass_on_exact_boundary(self):
        assert ResponseTimeAssertion(500).check(make_response(elapsed_ms=500)).passed

    def test_fail_when_slower(self):
        result = ResponseTimeAssertion(100).check(make_response(elapsed_ms=250.456))

        assert result.passed is False
        assert result.message == "Expected elapsed time <= 100 ms, got 250.46 ms"


class TestCheckAllAssertion:
    def test_no_kwargs_returns_empty_list(self):
        assert check_all_assertions(make_response()) == []

    def test_unknown_kwargs_are_ignored(self):
        assert check_all_assertions(make_response(), something_else=1) == []

    def test_only_status(self):
        results = check_all_assertions(
            make_response(status_code=200), expected_status=200
        )

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].expected == 200

    def test_only_header(self):
        results = check_all_assertions(make_response(), expected_header="a: b")

        assert len(results) == 1
        assert results[0].expected == "a: b"

    def test_only_max_time(self):
        results = check_all_assertions(make_response(elapsed_ms=10), max_time=100)

        assert len(results) == 1
        assert results[0].passed is True

    def test_only_json(self, fake_json_util):
        results = check_all_assertions(
            make_response(body={"from": "string"}), expected_json='{"a": 1}'
        )

        assert len(results) == 1
        assert results[0].passed is True

    def test_zero_status_is_still_checked(self):
        results = check_all_assertions(make_response(), expected_status=0)

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].expected == 0

    def test_zero_max_time_is_still_checked(self):
        results = check_all_assertions(make_response(elapsed_ms=1), max_time=0)

        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].expected == 0

    def test_empty_header_expression_is_rejected(self):
        with pytest.raises(ApiError, match="Invalid header assertion"):
            check_all_assertions(make_response(), expected_header="")

    def test_false_json_value_is_still_checked(self):
        results = check_all_assertions(make_response(body=False), expected_json=False)

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].expected is False

    def test_empty_mapping_json_value_is_still_checked(self):
        results = check_all_assertions(make_response(body={}), expected_json={})

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].expected == {}

    def test_invalid_json_raises_api_error(self, fake_json_util):
        with pytest.raises(ApiError):
            check_all_assertions(make_response(), expected_json="garbage")
