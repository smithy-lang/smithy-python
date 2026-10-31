# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Expected digests shared by the checksum tests."""

ALGORITHMS = ("crc32", "crc32c", "crc64nvme", "xxhash64", "xxhash3", "xxhash128")


def xxhash_sanity_input(length: int) -> bytes:
    """Returns the first ``length`` bytes of the buffer xxHash's sanity tests hash."""
    data = bytearray()
    generator = 0x9E3779B1
    for _ in range(length):
        data.append(generator >> 56)
        generator = (generator * 0x9E3779B185EBCA8D) & 0xFFFFFFFFFFFFFFFF
    return bytes(data)


# Digests of xxhash_sanity_input(length) with a seed of zero, from xxHash's
# tests/sanity_test_vectors.h at commit c629a3113f8bf6a2e4dbab151741dbaa776af8fa.
XXHASH_SANITY_DIGESTS: dict[str, dict[int, str]] = {
    "xxhash64": {
        1: "e934a84adb052768",
        3: "ff7e1959cb50794a",
        4: "9136a0dca57457ee",
        8: "cdbcf538e71d1348",
        9: "554b1ae991eda6b6",
        16: "98c90b57fdfcb55c",
        17: "0d39a2d051a30c2c",
        128: "90ca021457d96dc5",
        129: "41c280132d697aba",
        240: "b81838d483baee53",
        241: "95d76c8b4d8fc4d6",
        1024: "4775bf7cace4d177",
        1025: "847fa6006d7c2ac0",
        2048: "5940f2752bc04387",
        4160: "eee6a4e2ac952a5e",
    },
    "xxhash3": {
        1: "c44bdff4074eecdb",
        3: "54247382a8d6b94d",
        4: "e5dc74bc51848a51",
        8: "24ccc9acaa9f65e4",
        9: "14d5001c15dd3f2b",
        16: "981b17d36c7498c9",
        17: "796f5acd3a60f862",
        128: "fcff24126754d861",
        129: "98f1b0a679a2ca29",
        240: "81c3c2b67f568ccf",
        241: "c5a639ecd2030e5e",
        1024: "dd85c9b5c1109c5c",
        1025: "d870c0fa13211c6a",
        2048: "dd59e2c3a5f038e0",
        4160: "4f323b15321e94e1",
    },
    "xxhash128": {
        1: "a6cd5e9392000f6ac44bdff4074eecdb",
        3: "20efc49ff02422ea54247382a8d6b94d",
        4: "970d585ac632bf8e2e7d8d6876a39fe9",
        8: "47a7f080d82bb45664c69cab4bb21dc5",
        9: "564ef6078950d457ed7ccbc501eb7501",
        16: "c68c368ecf8a9c05562980258a998629",
        17: "955fa78643ed3669abbc12d11973d7db",
        128: "39992220e045260aebb15e34a7fb5ab1",
        129: "03815fc91f1b30b686c9e3bc8f0a3b5c",
        240: "aa4202daa2769dc85c9aae94c8ebe5a0",
        241: "99a80ecf0ecfc647c5a639ecd2030e5e",
        1024: "0d30d24071c64c57dd85c9b5c1109c5c",
        1025: "fd3ee4fe7f2954c6d870c0fa13211c6a",
        2048: "f736557fd47073a5dd59e2c3a5f038e0",
        4160: "67140711c1e3e3354f323b15321e94e1",
    },
}


def _xxhash_sanity_answers(algorithm: str) -> dict[bytes, str]:
    return {
        xxhash_sanity_input(length): digest
        for length, digest in XXHASH_SANITY_DIGESTS[algorithm].items()
    }


