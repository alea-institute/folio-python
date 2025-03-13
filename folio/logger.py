"""
This module contains the logger utility functions for the FOLIO package.
"""

# imports
import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger with the specified name.
    """
    # module logger
    logger_instance = logging.getLogger(name)

    # configure the module logger
    logger_instance.setLevel(logging.WARNING)
    logger_instance.addHandler(logging.StreamHandler())

    return logger_instance
