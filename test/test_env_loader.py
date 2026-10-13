import pytest

from apix.env_loader import load_env
from apix.errors import ApiError


def test_load_env_accepts_uppercase_env_suffix(tmp_path):
    env_file = tmp_path / "local.ENV"
    env_file.write_text("API_NAME=Привіт\n", encoding="utf-8")

    assert load_env(env_file) == {"API_NAME": "Привіт"}


def test_load_env_directory_returns_api_error(tmp_path):
    env_dir = tmp_path / "config.env"
    env_dir.mkdir()

    with pytest.raises(ApiError, match="Environment file not found"):
        load_env(env_dir)


def test_load_env_invalid_utf8_returns_api_error(tmp_path):
    env_file = tmp_path / "invalid.env"
    env_file.write_bytes(b"NAME=\xff")

    with pytest.raises(ApiError, match="Could not read environment file"):
        load_env(env_file)
