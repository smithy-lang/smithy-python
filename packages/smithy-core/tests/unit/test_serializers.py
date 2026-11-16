#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

import pytest
from smithy_core.exceptions import UnsupportedStreamError
from smithy_core.prelude import BLOB
from smithy_core.serializers import ShapeSerializer, SpecificShapeSerializer


class _BlobRecorder(SpecificShapeSerializer):
    # SpecificShapeSerializer rejects data streams; the protocol default is under test.
    write_data_stream = ShapeSerializer.write_data_stream

    def __init__(self) -> None:
        self.blobs: list[bytes] = []

    def write_blob(self, schema: Any, value: bytes) -> None:
        self.blobs.append(value)


@pytest.mark.parametrize("value", [b"abc", bytearray(b"abc")])
def test_write_data_stream_writes_bytes_as_blob(value: bytes | bytearray) -> None:
    serializer = _BlobRecorder()

    serializer.write_data_stream(BLOB, value)

    assert serializer.blobs == [b"abc"]


def test_write_data_stream_rejects_streams() -> None:
    class _Reader:
        def read(self, size: int = -1, /) -> bytes:
            return b""

    with pytest.raises(UnsupportedStreamError):
        _BlobRecorder().write_data_stream(BLOB, _Reader())
