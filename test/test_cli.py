from unittest.mock import MagicMock

import pytest
from conftest import make_fake_client, make_fake_response
from typer.testing import CliRunner

from apix.assertions import AssertionResult
from apix.cli import app
from apix.errors import ApiError

runner = CliRunner()


def test_command_help():
    result = runner.invoke(app, ["command", "--help"])
    assert result.exit_code == 0
    assert "method" in result.stdout
    assert "url" in result.stdout
    assert "--header" in result.stdout
    assert "--json" in result.stdout
    assert "--json-file" in result.stdout
    assert "--timeout" in result.stdout
    assert "--verbose" in result.stdout
    assert "--expect-status" in result.stdout
    assert "--expect-header" in result.stdout
    assert "--expect-json" in result.stdout
    assert "--max-time" in result.stdout


def test_missing_argument():
    result = runner.invoke(app, ["command", "get"])
    assert result.exit_code == 2
    assert "Missing argument 'url'." in result.stderr


def test_command_passes_args_to_client(monkeypatch):
    fake_client = make_fake_client(monkeypatch, response="fake-response")
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "POST",
            "https://api.example.com/users",
            "--json",
            '{"name": "Dude"}',
            "--header",
            "Authorization:Bearer abc",
        ],
    )

    assert result.exit_code == 0, result.output
    fake_client.request.assert_called_once_with(
        method="POST",
        url="https://api.example.com/users",
        header=["Authorization:Bearer abc"],
        json='{"name": "Dude"}',
        json_file=None,
        timeout=10,
    )
    fake_formatter.print_response.assert_called_once_with("fake-response", False)


def test_defaults(monkeypatch):
    fake_client = make_fake_client(monkeypatch)
    monkeypatch.setattr("apix.cli.Formatter", lambda: MagicMock())

    runner.invoke(app, ["command", "GET", "https://x.com"])

    fake_client.request.assert_called_once_with(
        method="GET",
        url="https://x.com",
        header=[],
        json=None,
        json_file=None,
        timeout=10,
    )


def test_verbose_and_timeout(monkeypatch):
    make_fake_client(monkeypatch, response="Fake Response Verbose")
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    runner.invoke(
        app, ["command", "GET", "https://x.com", "--verbose", "--timeout", "3"]
    )

    fake_formatter.print_response.assert_called_once_with("Fake Response Verbose", True)


def test_expect_status(monkeypatch):

    fake_response = make_fake_response(status_code=200)

    make_fake_client(monkeypatch, response=fake_response)
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-status",
            "200",
        ],
    )

    assert result.exit_code == 0, result.output


def test_expect_status_fails(monkeypatch):

    fake_response = make_fake_response(status_code=404)

    make_fake_client(monkeypatch, response=fake_response)
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-status",
            "200",
        ],
    )

    assert result.exit_code == 0, result.output
    fake_formatter.print_assertions.assert_called_once_with(
        AssertionResult(
            passed=False,
            expected=200,
            actual=404,
            message="Expected status: 200, got 404",
        )
    )


