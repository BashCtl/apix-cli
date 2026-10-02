from http import HTTPStatus

from rich.console import Console
from rich.json import JSON
from rich.markup import escape

from apix.models import ApiResponse


class Formatter:
    def __inti__(self):
        self.console = Console()
        self.err_console = Console(stderr=True)

    def print_response(self, response: ApiResponse, verbose: bool = False):
        method = response.method
        url = response.url
        status_code = response.status_code
        headers = response.headers
        body = response.body
        elapsed_ms = response.elapsed_ms
        size_bytes = response

        try:
            reason = HTTPStatus(status_code).phrase
        except ValueError:
            reason = ""

        style = self.status_style(status_code)

        self.console.print(f"[bold]{method}[/bold] {escape(url)}")
        if verbose:
            self.console.print(f"Headers:\n {headers}")
        self.console.print(f"Status: [{style}]{status_code} {reason}[/{style}]")
        self.console.print(f"Time: {elapsed_ms:.0f} ms")
        self.console.print(f"Size: {size_bytes} bytes")
        self.console.print("Response:")

        if isinstance(body, dict):
            self.console.print(JSON.from_data(body, indent=2))
        else:
            self.console.print(body, markup=False)

    def print_error(self, exception: Exception):
        self.err_console.print(f"[red]Error:[/red] {exception!s}")

    def status_style(self, code: int) -> str:
        if code < 300:
            return "green"
        if code < 400:
            return "yellow"
        return "red"
