#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Buffer


def as_bytes(data: Buffer) -> bytes | bytearray:
    """Returns the bytes of ``data``, copying only if it isn't already bytes-like."""
    if isinstance(data, bytes | bytearray):
        return data
    return memoryview(data).tobytes()


def as_byte_view(data: Buffer) -> bytes | bytearray | memoryview:
    """Returns ``data`` as a C-contiguous buffer of bytes, without copying.

    Both implementations accept the result. Buffers with other formats (such as an
    ``array('I')``) are recast to bytes.

    :raises BufferError: If ``data`` isn't C-contiguous, as :mod:`hashlib` does.
    """
    if isinstance(data, bytes | bytearray):
        return data
    view = memoryview(data)
    if not view.c_contiguous:
        raise BufferError("memoryview: underlying buffer is not C-contiguous")
    return view if view.format == "B" else view.cast("B")
