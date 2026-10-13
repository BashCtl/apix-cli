from pathlib import Path

from dotenv import dotenv_values

from apix.errors import ApiError
from apix.yaml_loader import load_yaml


def load_env(filepath) -> dict:
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        data = load_yaml(path)

        if not isinstance(data, dict):
            raise ApiError("Environment YAML must be a mapping")

        variables = data.get("variables", {})

        if not isinstance(variables, dict):
            raise ApiError("'variables' must be a mapping")

        return variables
    elif path.name.lower().endswith(".env"):
        return load_dotenv_file(path)

    raise ApiError(f"Unsupported environment file: {filepath}")


def load_dotenv_file(filepath) -> dict[str, str | None]:
    if not Path(filepath).is_file():
        raise ApiError(f"Environment file not found: {filepath}")

    try:
        return dotenv_values(filepath, encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ApiError(f"Could not read environment file: {filepath}") from exc
