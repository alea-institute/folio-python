"""Opt in to sustained pressure without changing ordinary benchmark selection."""

import pytest

pytest_plugins = ["pytester"]


def pytest_addoption(parser):
    parser.addoption(
        "--run-cache-pressure",
        action="store_true",
        default=False,
        help="run sustained cache-pressure benchmarks (at least three minutes)",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-cache-pressure"):
        skip = pytest.mark.skip(reason="requires --run-cache-pressure")
        for item in items:
            if item.get_closest_marker("cache_pressure"):
                item.add_marker(skip)
