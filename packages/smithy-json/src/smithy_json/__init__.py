#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import importlib.metadata
from io import BytesIO

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.interfaces import BytesReader, BytesWriter
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import TimestampFormat

from ._private.deserializers import JSONShapeDeserializer as _JSONShapeDeserializer
from ._private.serializers import JSONShapeSerializer as _JSONShapeSerializer

__version__: str = importlib.metadata.version("smithy-json")


class JSONCodec(Codec):
    """A codec for converting shapes to/from JSON."""

    _use_json_name: bool
    _use_timestamp_format: bool
    _default_timestamp_format: TimestampFormat

    def __init__(
        self,
        use_json_name: bool = True,
        use_timestamp_format: bool = True,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
    ) -> None:
        """Initializes a JSONCodec.

        :param use_json_name: Whether the codec should use `smithy.api#jsonName` trait,
            if present.
        :param use_timestamp_format: Whether the codec should use the
            `smithy.api#timestampFormat` trait, if present.
        :param default_timestamp_format: The default timestamp format to use if the
            `smithy.api#timestampFormat` trait is not enabled or not present.
        """
        self._use_json_name = use_json_name
        self._use_timestamp_format = use_timestamp_format
        self._default_timestamp_format = default_timestamp_format

    @property
    def media_type(self) -> str:
        return "application/json"

    def create_serializer(self, sink: BytesWriter) -> "ShapeSerializer":
        return _JSONShapeSerializer(
            sink,
            use_json_name=self._use_json_name,
            use_timestamp_format=self._use_timestamp_format,
            default_timestamp_format=self._default_timestamp_format,
        )

    def create_deserializer(self, source: bytes | BytesReader) -> "ShapeDeserializer":
        if isinstance(source, bytes):
            source = BytesIO(source)
        return _JSONShapeDeserializer(
            source,
            use_json_name=self._use_json_name,
            use_timestamp_format=self._use_timestamp_format,
            default_timestamp_format=self._default_timestamp_format,
        )
