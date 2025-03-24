import datetime
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from decimal import Decimal
from typing import TYPE_CHECKING, Never, Protocol, runtime_checkable

from .exceptions import SmithyException, UnsupportedStreamException

if TYPE_CHECKING:
    from .aio.interfaces import StreamingBlob as _Stream
    from .documents import Document
    from .schemas import Schema


@runtime_checkable
class ShapeSerializer(Protocol):
    """Protocol for serializing shapes based on the Smithy data model.

    If used as a base class, all non-float number methods default to calling
    ``write_integer`` and ``write_double`` defaults to calling ``write_float``.
    These extra numeric methods are for types in the Smithy data model that
    don't have Python equivalents, but may have equivalents in the format
    being written.
    """

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        """Open a structure for writing.

        The returned context manager is responsible for closing the structure when the
        caller has finished writing members.

        The shape serializer contained in the context manager is responsible for writing
        out the member name as well as any additional data needed between the member
        name and value and between members.

        :param schema: The schema of the structure.
        :returns: A context manager containing a member serializer.
        """
        ...

    def write_struct(self, schema: "Schema", struct: "SerializeableStruct") -> None:
        """Write a structured shape to the output.

        This method is primarily intended to be used to serialize members that target
        structure or union shapes.

        :param schema: The member schema of the structure.
        :param struct: The structure to serialize.
        """
        with self.begin_struct(schema=schema) as struct_serializer:
            struct.serialize_members(struct_serializer)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        """Open a list for writing.

        The returned context manager is responsible for closing the list when the caller
        has finished writing elements.

        The shape serializer contained in the context manager is responsible for
        inserting any data needed between elements.

        :param schema: The schema of the list.
        :param size: The size of the list.
        :returns: A context manager containing an element serializer.
        """
        ...

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        """Open a map for writing.

        The returned context manager is responsible for closing the map when the caller
        has finished writing members.

        The MapSerializer contained in the context manager is responsible for writing
        out any additional data needed between the entry name and value as well as any
        data needed between entries.

        :param schema: The schema of the map.
        :param size: The size of the map.
        :returns: A context manager containing a map serializer.
        """
        ...

    def write_null(self, schema: "Schema") -> None:
        """Write a null value to the output.

        :param schema: The shape's schema.
        """
        ...

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        """Write a boolean value to the output.

        :param schema: The shape's schema.
        :param value: The boolean value to write.
        """
        ...

    def write_byte(self, schema: "Schema", value: int) -> None:
        """Write a byte (8-bit integer) value to the output.

        :param schema: The shape's schema.
        :param value: The byte value to write.
        """
        self.write_integer(schema, value)

    def write_short(self, schema: "Schema", value: int) -> None:
        """Write a short (16-bit integer) value to the output.

        :param schema: The shape's schema.
        :param value: The short value to write.
        """
        self.write_integer(schema, value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        """Write an integer (32-bit) value to the output.

        :param schema: The shape's schema.
        :param value: The integer value to write.
        """
        ...

    def write_long(self, schema: "Schema", value: int) -> None:
        """Write a long (64-bit integer) value to the output.

        :param schema: The shape's schema.
        :param value: The long value to write.
        """
        self.write_integer(schema, value)

    def write_float(self, schema: "Schema", value: float) -> None:
        """Write a float (32-bit) value to the output.

        :param schema: The shape's schema.
        :param value: The float value to write.
        """
        ...

    def write_double(self, schema: "Schema", value: float) -> None:
        """Write a double (64-bit float) value to the output.

        :param schema: The shape's schema.
        :param value: The double value to write.
        """
        self.write_float(schema, value)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        """Write a big integer (arbirtrarily large integer) value to the output.

        :param schema: The shape's schema.
        :param value: The big integer value to write.
        """
        self.write_integer(schema, value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        """Write a big decimal (arbitrarily large float) value to the output.

        :param schema: The shape's schema.
        :param value: The big decimal value to write.
        """
        ...

    def write_string(self, schema: "Schema", value: str) -> None:
        """Write a string value to the output.

        :param schema: The shape's schema.
        :param value: The string value to write.
        """
        ...

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        """Write a blob value to the output.

        :param schema: The shape's schema.
        :param value: The blob value to write.
        """
        ...

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        """Write a timestamp value to the output.

        :param schema: The shape's schema.
        :param value: The timestamp value to write.
        """
        ...

    def write_document(self, schema: "Schema", value: "Document") -> None:
        """Write a document value to the output.

        :param schema: The shape's schema.
        :param value: The document value to write.
        """
        ...

    def write_data_stream(self, schema: "Schema", value: "_Stream") -> None:
        """Write a data stream to the output.

        If the value is a stream (i.e. not bytes or bytearray) it MUST NOT be read
        directly by this method. Such values are intended to only be read as needed when
        sending a message, and so should be bound directly to the request / response
        type and then read by the transport.

        Data streams are only supported at the top-level input and output for
        operations.

        :param schema: The shape's schema.
        :param value: The streaming value to write.
        """
        if isinstance(value, bytes | bytearray):
            self.write_blob(schema, bytes(value))
        raise UnsupportedStreamException()

    def flush(self) -> None:
        """Flush the underlying data."""


@runtime_checkable
class MapSerializer(Protocol):
    """Protocol for serializing maps.

    These are responsible for writing any data needed between keys and values as well as
    any data needed between entries.
    """

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        """Write a map entry.

        :param key: The entry's key.
        :param value_writer: A callable that accepts a shape serializer to write values.
        """
        ...


class InterceptingSerializer(ShapeSerializer, metaclass=ABCMeta):
    """A shape serializer capable of injecting data before writing.

    This can, for example, be used to add in structure member keys, commas between
    structure members, or commas between lists.
    """

    @abstractmethod
    def before(self, schema: "Schema") -> ShapeSerializer: ...

    @abstractmethod
    def after(self, schema: "Schema") -> None: ...

    @contextmanager
    def begin_struct(self, schema: "Schema") -> Iterator[ShapeSerializer]:
        delegate = self.before(schema)

        try:
            with delegate.begin_struct(schema) as s:
                yield s
        except Exception:
            raise
        else:
            self.after(schema)

    @contextmanager
    def begin_list(self, schema: "Schema", size: int) -> Iterator[ShapeSerializer]:
        delegate = self.before(schema)

        try:
            with delegate.begin_list(schema, size) as s:
                yield s
        except Exception:
            raise
        else:
            self.after(schema)

    @contextmanager
    def begin_map(self, schema: "Schema", size: int) -> Iterator[MapSerializer]:
        delegate = self.before(schema)

        try:
            with delegate.begin_map(schema, size) as s:
                yield s
        except Exception:
            raise
        else:
            self.after(schema)

    def write_null(self, schema: "Schema") -> None:
        self.before(schema).write_null(schema)
        self.after(schema)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self.before(schema).write_boolean(schema, value)
        self.after(schema)

    def write_byte(self, schema: "Schema", value: int) -> None:
        self.before(schema).write_byte(schema, value)
        self.after(schema)

    def write_short(self, schema: "Schema", value: int) -> None:
        self.before(schema).write_short(schema, value)
        self.after(schema)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self.before(schema).write_integer(schema, value)
        self.after(schema)

    def write_long(self, schema: "Schema", value: int) -> None:
        self.before(schema).write_long(schema, value)
        self.after(schema)

    def write_float(self, schema: "Schema", value: float) -> None:
        self.before(schema).write_float(schema, value)
        self.after(schema)

    def write_double(self, schema: "Schema", value: float) -> None:
        self.before(schema).write_double(schema, value)
        self.after(schema)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        self.before(schema).write_big_integer(schema, value)
        self.after(schema)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self.before(schema).write_big_decimal(schema, value)
        self.after(schema)

    def write_string(self, schema: "Schema", value: str) -> None:
        self.before(schema).write_string(schema, value)
        self.after(schema)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self.before(schema).write_blob(schema, value)
        self.after(schema)

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self.before(schema).write_timestamp(schema, value)
        self.after(schema)

    def write_document(self, schema: "Schema", value: "Document") -> None:
        self.before(schema).write_document(schema, value)
        self.after(schema)

    def write_data_stream(self, schema: "Schema", value: "_Stream") -> None:
        self.before(schema).write_data_stream(schema, value)
        self.after(schema)


class SpecificShapeSerializer(ShapeSerializer):
    """Expects to serialize a specific kind of shape, failing if other shapes are
    serialized."""

    def _invalid_state(
        self, schema: "Schema | None" = None, message: str | None = None
    ) -> Never:
        if message is None:
            message = f"Unexpected schema type: {schema}"
        raise SmithyException(message)

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        self._invalid_state(schema)

    def begin_list(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["ShapeSerializer"]:
        self._invalid_state(schema)

    def begin_map(
        self, schema: "Schema", size: int
    ) -> AbstractContextManager["MapSerializer"]:
        self._invalid_state(schema)

    def write_null(self, schema: "Schema") -> None:
        self._invalid_state(schema)

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self._invalid_state(schema)

    def write_byte(self, schema: "Schema", value: int) -> None:
        self._invalid_state(schema)

    def write_short(self, schema: "Schema", value: int) -> None:
        self._invalid_state(schema)

    def write_integer(self, schema: "Schema", value: int) -> None:
        self._invalid_state(schema)

    def write_long(self, schema: "Schema", value: int) -> None:
        self._invalid_state(schema)

    def write_float(self, schema: "Schema", value: float) -> None:
        self._invalid_state(schema)

    def write_double(self, schema: "Schema", value: float) -> None:
        self._invalid_state(schema)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        self._invalid_state(schema)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self._invalid_state(schema)

    def write_string(self, schema: "Schema", value: str) -> None:
        self._invalid_state(schema)

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self._invalid_state(schema)

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self._invalid_state(schema)

    def write_document(self, schema: "Schema", value: "Document") -> None:
        self._invalid_state(schema)

    def write_data_stream(self, schema: "Schema", value: "_Stream") -> None:
        self._invalid_state(schema)


@runtime_checkable
class SerializeableShape(Protocol):
    """Protocol for shapes that are serializeable using a ShapeSerializer."""

    def serialize(self, serializer: ShapeSerializer) -> None:
        """Serialize the shape using the given serializer.

        :param serializer: The serializer to write shape data to.
        """
        ...


@runtime_checkable
class SerializeableStruct(SerializeableShape, Protocol):
    """Protocol for structures that are serializeable using a ShapeSerializer."""

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        """Serialize structure members using the given serializer.

        :param serializer: The serializer to write member data to.
        """
        ...
