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

Use Python 3.10 or newer and [uv](https://docs.astral.sh/uv/getting-started/installation/). The hygiene workflow uses uv 0.9.22 and checks Python 3.10 and 3.14 on Linux.

```bash
uv sync --frozen --no-default-groups --group dev --extra search
uv run --frozen ruff check folio/ tests/
uv run --frozen ruff format --check folio/ tests/
uv run --frozen ty check folio/
```

The locked checker targets Python 3.10. Optional search dependencies are installed for static checking, but remain optional for library users.

For the deterministic suite, first build an isolated core-only installation. Choose the same Python version for both environments; this example uses 3.10:

```bash
uv sync --frozen --python 3.10 --no-default-groups --group dev --extra search
UV_PROJECT_ENVIRONMENT=/tmp/folio-core uv sync --frozen --python 3.10 --no-default-groups --no-editable
FOLIO_CORE_PYTHON=/tmp/folio-core/bin/python uv run --frozen pytest tests/ --ignore=tests/test_folio.py -o addopts='--cov=folio --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=58'
```

The 58% floor is the rounded-down combined statement/branch coverage of this exact offline selection. Coverage includes every `folio` module. The core-only test runs the installed wheel with an isolated Python import path, verifies that all three optional search distributions are absent, and exercises local parsing, prefix/text queries, and missing-extra errors. Without `FOLIO_CORE_PYTHON`, that one test explicitly skips. The subprocess contributes no coverage credit.

Keep the live ontology integration tests and benchmarks passing too:

```bash
FOLIO_CORE_PYTHON=/tmp/folio-core/bin/python uv run --frozen pytest tests/
```

That suite uses public GitHub/HTTP ontology inputs. Record network failures separately from library regressions. The existing full-suite and release workflows remain separate from `.github/workflows/hygiene.yml`.

### Dependency audits

Audit locked scopes explicitly: the development group named `search` is distinct from the published extra. These exports preserve version markers and hashes and omit the local project:

```bash
uv export --frozen --no-default-groups --no-emit-project --no-header --no-annotate -o /tmp/folio-core.txt
uv export --frozen --no-default-groups --extra search --no-emit-project --no-header --no-annotate -o /tmp/folio-search.txt
uv export --frozen --only-group dev --no-emit-project --no-header --no-annotate -o /tmp/folio-dev.txt
uvx --python 3.12 pip-audit==2.9.0 -r /tmp/folio-core.txt --require-hashes --disable-pip --strict --progress-spinner off --format json -o /tmp/folio-core-audit.json
uvx --python 3.12 pip-audit==2.9.0 -r /tmp/folio-search.txt --require-hashes --disable-pip --strict --progress-spinner off --format json -o /tmp/folio-search-audit.json
uvx --python 3.12 pip-audit==2.9.0 -r /tmp/folio-dev.txt --require-hashes --disable-pip --strict --progress-spinner off --format json -o /tmp/folio-dev-audit.json
```

Use `--disable-pip` only with these complete locked exports: it avoids resolution and installation during auditing. Retain the interpreter/platform, export digests, inventories, exit codes, and collection errors. Markers for other interpreters/platforms are not evaluated by a single run. A clean scan means no known advisories returned by that feed for those selected versions, not proof of safety for every version allowed by the published dependency ranges. Check direct published minimum versions separately when changing constraints. Do not suppress findings or use automatic audit fixes.

The [fp-4 receipt](docs/plans/evidence/fp-4-hygiene.md) contains baseline/final metrics, dependency remediation, and the limits of local verification.

## Documentation

User-facing documentation lives in the [openlegalstandard.org](https://github.com/alea-institute/openlegalstandard.org) repository under [`src/pages/resources/folio-python-library/`](https://github.com/alea-institute/openlegalstandard.org/tree/main/src/pages/resources/folio-python-library), and is published at **[openlegalstandard.org/resources/folio-python-library](https://openlegalstandard.org/resources/folio-python-library)**.

PRs that change public API (signatures, defaults, behavior) should also update the matching sub-page in that repo so the docs stay in sync. Every code snippet in the docs is validated against the published wheel via `uv run python`, so please run any new examples before submitting.

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
