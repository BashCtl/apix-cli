from pathlib import Path

from dotenv import dotenv_values

from apix.errors import ApiError
from apix.yaml_loader import load_yaml


def load_env(filepath) -> dict:
    suffix = Path(filepath).suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return load_yaml(filepath)
    elif filepath.endswith(".env"):
        return load_dotenv_file(filepath)

    raise ApiError(f"Unsupported environment file: {filepath}")


def load_dotenv_file(filepath) -> dict[str, str | None]:
    if not Path(filepath).is_file():
        raise ApiError(f"Environment file not found: {filepath}")

    try:
        return dotenv_values(filepath)
    except (OSError, UnicodeError) as exc:
        raise ApiError(f"Could not read environment file: {filepath}") from exc