def test_expect_header(monkeypatch):
    fake_response = make_fake_response(headers={"content-type": "application/json"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-header",
            "Content-Type: application/json",
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is True
    assert assertion.expected == "Content-Type: application/json"
    assert assertion.actual == "application/json"


def test_expect_header_fails(monkeypatch):
    fake_response = make_fake_response(headers={"content-type": "multipart/form-data"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-header",
            "Content-Type: application/json",
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is False
    assert assertion.expected == "Content-Type: application/json"
    assert assertion.actual == "multipart/form-data"


def test_expect_json_valid(monkeypatch):
    fake_response = make_fake_response(body={"user": "Dude"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-json",
            '{"user": "Dude"}',
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is True
    assert assertion.expected == {"user": "Dude"}
    assert assertion.actual == {"user": "Dude"}


def test_expect_json_different(monkeypatch):
    fake_response = make_fake_response(body={"user": "Dude"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-json",
            '{"user": "MadMax"}',
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is False
    assert assertion.expected == {"user": "MadMax"}
    assert assertion.actual == {"user": "Dude"}


def test_expect_json_invalid(monkeypatch):
    fake_response = make_fake_response(body={"user": "Dude"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-json",
            '"user": "MadMax"}',
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_error.assert_called_once()

    error = fake_formatter.print_error.call_args.args[0]
    assert "is invalid JSON" in str(error)


def test_expect_json_ignores_key_order(monkeypatch):
    fake_response = make_fake_response(body={"user": "Dude", "id": 1})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-json",
            '{"id": 1, "user": "Dude"}',
        ],
    )

    assert result.exit_code == 0, result.output

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is True
    assert assertion.expected == {"id": 1, "user": "Dude"}
    assert assertion.actual == {"user": "Dude", "id": 1}


def test_expect_json_valid_file(monkeypatch, tmp_path):
    expected_file = tmp_path / "expected.json"
    expected_file.write_text('{"user": "Dude"}')

    fake_response = make_fake_response(body={"user": "Dude"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-json",
            str(expected_file),
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is True
    assert assertion.expected == {"user": "Dude"}
    assert assertion.actual == {"user": "Dude"}


def test_expect_json_invalid_file(monkeypatch, tmp_path):
    expected_file = tmp_path / "expected.json"
    expected_file.write_text('"user": "Dude"}')

    fake_response = make_fake_response(body={"user": "Dude"})

    make_fake_client(monkeypatch, response=fake_response)

    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--expect-json",
            str(expected_file),
        ],
    )

    assert result.exit_code == 0, result.output

    fake_formatter.print_error.assert_called_once()

    error = fake_formatter.print_error.call_args.args[0]
    assert f"Invalid JSON in {expected_file}" in str(error)


def test_expect_response_max_time(monkeypatch):

    fake_response = make_fake_response(elapsed_ms=500)

    make_fake_client(monkeypatch, response=fake_response)
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--max-time",
            "500",
        ],
    )

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is True
    assert assertion.expected == 500
    assert assertion.actual == 500


def test_expect_response_max_time_fails(monkeypatch):

    fake_response = make_fake_response(elapsed_ms=500)

    make_fake_client(monkeypatch, response=fake_response)
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
            "command",
            "GET",
            "https://x.com",
            "--max-time",
            "400",
        ],
    )

    fake_formatter.print_assertions.assert_called_once()

    assertion = fake_formatter.print_assertions.call_args.args[0]

    assert assertion.passed is False
    assert assertion.expected == 400
    assert assertion.actual == 500


def test_run_help():
    result = runner.invoke(app, ["run", "--help"])
    assert "Usage: root run [OPTIONS] {filepath}" in result.stdout
    assert "Run API test cases from a YAML test suite.  " in result.stdout


def test_runs_suite_without_env(mocks):
    result = runner.invoke(app, ["run", "suite.yaml"])

    assert result.exit_code == 0, result.output
    mocks.load_yaml.assert_called_once_with("suite.yaml")
    mocks.parse_test_suite.assert_called_once_with({"raw": True})
    mocks.run_test_suite.assert_called_once_with("suite")
    mocks.load_env.assert_not_called()
    mocks.resolve_variables.assert_not_called()
    mocks.formatter.print_error.assert_not_called()


def test_env_is_loaded_and_variables_are_resolved_before_parsing(mocks):
    result = runner.invoke(app, ["run", "suite.yaml", "--env", ".env"])

    assert result.exit_code == 0, result.output
    mocks.load_env.assert_called_once_with(".env")
    mocks.resolve_variables.assert_called_once_with({"raw": True}, {"token": "abc"})
    mocks.parse_test_suite.assert_called_once_with({"resolved": True})
    mocks.run_test_suite.assert_called_once_with("suite")


def test_empty_env_value_is_ignored(mocks):
    result = runner.invoke(app, ["run", "suite.yaml", "--env", ""])

    assert result.exit_code == 0, result.output
    mocks.load_env.assert_not_called()
    mocks.resolve_variables.assert_not_called()
    mocks.parse_test_suite.assert_called_once_with({"raw": True})


@pytest.mark.parametrize(
    "stage",
    [
        "load_yaml",
        "load_env",
        "resolve_variables",
        "parse_test_suite",
        "run_test_suite",
    ],
)
def test_api_error_from_any_step_is_printed(mocks, stage):
    err = ApiError(f"{stage} failed")
    getattr(mocks, stage).side_effect = err

    runner.invoke(app, ["run", "suite.yaml", "--env", ".env"])

    mocks.formatter.print_error.assert_called_once_with(err)


def test_api_error_while_loading_yaml_stops_everything_else(mocks):
    mocks.load_yaml.side_effect = ApiError("bad yaml")

    runner.invoke(app, ["run", "suite.yaml", "--env", ".env"])

    mocks.load_env.assert_not_called()
    mocks.resolve_variables.assert_not_called()
    mocks.parse_test_suite.assert_not_called()
    mocks.run_test_suite.assert_not_called()


def test_api_error_while_resolving_variables_does_not_run_the_suite(mocks):
    mocks.resolve_variables.side_effect = ApiError("Variable 'x' is not defined")

    runner.invoke(app, ["run", "suite.yaml", "--env", ".env"])

    mocks.parse_test_suite.assert_not_called()
    mocks.run_test_suite.assert_not_called()


def test_var_only_resolves_without_loading_env_file(mocks):
    result = runner.invoke(app, ["run", "suite.yaml", "--var", "status=200"])

    assert result.exit_code == 0, result.output
    mocks.load_env.assert_not_called()
    mocks.resolve_variables.assert_called_once_with({"raw": True}, {"status": "200"})
    mocks.parse_test_suite.assert_called_once_with({"resolved": True})


def test_multiple_vars(mocks):
    runner.invoke(
        app, ["run", "suite.yaml", "--var", "token=TOKEN", "--var", "status=200"]
    )

    mocks.resolve_variables.assert_called_once_with(
        {"raw": True}, {"token": "TOKEN", "status": "200"}
    )


def test_var_value_may_contain_equals_sign(mocks):
    runner.invoke(app, ["run", "suite.yaml", "--var", "url=https://x.com?a=b"])

    assert mocks.resolve_variables.call_args.args[1] == {"url": "https://x.com?a=b"}


def test_env_file_and_vars_are_merged(mocks):
    mocks.load_env.return_value = {"token": "abc", "host": "dev"}

    runner.invoke(app, ["run", "suite.yaml", "--env", ".env", "--var", "status=200"])

    mocks.resolve_variables.assert_called_once_with(
        {"raw": True}, {"token": "abc", "host": "dev", "status": "200"}
    )


def test_var_overrides_env_file(mocks):
    mocks.load_env.return_value = {"status": "404", "token": "abc"}

    runner.invoke(app, ["run", "suite.yaml", "--env", ".env", "--var", "status=200"])

    assert mocks.resolve_variables.call_args.args[1] == {
        "status": "200",
        "token": "abc",
    }


def test_repeated_var_keeps_last_value(mocks):
    runner.invoke(app, ["run", "suite.yaml", "--var", "a=1", "--var", "a=2"])

    assert mocks.resolve_variables.call_args.args[1] == {"a": "2"}


def test_empty_env_with_var_still_resolves(mocks):
    runner.invoke(app, ["run", "suite.yaml", "--env", "", "--var", "a=1"])

    mocks.load_env.assert_not_called()
    mocks.resolve_variables.assert_called_once_with({"raw": True}, {"a": "1"})


def test_no_env_and_no_var_skips_resolving(mocks):
    runner.invoke(app, ["runsuite.yaml"])

    mocks.resolve_variables.assert_not_called()
