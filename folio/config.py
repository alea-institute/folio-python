"""
Configuration for the FOLIO (Federated Open Legal Information Ontology) Python library.
"""

# annotations
from __future__ import annotations

# imports
import json
from pathlib import Path
from typing import Literal, Optional

# packages
from pydantic import BaseModel, ConfigDict, Field

# project imports
from folio.logger import get_logger

# Default configuration path
DEFAULT_CONFIG_PATH: Path = Path.home() / ".folio/config.json"

# Default GitHub API URL
DEFAULT_GITHUB_API_URL: str = "https://api.github.com"
DEFAULT_GITHUB_OBJECT_URL: str = "https://raw.githubusercontent.com"

# Default source type, which determines how the ontology is loaded.
DEFAULT_SOURCE_TYPE: Literal["github", "http"] = "github"

# Default HTTP URL for the ontology
DEFAULT_HTTP_URL: Optional[str] = None

# Default GitHub owner, repo, and branch for the ontology
DEFAULT_GITHUB_REPO_OWNER: str = "alea-institute"
DEFAULT_GITHUB_REPO_NAME: str = "FOLIO"
DEFAULT_GITHUB_REPO_BRANCH: str = "2.0.0"

# set up the logger
LOGGER = get_logger(__name__)


class FOLIOConfiguration(BaseModel):
    """
    Configuration for the FOLIO (Federated Open Legal Information Ontology) Python library.
    """

    source: Literal["github", "http"] = Field(
        ...,
        description="The source of the FOLIO configuration. Must be either 'github' or 'http'.",
    )
    url: Optional[str] = Field(
        None, description="The URL of the FOLIO configuration if source is 'http'."
    )
    repo_owner: Optional[str] = Field(
        None, description="The owner of the GitHub repository if source is 'github'."
    )
    repo_name: Optional[str] = Field(
        None, description="The name of the GitHub repository if source is 'github'."
    )
    branch: Optional[str] = Field(
        None, description="The branch of the GitHub repository if source is 'github'."
    )
    path: Optional[str] = Field(
        None, description="The path to the FOLIO.owl file in the repository or URL."
    )
    use_cache: bool = Field(
        True, description="Whether to use caching for the FOLIO configuration."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "folio": {
                        "source": "github",
                        "repo_owner": "alea-institute/",
                        "repo_name": "folio",
                        "branch": "2.0.0",
                        "path": "FOLIO.owl",
                        "use_cache": True,
                    }
                }
            ]
        }
    )

    @staticmethod
    def load_config(
        config_path: str | Path = DEFAULT_CONFIG_PATH,
    ) -> FOLIOConfiguration:
        """
        Load the configuration from a JSON file.

        Args:
            config_path (str | Path): The path to the configuration file.

        Returns:
            dict: The configuration dictionary.
        """
        # determine the configuration file path
        if isinstance(config_path, str):
            config_file_path = Path(config_path)
        else:
            config_file_path = config_path

        # check if the configuration file exists
        if config_file_path.exists():
            with config_file_path.open("rt", encoding="utf-8") as input_file:
                config_data = json.load(input_file)
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

        LOGGER.info("Loaded configuration from %s", config_file_path)

        # return the configuration dictionary
        return FOLIOConfiguration(
            source=config_data.get("folio", {}).get("source", DEFAULT_SOURCE_TYPE),
            url=config_data.get("folio", {}).get("url", DEFAULT_HTTP_URL),
            repo_owner=config_data.get("folio", {}).get(
                "repo_owner", DEFAULT_GITHUB_REPO_OWNER
            ),
            repo_name=config_data.get("folio", {}).get(
                "repo_name", DEFAULT_GITHUB_REPO_NAME
            ),
            branch=config_data.get("folio", {}).get(
                "branch", DEFAULT_GITHUB_REPO_BRANCH
            ),
            path=config_data.get("folio", {}).get("path", "FOLIO.owl"),
        )
