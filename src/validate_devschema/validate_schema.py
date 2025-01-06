import json
import click
import jsonschema
from urllib.parse import urljoin
from .utils import load_json


def resolve_internal_ref(
    schema: dict, ref: str, verbose: bool = False
) -> dict:
    """
    Resolve an internal reference within the schema by walking through
    the reference path to find the target value.

    Args:
        schema (dict): The JSON schema where the reference is to be resolved.
        ref (str): The reference path to resolve, in the format "#/path/to/ref"
        verbose (bool): Whether to print additional debug information.

    Returns:
        dict: The value resolved from the reference.

    Raises:
        ValueError: If the reference is invalid or cannot be resolved.
    """
    parts = ref.lstrip("#/").split("/")
    resolved = schema

    for part in parts:
        if part not in resolved:
            raise ValueError(f"Invalid internal reference: {ref}")
        resolved = resolved[part]

    return resolved


def resolve_references(
    schema: dict, base_url: str, verbose: bool = False
) -> dict:
    """
    Recursively resolve `$ref` references within the schema. This function
    will handle both internal and external references, resolving them
    accordingly.

    Args:
        schema (dict): The JSON schema to resolve references within.
        base_url (str): The base URL for resolving relative `$ref` references.
        verbose (bool): Whether to output detailed information during the
            resolution process.

    Returns:
        dict: The schema with resolved references.
    """
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref = schema["$ref"]

            if ref.startswith("#"):
                try:
                    resolved = resolve_internal_ref(schema, ref, verbose)
                    return resolve_references(resolved, base_url, verbose)
                except ValueError as e:
                    if verbose:
                        print(f"Warning: {e}")
                    return {"$ref": ref}

            if ref.startswith(("./", "../", "http://", "https://")):
                try:
                    full_url = urljoin(base_url, ref)
                    external_schema = load_json(full_url, verbose)
                    return resolve_references(
                        external_schema, full_url, verbose
                    )
                except Exception as e:
                    if verbose:
                        print(f"Warning: Failed to resolve external refs: {e}")
                    return {"$ref": ref}

            if ref.startswith("vscode://"):
                if verbose:
                    print(f"Skipping unsupported reference: {ref}")
                return {"$ref": ref}

            raise ValueError(f"Invalid reference: {ref}")

        return {
            key: resolve_references(value, base_url, verbose)
            for key, value in schema.items()
        }

    elif isinstance(schema, list):
        return [resolve_references(item, base_url, verbose) for item in schema]

    return schema


def merge_all_of(schema: dict, base_url: str, verbose: bool = False) -> dict:
    """
    Resolve and merge all `allOf` schemas into a single schema.

    Args:
        schema: The JSON schema to process.
        base_url: The base URL for resolving relative $refs.
        verbose: Flag to enable verbose output.

    Returns:
        The schema with merged `allOf` entries.
    """
    if "allOf" not in schema:
        return schema

    if verbose:
        click.secho(
            "INFO: Resolving and merging `allOf` entries...", fg="blue"
        )

    merged = {}
    for i, sub_schema in enumerate(schema["allOf"]):
        if verbose:
            click.secho(
                f"DEBUG: Processing allOf[{i}]: {sub_schema}", fg="cyan"
            )
        if "$ref" in sub_schema:
            ref_url = sub_schema["$ref"]
            resolved_url = urljoin(base_url, ref_url)
            if verbose:
                click.secho(
                    f"INFO: Resolving $ref in `allOf`: {resolved_url}",
                    fg="yellow",
                )
            try:
                sub_schema = load_json(resolved_url, verbose)
                sub_schema = resolve_references(sub_schema, base_url, verbose)
            except Exception as e:
                if verbose:
                    print(f"Warning: Failed to resolve $ref {ref_url}: {e}")
                continue
        merged.update(sub_schema)

    schema.pop("allOf", None)
    schema.update(merged)
    return schema


def validate_schema(
    schema: dict, instance: dict, schema_url: str, verbose: bool = False
) -> bool:
    """
    Validate a JSON instance against a JSON schema.
    Only validate the instance attributes that are present in the schema.

    Args:
        schema: The JSON schema.
        instance: The JSON instance to validate.
        schema_url: The URL or path of the schema (for resolving references).
        verbose: Flag to enable verbose output.

    Returns:
        True if validation is successful, False otherwise.
    """
    try:
        base_url = schema.get("$id", schema_url).rsplit("/", 1)[0] + "/"
        if verbose:
            click.secho(
                f"INFO: Base URL for schema resolution: {base_url}",
                fg="yellow",
            )

        schema = resolve_references(schema, base_url, verbose)

        schema = merge_all_of(schema, base_url, verbose)

        if verbose:
            click.secho("INFO: Resolved Schema:", fg="blue")
            click.echo(json.dumps(schema, indent=2))

        click.secho("INFO: Starting schema validation...", fg="blue")
        valid = True
        for key, value in instance.items():
            if "properties" in schema and key in schema["properties"]:
                try:
                    jsonschema.validate(
                        {key: value}, {key: schema["properties"][key]}
                    )
                except jsonschema.ValidationError as e:
                    click.secho(
                        f"ERROR: Validation failed for {key}: {e.message}",
                        fg="red",
                    )
                    valid = False

        if valid:
            click.secho("INFO: Validation successful!", fg="green")
        return valid

    except jsonschema.ValidationError as e:
        print(f"DEBUG: Caught ValidationError: {e}")
        click.secho(f"ERROR: Validation failed: {e.message}", fg="red")
        if verbose:
            click.secho(f"DEBUG: Validation details: {e}", fg="red")
        return False
    except Exception as e:
        print(f"DEBUG: Caught Unexpected Exception: {e}")
        click.secho(
            f"ERROR: Unexpected error during validation: {e}", fg="red"
        )
        if verbose:
            click.secho(f"DEBUG: Exception details: {e}", fg="red")
        return False
