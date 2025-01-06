# Validate DevSchema

A lightweight GitHub Action DevContainer JSON Schema validator that can be used both as a **CLI** and in **GitHub Actions**.

## Prerequisites

- **Python 3.8+**
- **Poetry** (for dependency and environment management)

To install Poetry:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/validate-devschema.git
   cd validate-devschema
   ```

2. Install dependencies:

   ```bash
   poetry install --with dev
   ```

3. Ensure the virtual environment is activated:

   ```bash
   poetry shell
   ```

4. (Optional) Configure `PYTHONPATH` for testing:

   ```bash
   export PYTHONPATH=$(pwd)/src:$PYTHONPATH
   ```

## Exporting `requirements.txt` Using Poetry Add-on Plugin

If you need a `requirements.txt` file for environments that use `pip` (e.g., GitHub Actions):

1. Ensure the `poetry-plugin-export` plugin is installed:

   ```bash
   poetry self add poetry-plugin-export
   ```

2. Export dependencies to `requirements.txt`:

   ```bash
   poetry export --without-hashes --format=requirements.txt --output=requirements.txt
   ```

3. (Optional) To include development dependencies, use:

   ```bash
   poetry export --with dev --without-hashes --format=requirements.txt --output=requirements-dev.txt
   ```

The generated `requirements.txt` will contain all dependencies required for your project.

## Usage

Run the `validate-devschema` command to validate a JSON schema against data.

### Command Syntax

```bash
validate-devschema [OPTIONS] [SCHEMA] [DATA]
```

### Example

Validate a JSON file `data.json` against a schema `schema.json`:

```bash
validate-devschema schema.json data.json --verbose
```

Validate `.devcontainer/devcontainer.json` against the schema from DevContainer spec:

```bash
validate-devschema https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json .devcontainer/devcontainer.json --verbose
```

To see the help message:

```bash
validate-devschema --help
```

## Running Tests

Tests are located in the `tests/` directory. Use `pytest` to run them.

1. Run all tests:

   ```bash
   poetry run pytest
   ```

2. Run a specific test file:

   ```bash
   poetry run pytest tests/test_validate_schema.py
   ```

3. Run tests with coverage tracking:

   ```bash
   poetry run pytest --cov=src/validate_devschema --cov-report=term-missing tests/test_validate_schema.py
   ```

4. Run tests with coverage:

   ```bash
   poetry run pytest --cov=validate_devschema
   ```

## Common Issues

### `validate-devschema: command not found`

Ensure the Poetry virtual environment is active:

```bash
poetry shell
```

If you prefer not to use `poetry shell`, run the command with `poetry`:

```bash
poetry run validate-devschema --help
```

### Import Errors in Tests

Ensure `PYTHONPATH` includes the `src` directory:

```bash
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
```

## Project Structure

```plaintext
.
├── src
│   └── validate_devschema
│       ├── __init__.py
│       ├── main.py
│       ├── utils.py
│       └── validate_schema.py
├── tests
│   ├── test_utils.py
│   └── test_validate_schema.py
├── pyproject.toml
├── README.md
└── devcontainer-setup.sh
```
