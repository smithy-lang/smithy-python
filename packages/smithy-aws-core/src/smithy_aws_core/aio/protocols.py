from typing import Final

from smithy_core.codecs import Codec
from smithy_core.shapes import ShapeID
from smithy_http.aio.protocols import HttpBindingClientProtocol
from smithy_json import JSONCodec

from ..traits import RestJson1Trait


class RestJsonClientProtocol(HttpBindingClientProtocol):
    """An implementation of the aws.protocols#restJson1 protocol."""

    _id: ShapeID = RestJson1Trait.id
    _codec: JSONCodec = JSONCodec()
    _contentType: Final = "application/json"

    @property
    def id(self) -> ShapeID:
        return self._id

    @property
    def payload_codec(self) -> Codec:
        return self._codec

    @property
    def content_type(self) -> str:
        return self._contentType
