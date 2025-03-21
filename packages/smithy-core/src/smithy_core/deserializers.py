import datetime
from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING, Never, Protocol, Self, runtime_checkable

from .exceptions import SmithyException, UnsupportedStreamException

if TYPE_CHECKING:
    from .aio.interfaces import StreamingBlob as _Stream
    from .documents import Document
    from .schemas import Schema


@runtime_checkable
class ShapeDeserializer(Protocol):
    """Protocol used for deserializing shapes based on the Smithy data model.

    If used as a base class, all non-float number methods default to calling
    ``read_integer`` and ``read_double`` defaults to calling ``read_float``.
    These extra numeric methods are for types in the Smithy data model that
    don't have Python equivalents, but may have equivalents in the format
    being read.
    """

    def read_struct(
        self,
        schema: "Schema",
        consumer: Callable[["Schema", "ShapeDeserializer"], None],
    ) -> None:
        """Read a struct value from the underlying data.

        :param schema: The shape's schema.
        :param consumer: A callable to read struct members with.
        """
        ...

    def read_list(
        self, schema: "Schema", consumer: Callable[["ShapeDeserializer"], None]
    ) -> None:
        """Read a list value from the underlying data.

        :param schema: The shape's schema.
        :param consumer: A callable to read list elements with.
        """
        ...

    def read_map(
        self,
        schema: "Schema",
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ) -> None:
        """Read a map value from the underlying data.

        :param schema: The shape's schema.
        :param consumer: A callable to read map values with.
        """
        ...

    def is_null(self) -> bool:
        """Returns whether the next value in the underlying data represents null.

        :param schema: The shape's schema.
        """
        ...

    def read_null(self) -> None:
        """Read a null value from the underlying data."""
        ...

    def read_boolean(self, schema: "Schema") -> bool:
        """Read a boolean value from the underlying data.

        :param schema: The shape's schema.
        :returns: A bool from the underlying data.
        """
        ...

    def read_blob(self, schema: "Schema") -> bytes:
        """Read a blob value from the underlying data.

        :param schema: The shape's schema.
        :returns: A blob from the underlying data.
        """
        ...

    def read_byte(self, schema: "Schema") -> int:
        """Read a byte (8-bit integer) value from the underlying data.

        :param schema: The shape's schema.
        :returns: A byte from the underlying data.
        """
        return self.read_integer(schema)

    def read_short(self, schema: "Schema") -> int:
        """Read a short (16-bit integer) value from the underlying data.

        :param schema: The shape's schema.
        :returns: A short from the underlying data.
        """
        return self.read_integer(schema)

    def read_integer(self, schema: "Schema") -> int:
        """Read an integer (32-bit) value from the underlying data.

        :param schema: The shape's schema.
        :returns: An integer from the underlying data.
        """
        ...

    def read_long(self, schema: "Schema") -> int:
        """Read a long (64-bit integer) value from the underlying data.

        :param schema: The shape's schema.
        :returns: A long from the underlying data.
        """
        return self.read_integer(schema)

    def read_float(self, schema: "Schema") -> float:
        """Read a float (32-bit) value from the underlying data.

        :param schema: The shape's schema.
        :returns: A float from the underlying data.
        """
        ...

    def read_double(self, schema: "Schema") -> float:
        """Read a double (64-bit float) value from the underlying data.

        :param schema: The shape's schema.
        :returns: A double from the underlying data.
        """
        return self.read_float(schema)

    def read_big_integer(self, schema: "Schema") -> int:
        """Read a big integer (arbitrarily large integer) value from the underlying
        data.

        :param schema: The shape's schema.
        :returns: A big integer from the underlying data.
        """
        return self.read_integer(schema)

    def read_big_decimal(self, schema: "Schema") -> Decimal:
        """Read a big decimal (arbitrarily large float) value from the underlying data.

        :param schema: The shape's schema.
        :returns: A big decimal from the underlying data.
        """
        ...

    def read_string(self, schema: "Schema") -> str:
        """Read a string value from the underlying data.

        :param schema: The shape's schema.
        :returns: A string from the underlying data.
        """
        ...

    def read_document(self, schema: "Schema") -> "Document":
        """Read a document value from the underlying data.

        :param schema: The shape's schema.
        :returns: A document from the underlying data.
        """
        ...

    def read_timestamp(self, schema: "Schema") -> datetime.datetime:
        """Read a timestamp value from the underlying data.

        :param schema: The shape's schema.
        :returns: A timestamp from the underlying data.
        """
        ...

    def read_data_stream(self, schema: "Schema") -> "_Stream":
        """Read a data stream from the underlying data.

        The data itself MUST NOT be read by this method. The value returned is intended
        to be read later by the consumer. In an HTTP implementation, for example, this
        would directly return the HTTP body stream. The stream MAY be wrapped to provide
        a more consistent interface or to avoid exposing implementation details.

        Data streams are only supported at the top-level input and output for
        operations.

        :param schema: The shape's schema.
        :returns: A data stream derived from the underlying data.
        """
        raise UnsupportedStreamException()


class SpecificShapeDeserializer(ShapeDeserializer):
    """Expects to deserialize a specific kind of shape, failing if other shapes are
    deserialized."""

    def _invalid_state(
        self, schema: "Schema | None" = None, message: str | None = None
    ) -> Never:
        if message is None:
            message = f"Unexpected schema type: {schema}"
        raise SmithyException(message)

    def read_struct(
        self,
        schema: "Schema",
        consumer: Callable[["Schema", "ShapeDeserializer"], None],
    ) -> None:
        self._invalid_state(schema)

    def read_list(
        self, schema: "Schema", consumer: Callable[["ShapeDeserializer"], None]
    ) -> None:
        self._invalid_state(schema)

    def read_map(
        self,
        schema: "Schema",
        consumer: Callable[[str, "ShapeDeserializer"], None],
    ) -> None:
        self._invalid_state(schema)

    def is_null(self) -> bool:
        self._invalid_state(message="Unexpected attempt to read null.")

    def read_null(self) -> None:
        self._invalid_state(message="Unexpected attempt to read null.")

    def read_boolean(self, schema: "Schema") -> bool:
        self._invalid_state(schema)

    def read_blob(self, schema: "Schema") -> bytes:
        self._invalid_state(schema)

    def read_byte(self, schema: "Schema") -> int:
        self._invalid_state(schema)

    def read_short(self, schema: "Schema") -> int:
        self._invalid_state(schema)

    def read_integer(self, schema: "Schema") -> int:
        self._invalid_state(schema)

    def read_long(self, schema: "Schema") -> int:
        self._invalid_state(schema)

    def read_float(self, schema: "Schema") -> float:
        self._invalid_state(schema)

    def read_double(self, schema: "Schema") -> float:
        self._invalid_state(schema)

    def read_big_integer(self, schema: "Schema") -> int:
        self._invalid_state(schema)

    def read_big_decimal(self, schema: "Schema") -> Decimal:
        self._invalid_state(schema)

    def read_string(self, schema: "Schema") -> str:
        self._invalid_state(schema)

    def read_document(self, schema: "Schema") -> "Document":
        self._invalid_state(schema)

    def read_timestamp(self, schema: "Schema") -> datetime.datetime:
        self._invalid_state(schema)

    def read_data_stream(self, schema: "Schema") -> "_Stream":
        self._invalid_state(schema)


@runtime_checkable
class DeserializeableShape(Protocol):
    """Protocol for shapes that are deserializeable using a ShapeDeserializer."""

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        """Construct an instance of this class using the given deserializer.

        :param deserializer: The deserializer to read from.
        :returns: An instance of this class created from the deserializer.
        """
        ...
