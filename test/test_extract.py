import pytest

from apix.parser import extract_variables
from apix.errors import ApiError

def test_extract_top_level_key(body):
    assert extract_variables(body, {"z": "zero"}) == {"z": 0}


def test_extract_nested_key(body):
    assert extract_variables(body, {"user_id": "user.id"}) == {"user_id": 1}


def test_extract_multiple_variables(body):
    result = extract_variables(body, {"user_id": "user.id", "name": "user.name"})
    assert result == {"user_id": 1, "name": "Alice"}


def test_extract_list_index(body):
    assert extract_variables(body, {"tag": "user.tags.1"}) == {"tag": "b"}


def test_extract_dict_inside_list(body):
    assert extract_variables(body, {"p": "items.1.price"}) == {"p": 20}


def test_extract_returns_whole_subtree(body):
    result = extract_variables(body, {"tags": "user.tags"})
    assert result == {"tags": ["a", "b", "c"]}


def test_dict_with_digit_string_key_is_not_treated_as_list_index(body):
    result = extract_variables(body, {"v": "numeric_keys.0"})
    assert result == {"v": "zero-as-string-key"}


def test_falsy_but_not_none_values_are_allowed(body):
    result = extract_variables(body, {"z": "zero", "f": "flag"})
    assert result == {"z": 0, "f": False}


def test_empty_extract_returns_empty_dict(body):
    assert extract_variables(body, {}) == {}


@pytest.mark.parametrize("bad_body", [None, [], "text", 123, [{"a": 1}]])
def test_body_must_be_dict(bad_body):
    with pytest.raises(ApiError, match="must be a dictionary"):
        extract_variables(bad_body, {"x": "a"})


@pytest.mark.parametrize("bad_path", [None, 123, ["user", "id"], {"a": 1}])
def test_path_must_be_string(body, bad_path):
    with pytest.raises(ApiError, match="path must be a string"):
        extract_variables(body, {"x": bad_path})


def test_path_type_name_in_message(body):
    with pytest.raises(ApiError, match="got int"):
        extract_variables(body, {"x": 123})


@pytest.mark.parametrize(
    "bad_path",
    ["", ".", "user..id", ".user.id", "user.id."],
)
def test_empty_segments_are_invalid(body, bad_path):
    with pytest.raises(ApiError, match="is not a valid path"):
        extract_variables(body, {"x": bad_path})


def test_missing_key(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "user.missing"})


def test_missing_top_level_key(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "nope"})


def test_walking_into_scalar(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "user.id.deeper"})


def test_walking_into_none(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "user.profile.email"})


def test_list_index_out_of_range(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "user.tags.10"})


def test_index_into_empty_list(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "empty_list.0"})


def test_non_numeric_key_on_list(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "user.tags.first"})


def test_negative_list_index_not_supported(body):
    with pytest.raises(ApiError, match="was not found"):
        extract_variables(body, {"x": "user.tags.-1"})


def test_explicit_none_value_raises(body):
    with pytest.raises(ApiError, match="Extracted value is None for 'p'"):
        extract_variables(body, {"p": "user.profile"})


def test_error_message_contains_variable_and_path(body):
    with pytest.raises(ApiError) as exc_info:
        extract_variables(body, {"my_var": "user.missing"})
    assert "my_var" in str(exc_info.value)
    assert "user.missing" in str(exc_info.value)