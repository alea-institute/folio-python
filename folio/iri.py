"""
Concept IRI generation for the FOLIO namespace.

FOLIO concept IRIs are permanent: once published, one is never deleted and never
reused, so minting is a one-way door. This module is the single place where a
new one is generated.

Convention
----------
A new local name is ``R`` followed by the base62 encoding of 127 random bits::

    https://folio.openlegalstandard.org/R1cNH7TLMiSlSbIbdFsynUk

That is the scheme the great majority of published FOLIO concepts already use.
Measured over the 18,325 ``owl:Class`` declarations in ``FOLIO.owl`` at
``alea-institute/FOLIO@8ebf17b``, the local names fall into these families:

=========================================  ======  ==========
family                                     count   share
=========================================  ======  ==========
``R`` + base62 (this module)               11,427  62.4%
``R`` + 23 hex characters (SALI legacy)     4,751  25.9%
raw base64url of a uuid4, 22 characters     1,992  10.9%
``R`` + base64url                             151   0.8%
other                                           4   0.02%
=========================================  ======  ==========

The 127-bit width is not arbitrary; it is recoverable from the published data.
Local-name body lengths of 20/21/22 characters occur at 0.39%/25.75%/73.85%.
Base62 of a uniform 127-bit integer predicts 0.39%/25.31%/74.29%. A 128-bit
generator predicts 0.21%/12.9%/86.9% and is excluded. Changing the width would
silently change the length profile of future IRIs, which is the only evidence
of how FOLIO IRIs are generated -- so it is pinned and tested.

NOTE (for review): this replaces a base64url-derived scheme that emitted no
``R`` prefix. The intent is to continue the scheme the vast majority of FOLIO
items already use, so that a concept minted today is indistinguishable from its
siblings. If dropping the ``R`` prefix was deliberate rather than incidental,
say so and this should be reverted to match -- the two schemes should not both
be in use.

This module itself imports only the standard library, so minting no longer
requires constructing a ``FOLIO`` graph -- which downloads and parses the full
18 MB ontology purely to produce one 23-character string. (Importing it through
the package still initialises ``folio``, and therefore ``folio.graph``; making
``folio/__init__.py`` lazy would remove that too, but is out of scope here.)
"""

# SPDX-License-Identifier: MIT
# (c) 2024 ALEA Institute.

from __future__ import annotations

import secrets
from collections.abc import Callable, Container

# The FOLIO namespace that concept IRIs are minted under.
FOLIO_NAMESPACE: str = "https://folio.openlegalstandard.org/"

# Prefix carried by every minted local name.
IRI_PREFIX: str = "R"

# Base62 digits, least significant value first. Ordering matters: it is the
# ordering already present in published IRIs.
BASE62_ALPHABET: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Random bits per local name. Recovered from the published length distribution;
# see the module docstring before changing this.
IRI_ENTROPY_BITS: int = 127

# Safety bound on collision retries.
MAX_IRI_ATTEMPTS: int = 16


def encode_base62(value: int) -> str:
    """
    Encode a non-negative integer in base62, most significant digit first.

    Args:
        value (int): The integer to encode.

    Returns:
        str: The base62 encoding.

    Raises:
        ValueError: If value is negative.
    """
    if value < 0:
        raise ValueError("base62 encoding requires a non-negative integer")
    if value == 0:
        return BASE62_ALPHABET[0]

    digits: list[str] = []
    while value:
        value, remainder = divmod(value, 62)
        digits.append(BASE62_ALPHABET[remainder])
    return "".join(reversed(digits))


def generate_local_name(*, randbits: Callable[[int], int] = secrets.randbits) -> str:
    """
    Generate one local name, without checking it against anything.

    Args:
        randbits (Callable[[int], int]): Source of randomness. Injectable for
            tests; production callers should leave this as secrets.randbits.

    Returns:
        str: A local name such as "R1cNH7TLMiSlSbIbdFsynUk".
    """
    return IRI_PREFIX + encode_base62(randbits(IRI_ENTROPY_BITS))


def generate_iri(
    existing: Container[str] | None = None,
    *,
    max_attempts: int = MAX_IRI_ATTEMPTS,
    randbits: Callable[[int], int] = secrets.randbits,
) -> str:
    """
    Generate a new, unused FOLIO concept IRI.

    Args:
        existing (Optional[Container[str]]): Names already in use. Both full
            IRIs and bare local names are recognised, so an index keyed either
            way can be passed directly.
        max_attempts (int): Collision retries before giving up.
        randbits (Callable[[int], int]): Source of randomness.

    Returns:
        str: The new IRI.

    Raises:
        RuntimeError: If no unused IRI was found within max_attempts.
    """
    for _ in range(max_attempts):
        local_name = generate_local_name(randbits=randbits)
        iri = f"{FOLIO_NAMESPACE}{local_name}"

        # Check both spellings. The previous implementation tested a bare local
        # name against FOLIO.iri_to_index, whose keys are full IRIs taken from
        # rdf:about -- so the guard could never fire and the retry loop could
        # never run. Accepting either form makes the check work regardless of
        # how the caller's index is keyed.
        if existing is not None and (iri in existing or local_name in existing):
            continue

        return iri

    raise RuntimeError("Failed to generate a unique IRI.")
