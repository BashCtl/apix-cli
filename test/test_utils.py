import pytest

from apix.errors import ApiError
from apix.utils import JsonUtil


def test_load_json_file_reads_utf8(tmp_path):
    json_file = tmp_path / "data.json"
    json_file.write_text('{"name": "Привіт"}', encoding="utf-8")

    assert JsonUtil.load_json_file(json_file) == {"name": "Привіт"}


def test_load_json_file_directory_returns_api_error(tmp_path):
    with pytest.raises(ApiError, match="Could not read"):
        JsonUtil.load_json_file(tmp_path)


def test_load_json_file_invalid_utf8_returns_api_error(tmp_path):
    json_file = tmp_path / "invalid.json"
    json_file.write_bytes(b'{"name":"\xff"}')

    with pytest.raises(ApiError, match="Could not read"):
        JsonUtil.load_json_file(json_file)
