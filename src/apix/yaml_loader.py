from pathlib import Path
from typing import Any

import yaml

from apix.errors import ApiError


def load_yaml(filepath: str | Path) -> Any:
    try:
        with Path(filepath).open(encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise ApiError(f"File not found: {filepath}") from None
    except yaml.YAMLError as exc:
        raise ApiError(f"Invalid YAML: {exc}") from exc
    except (OSError, UnicodeError) as exc:
        raise ApiError(f"Could not read YAML file {filepath}: {exc}") from exc

