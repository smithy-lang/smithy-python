#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.interfaces import BytesReader, BytesWriter
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import TimestampFormat

from ._private.deserializers import JSONShapeDeserializer as _JSONShapeDeserializer
from ._private.documents import JSONDocument
from ._private.serializers import JSONShapeSerializer as _JSONShapeSerializer
from .settings import JSONSettings

__version__ = "0.1.0"
__all__ = ("JSONCodec", "JSONDocument", "JSONSettings")


class JSONCodec(Codec):
    """A codec for converting shapes to/from JSON."""

    def __init__(
        self,
        use_json_name: bool = True,
        use_timestamp_format: bool = True,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
        default_namespace: str | None = None,
        document_class: type[JSONDocument] = JSONDocument,
    ) -> None:
        """Initializes a JSONCodec.

        :param use_json_name: Whether the codec should use `smithy.api#jsonName` trait,
            if present.
        :param use_timestamp_format: Whether the codec should use the
            `smithy.api#timestampFormat` trait, if present.
        :param default_timestamp_format: The default timestamp format to use if the
            `smithy.api#timestampFormat` trait is not enabled or not present.
        :param default_namespace: The default namespace to use when determining a
            document's discriminator.
        :param document_class: The document class to deserialize to.
        """
        self._settings = JSONSettings(
            use_json_name=use_json_name,
            use_timestamp_format=use_timestamp_format,
            default_timestamp_format=default_timestamp_format,
            default_namespace=default_namespace,
            document_class=document_class,
        )

    @property
    def media_type(self) -> str:
        return "application/json"

    def create_serializer(self, sink: BytesWriter) -> "ShapeSerializer":
        return _JSONShapeSerializer(sink, settings=self._settings)

    def create_deserializer(self, source: bytes | BytesReader) -> "ShapeDeserializer":
        if isinstance(source, bytes):
            source = BytesIO(source)
        return _JSONShapeDeserializer(source, settings=self._settings)
