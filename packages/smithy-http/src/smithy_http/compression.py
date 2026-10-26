# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Modeled HTTP request compression, applied before signing."""

import gzip
import zlib
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import read_streaming_blob
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeType
from smithy_core.traits import RequestCompressionTrait, RequiresLengthTrait

from . import Field
from .interfaces import Fields


@dataclass(frozen=True, kw_only=True)
class RequestCompression:
    """Compression policy resolved once for a modeled operation."""

    encoding: str | None = None
    minimum_size: int = 10240

    @classmethod
    def from_operation(
        cls, operation: APIOperation[Any, Any], context: TypedProperties
    ) -> "RequestCompression":
        config = context.get("config")
        disabled = getattr(config, "disable_request_compression", False)
        minimum_size = getattr(config, "request_min_compression_size_bytes", 10240)
        if not isinstance(disabled, bool):
            raise ValueError("disable_request_compression must be a boolean")
        if (
            not isinstance(minimum_size, int)
            or isinstance(minimum_size, bool)
            or not 0 <= minimum_size <= 10485760
        ):
            raise ValueError(
                "request_min_compression_size_bytes must be an integer between 0 and 10485760"
            )
        trait = operation.schema.get_trait(RequestCompressionTrait)
        encodings = trait.encodings if trait is not None else []
        supported = any(encoding.lower() == "gzip" for encoding in encodings)
        if disabled or not supported:
            return cls()
        stream = operation.input_stream_member
        unsafe_stream = stream is not None and (
            RequiresLengthTrait in stream
            or (
                stream.member_target is not None
                and stream.member_target.shape_type == ShapeType.UNION
            )
        )
        if unsafe_stream:
            return cls()
        return cls(encoding="gzip", minimum_size=minimum_size)

    def compress(
        self, body: StreamingBlob, fields: Fields, *, streaming: bool = False
    ) -> StreamingBlob:
        """Compress buffered content or wrap a stream without reading it eagerly."""
        if self.encoding is None:
            return body
        if streaming:
            result = _GzipReader(body)
            if "content-length" in fields:
                del fields["content-length"]
        else:
            payload = read_streaming_blob(body)
            if len(payload) < self.minimum_size:
                return payload
            compressed = gzip.compress(payload, mtime=0)
            result = AsyncBytesReader(compressed)
            fields.set_field(
                Field(name="content-length", values=[str(len(compressed))])
            )
        previous = fields["content-encoding"] if "content-encoding" in fields else None
        existing_encoding = previous.as_string() if previous is not None else ""
        encoding = f"{existing_encoding}, gzip" if existing_encoding else "gzip"
        fields.set_field(Field(name="content-encoding", values=[encoding]))
        return result


class _GzipReader(AsyncBytesReader):
    def __init__(self, body: StreamingBlob) -> None:
        self._source = AsyncBytesReader(body)
        self._origin: int | None = None
        self._position = 0
        self._compressed = _gzip_chunks(self._source)
        super().__init__(self._compressed)

    async def _ensure_origin(self) -> None:
        if self._origin is None and self._source.seekable():
            self._origin = await self._source.seek(0, 1)

    async def read(self, size: int = -1) -> bytes:
        await self._ensure_origin()
        result = await super().read(size)
        self._position += len(result)
        return result

    def seekable(self) -> bool:
        return self._source.seekable()

    def tell(self) -> int:
        if not self.seekable():
            raise NotImplementedError
        if self.closed:
            raise ValueError("I/O operation on closed file.")
        return self._position

    async def seek(self, offset: int, whence: int = 0) -> int:
        """Seek compressed bytes by rewinding and recompressing in bounded chunks.

        Positions beyond EOF are clamped to EOF, as with gzip.GzipFile.
        """
        if not self.seekable():
            raise NotImplementedError
        if self.closed:
            raise ValueError("I/O operation on closed file.")
        await self._ensure_origin()
        if self._origin is None:
            raise NotImplementedError("The source did not return its seek position")
        if whence == 0:
            target = offset
        elif whence == 1:
            target = self._position + offset
        elif whence == 2:
            while await self.read(65536):
                pass
            target = self._position + offset
        else:
            raise ValueError(f"Invalid whence: {whence}")
        if target < 0:
            raise ValueError("Negative seek position")
        # A failed read may advance the source without emitting compressed bytes.
        # Absolute seeks must restart it even when the logical position matches.
        if target == self._position and whence != 0:
            return self._position
        await self._compressed.aclose()
        await self._source.seek(self._origin)
        self._compressed = _gzip_chunks(self._source)
        super().__init__(self._compressed)
        self._position = 0
        while self._position < target:
            if not await self.read(min(65536, target - self._position)):
                break
        return self._position

    async def close(self) -> None:
        try:
            await super().close()
        finally:
            await self._source.close()


async def _gzip_chunks(reader: AsyncBytesReader) -> AsyncGenerator[bytes]:
    compressor = zlib.compressobj(wbits=31)
    async for chunk in reader.iter_chunks(65536):
        if encoded := compressor.compress(chunk):
            yield encoded
    if encoded := compressor.flush():
        yield encoded
