#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from io import BytesIO

from smithy_core.codecs import Codec
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.interfaces import BytesReader, BytesWriter
from smithy_core.serializers import ShapeSerializer

from ._private.deserializers import CBORShapeDeserializer as _CBORShapeDeserializer
from ._private.generic import loads as loads
from ._private.generic import strip_default_members as strip_default_members
from ._private.serializers import CBORShapeSerializer as _CBORShapeSerializer
from .settings import CBORSettings

__version__ = "0.0.1"
__all__ = ("CBORCodec", "CBORSettings", "loads", "strip_default_members")


class CBORCodec(Codec):
    """Targets the subset of CBOR used by the ``smithy.protocols#rpcv2Cbor`` protocol."""

    def __init__(
        self,
        default_namespace: str | None = None,
    ) -> None:
        self._settings = CBORSettings(
            default_namespace=default_namespace,
        )

    @property
    def media_type(self) -> str:
        return "application/cbor"

    def create_serializer(self, sink: BytesWriter) -> "ShapeSerializer":
        return _CBORShapeSerializer(sink, settings=self._settings)

    def create_deserializer(self, source: bytes | BytesReader) -> "ShapeDeserializer":
        if isinstance(source, bytes):
            source = BytesIO(source)
        return _CBORShapeDeserializer(source, settings=self._settings)
