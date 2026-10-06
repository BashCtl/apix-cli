from http import HTTPStatus

from rich.console import Console
from rich.json import JSON
from rich.markup import escape

from apix.models import ApiResponse
from apix.assertions import AssertionResult


class Formatter:
    def __init__(self):
        self.console = Console()
        self.err_console = Console(stderr=True)

    def print_response(self, response: ApiResponse, verbose: bool = False):
        method = response.method
        url = response.url
        status_code = response.status_code
        headers = response.headers
        body = response.body
        elapsed_ms = response.elapsed_ms
        size_bytes = response.size_bytes

        try:
            reason = HTTPStatus(status_code).phrase
        except ValueError:
            reason = ""

        style = self.status_style(status_code)

        self.console.print(f"\n[bold]{method}[/bold] {escape(url)}\n")
        if verbose:
            self.console.print("[green][bold]Headers:[/bold][/green]")
            self.console.print(self.format_headers(headers))

        self.console.print(f"Status: [{style}]{status_code} {reason}[/{style}]")
        self.console.print(f"Time: {elapsed_ms:.0f} ms")
        self.console.print(f"Size: {size_bytes} bytes\n")
        self.console.print("Response:")

        if isinstance(body, dict):
            self.console.print(JSON.from_data(body, indent=2))
        else:
            self.console.print(body, markup=False)

    def print_error(self, exception: Exception):
        self.err_console.print(f"[red]Error:[/red] {exception!s}")

    def print_assertions(self, *results: AssertionResult):
        for result in results:
            if result.passed:
                self.console.print(f"[green][PASS][/green] {result.message}")
            else:
                self.console.print(f"[red][FAIL][/red] {result.message}")
                self.console.print(f"   Expected: {result.expected}")
                self.console.print(f"   Actual: {result.actual}")

    def status_style(self, code: int) -> str:
        if code < 300:
            return "green"
        if code < 400:
            return "yellow"
        return "red"

    def format_headers(self, headers):
        lines = []
        for name, value in headers.items():
            lines.append(f" '{name}': '{value}'")
        return "\n".join(lines) + "\n"
