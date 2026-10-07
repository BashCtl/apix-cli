import yaml

from apix.errors import ApiError


def load_yaml(filepath: str) -> dict:
    try:
        with open(filepath, encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise ApiError(f"File not found: {filepath}") from None
    except yaml.YAMLError as exc:
        raise ApiError(f"Invalid YAML: {exc}") from exc


