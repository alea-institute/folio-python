"""Test GitHub branch-list authentication without network requests."""

import httpx
import pytest

from folio import FOLIO


@pytest.mark.parametrize(
    ("github_token", "gh_token", "expected_authorization"),
    [
        pytest.param("github-token", None, "Bearer github-token", id="github-token"),
        pytest.param(None, "gh-token", "Bearer gh-token", id="gh-token"),
        pytest.param(None, None, None, id="no-token"),
        pytest.param(
            "github-token", "gh-token", "Bearer github-token", id="precedence"
        ),
        pytest.param("", "gh-token", "Bearer gh-token", id="empty-github-token"),
    ],
)
def test_list_branches_auth(
    monkeypatch, github_token, gh_token, expected_authorization
):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    if github_token is not None:
        monkeypatch.setenv("GITHUB_TOKEN", github_token)
    if gh_token is not None:
        monkeypatch.setenv("GH_TOKEN", gh_token)

    def send(client, request, **kwargs):
        assert request.headers["Accept"] == "application/vnd.github.v3+json"
        assert request.headers.get("Authorization") == expected_authorization
        return httpx.Response(200, json=[{"name": "main"}], request=request)

    monkeypatch.setattr(httpx.Client, "send", send)

    assert FOLIO.list_branches() == ["main"]
