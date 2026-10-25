# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import array
import hashlib
import importlib.util
from concurrent.futures import ThreadPoolExecutor

import pytest
import smithy_checksums
from smithy_checksums import (
    CRC32,
    CRC32C,
    Checksum,
    new,
)

from .vectors import ALGORITHMS, KNOWN_ANSWERS, PATTERN_DIGESTS, pattern

CLASSES = {
    "crc32": CRC32,
    "crc32c": CRC32C,
}


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_class_attributes(algorithm: str) -> None:
    checksum = CLASSES[algorithm]()
    assert checksum.name == algorithm
    assert checksum.digest_size == len(checksum.digest())


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_known_answers(algorithm: str) -> None:
    for data, expected in KNOWN_ANSWERS[algorithm].items():
        checksum = CLASSES[algorithm]()
        checksum.update(data)
        assert checksum.digest().hex() == expected


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_copy_returns_same_type(algorithm: str) -> None:
    checksum = CLASSES[algorithm]()
    checksum.update(b"Hello ")
    copied = checksum.copy()
    copied.update(b"world")
    assert type(copied) is type(checksum)
    assert copied.digest().hex() == KNOWN_ANSWERS[algorithm][b"Hello world"]
    assert checksum.digest().hex() != copied.digest().hex()


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_accepts_non_byte_formats(algorithm: str) -> None:
    data = array.array("I", range(1024))
    checksum = CLASSES[algorithm]()
    checksum.update(data)
    expected = CLASSES[algorithm]()
    expected.update(data.tobytes())
    assert checksum.digest() == expected.digest()


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_rejects_non_contiguous_buffers(algorithm: str) -> None:
    with pytest.raises(TypeError):
        CLASSES[algorithm]().update(memoryview(array.array("I", range(8)))[::2])


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_rejects_non_buffers(algorithm: str) -> None:
    with pytest.raises(TypeError):
        CLASSES[algorithm]().update("text")  # type: ignore[arg-type]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_concurrent_checksums(algorithm: str) -> None:
    data = pattern(16385)

    def compute(_: int) -> str:
        checksum = CLASSES[algorithm]()
        for offset in range(0, len(data), 4096):
            checksum.update(data[offset : offset + 4096])
        return checksum.digest().hex()

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = set(executor.map(compute, range(8)))
    assert results == {PATTERN_DIGESTS[algorithm][16385]}


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("crc32", CRC32),
        ("CRC32C", CRC32C),
    ],
)
def test_new_returns_checksum_classes(name: str, expected: type[Checksum]) -> None:
    assert type(new(name)) is expected


@pytest.mark.parametrize("name", ["SHA1", "sha256", "SHA512", "MD5"])
def test_new_returns_hashlib_checksums(name: str) -> None:
    checksum = new(name)
    checksum.update(b"Hello world")
    assert checksum.name == name.lower()
    assert checksum.digest() == hashlib.new(name.lower(), b"Hello world").digest()


def test_new_rejects_unknown_algorithms() -> None:
    with pytest.raises(ValueError, match="crc16"):
        new("crc16")


def test_has_native_extension() -> None:
    built = importlib.util.find_spec("smithy_checksums._native") is not None
    assert smithy_checksums.HAS_NATIVE_EXTENSION is built
