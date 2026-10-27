# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests that run against both the native and pure-Python implementations.

The native cases are skipped when the extension isn't built, but the pure-Python
cases always run, regardless of which implementation the package selected.
"""

import os
import random
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from types import ModuleType

import pytest
from smithy_checksums._private import crc
from smithy_checksums._private.backend import ChecksumImpl

from .vectors import ALGORITHMS, KNOWN_ANSWERS, PATTERN_DIGESTS, pattern

type Factory = Callable[[], ChecksumImpl]

PURE: dict[str, Factory] = {
    "crc32": crc.Crc32,
    "crc32c": crc.Crc32C,
}


def _load_native() -> ModuleType | None:
    try:
        from smithy_checksums import _native
    except ImportError:
        return None
    return _native


_NATIVE_MODULE = _load_native()
NATIVE: dict[str, Factory] = (
    {}
    if _NATIVE_MODULE is None
    else {
        "crc32": _NATIVE_MODULE.Crc32,
        "crc32c": _NATIVE_MODULE.Crc32C,
    }
)
requires_native = pytest.mark.skipif(
    _NATIVE_MODULE is None, reason="native extension not built"
)


IMPLEMENTATIONS = [
    pytest.param(PURE, id="pure"),
    pytest.param(NATIVE, id="native", marks=requires_native),
]


def _digest(factory: Factory, *chunks: bytes) -> str:
    checksum = factory()
    for chunk in chunks:
        checksum.update(chunk)
    return checksum.digest().hex()


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_known_answers(impls: dict[str, Factory], algorithm: str) -> None:
    for data, expected in KNOWN_ANSWERS[algorithm].items():
        assert _digest(impls[algorithm], data) == expected


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_pattern_digests(impls: dict[str, Factory], algorithm: str) -> None:
    for length, expected in PATTERN_DIGESTS[algorithm].items():
        assert _digest(impls[algorithm], pattern(length)) == expected, length


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_streaming_matches_one_shot(impls: dict[str, Factory], algorithm: str) -> None:
    data = pattern(16385)
    expected = PATTERN_DIGESTS[algorithm][16385]
    rng = random.Random(algorithm)
    for _ in range(5):
        chunks: list[bytes] = []
        offset = 0
        while offset < len(data):
            size = rng.choice((1, 7, 63, 64, 65, 239, 240, 241, 1023, 1024, 4096))
            chunks.append(data[offset : offset + size])
            offset += size
        assert _digest(impls[algorithm], *chunks) == expected


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_copy_is_independent(impls: dict[str, Factory], algorithm: str) -> None:
    data = pattern(2049)
    original = impls[algorithm]()
    original.update(data[:1000])
    copied = original.copy()
    copied.update(data[1000:])
    assert copied.digest().hex() == _digest(impls[algorithm], data)
    assert original.digest().hex() == _digest(impls[algorithm], data[:1000])


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_digest_does_not_reset(impls: dict[str, Factory], algorithm: str) -> None:
    checksum = impls[algorithm]()
    checksum.update(b"Hello ")
    first = checksum.digest()
    assert checksum.digest() == first
    checksum.update(b"world")
    assert checksum.digest().hex() == KNOWN_ANSWERS[algorithm][b"Hello world"]


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize(
    "wrap",
    [bytes, bytearray, memoryview],
    ids=["bytes", "bytearray", "memoryview"],
)
def test_accepts_byte_buffers(
    impls: dict[str, Factory],
    algorithm: str,
    wrap: Callable[[bytes], bytes | bytearray | memoryview],
) -> None:
    # 4096 bytes is above the size at which the native extension detaches from
    # the interpreter while hashing.
    data = pattern(4096)
    checksum = impls[algorithm]()
    checksum.update(wrap(data))
    assert checksum.digest().hex() == _digest(impls[algorithm], data)


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_shared_instance_updates_are_atomic(
    impls: dict[str, Factory], algorithm: str
) -> None:
    # Every update adds the same chunk, so the result doesn't depend on the order
    # the threads run in, only on each update being applied whole.
    chunk = pattern(4096)
    threads, updates = 4, 8
    shared = impls[algorithm]()

    def run(_: int) -> None:
        for _ in range(updates):
            shared.update(chunk)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        list(executor.map(run, range(threads)))
    assert shared.digest().hex() == _digest(
        impls[algorithm], chunk * (threads * updates)
    )


@requires_native
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_native_matches_pure(algorithm: str) -> None:
    data = os.urandom(5000)
    for length in [*range(300), 1023, 1024, 1025, 2047, 2048, 2049, 5000]:
        assert _digest(NATIVE[algorithm], data[:length]) == _digest(
            PURE[algorithm], data[:length]
        ), length


@pytest.mark.parametrize("impls", IMPLEMENTATIONS)
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_matches_crt(impls: dict[str, Factory], algorithm: str) -> None:
    crt = pytest.importorskip("awscrt.checksums")
    compute: dict[str, Callable[[bytes], bytes]] = {
        "crc32": lambda data: crt.crc32(data).to_bytes(4, "big"),
        "crc32c": lambda data: crt.crc32c(data).to_bytes(4, "big"),
    }
    data = os.urandom(3000)
    for length in [*range(0, 300, 7), 1023, 1024, 1025, 3000]:
        assert (
            _digest(impls[algorithm], data[:length])
            == compute[algorithm](data[:length]).hex()
        ), length


def _bitwise_crc(poly: int, width: int, data: bytes) -> str:
    """Computes a reflected CRC with all-ones init and final XOR, a bit at a time."""
    mask = (1 << width) - 1
    value = mask
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ poly if value & 1 else value >> 1
    return (value ^ mask).to_bytes(width // 8, "big").hex()


@pytest.mark.parametrize(
    ("algorithm", "poly", "width"),
    [("crc32c", 0x82F63B78, 32)],
)
def test_chunked_crc_matches_bitwise(algorithm: str, poly: int, width: int) -> None:
    # The pure CRCs hash whole chunks with masks, short tails with a table, and
    # long tails with the masks again, so check lengths on either side of each.
    chunk = crc._CHUNK_SIZE  # pyright: ignore[reportPrivateUsage]
    tail = crc._MIN_MASKED_TAIL  # pyright: ignore[reportPrivateUsage]
    data = os.urandom(2 * chunk + tail + 1)
    for length in [0, 1, 8, tail - 1, tail, chunk - 1, chunk, chunk + 1, len(data)]:
        assert _digest(PURE[algorithm], data[:length]) == _bitwise_crc(
            poly, width, data[:length]
        ), length

    rng = random.Random(algorithm)
    chunks: list[bytes] = []
    offset = 0
    while offset < len(data):
        size = rng.choice((1, 100, tail, chunk - 1, chunk, chunk + 1))
        chunks.append(data[offset : offset + size])
        offset += size
    assert _digest(PURE[algorithm], *chunks) == _bitwise_crc(poly, width, data)
