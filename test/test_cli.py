from unittest.mock import MagicMock

from typer.testing import CliRunner

from apix.assertions import AssertionResult
from apix.cli import app
from conftest import make_fake_response, make_fake_client

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