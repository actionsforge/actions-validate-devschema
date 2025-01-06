import jsonschema
import pytest
from jsonschema import ValidationError
from unittest.mock import call, patch
from validate_devschema.validate_schema import (
    merge_all_of,
    resolve_references,
    resolve_internal_ref,
    validate_schema,
)


@patch("validate_devschema.validate_schema.load_json")
def test_no_ref_in_schema(mock_load_json):
    schema_without_refs = {
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "type": "object",
    }

    mock_load_json.return_value = {}

    base_url = "http://mocked-schemas.local/"

    resolved_schema = resolve_references(
        schema_without_refs, base_url, verbose=True
    )

    assert resolved_schema == schema_without_refs
    assert "properties" in resolved_schema
    assert "name" in resolved_schema["properties"]
    assert "age" in resolved_schema["properties"]


@patch("validate_devschema.validate_schema.load_json")
def test_invalid_ref_in_schema(mock_load_json):
    schema_with_invalid_ref = {
        "properties": {"mount": {"$ref": "nonexistent-ref"}},
        "type": "object",
    }

    mock_load_json.side_effect = ValueError(
        "Invalid internal reference: nonexistent-ref"
    )

    base_url = "http://mocked-schemas.local/"

    with pytest.raises(ValueError, match="Invalid reference: nonexistent-ref"):
        resolve_references(schema_with_invalid_ref, base_url, verbose=False)


@patch("validate_devschema.validate_schema.load_json")
def test_relative_ref(mock_load_json):
    schema = {
        "properties": {"config": {"$ref": "./base-schema.json"}},
        "type": "object",
    }
    mock_base_schema = {
        "type": "object",
        "properties": {"key": {"type": "string"}},
    }
    mock_load_json.return_value = mock_base_schema

    resolved = resolve_references(
        schema, "http://mocked-base.local", verbose=True
    )
    assert "config" in resolved["properties"]
    assert "key" in resolved["properties"]["config"]["properties"]


def test_skip_unsupported_references():
    schema_with_unsupported_ref = {
        "properties": {
            "config": {"$ref": "vscode://schemas/settings/machine"}
        },
        "type": "object",
    }

    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(
        schema_with_unsupported_ref, base_url, verbose=False
    )

    assert "config" in resolved_schema["properties"]
    assert (
        resolved_schema["properties"]["config"]["$ref"]
        == "vscode://schemas/settings/machine"
    )


def test_missing_definitions():
    schema_with_missing_def = {
        "properties": {"mount": {"$ref": "#/definitions/Mount"}},
        "type": "object",
    }

    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(
        schema_with_missing_def, base_url, verbose=False
    )

    assert "mount" in resolved_schema["properties"]
    mount_schema = resolved_schema["properties"]["mount"]
    assert "$ref" in mount_schema
    assert mount_schema["$ref"] == "#/definitions/Mount"


def test_valid_schema():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
    }
    resolved_schema = resolve_references(
        schema, "http://mocked-schemas.local/"
    )
    assert "name" in resolved_schema["properties"]
    assert resolved_schema["properties"]["name"]["type"] == "string"


def test_circular_references():
    circular_schema = {
        "properties": {"mount": {"$ref": "#/properties/mount"}},
        "type": "object",
    }
    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(circular_schema, base_url)
    assert "mount" in resolved_schema["properties"]
    assert (
        resolved_schema["properties"]["mount"]["$ref"] == "#/properties/mount"
    )


def test_no_references_in_schema():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
    }
    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(schema, base_url)
    assert resolved_schema == schema


@patch("validate_devschema.validate_schema.load_json")
def test_external_url_ref(mock_load_json):
    schema_with_url_ref = {
        "properties": {
            "mount": {"$ref": "http://external-schema.local/mount"}
        },
        "type": "object",
    }
    resolved_external_ref = {
        "type": "object",
        "properties": {"source": {"type": "string"}},
    }
    mock_load_json.return_value = resolved_external_ref

    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(schema_with_url_ref, base_url)
    assert "mount" in resolved_schema["properties"]
    assert (
        resolved_schema["properties"]["mount"]["properties"]["source"]["type"]
        == "string"
    )


