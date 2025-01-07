# Validate DevSchema GitHub Action

![Validate DevSchema Test](https://github.com/actionsforge/actions-validate-devschema/actions/workflows/validate-schema-test.yml/badge.svg)

This GitHub Action validates JSON files against a specified DevContainer schema.

## Inputs

**Note**: The default `schema` has been tested and verified to work. If you customize the `schema`, ensure that it is a valid JSON schema to avoid validation errors.

| Name           | Description                              | Required | Default                                                                 |
|----------------|------------------------------------------|----------|-------------------------------------------------------------------------|
| `schema`       | Path or URL to the JSON schema.          | No       | `https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json` |
| `data`         | Path or URL to the JSON data.            | No       | `devcontainer/devcontainer.json`                                       |
| `verbose`      | Enable verbose output (true/false).      | No       | `false`                                                                |
| `python-version` | Python version to use. Allowed versions are: 3.9, 3.10, 3.11, 3.12, 3.13.                  | No       | `3.13`                                                                 |

## Usage

```yaml
jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Validate Devcontainer Schema
        uses: actionsforge/actions-validate-devschema@v1
        with:
          verbose: true
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
