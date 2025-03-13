# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# import for path resolution for autodoc
import pathlib
import sys

DOCS_PATH = pathlib.Path(__file__).parent.resolve()
PROJECT_PATH = DOCS_PATH.parent.resolve()
print("DOCS_PATH", DOCS_PATH)
print("PROJECT_PATH", PROJECT_PATH)

# inject the project root dir into sys.path
sys.path.insert(0, str(PROJECT_PATH))

# we need to be able to import
print("sys.path", sys.path)

# config
project = "folio-python"
copyright = "2024, ALEA Institute"
author = "ALEA Institute (https://aleainstitute.ai)"
release = "0.1.5"
version = "0.1.5"
master_doc = "index"
language = "en"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx_plausible",
]

plausible_domain = "openlegalstandard.org"


autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_logo = "_static/folio-logo.png"
html_favicon = "_static/favicon-32x32.png"


html_theme_options = {
    # "announcement": "<p class='mystyle'>Some custom HTML!</p>",
    "use_sidenotes": True,
    "collapse_navbar": True,
    "show_navbar_depth": 2,
    "repository_url": "https://github.com/alea-institute/folio-python",
    "repository_branch": "main",
    "path_to_docs": "sphinx",
    "use_issues_button": True,
    "use_repository_button": True,
    "home_page_in_toc": True,
    "pygments_light_style": "default",
    "pygments_dark_style": "default",
    "logo": {
        "dark": "folio-logo.png",
        "light": "folio-logo.png",
        "favicon": "favicon-32x32.png",
        "alt_text": "FOLIO",
    },
}