# Digests from independent sources: the standard check value of each CRC (the
# digest of "123456789"), the CRC32C test vectors from RFC 3720, the CRC64NVME test
# cases from the NVMe NVM Command Set specification, xxHash's own sanity-test vectors,
# and "Hello world" digests that match the ones the CRT produces.
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
    "crc64nvme": {
        b"123456789": "ae8b14860a799888",
        b"Hello world": "38e259d03f312adb",
        # The 64b CRC test cases in the NVMe NVM Command Set specification.
        bytes(4096): "6482d367eb22b64e",
        b"\xff" * 4096: "c0ddba7302eca3ac",
        bytes(i % 256 for i in range(4096)): "3e729f5f6750449c",
        bytes(255 - i % 256 for i in range(4096)): "9a2df64b8e9e517e",
    },
    "xxhash64": {
        b"": "ef46db3751d8e999",
        b"Hello world": "c500b0c912b376d8",
        **_xxhash_sanity_answers("xxhash64"),
    },
    "xxhash3": {
        b"": "2d06800538d394c2",
        b"Hello world": "b6acb9d84a38ff74",
        **_xxhash_sanity_answers("xxhash3"),
    },
    "xxhash128": {
        b"": "99aa06d3014798d86001c324468d497f",
        b"Hello world": "7351f89812f97382b91d05b31e04dd7f",
        **_xxhash_sanity_answers("xxhash128"),
    },
}


def pattern(length: int) -> bytes:
    """Returns deterministic input that doesn't repeat on a power-of-two boundary."""
    return bytes(i % 251 for i in range(length))


# Digests of pattern(length). The lengths cover each size class of XXH3 and the
# boundaries of its 64-byte stripes and 1024-byte blocks.
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
    "crc64nvme": {
        0: "0000000000000000",
        1: "d5da5047efec8728",
        3: "3f3990291e6454d7",
        4: "29513a0b0028dea8",
        8: "7703cc98ac9209d7",
        9: "0eb6fdbb89d04d0b",
        16: "cf6454c75df95620",
        17: "5c34355fb173cefd",
        128: "a5296136625de4f7",
        129: "c3d556fcf23d6a24",
        240: "717e94e4fd87236d",
        241: "2737bbceef8467bc",
        1024: "fee95dc7adac063f",
        1025: "034aba81017791d2",
        16385: "9c0531959bc1eacf",
    },
    "xxhash64": {
        0: "ef46db3751d8e999",
        1: "e934a84adb052768",
        3: "e5c7bb4533bc65dd",
        4: "ffced8604453cc1e",
        8: "884a173614b81b8d",
        9: "67d85784a7c78c5b",
        16: "44b6ef2fb84169f7",
        17: "5603e60c527599b6",
        128: "7a7fe14647b9ab92",
        129: "0ba25dfd6e891fcf",
        240: "012947f0da6a27b1",
        241: "8d643f23bf2808e1",
        1024: "138e26c65048ce29",
        1025: "cfd73aedd2d6a39d",
        16385: "70c0f3c188d8aa7f",
    },
    "xxhash3": {
        0: "2d06800538d394c2",
        1: "c44bdff4074eecdb",
        3: "5f4299fc161c9cbb",
        4: "60dab036a58211f2",
        8: "3a1c2d7c85af88f8",
        9: "e9612598145bb9dc",
        16: "8355e3a6f61770db",
        17: "9ef341a99de37328",
        128: "85c6174c7ff4c46b",
        129: "ec7642b431ba3e5a",
        240: "375a384d957fe865",
        241: "02e8cd95421c6d02",
        1024: "e5d78bafa45b2aa5",
        1025: "e95c42288f28186e",
        16385: "fea38d9173737a4b",
    },
    "xxhash128": {
        0: "99aa06d3014798d86001c324468d497f",
        1: "a6cd5e9392000f6ac44bdff4074eecdb",
        3: "e3b55f57945a17cf5f4299fc161c9cbb",
        4: "eb70bf5fc779e9e6a6111d53e80a3db5",
        8: "e1e4432a62217fe4cfd50c61c8bb98c1",
        9: "16c769d83e4aebce907931979dca3746",
        16: "72950631827607e2842812cc870dcae2",
        17: "685bc458b37d057fc06e233df7729217",
        128: "14792fc3af88dc6c05321a0b64d67b41",
        129: "dd5e74ac6b45f54ebc30b63382b09a3b",
        240: "65b5be86da5540e7c92b68e16f83bbb6",
        241: "1da1cb61bcb8a2a102e8cd95421c6d02",
        1024: "d0ac1f7b93bf57b9e5d78bafa45b2aa5",
        1025: "2882ebca04ec915ce95c42288f28186e",
        16385: "7f1012a369696b6dfea38d9173737a4b",
    },
}
