from unittest.mock import MagicMock

from typer.testing import CliRunner

from apix.cli import app
from apix.errors import ApiError

runner = CliRunner()


def make_fake_client(monkeypatch, response=None):
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.request.return_value = response
    monkeypatch.setattr("apix.cli.ApiClient", lambda: fake_client)
    return fake_client


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


def test_missing_argument():
    result = runner.invoke(app, ["command"])
    assert result.exit_code == 2
    assert "Missing argument 'url'." in result.stderr


def test_command_passes_args_to_client(monkeypatch):
    fake_client = make_fake_client(monkeypatch, response="fake-response")
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    result = runner.invoke(
        app,
        [
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

    runner.invoke(app, ["GET", "https://x.com"])

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

    runner.invoke(app, ["GET", "https://x.com", "--verbose", "--timeout", "3"])

    fake_formatter.print_response.assert_called_once_with("Fake Response Verbose", True)

def test_api_error_is_printed(monkeypatch):
    fake_client = make_fake_client(monkeypatch)
    err = ApiError("Error Here")          
    fake_client.request.side_effect = err
    fake_formatter = MagicMock()
    monkeypatch.setattr("apix.cli.Formatter", lambda: fake_formatter)

    runner.invoke(app, ["GET", "https://x.com"])
    fake_formatter.print_error.assert_called_once_with(err)