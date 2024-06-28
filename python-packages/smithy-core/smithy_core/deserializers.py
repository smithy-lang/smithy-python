import datetime
from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
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

    def read_null(self, schema: "Schema") -> None:
        """Read a null value from the underlying data.

        :param schema: The shape's schema.
        """
        ...

    def read_optional[
        T
    ](self, schema: "Schema", optional: Callable[["Schema"], T]) -> T | None:
        """Read an optional value from the underlying data.

        This is intended to be used with sparse lists or maps.

        :param schema: The shape's schema.
        :param optional: A callable that takes a schema and reads a non-nullable value
            from the underlying data.
        """
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
        return self.read_double(schema)

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
