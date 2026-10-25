#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Buffer


def as_bytes(data: Buffer) -> bytes | bytearray:
    """Returns the bytes of ``data``, copying only if it isn't already bytes-like."""
    if isinstance(data, bytes | bytearray):
        return data
    return memoryview(data).tobytes()


def as_byte_view(data: Buffer) -> bytes | bytearray | memoryview:
    """Returns ``data`` as an object the native extension accepts, without copying.

    The native extension reads any buffer with a byte format. Other formats (such
    as an ``array('I')``) are recast to bytes, which requires a C-contiguous buffer,
    the same requirement :mod:`hashlib` has.
    """
    if isinstance(data, bytes | bytearray):
        return data
    view = memoryview(data)
    return view if view.format == "B" else view.cast("B")
