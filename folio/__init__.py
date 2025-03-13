"""
Python library for FOLIO, the Federated Open Legal Information Ontology
"""

# SPDX-License-Identifier: MIT
# (c) 2024 ALEA Institute.

__version__ = "0.1.6"
__author__ = "ALEA Institute"
__license__ = "MIT"
__description__ = (
    "Python library for FOLIO, the Federated Open Legal Information Ontology"
)
__url__ = "https://openlegalstandard.org/"


# import graph to re-export
from .graph import FOLIO, FOLIOTypes, FOLIO_TYPE_IRIS
from .models import OWLClass, NSMAP

__all__ = ["FOLIO", "FOLIOTypes", "FOLIO_TYPE_IRIS", "OWLClass", "NSMAP"]
