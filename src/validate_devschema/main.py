import click
from .validate_schema import validate_schema
from .utils import load_json, is_url


@click.command()
@click.argument("schema", required=False, type=str)
@click.argument("data", required=False, type=str)
@click.option(
    "--schema",
    "-s",
    "schema_flag",
    type=str,
    help="Path or URL to the JSON schema.",
)
@click.option(
    "--data", "-d", "data_flag", type=str, help="Path or URL to the JSON data."
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def main(schema, data, schema_flag, data_flag, verbose):
    """
    Validate a JSON file or URL (DATA) against a JSON schema file or URL
    (SCHEMA).
    """
    schema_path = schema_flag or schema
    data_path = data_flag or data

    if not schema_path or not data_path:
        click.secho(
            "ERROR: Either provide positional arguments <schema> <data> or "
            "use the --schema and --data options.",
            fg="red",
        )
        exit(1)

    if verbose:
        schema_type = "URL" if is_url(schema_path) else "file"
        data_type = "URL" if is_url(data_path) else "file"
        click.secho(
            f"INFO: Schema is a {schema_type}: {schema_path}", fg="blue"
        )
        click.secho(f"INFO: Data is a {data_type}: {data_path}", fg="blue")
        click.secho(
            f"INFO: Validating {data_path} against {schema_path}...",
            fg="yellow",
        )

    try:
        schema = load_json(schema_path, verbose=verbose)
        data = load_json(data_path, verbose=verbose)

        success = validate_schema(schema, data, schema_path, verbose)

        if success:
            click.secho(
                "✅ INFO: Schema validation completed successfully.",
                fg="green",
            )
        else:
            click.secho(
                "❌ ERROR: Schema validation failed. Please check the errors.",
                fg="red",
            )
        exit(0 if success else 1)

    except Exception as e:
        click.secho(f"ERROR: {e}", fg="red")
        if verbose:
            click.secho(f"DEBUG: Exception details: {e}", fg="red")
        exit(1)


if __name__ == "__main__":
    main()
