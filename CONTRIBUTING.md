# Contributing to the FOLIO Python Library

Thank you for your interest in contributing to the FOLIO Python library! 

We welcome contributions from the community and appreciate your help in making this project better.

## How to Contribute

### How to Report Bugs

If you find a bug in the project, please open an issue on our [GitHub Issues](https://github.com/alea-institute/folio-python/issues) page.

When reporting a bug, please include:
 - A clear and descriptive title
 - A detailed description of the issue, including:
   - Steps to reproduce the bug
   - Expected behavior
   - Actual behavior, including any relevant logs, error messages, or screenshots


## How to Suggest Enhancements

If you have an idea for an enhancement to the project, please open an issue on our [GitHub Issues](https://github.com/alea-institute/folio-python/issues) page
with the prefix ENH, like this:
`[ENH] Suggested feature`

## How to PR

If you'd like to PR code to the project, please follow these steps to submit a pull request:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes in the new branch
4. Add tests for your changes (if applicable)
5. Run the docker test suite to ensure all tests pass
6. Commit your changes with a clear and descriptive commit message
7. Push your branch to your fork
8. Open a pull request against the main repository


## Development and Testing

To set up the project for development:

* Fork the repository
* Clone the repository to your development environment
* Ensure that you have poetry installed:
  - You can install via the [official instructions](https://python-poetry.org/docs/main/#installing-with-the-official-installer).
  - Or you can install via [pipx](https://github.com/pypa/pipx): `pipx install poetry`
* Install the development dependencies: `poetry install`
* Make your changes.
* Test:
  - Run the test suite: `PYTHONPATH=. poetry run pytest tests/`
  - Test full build via docker (Ubuntu 24.04): `bash docker/build.sh`
  - Test clean install via docker (Ubuntu 22.04, Ubuntu 24.04): `bash docker/install.sh`

## Coding Style

We generally follow the [PEP 8](https://pep8.org/) style guide for Python code, but the good news is that most style
is enforced automatically via the `pre-commit` hooks in this repository.

Simply install [pre-commit](https://pre-commit.com/) and run `pre-commit install` to set up the hooks. 

If you'd like to run the formatting and linting checks manually, you can do so with the following commands:
```bash
$ pre-commit run --all-files
```

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Discussion Forums

Additional discussions about the project can be found on the [FOLIO Discourse community](https://discourse.openlegalstandard.org/).

## Questions

If you have any questions about contributing, please open an issue or contact the project maintainers.

Thank you for your contributions to the FOLIO Python library!
