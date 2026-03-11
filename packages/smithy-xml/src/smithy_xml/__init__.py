#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from xml.etree.ElementTree import iterparse

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.interfaces import BytesReader, BytesWriter
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import TimestampFormat

from ._private.deserializers import XMLShapeDeserializer as _XMLShapeDeserializer
from ._private.readers import XMLEventReader as _XMLEventReader
from ._private.serializers import XMLShapeSerializer as _XMLShapeSerializer
from .settings import XMLSettings

__version__ = "0.0.1"
__all__ = ("XMLCodec", "XMLSettings")


class XMLCodec(Codec):
    """A codec for converting shapes to/from XML."""

    def __init__(
        self,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
        default_namespace: str | None = None,
    ) -> None:
        self._settings = XMLSettings(
            default_timestamp_format=default_timestamp_format,
            default_namespace=default_namespace,
        )

    @property
    def media_type(self) -> str:
        return "application/xml"

    def create_serializer(self, sink: BytesWriter) -> ShapeSerializer:
        return _XMLShapeSerializer(sink=sink, settings=self._settings)

    def create_deserializer(
        self,
        source: bytes | BytesReader,
        *,
        wrapper_elements: tuple[str, ...] = (),
    ) -> ShapeDeserializer:
        if isinstance(source, bytes):
            source = BytesIO(source)
        reader = _XMLEventReader(
            iterparse(source, events=("start", "end"))  # noqa: S314
        )
        return _XMLShapeDeserializer(
            settings=self._settings, reader=reader, wrapper_elements=wrapper_elements
        )