@patch("validate_devschema.validate_schema.load_json")
def test_unsupported_vscode_reference(mock_load_json):
    schema_with_vscode_ref = {
        "properties": {"mount": {"$ref": "vscode://unsupported-ref"}},
        "type": "object",
    }

    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(
        schema_with_vscode_ref, base_url, verbose=True
    )

    assert "mount" in resolved_schema["properties"]
    assert "$ref" in resolved_schema["properties"]["mount"]
    assert (
        resolved_schema["properties"]["mount"]["$ref"]
        == "vscode://unsupported-ref"
    )


@patch("validate_devschema.validate_schema.resolve_internal_ref")
def test_internal_reference(mock_resolve_internal_ref):
    schema_with_internal_ref = {
        "properties": {"mount": {"$ref": "#/definitions/Mount"}},
        "definitions": {
            "Mount": {
                "type": "object",
                "properties": {"source": {"type": "string"}},
            }
        },
        "type": "object",
    }

    mock_resolve_internal_ref.return_value = schema_with_internal_ref[
        "definitions"
    ]["Mount"]
    base_url = "http://mocked-schemas.local/"
    resolved_schema = resolve_references(
        schema_with_internal_ref, base_url, verbose=True
    )

    assert "mount" in resolved_schema["properties"]
    assert "source" in resolved_schema["properties"]["mount"]["properties"]


def test_resolve_internal_ref_nested():
    schema = {
        "definitions": {
            "Mount": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                    }
                },
            }
        }
    }
    ref = "#/definitions/Mount/properties/source"
    resolved = resolve_internal_ref(schema, ref)

    assert resolved == {
        "type": "object",
        "properties": {"url": {"type": "string"}},
    }


def test_resolve_external_ref_with_error_verbose():
    schema_with_external_ref = {
        "properties": {
            "mount": {"$ref": "http://mocked-schemas.local/mocked-ref"}
        }
    }
    base_url = "http://mocked-schemas.local/"

    with patch(
        "validate_devschema.validate_schema.load_json",
        side_effect=Exception("Network error"),
    ), patch("builtins.print") as mock_print:
        result = resolve_references(
            schema_with_external_ref, base_url, verbose=True
        )

    mock_print.assert_called_once_with(
        "Warning: Failed to resolve external refs: Network error"
    )

    expected_result = {
        "properties": {
            "mount": {"$ref": "http://mocked-schemas.local/mocked-ref"}
        }
    }
    assert result == expected_result


def test_resolve_internal_ref_error_verbose():
    schema_with_invalid_internal_ref = {
        "properties": {"mount": {"$ref": "#/invalid/path"}}
    }
    base_url = "http://mocked-schemas.local/"

    with patch("builtins.print") as mock_print:
        result = resolve_references(
            schema_with_invalid_internal_ref, base_url, verbose=True
        )

    mock_print.assert_called_once_with(
        "Warning: Invalid internal reference: #/invalid/path"
    )
    assert result == {"properties": {"mount": {"$ref": "#/invalid/path"}}}


def test_merge_all_of_no_allof():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    result = merge_all_of(
        schema, base_url="http://mocked-schemas.local/", verbose=False
    )
    assert result == schema


def test_merge_all_of_with_verbose_output():
    schema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string"}}},
            {"type": "object", "properties": {"age": {"type": "integer"}}},
        ]
    }
    with patch("click.secho") as mock_secho:
        merge_all_of(
            schema, base_url="http://mocked-schemas.local/", verbose=True
        )
        assert mock_secho.call_count >= 2


@patch("validate_devschema.validate_schema.load_json")
@patch("validate_devschema.validate_schema.resolve_references")
def test_merge_all_of_ref_resolution_simple(
    mock_resolve_references, mock_load_json
):
    schema = {
        "allOf": [
            {"$ref": "schema1.json"},
            {"type": "object", "properties": {"age": {"type": "integer"}}},
        ]
    }
    base_url = "http://mocked-schemas.local/"
    resolved_schema1 = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }

    mock_load_json.return_value = resolved_schema1
    mock_resolve_references.side_effect = lambda s, b, v: s

    result = merge_all_of(schema, base_url, verbose=False)

    expected = {
        "properties": {
            "age": {"type": "integer"},
        },
        "type": "object",
    }

    assert result == expected

    mock_load_json.assert_called_once_with(
        "http://mocked-schemas.local/schema1.json", False
    )


