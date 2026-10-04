import typer

from apix.client import ApiClient
from apix.errors import ApiError
from apix.formatter import Formatter
from apix.assertion import check_all_assetion

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
    excpected_status: int = typer.Option(
        None, "--excpect-status", help="Expected HTTP response code"
    ),
):
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
        assertions_result = check_all_assetion(
            response=response, expected_status=excpected_status
        )
        formatter.print_response(response, verbose)
    except ApiError as e:
        formatter.print_error(e)


if __name__ == "__main__":
    app()
