import json
import requests
from urllib.parse import urlparse
import click


def is_url(path: str) -> bool:
    """
    Check if a given path is a URL.

    Args:
        path: The path to check.

    Returns:
        True if the path is a valid URL, False otherwise.
    """
    parsed = urlparse(path)
    return parsed.scheme in ("http", "https")


def load_json(path_or_url: str, verbose: bool = False) -> dict:
    """
    Load JSON from a file or URL.

    Args:
        path_or_url: The path or URL to load JSON from.
        verbose: Flag to enable verbose output.

    Returns:
        The loaded JSON object.
    """
    if is_url(path_or_url):
        if verbose:
            click.secho(
                f"INFO: Fetching JSON from URL: {path_or_url}", fg="blue"
            )
        try:
            response = requests.get(path_or_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if verbose:
                click.secho(
                    f"ERROR: Failed to fetch JSON from URL: {e}", fg="red"
                )
            raise
    else:
        if verbose:
            click.secho(
                f"INFO: Loading JSON from file: {path_or_url}", fg="blue"
            )
        try:
            with open(path_or_url, "r") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            if verbose:
                click.secho(
                    f"ERROR: Failed to load JSON from file: {e}", fg="red"
                )
            raise


def collect_refs(
    schema: dict, base_url: str = "", verbose: bool = False
) -> list[str]:
    """
    Collect all `$ref` URLs from a schema.

    Args:
        schema: The JSON schema to scan.
        base_url: The base URL for resolving relative $refs.
        verbose: Flag to enable verbose output.

    Returns:
        A list of all resolved `$ref` URLs.
    """
    refs = []

    def _collect(schema_part, current_base_url):
        if isinstance(schema_part, dict):
            if "$ref" in schema_part:
                ref = schema_part["$ref"]
                if (
                    not ref.startswith(("http://", "https://"))
                    and current_base_url
                ):
                    ref = f"{current_base_url.rstrip('/')}/{ref.lstrip('./')}"
                refs.append(ref)
                if verbose:
                    click.secho(f"INFO: Found $ref: {ref}", fg="cyan")
            for value in schema_part.values():
                _collect(value, current_base_url)
        elif isinstance(schema_part, list):
            for item in schema_part:
                _collect(item, current_base_url)

    _collect(schema, base_url)
    return refs
