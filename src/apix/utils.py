import json

from apix.errors import ApiError


class JsonUtil:
    @staticmethod
    def is_json(data) -> bool:
        try:
            json.loads(data)
        except ValueError:
            return False
        return True

    @staticmethod
    def load_json_file(filepath):
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            raise ApiError(f"File not found: {filepath}") from None
        except json.JSONDecodeError as exc:
            raise ApiError(f"Invalid JSON in {filepath}: {exc}") from exc
        except OSError as exc:
            raise ApiError(f"Could not read {filepath}: {exc}") from exc

    @staticmethod
    def load_json_str(data):
        return json.loads(data)
