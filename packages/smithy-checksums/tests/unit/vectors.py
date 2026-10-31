# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Expected digests shared by the checksum tests."""

ALGORITHMS = ("crc32", "crc32c")

# Digests from independent sources: the standard check value of each CRC (the
# digest of "123456789"), the CRC32C test vectors from RFC 3720, and "Hello world"
# digests that match the ones the CRT produces.
KNOWN_ANSWERS: dict[str, dict[bytes, str]] = {
    "crc32": {b"123456789": "cbf43926", b"Hello world": "8bd69e52"},
    "crc32c": {
        b"123456789": "e3069283",
        b"Hello world": "72b51f78",
        # RFC 3720, appendix B.4. The RFC lists each CRC in transmission order,
        # least significant byte first, so these are its values byte-reversed.
        bytes(32): "8a9136aa",
        b"\xff" * 32: "62a8ab43",
        bytes(range(32)): "46dd794e",
        bytes(range(31, -1, -1)): "113fdb5c",
    },
}


def pattern(length: int) -> bytes:
    """Returns deterministic input that doesn't repeat on a power-of-two boundary."""
    return bytes(i % 251 for i in range(length))


# Digests of pattern(length), from inputs shorter than a word to several
# kilobytes.
PATTERN_DIGESTS: dict[str, dict[int, str]] = {
    "crc32": {
        0: "00000000",
        1: "d202ef8d",
        3: "0854897f",
        4: "8bb98613",
        8: "88aa689f",
        9: "bce14302",
        16: "cecee288",
        17: "2c183a19",
        128: "24650d57",
        129: "ca91cdf7",
        240: "a60b0b66",
        241: "cbc8d2f7",
        1024: "7be4dfd0",
        1025: "4e700dfb",
        16385: "e033bd2c",
    },
    "crc32c": {
        0: "00000000",
        1: "527d5351",
        3: "92fd4bfa",
        4: "d9331aa3",
        8: "8a2cbc3b",
        9: "7144c5a8",
        16: "d9c908eb",
        17: "38435e17",
        128: "30d9c515",
        129: "f514629f",
        240: "9f4f71d6",
        241: "54fe7516",
        1024: "2af62c0c",
        1025: "c8d03add",
        16385: "896b2de8",
    },
}