@patch(
    "validate_devschema.validate_schema.resolve_references",
    return_value={
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}
    },
)
@patch(
    "validate_devschema.validate_schema.merge_all_of",
    return_value={
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}
    },
)
@patch("validate_devschema.validate_schema.jsonschema.validate")
def test_validate_schema_success(
    mock_validate, mock_merge_all_of, mock_resolve_references
):
    schema = {"$id": "http://mocked-schemas.local/schema.json"}
    instance = {"name": "Alice", "age": 30}
    result = validate_schema(
        schema, instance, schema_url=schema["$id"], verbose=False
    )
    assert result is True


@patch(
    "validate_devschema.validate_schema.resolve_references",
    return_value={
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}
    },
)
@patch(
    "validate_devschema.validate_schema.merge_all_of",
    return_value={
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}
    },
)
@patch(
    "validate_devschema.validate_schema.jsonschema.validate",
    side_effect=[
        None,
        jsonschema.ValidationError("Validation failed for age"),
    ],
)
def test_validate_schema_failure(
    mock_validate, mock_merge_all_of, mock_resolve_references
):
    schema = {"$id": "http://mocked-schemas.local/schema.json"}
    instance = {"name": "Alice", "age": "invalid"}

    result = validate_schema(
        schema, instance, schema_url=schema["$id"], verbose=True
    )

    expected_calls = [
        call({"name": "Alice"}, {"name": {"type": "string"}}),
        call({"age": "invalid"}, {"age": {"type": "integer"}}),
    ]
    print(mock_validate.mock_calls)
    assert mock_validate.call_count == 2
    mock_validate.assert_has_calls(expected_calls, any_order=False)

    assert result is False


@patch("validate_devschema.validate_schema.load_json")
def test_resolve_references_list(mock_load_json):
    base_url = "http://mocked-schemas.local/"
    schema_with_list = [
        {"$ref": "./schema1.json"},
        {"type": "object", "properties": {"age": {"type": "integer"}}},
    ]

    resolved_schema1 = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }

    mock_load_json.return_value = resolved_schema1

    result = resolve_references(schema_with_list, base_url, verbose=False)

    expected_result = [
        {"type": "object", "properties": {"name": {"type": "string"}}},
        {"type": "object", "properties": {"age": {"type": "integer"}}},
    ]

    assert result == expected_result
    mock_load_json.assert_called_once_with(
        "http://mocked-schemas.local/schema1.json", False
    )


@patch("validate_devschema.validate_schema.load_json")
@patch("validate_devschema.validate_schema.resolve_references")
@patch("validate_devschema.validate_schema.click.secho")
def test_merge_all_of_resolving_ref_message(
    mock_secho, mock_resolve_references, mock_load_json
):
    base_url = "http://mocked-schemas.local/"
    schema = {
        "allOf": [
            {"$ref": "./schema1.json"},
            {"type": "object", "properties": {"age": {"type": "integer"}}},
        ]
    }

    resolved_schema1 = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }

    mock_load_json.return_value = resolved_schema1
    mock_resolve_references.side_effect = (
        lambda schema, base_url, verbose: schema
    )

    merge_all_of(schema, base_url, verbose=True)

    expected_message = (
        "INFO: Resolving $ref in `allOf`: "
        "http://mocked-schemas.local/schema1.json"
    )
    mock_secho.assert_any_call(expected_message, fg="yellow")


def dummy_jsonschema_validate(instance, schema):
    """
    Dummy jsonschema.validate implementation for testing.
    Raises exceptions based on input.
    """
    if "name" in instance and instance["name"] == "invalid":
        raise jsonschema.ValidationError("Validation failed")
    if "age" in instance and instance["age"] == "unexpected":
        raise Exception("Unexpected error occurred")
