# Technology Stack

**Analysis Date:** 2026-04-07

## Languages

**Primary:**
- Python 3.10+ - Full library implementation; supports 3.10, 3.11, 3.12, 3.13
- XML/OWL - Ontology format (FOLIO.owl files parsed via lxml)

**Configuration:**
- TOML - Project configuration (`pyproject.toml`)
- YAML - CI/CD and documentation config
- JSON - Runtime configuration files

## Runtime

**Environment:**
- Python 3.10–3.13 (configurable, currently testing on 3.13)

**Package Manager:**
- UV (fast Python package manager) - Primary
- pip - Fallback in CI/CD workflows
- poetry - Used in legacy CI workflow (`.github/workflows/CI.yml` line 56)
- Lockfile: `uv.lock` present (reproducible builds)

## Frameworks

**Core:**
- pydantic 2.8.2+ - Data validation and OWL model definitions (`folio/models.py`)
- lxml 5.2.2+ - XML/OWL ontology parsing (`folio/graph.py`)
- httpx 0.27.2+ - HTTP client for GitHub API and remote ontology loading (`folio/graph.py` lines 31, 279–281, 420, 447)

**Search (Optional):**
- rapidfuzz 3.10.0–3.x - Fuzzy string matching for label search (`folio/graph.py` lines 132–134, 1357–1363)
- marisa-trie 1.2.0–1.x - Trie-based efficient label indexing (`folio/graph.py` lines 138–139, 1005, 1012)
- alea-llm-client 0.1.1+ - AI model integration for semantic search (`folio/graph.py` lines 144–152, 247)

**Testing:**
- pytest 8.3.1–8.x - Test runner
- pytest-asyncio 0.23.8–0.24.x - Async test support
- pytest-benchmark 4.0.0–4.x - Performance benchmarking
- pytest-cov 5.0.0–5.x - Code coverage reporting

**Development:**
- black 24.4.2–24.x - Code formatting
- pylint 3.2.7–3.x - Linting
- ruff (v0.6.3) - Fast linting and formatting via pre-commit
- isort - Import sorting (configured via `pyproject.toml` lines 127–129)
- types-lxml 2024.8.7–2024.x - Type hints for lxml

**Documentation:**
- Sphinx 7.4.7–7.x - Documentation generation
- myst-parser 3.0.1–3.x - Markdown support in Sphinx
- sphinx-book-theme 1.1.3–1.x - Modern Sphinx theme
- sphinxcontrib-mermaid 0.9.2–0.10.x - Diagram support
- sphinx-copybutton 0.5.2–0.6.x - Copy-to-clipboard for code
- sphinxext-opengraph 0.9.1–0.10.x - Open Graph meta tags
- sphinx-plausible 0.1.2–0.2.x - Privacy-focused analytics

**Build:**
- hatchling (build backend in `pyproject.toml` line 106)
- pip - Build tool wrapper

## Key Dependencies

**Critical:**
- pydantic - Validates and structures OWL class/property models; required for all parsing
- lxml - Parses OWL XML ontology files; no fallback
- httpx - Fetches ontology from GitHub API (`https://api.github.com`) and GitHub Objects (`https://raw.githubusercontent.com`)

**Infrastructure:**
- alea-llm-client 0.1.3 (in uv.lock) - Wraps OpenAI API for LLM-based semantic search; graceful fallback if not installed (`folio/graph.py` lines 144–152)
- rapidfuzz - Enables fuzzy label search; degrades gracefully (`folio/graph.py` line 135)
- marisa-trie - Enables prefix-based label trie search; degrades gracefully (`folio/graph.py` line 141)

## Configuration

**Environment:**
- Configuration loaded from `~/.folio/config.json` via `FOLIOConfiguration.load_config()` in `folio/config.py` lines 87–128
- Environment variables: None required; all config via JSON file or constructor parameters
- GitHub API: Accessed via httpx with default base URL `https://api.github.com` (`folio/config.py` line 23)
- GitHub Objects: Accessed via `https://raw.githubusercontent.com` for raw file downloads (`folio/config.py` line 24)

**Build:**
- `pyproject.toml` lines 75–79: UV default dependency groups include `["dev", "search"]`
- ruff configuration: black profile, 120 character line length (`.pre-commit-config.yaml` line 21)
- isort configuration: black profile, 120 character line length (`pyproject.toml` lines 127–129)

**Key Configs Required:**
- Source type: `"github"` (default) or `"http"` (`folio/config.py` lines 46–47)
- GitHub repo owner: `"alea-institute"` (default, `folio/config.py` line 33)
- GitHub repo name: `"FOLIO"` (default, `folio/config.py` line 34)
- GitHub repo branch: `"2.0.0"` (default, `folio/config.py` line 35)
- HTTP URL: Optional, only for `"http"` source type (`folio/config.py` line 30)
- Caching: Enabled by default at `~/.folio/cache/` (`folio/graph.py` line 110)

## Platform Requirements

**Development:**
- Python 3.10+ with pip/UV
- lxml build dependencies (libxml2, libxslt on Ubuntu: `sudo apt-get install libxml2-dev libxslt1-dev`)
- Git (for cloning FOLIO ontology from GitHub)
- Pre-commit hooks configured (ruff, gitleaks security scanner)

**Production:**
- Python 3.10+
- Network access to `https://api.github.com` and `https://raw.githubusercontent.com` (if using GitHub source)
- Local filesystem access for caching (`~/.folio/cache/`)
- OpenAI API key environment variable if using LLM search (`OPENAI_API_KEY` for alea-llm-client)

**CI/CD Deployment:**
- GitHub Actions workflow triggers on release (publish.yml) and push/PR to main/dev (CI.yml)
- PyPI publishing via `pypa/gh-action-pypi-publish@release/v1` (trusted publishing, OIDC)
- Read the Docs integration: Build configuration in `.readthedocs.yaml` lines 1–32 (Python 3.11, Sphinx)
- Supported architectures: x86_64, x86, aarch64, armv7, s390x, ppc64le (via maturin in CI.yml)

## Dependency Groups

**[project.optional-dependencies] - search:**
- rapidfuzz 3.10.0–3.x
- marisa-trie 1.2.0–1.x
- alea-llm-client 0.1.1+

**[dependency-groups.dev:**
- Testing: pytest, pytest-asyncio, pytest-benchmark, pytest-cov
- Linting: pylint, black (deprecated in favor of ruff)
- Documentation: Sphinx, myst-parser, sphinx-book-theme, sphinxcontrib-mermaid
- Type hints: types-lxml

**[dependency-groups.search:**
- Same as `[project.optional-dependencies.search]` but with explicit versions (rapidfuzz 3.9.7+, alea-llm-client <0.2)

---

*Stack analysis: 2026-04-07*
