#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Any
from xml.etree.ElementTree import fromstring, parse

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.interfaces import BytesReader, BytesWriter
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID
from smithy_core.types import TimestampFormat

from ._private.serializers import XMLShapeSerializer as _XMLShapeSerializer
from ._private.value_deserializer import (
    XMLValueDeserializer as _XMLValueDeserializer,
)
from .settings import XMLSettings

__version__ = "0.2.0"
__all__ = ("XMLCodec", "XMLSettings")


class XMLCodec(Codec):
    """A codec for converting shapes to/from XML."""

    def __init__(
        self,
        use_timestamp_format: bool = True,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
        default_namespace: str | None = None,
    ) -> None:
        """Initializes an XMLCodec.

        :param use_timestamp_format: Whether the codec should use the
            `smithy.api#timestampFormat` trait, if present.
        :param default_timestamp_format: The default timestamp format to use if the
            `smithy.api#timestampFormat` trait is not enabled or not present.
        :param default_namespace: Default XML namespace (`xmlns`) applied to the root
            element during serialization.
        """
        self._settings = XMLSettings(
            use_timestamp_format=use_timestamp_format,
            default_timestamp_format=default_timestamp_format,
            default_namespace=default_namespace,
        )
        # Member element renderings, shared by every serializer this codec creates.
        self._elements: dict[ShapeID, Any] = {}

    @property
    def media_type(self) -> str:
        return "application/xml"

    def create_serializer(self, sink: BytesWriter) -> ShapeSerializer:
        return _XMLShapeSerializer(sink, self._settings, self._elements)

    def create_deserializer(
        self,
        source: bytes | BytesReader,
        *,
        wrapper_elements: tuple[str, ...] = (),
    ) -> ShapeDeserializer:
        root = (
            fromstring(source)  # noqa: S314
            if isinstance(source, bytes)
            else parse(source).getroot()  # noqa: S314
        )
        return _XMLValueDeserializer(
            settings=self._settings,
            root=root,
            wrapper_elements=wrapper_elements,
        )
