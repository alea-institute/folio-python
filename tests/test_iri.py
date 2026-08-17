"""Tests for folio.iri, the concept IRI generator.

folio.iri imports only the standard library, so these run without network
access, without a FOLIO graph, and without the optional search extras.
"""

# SPDX-License-Identifier: MIT
# (c) 2024 ALEA Institute.

import re

import pytest

from folio.iri import (
    BASE62_ALPHABET,
    FOLIO_NAMESPACE,
    IRI_ENTROPY_BITS,
    IRI_PREFIX,
    encode_base62,
    generate_iri,
    generate_local_name,
)

# "R" plus 19-22 base62 characters. 127 bits encodes to 22 digits 74% of the
# time and 21 digits 25% of the time; shorter outputs are rare but legitimate
# and one (R92xsHpdHu6BJjtepuRu) is already published.
LOCAL_NAME = re.compile(r"R[0-9A-Za-z]{19,22}\Z")


def decode_base62(text: str) -> int:
    """Independent inverse; Python's int() only parses up to base 36."""
    value = 0
    for character in text:
        value = value * 62 + BASE62_ALPHABET.index(character)
    return value


def test_base62_round_trips() -> None:
    for value in (0, 1, 61, 62, 3843, 62**21 + 5, 2**127 - 1):
        assert decode_base62(encode_base62(value)) == value


def test_base62_digit_order() -> None:
    assert encode_base62(0) == "0"
    assert encode_base62(10) == "A"
    assert encode_base62(61) == "z"
    assert encode_base62(62) == "10"


def test_base62_rejects_negative() -> None:
    with pytest.raises(ValueError):
        encode_base62(-1)


def test_generate_local_name_shape() -> None:
    for _ in range(200):
        local_name = generate_local_name()
        assert LOCAL_NAME.fullmatch(local_name)
        assert local_name.isalnum()
        assert local_name.startswith(IRI_PREFIX)


def test_generate_iri_shape() -> None:
    for _ in range(50):
        iri = generate_iri()
        assert iri.startswith(FOLIO_NAMESPACE)
        local_name = iri[len(FOLIO_NAMESPACE) :]
        assert LOCAL_NAME.fullmatch(local_name)
        # The previous implementation could emit a local name of 16 characters
        # or fewer roughly once in 29,000 mints, because it stripped
        # non-alphanumeric characters after base64 encoding. Base62 has no
        # such step.
        assert len(local_name) > 16


def test_entropy_width_is_pinned() -> None:
    """Recovered from the published length distribution; see folio/iri.py."""
    assert IRI_ENTROPY_BITS == 127


def test_generate_iri_is_deterministic_given_randbits() -> None:
    value = 62**21 + 5
    iri = generate_iri(randbits=lambda _bits: value)
    assert iri == f"{FOLIO_NAMESPACE}R{encode_base62(value)}"


def test_collision_check_accepts_full_iris() -> None:
    """An index keyed by full IRI -- what FOLIO.iri_to_index actually holds."""
    taken, free = 62**21 + 5, 62**21 + 7
    taken_iri = f"{FOLIO_NAMESPACE}R{encode_base62(taken)}"
    values = iter([taken, taken, free])
    iri = generate_iri({taken_iri}, randbits=lambda _bits: next(values))
    assert iri == f"{FOLIO_NAMESPACE}R{encode_base62(free)}"


def test_collision_check_accepts_bare_local_names() -> None:
    """An index keyed by bare local name is also honoured."""
    taken, free = 62**21 + 5, 62**21 + 7
    values = iter([taken, taken, free])
    iri = generate_iri({f"R{encode_base62(taken)}"}, randbits=lambda _bits: next(values))
    assert iri == f"{FOLIO_NAMESPACE}R{encode_base62(free)}"


def test_collision_retries_are_bounded() -> None:
    taken = 62**21 + 5
    taken_iri = f"{FOLIO_NAMESPACE}R{encode_base62(taken)}"
    with pytest.raises(RuntimeError):
        generate_iri({taken_iri}, max_attempts=4, randbits=lambda _bits: taken)


def test_generated_iris_are_distinct() -> None:
    assert len({generate_iri() for _ in range(500)}) == 500


@pytest.mark.parametrize(
    "published",
    [
        "RCzxVprwB3RwZ8EMewt18Jt",  # Investment Funds
        "R7e7pNl5IOMFbxKN2GV2C41",  # Hedge Fund
        "RSYBzf149Mi5KE0YtmpUmr",  # Area of Law
        "R92xsHpdHu6BJjtepuRu",  # shortest published local name
    ],
)
def test_published_iris_match_the_generated_shape(published: str) -> None:
    """Minted names must be indistinguishable from ones already published."""
    assert LOCAL_NAME.fullmatch(published)
