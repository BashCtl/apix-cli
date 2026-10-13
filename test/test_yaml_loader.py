import pytest

from apix.errors import ApiError
from apix.yaml_loader import load_yaml


def test_load_yaml(tmp_path):
    yaml_file = tmp_path / "users.yaml"
    yaml_file.write_text(
        """
name: Users
tests:
  - name: Get user
    method: GET
    url: https://example.com/users/1
""",
        encoding="utf-8",
    )

    result = load_yaml(yaml_file)

    assert result["name"] == "Users"
    assert result["tests"][0]["method"] == "GET"


def test_load_invalid_yaml(tmp_path):
    yaml_file = tmp_path / "users.yaml"
    yaml_file.write_text(
        """
name: Users
tests:
  - name= Get user
    method: GET
    url: https://example.com/users/1
""",
        encoding="utf-8",
    )

    with pytest.raises(ApiError) as excinfo:
        load_yaml(yaml_file)

    assert "Invalid YAML: mapping values are not allowed here" in str(excinfo.value)


def test_load_invalid_filepath(tmp_path):
    with pytest.raises(ApiError) as excinfo:
        load_yaml(tmp_path / "/data.yaml")

    assert "File not found" in str(excinfo.value)


def test_load_yaml_directory_returns_api_error(tmp_path):
    with pytest.raises(ApiError, match="Could not read YAML file"):
        load_yaml(tmp_path)


def test_load_yaml_invalid_utf8_returns_api_error(tmp_path):
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_bytes(b"name: \xff")

    with pytest.raises(ApiError, match="Could not read YAML file"):
        load_yaml(yaml_file)
