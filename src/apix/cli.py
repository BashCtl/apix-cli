import typer

from apix.client import ApiClient
from apix.errors import ApiError
from apix.formatter import Formatter
from apix.assertions import check_all_assertions
from apix.yaml_loader import load_yaml
from apix.parser import parse_test_suite
from apix.runner import run_test_suite
from apix.env_loader import load_env
from apix.parser import  parse_vars

app = typer.Typer()


@app.command()
def command(
    method: str,
    url: str,
    header: list[str] = typer.Option(
        [], "--header", "-H", help="Specify request headers"
    ),
    json: str | None = typer.Option(
        None, "--json", help="Specify request json string payload"
    ),
    json_file: str = typer.Option(
        None, "--json-file", help="Path to json file payload"
    ),
    timeout: int = typer.Option(
        10,
        "--timeout",
        help="Seconds before the request is abandoned (default 10)",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Print response headers"),
    excpected_status: int | None = typer.Option(
        None, "--expect-status", help="Expected HTTP response code"
    ),
    expected_header: str | None = typer.Option(
        None, "--expect-header", help="Expected response header"
    ),
    max_time: int | None = typer.Option(
        None, "--max-time", help="Elapsed time is below specified value"
    ),
    expected_json: str | None = typer.Option(
        None, "--expect-json", help="Response body equals expected JSON"
    ),
):
    """Run HTTP methods (get, post, put, patch, delete)"""
    formatter = Formatter()
    try:
        with ApiClient() as client:
            response = client.request(
                method=method,
                url=url,
                header=header,
                json=json,
                json_file=json_file,
                timeout=timeout,
            )
        assertions_result = check_all_assertions(
            response=response,
            expected_status=excpected_status,
            max_time=max_time,
            expected_header=expected_header,
            expected_json=expected_json,
        )
        formatter.print_response(response, verbose)
        if not formatter.print_assertions(*assertions_result):
            raise typer.Exit(1)
    except ApiError as e:
        formatter.print_error(e)


@app.command()
def run(
    filepath: str,
    env: str | None = typer.Option(
        None, "--env", help="Path to an env or yaml file with variables"
    ),
    var: list[str] = typer.Option(
        [],
        "--var",
        help="Variable as KEY=VALUE, repeatable. Overrides values from --env",
    ),
):
    """
    Run API test cases from a YAML test suite.

    YAML `expect` supports:

      expected_status  Expected HTTP status code.
      expected_header  Expected response header.
      max_time         Maximum response time in milliseconds.
      expected_json    Expected JSON response body.

    Example:

      expect:
        expected_status: 200
        expected_header: "content-type: application/json"
        max_time: 500
        expected_json:
          id: 1
    """
    formatter = Formatter()

    variables = {}
    try:
        yaml_data = load_yaml(filepath)
        cli_vars = parse_vars(var)
        if env:
            variables.update(load_env(env))

        variables.update(cli_vars)

        test_suite = parse_test_suite(yaml_data)
        all_passed = run_test_suite(test_suite, variables)
        if not all_passed:
            raise typer.Exit(1)
    except ApiError as exc:
        formatter.print_error(exc)


if __name__ == "__main__":
    app()
