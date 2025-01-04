import pytest
from unittest.mock import patch, mock_open
from requests.exceptions import RequestException
from validate_devschema.utils import (
    collect_refs,
    load_json,
)


@patch("validate_devschema.validate_schema.click.secho")
@patch("requests.get")
def test_fetching_json_verbose_logging(mock_requests_get, mock_secho):
    """
    Test that `click.secho` logs the correct message when fetching JSON
    from a URL in verbose mode.
    """
    url = "http://example.com/schema.json"
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"key": "value"}

    load_json(url, verbose=True)

    mock_secho.assert_any_call(
        f"INFO: Fetching JSON from URL: {url}", fg="blue"
    )
    mock_requests_get.assert_called_once_with(url)


@patch("validate_devschema.validate_schema.click.secho")
@patch("requests.get")
def test_fetching_json_logs_error(mock_requests_get, mock_secho):
    """
    Test that `click.secho` logs the correct error message when fetching
    JSON from a URL fails, and the error is raised.
    """
    url = "http://example.com/schema.json"
    mock_requests_get.side_effect = RequestException("Failed to fetch data")

    with pytest.raises(RequestException):
        load_json(url, verbose=True)

    mock_secho.assert_any_call(
        "ERROR: Failed to fetch JSON from URL: Failed to fetch data", fg="red"
    )


@patch("validate_devschema.validate_schema.click.secho")
@patch("builtins.open", new_callable=mock_open)
def test_loading_json_logs_error_on_exception(mock_open_func, mock_secho):
    """
    Test that `click.secho` logs an error message when an exception occurs
    while loading JSON from a file.
    """
    file_path = "path/to/file.json"
    error_message = "File not found"

    mock_open_func.side_effect = OSError(error_message)

    with pytest.raises(OSError):
        load_json(file_path, verbose=True)

    mock_secho.assert_any_call(
        f"ERROR: Failed to load JSON from file: {error_message}", fg="red"
    )


@patch("validate_devschema.validate_schema.click.secho")
@patch("builtins.open", new_callable=mock_open)
def test_loading_json_logs_info(mock_open_func, mock_secho):
    """
    Test that `click.secho` logs the correct info message when loading JSON
    from a file.
    """
    file_path = "path/to/file.json"
    json_data = '{"key": "value"}'

    mock_open_func.return_value.read.return_value = json_data

    load_json(file_path, verbose=True)

    mock_secho.assert_any_call(
        f"INFO: Loading JSON from file: {file_path}", fg="blue"
    )


@patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
def test_load_json_from_file(mock_file):
    result = load_json("fake_file.json", verbose=False)
    assert result == {"key": "value"}
    mock_file.assert_called_once_with("fake_file.json", "r")


@patch("requests.get")
def test_load_json_from_url_success(mock_get):
    mock_get.return_value.json.return_value = {"key": "value"}
    mock_get.return_value.status_code = 200

    result = load_json("http://example.com", verbose=False)
    assert result == {"key": "value"}
    mock_get.assert_called_once_with("http://example.com")


@patch("requests.get")
def test_load_json_from_url_failure(mock_get):
    mock_get.side_effect = Exception("Request failed")

    with pytest.raises(Exception):
        load_json("http://example.com", verbose=False)


def test_collect_refs():
    schema = {
        "properties": {
            "name": {"$ref": "http://example.com/schema1"},
            "age": {"type": "integer"},
        }
    }

    refs = collect_refs(schema)
    assert refs == ["http://example.com/schema1"]


def test_collect_refs_with_relative_refs():
    schema = {
        "properties": {
            "name": {"$ref": "./schema1"},
            "age": {"type": "integer"},
        }
    }

    refs = collect_refs(schema, base_url="http://example.com")
    assert refs == ["http://example.com/schema1"]


@patch("validate_devschema.utils.click.secho")
def test_collect_refs_iterates_over_list(mock_secho):
    """
    Test that `collect_refs` processes each item in a list and constructs refs.
    """
    schema = {
        "$id": "http://mocked-schemas.local/schema.json",
        "properties": {
            "name": {
                "type": "string",
                "items": [
                    {"$ref": "http://example.com/schema1.json"},
                    {"$ref": "http://example.com/schema2.json"},
                ],
            }
        },
    }
    base_url = "http://mocked-schemas.local"

    refs = collect_refs(schema, base_url=base_url, verbose=True)

    assert refs == [
        "http://example.com/schema1.json",
        "http://example.com/schema2.json",
    ]

    expected_ref1 = "INFO: Found $ref: http://example.com/schema1.json"
    expected_ref2 = "INFO: Found $ref: http://example.com/schema2.json"

    mock_secho.assert_any_call(expected_ref1, fg="cyan")
    mock_secho.assert_any_call(expected_ref2, fg="cyan")

    assert mock_secho.call_count == 2
