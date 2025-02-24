from io import BytesIO
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .interfaces import BytesReader, BytesWriter

if TYPE_CHECKING:
    from .deserializers import DeserializeableShape, ShapeDeserializer
    from .serializers import SerializeableShape, ShapeSerializer


@runtime_checkable
class Codec(Protocol):
    """A protocol for Smithy codecs.

    Smithy codecs are responsible for serializing and deserializing shapes in a
    particular format.
    """

    @property
    def media_type(self) -> str:
        """The media type that the codec supports."""
        ...

    def create_serializer(self, sink: BytesWriter) -> "ShapeSerializer":
        """Create a serializer that writes to the given bytes writer.

        :param sink: The output class to write to.
        :returns: A serializer that will write to the given output.
        """
        ...

    def create_deserializer(self, source: bytes | BytesReader) -> "ShapeDeserializer":
        """Create a deserializer that reads from the given bytes reader.

        :param source: The source to read bytes from.
        :returns: A deserializer that reads from the given source.
        """
        ...

    def serialize(self, shape: "SerializeableShape") -> bytes:
        """Serialize a shape to bytes.

        :param shape: The shape to serialize.
        :returns: Bytes representing the shape serialized in the codec's media type.
        """
        stream = BytesIO()
        serializer = self.create_serializer(sink=stream)
        shape.serialize(serializer=serializer)
        serializer.flush()
        stream.seek(0)
        return stream.read()

    def deserialize[S: DeserializeableShape](
        self, source: bytes | BytesReader, shape: type[S]
    ) -> S:
        """Deserialize bytes into a shape.

        :param source: The bytes to deserialize.
        :param shape: The shape class to deserialize into.
        :returns: An instance of the given shape class with the data from the source.
        """
        deserializer = self.create_deserializer(source=source)
        return shape.deserialize(deserializer=deserializer)
