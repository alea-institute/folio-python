# Sweep handoff: folio-python (cloud lane, cycle sweep-2026-10-20)

## Status on 2026-10-20

- **v0.4.1 has a GitHub release but is not on PyPI.**
  - 2026-09-30: PR #21 merged the v0.4.1 bump and `publish.yml`.
  - 2026-10-20 14:19 UTC: tag `v0.4.1` (`35814e6`) and its GitHub release were published.
  - 2026-10-20 14:20 UTC: Publish run 39438179508 built the package, then PyPI rejected the upload: `invalid-publisher: valid token, but no corresponding publisher`.
  - PyPI still lists `folio-python` 0.4.0 as latest.
  - Earlier publish runs for v0.3.4 and v0.3.5 also failed.
- **Code health at v0.4.1:**
  - CI run 39438179267 on the tag passed.
  - Cloud container, non-benchmark tests: 66 passed, 4 failed. All 4 failures (`test_list_branches`, `test_load_owl`, `test_load_owl_http`, `test_load_owl_nocache`) occur because this container's proxy blocks `api.github.com` and `github.com/.../raw`. The code itself does not cause them.
  - `ruff check` (pinned 0.15.6) passes. `ruff format` wanted one blank line in `folio/graph.py`; this branch adds it.
- **`fix/altlabel-lang-search`: nothing left to merge.**
  - 2026-03-17: PR #13 squash-merged it.
  - `folio/graph.py:701-703` on main already carries the change.
  - `git merge-tree` of main with the branch returns main's exact tree.

## Open questions and steps for Damien

### 1. Register the PyPI Trusted Publisher, then re-run publish (browser-with-logins)

Recommendation: do it. The v0.4.1 release cannot reach PyPI until this is done.

1. In PyPI, open `folio-python`, then Publishing, then "Add a new publisher" (GitHub). Enter: owner `alea-institute`, repository `folio-python`, workflow `publish.yml`, environment `pypi`. This must be done by a PyPI owner or maintainer of the project.
2. Re-run the failed jobs of Actions run 39438179508. The run uses the existing release, so no new tag or release is needed.
3. Check that https://pypi.org/project/folio-python/0.4.1/ exists.

Alternative: if a PyPI owner (for example mjbommar) prefers manual uploads, they can run `uv build && uv publish` from tag `v0.4.1`. That needs their PyPI credentials.

### 2. Delete merged branches (quick-decision; any machine with push rights)

This cloud session's git proxy refused branch deletion (HTTP 403), and the GitHub tools here cannot delete branches. Each branch below is safe to delete: its tip is an ancestor of `main`, or its merge into `main` changes nothing. GitHub's immutable PR refs also keep every tip.

| Branch | Tip | Backup |
| --- | --- | --- |
| `release/v0.4.1` | `96269e5` | ancestor of main; `refs/pull/21/head` |
| `fix/index-preferred-label` | `fe877af` | ancestor of main; `refs/pull/11/head` |
| `fix/altlabel-lang-search` | `303eb54` | change is in main; `refs/pull/13/head` |

```bash
git push origin --delete release/v0.4.1 fix/index-preferred-label fix/altlabel-lang-search
```

### 3. Old version branches `v0.1.0` to `v0.1.6` and `v.0.1.2` (quick-decision)

All are ancestors of main. The repo has no git tags for 0.1.x, so these branches serve as the only version markers. Recommendation: keep them. If you want them gone, first convert each to a lightweight tag. Tags do not trigger `publish.yml`, which runs only on published releases. Then delete the branches.

### 4. Leave as is: branches not merged into main

`cleanup/docs-migration`, `feature/case-insensitive-prefix`, and `pr/case-insensitive-prefix` belong to merged PRs #18 and #16. Main has since changed the same files, so merging any of them would bring back files and dependency entries that main no longer has. Recommendation: delete them once you confirm nothing in them is still wanted. Their tips survive in `refs/pull/18/head` and `refs/pull/16/head`. `feature/case-insensitive-prefix` has no PR ref, so tag it before deleting.
