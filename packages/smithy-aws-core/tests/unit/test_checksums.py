#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_aws_core._private import checksums
from smithy_aws_core._private.checksums import (
    DEFAULT_ALGORITHM,
    SUPPORTED_ALGORITHMS,
    assert_checksums_installed,
    checksum_header,
    checksum_header_algorithm,
    create_checksum,
    decode_checksum,
    encode_digest,
    response_validation_order,
)
from smithy_core.exceptions import MissingDependencyError

# The checksum of b"hello world" for each algorithm, base64-encoded big-endian, as
# calculated by zlib, awscrt, hashlib, and the reference xxhash package.
HELLO_WORLD = {
    "CRC32": "DUoRhQ==",
    "CRC32C": "yZRlqg==",
    "CRC64NVME": "jSnVw/bqjr4=",
    "SHA1": "Kq5sNclPz7QV2+lfQIuc6R7oRu0=",
    "SHA256": "uU0nuZNNPgilLlLX2n2r+sSE7+N6U4DukIj3rOLvzek=",
    "SHA512": (
        "MJ7MSJwS1utMxA9QyQLytNDtd+5RGnx6m808qG1M2G+YndNbxf9JlnDaNCVbRbDP2DDoH2Bdz33F"
        "VC6TrpzXbw=="
    ),
    "XXHASH64": "RatnNLIeaWg=",
    "XXHASH3": "1Eex6kDmmIs=",
    "XXHASH128": "340J6T+HSQCpm4d1zBW2xw==",
}


def test_every_supported_algorithm_has_a_known_answer() -> None:
    assert set(HELLO_WORLD) == SUPPORTED_ALGORITHMS


@pytest.mark.parametrize(("algorithm", "expected"), HELLO_WORLD.items())
def test_create_checksum(algorithm: str, expected: str) -> None:
    checksum = create_checksum(algorithm)
    checksum.update(b"hello world")
    assert encode_digest(checksum.digest()) == expected


def test_algorithm_names_are_case_insensitive() -> None:
    checksum = create_checksum("crc32")
    checksum.update(b"hello world")
    assert encode_digest(checksum.digest()) == HELLO_WORLD["CRC32"]


@pytest.mark.parametrize("algorithm", ["MD5", "md5", "CRC16", ""])
def test_unsupported_algorithms_are_rejected(algorithm: str) -> None:
    with pytest.raises(ValueError, match="Unsupported checksum algorithm"):
        create_checksum(algorithm)


def test_checksums_require_smithy_aws_checksums(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(checksums, "_HAS_CHECKSUMS", False)
    match = r"smithy-aws-core\[checksums\]"
    with pytest.raises(MissingDependencyError, match=match):
        assert_checksums_installed()
    with pytest.raises(MissingDependencyError, match=match):
        create_checksum("CRC32")


@pytest.mark.parametrize(
    ("algorithm", "header"),
    [
        ("CRC32", "x-amz-checksum-crc32"),
        ("CRC64NVME", "x-amz-checksum-crc64nvme"),
        ("XXHASH128", "x-amz-checksum-xxhash128"),
    ],
)
def test_checksum_header(algorithm: str, header: str) -> None:
    assert checksum_header(algorithm) == header


def test_decode_checksum() -> None:
    assert decode_checksum("DUoRhQ==") == b"\x0dJ\x11\x85"
    # A value of the wrong size is decoded, so that validating it fails.
    assert decode_checksum("jSnVw/bqjr4=") == b"\x8d)\xd5\xc3\xf6\xea\x8e\xbe"


@pytest.mark.parametrize(
    "value",
    [
        "",
        # A header sent twice is joined with a comma.
        "DUoRhQ==,DUoRhQ==",
        # Composite checksums of multipart objects end in the number of parts.
        "DUoRhQ==-3",
        "not base64!",
    ],
)
def test_decode_checksum_rejects_values_that_are_not_checksums(value: str) -> None:
    assert decode_checksum(value) is None


def test_response_validation_order() -> None:
    modeled = [
        "CRC64NVME",
        "CRC32",
        "CRC32C",
        "SHA256",
        "SHA1",
        "SHA512",
        "MD5",
        "XXHASH64",
        "XXHASH3",
        "XXHASH128",
    ]
    assert response_validation_order(modeled) == (
        "CRC32C",
        "CRC32",
        "CRC64NVME",
        "XXHASH64",
        "XXHASH3",
        "XXHASH128",
        "SHA1",
        "SHA256",
        "SHA512",
    )


def test_response_validation_order_skips_unsupported_algorithms() -> None:
    assert response_validation_order(["md5", "sha256", "future"]) == ("SHA256",)
    assert response_validation_order([]) == ()


def test_default_algorithm_is_supported() -> None:
    assert DEFAULT_ALGORITHM in SUPPORTED_ALGORITHMS


@pytest.mark.parametrize(
    ("name", "algorithm"),
    [
        ("x-amz-checksum-crc32", "CRC32"),
        ("X-Amz-Checksum-SHA256", "SHA256"),
        ("x-amz-checksum-md5", "MD5"),
        # Unknown algorithms are recognized too, so they're never calculated again.
        ("x-amz-checksum-emoji", "EMOJI"),
        ("x-amz-checksum-type", None),
        ("x-amz-checksum-mode", None),
        ("X-Amz-Checksum-Algorithm", None),
        ("x-amz-sdk-checksum-algorithm", None),
        ("content-md5", None),
    ],
)
def test_checksum_header_algorithm(name: str, algorithm: str | None) -> None:
    assert checksum_header_algorithm(name) == algorithm
