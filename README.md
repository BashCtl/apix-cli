# APIX
A tiny Python CLI for sending HTTP requests, inspecting responses, and
running API tests defined in YAML.


# APIX Example

The examples directory contain request data and a YAML test suite for trying APIX. APIX is a Python command-line tool for sending HTTP requests and running API checks described in YAML.

## Project structure

From the repository root:

```text
src/apix/             CLI and request, parsing, assertion, and formatting code
test/                 Automated tests
examples/
  booker.yaml         Example multi-step API test suite
  .env                Local variables used by the example suite
```

The `examples/.env` file contains local configuration. Keep credentials private and do not copy real secrets into documentation or commit them to a shared repository.

## Requirements and installation

APIX requires Python 3.12 or newer. From the repository root, install it in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If you use uv, install the project and its development dependencies with:

```bash
uv sync
```

Check that the command is available:

```bash
apix --help
```

If you did not activate the virtual environment, invoke the installed command as `.venv/bin/apix` on Linux or macOS.

## Send a single request

The `command` subcommand takes an HTTP method and URL. Headers can be repeated with `--header` or `-H`:

```bash
apix command GET https://api.example.com/users/1
apix command GET https://api.example.com/users/1 \
  --header 'Accept: application/json' \
  --verbose \
  --expect-status 200 \
  --expect-header 'content-type: application/json' \
  --max-time 500
```

`--max-time` is in milliseconds. Request bodies can be supplied as JSON text or read from a file. The two body options cannot be used together:

```bash
apix command POST https://api.example.com/users \
  --header 'Content-Type: application/json' \
  --json '{"name":"Ada"}'

apix command POST https://api.example.com/users --json-file path/to/body.json
```

Use `--expect-json` to compare the response body with JSON text or a JSON file:

```bash
apix command GET https://api.example.com/users/1 \
  --expect-json '{"id":1,"name":"Ada"}'
```

An assertion failure or API error exits with a nonzero status, which is useful in shell scripts and CI.

## Run the example YAML suite

Run this command from the repository root so the suite's relative `json_file` path resolves correctly:

```bash
apix run examples/booker.yaml --env examples/.env
```

The example suite sends requests to the URL configured by `BASE_URL` in `examples/.env`. It creates a token, creates a booking, extracts values from the responses, and uses them in the later request. It makes real HTTP requests, so configure the endpoint and credentials for an API environment you are allowed to use.

### YAML suite format

`examples/booker.yaml` is the runnable example. Its structure is:

```yaml
name: Booking
tests:
  - name: Create Token
    method: post
    url: ${{ BASE_URL }}/auth
    json:
      username: ${{ USERNAME }}
      password: ${{ PASSWORD }}
    expect:
      expected_status: ${{ STATUS }}
    extract:
      token: token
```

Each test case can define:

- `name`: a descriptive case name.
- `method` and `url`: the HTTP request method and target URL.
- `headers`: optional mapping of request header names to values.
- `json`: optional YAML data to send as a JSON body, or `json_file`: a path to a JSON body file. Supply at most one.
- `timeout`: optional request timeout in seconds; it must be greater than zero.
- `expect`: optional checks such as `expected_status`, `expected_header`, `max_time` in milliseconds, and `expected_json`.
- `extract`: optional mapping from a variable name to a dot-separated path in a JSON response. Extracted values are available to later tests.

Variables use the `${{ VARIABLE_NAME }}` form and can appear in strings throughout the suite. The `examples/.env` file defines `BASE_URL`, `USERNAME`, `PASSWORD`, and `STATUS`. The environment file can also be YAML, with variables under a `variables` mapping:

```yaml
variables:
  BASE_URL: https://api.example.com
  STATUS: 200
```

You can override or add values on the command line. Repeating `--var` is supported, and command-line values take precedence over values loaded from `--env`:

```bash
apix run examples/booker.yaml \
  --env examples/.env \
  --var BASE_URL=https://staging.example.com \
  --var STATUS=200
```

When no `--env` file is supplied, `--var` can provide all required variables:

```bash
apix run examples/booker.yaml \
  --var BASE_URL=https://staging.example.com \
  --var USERNAME=your-user \
  --var PASSWORD=your-password \
  --var STATUS=200
```

## Run the tests

With uv:

```bash
uv run pytest
```

If you installed with pip and also want to run the tests, install pytest and run:

```bash
python -m pip install pytest
python -m pytest
```
