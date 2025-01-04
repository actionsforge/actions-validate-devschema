import pytest
from unittest.mock import patch
from click.testing import CliRunner
from validate_devschema.main import main


@pytest.fixture
def mock_load_json():
    with patch("validate_devschema.main.load_json") as mock:
        yield mock


@pytest.fixture
def mock_validate_schema():
    with patch("validate_devschema.main.validate_schema") as mock:
        yield mock


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_is_url():
    with patch("validate_devschema.main.is_url") as mock:
        yield mock


def test_main_with_valid_file(
    mock_load_json, mock_validate_schema, mock_is_url
):
    mock_load_json.return_value = {"key": "value"}
    mock_validate_schema.return_value = True
    mock_is_url.return_value = False

    runner = CliRunner()
    result = runner.invoke(main, ["schema.json", "data.json", "--verbose"])

    print(f"Exit Code: {result.exit_code}")
    print(f"Output: {result.output}")

    assert result.exit_code == 0, f"Test failed with output: {result.output}"

    mock_load_json.assert_any_call("schema.json", verbose=True)
    mock_load_json.assert_any_call("data.json", verbose=True)


def test_main_with_missing_arguments(runner):
    result = runner.invoke(main)

    print(f"Exit Code: {result.exit_code}")
    print(f"Output: {result.output}")

    assert result.exit_code == 1, f"Test failed with output: {result.output}"
    assert (
        "ERROR: Either provide positional arguments <schema> <data> or "
        "use the --schema and --data options." in result.output
    )


def test_main_with_schema_validation_failure(runner):
    with patch("validate_devschema.main.load_json") as mock_load_json, patch(
        "validate_devschema.main.validate_schema"
    ) as mock_validate_schema:

        mock_load_json.return_value = {"key": "value"}

        mock_validate_schema.return_value = False

        result = runner.invoke(main, ["schema.json", "data.json", "--verbose"])

        print(f"Exit Code: {result.exit_code}")
        print(f"Output: {result.output}")

        assert (
            result.exit_code == 1
        ), f"Test failed with output: {result.output}"
        assert (
            "❌ ERROR: Schema validation failed. Please check the errors."
            in result.output
        )


def test_main_with_exception(runner):
    with patch("validate_devschema.main.click.secho") as mock_secho:
        with patch("validate_devschema.main.load_json") as mock_load_json:
            mock_load_json.side_effect = Exception("Simulated Exception")
            result = runner.invoke(
                main, ["schema.json", "data.json", "--verbose"]
            )

            print(f"Exit Code: {result.exit_code}")
            print(f"Output: {result.output}")
            assert (
                result.exit_code == 1
            ), f"Test failed with output: {result.output}"

            mock_secho.assert_any_call("ERROR: Simulated Exception", fg="red")
            mock_secho.assert_any_call(
                "DEBUG: Exception details: Simulated Exception", fg="red"
            )
