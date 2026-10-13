import io
import json

import pytest
from rich.console import Console

from apix.assertions import AssertionResult
from apix.formatter import Formatter
from apix.models import ApiResponse


def make_response(body, *, body_is_json=True, headers=None):
    return ApiResponse(
        method="GET",
        url="https://api.example.com/data",
        status_code=200,
        headers=headers or {},
        body=body,
        elapsed_ms=1.0,
        body_is_json=body_is_json,
    )


@pytest.mark.parametrize("body", [{"a": 1}, [1, "two"], "hello", 0, False, None])
def test_print_response_renders_all_json_values_as_json(body):
    output = io.StringIO()
    formatter = Formatter()
    formatter.console = Console(file=output, color_system=None, width=120)

    formatter.print_response(make_response(body))

    assert json.dumps(body, indent=2, ensure_ascii=False) in output.getvalue()


def test_print_response_keeps_plain_text_as_text():
    output = io.StringIO()
    formatter = Formatter()
    formatter.console = Console(file=output, color_system=None, width=120)

    formatter.print_response(make_response("<plain text>", body_is_json=False))

    assert "<plain text>" in output.getvalue()


def test_failed_assertion_previews_are_bounded():
    output = io.StringIO()
    formatter = Formatter()
    formatter.console = Console(file=output, color_system=None, width=1600)

    formatter.print_assertions(
        AssertionResult(False, "x" * 1000, "y" * 1000, "Values differ")
    )

    rendered = output.getvalue()
    assert "truncated" in rendered
    assert len(rendered) < 1300
