# External Integrations

**Analysis Date:** 2026-04-07

## APIs & External Services

**GitHub API:**
- GitHub Repositories - Fetch FOLIO ontology metadata and raw ontology files
  - SDK/Client: httpx (HTTP client)
  - Endpoint: `https://api.github.com/repos/{repo_owner}/{repo_name}/branches` (list branches)
  - Implementation: `folio/graph.py` lines 257–292 (`FOLIO.list_branches()`)
  - Authentication: Optional GitHub token via headers (not currently enforced)
  - Default repo: `alea-institute/FOLIO` branch `2.0.0`

**GitHub Objects (Raw Content):**
- GitHub Raw File CDN - Stream ontology OWL XML files
  - SDK/Client: httpx (HTTP client with redirect following)
  - Endpoint: `https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/FOLIO.owl`
  - Implementation: `folio/graph.py` lines 401–434 (`FOLIO.load_owl_github()`)
  - Authentication: None required for public repos
  - Caching: Local cache at `~/.folio/cache/` to reduce API calls

**HTTP/Generic URLs:**
- Remote ontology servers - Load FOLIO.owl from any HTTP endpoint
  - SDK/Client: httpx (HTTP client with redirect following)
  - Endpoint: User-provided via `http_url` parameter or config
  - Implementation: `folio/graph.py` lines 437–457 (`FOLIO.load_owl_http()`)
  - Authentication: None built-in; user responsible for including auth in URL
  - Default: None (GitHub is preferred)

**OpenAI API (via alea-llm-client):**
- GPT-4o model for semantic label search
  - SDK/Client: alea-llm-client 0.1.1+ (wraps OpenAI SDK)
  - Model: `gpt-4o` (hardcoded default in `folio/graph.py` line 247)
  - Authentication: `OPENAI_API_KEY` environment variable (managed by alea-llm-client)
  - Implementation: `folio/graph.py` lines 244–250 (optional LLM initialization)
  - Graceful degradation: If `alea_llm_client` not installed or initialization fails, search falls back to rapidfuzz
  - Used by: Semantic search functionality via `search_with_decoder()` method (not shown in excerpt but referenced in comments)

## Data Storage

**Databases:**
- None used - Folio is a read-only ontology library

**File Storage:**
- Local filesystem only for caching
  - Cache directory: `~/.folio/cache/` (default, configurable via `DEFAULT_CACHE_DIR` in `folio/graph.py` line 110)
  - Cache structure: `{cache_root}/{source_type}/{hash(cache_key)}.owl`
  - Hash algorithm: BLAKE2b (256-bit, `folio/graph.py` line 334)
  - Persistence: Persistent across sessions; users responsible for cleanup

**Caching:**
- Local filesystem-based caching enabled by default
  - Implementation: `folio/graph.py` lines 295–398 (`FOLIO.load_cache()` and `FOLIO.save_cache()`)
  - Cache invalidation: Manual (no TTL); caching can be disabled via `use_cache=False` parameter
  - Scope: Per ontology source (GitHub repo/branch or HTTP URL)

## Authentication & Identity

**Auth Provider:**
- None built-in; library is read-only for public ontologies
- GitHub: No auth required for public `alea-institute/FOLIO` repository (the default)
- Custom HTTP: Users must include auth in URL if required
- OpenAI: Delegated to alea-llm-client; expects `OPENAI_API_KEY` environment variable

**Implementation:**
- GitHub API calls pass minimal headers (`Accept: application/vnd.github.v3+json` in `folio/graph.py` line 275)
- No API key management in folio codebase
- All auth is caller's responsibility

## Monitoring & Observability

**Error Tracking:**
- None configured - Library logs errors but doesn't integrate with external error tracking
- Local logging via `folio/logger.py` (standard Python logging)

**Logs:**
- Standard Python logging at module level
  - Logger initialized: `LOGGER = get_logger(__name__)` in `folio/graph.py` line 128
  - Log handler configured in `folio/logger.py`
  - Key log points:
    - Ontology load start/end with duration (`folio/graph.py` lines 222–233, 236–240)
    - Cache hits/misses (`folio/graph.py` lines 342, 347)
    - Search functionality availability (`folio/graph.py` lines 135, 141, 151)
    - LLM model initialization success/failure (`folio/graph.py` lines 250, 252–254)
    - GitHub branch listing (`folio/graph.py` line 280)

## CI/CD & Deployment

**Hosting:**
- GitHub source repository: `https://github.com/alea-institute/folio-python`
- Documentation: Read the Docs (`.readthedocs.yaml` configured)
- Package distribution: PyPI (Python Package Index)

**CI Pipeline:**
- GitHub Actions workflows in `.github/workflows/`
  - `CI.yml`: Runs on push to main/master/dev/test, PRs, and manual dispatch
    - Tests on multiple Linux architectures (x86_64, x86, aarch64, armv7, s390x, ppc64le)
    - Runs pytest suite with coverage reporting
    - Builds distribution artifacts
  - `publish.yml`: Triggers on GitHub release (published event)
    - Builds distribution (wheel and source)
    - Publishes to PyPI via `pypa/gh-action-pypi-publish@release/v1` (trusted publishing with OIDC)
    - No manual credentials needed in CI environment

**Build Process:**
- Build tool: `hatchling` (backend in `pyproject.toml` line 106)
- Build command: `python -m build` (`.github/workflows/publish.yml` line 22)
- Artifacts:
  - Source distribution (sdist): excludes tests, docs, examples, docker
  - Wheel: Binary distribution, excludes same

**Documentation Build:**
- Read the Docs configuration: `.readthedocs.yaml` (version 2 format)
- Python version: 3.11
- OS: Ubuntu 24.04
- Build tool: Sphinx
- Config file: `docs/conf.py`
- Output formats: HTML, PDF, ePub
- Requirements: `docs/requirements.txt`

## Environment Configuration

**Required env vars:**
- `OPENAI_API_KEY` - Only if using LLM semantic search (alea-llm-client requires this)
- All other configuration via JSON file (`~/.folio/config.json`) or constructor parameters

**Secrets location:**
- Not stored in repository (GitHub Actions uses trusted publishing, no API tokens in code)
- `OPENAI_API_KEY` should be set in user environment or GitHub Actions secrets (not configured in visible workflows)
- Pre-commit hook `gitleaks` (`.pre-commit-config.yaml` line 22) prevents accidental secret commits

**Configuration file structure:**
```json
{
  "folio": {
    "source": "github",
    "repo_owner": "alea-institute",
    "repo_name": "FOLIO",
    "branch": "2.0.0",
    "path": "FOLIO.owl",
    "use_cache": true
  }
}
```
- Location: `~/.folio/config.json` (home directory, `folio/config.py` line 20)
- Loaded by: `FOLIOConfiguration.load_config()` in `folio/config.py` lines 87–128

## Webhooks & Callbacks

**Incoming:**
- None - Library does not provide webhook endpoints

**Outgoing:**
- None - Library does not send webhooks

---

*Integration audit: 2026-04-07*
