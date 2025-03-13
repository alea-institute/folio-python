from folio import FOLIO

if __name__ == "__main__":
    # Initialize the FOLIO client with default settings
    folio = FOLIO()
    print(folio)

    # Initialize with custom settings
    folio_custom = FOLIO(
        source_type="github",
        github_repo_owner="alea-institute",
        github_repo_name="FOLIO",
        github_repo_branch="main",
        use_cache=True,
    )
    print(folio_custom)

    # Initialize from a custom HTTP URL
    folio_http = FOLIO(
        source_type="http",
        http_url="https://github.com/alea-institute/FOLIO/raw/main/FOLIO.owl",
    )
    print(folio_http)
