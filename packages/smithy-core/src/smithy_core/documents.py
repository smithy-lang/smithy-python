import datetime
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from decimal import Decimal
from typing import TypeGuard, override

from .deserializers import DeserializeableShape, ShapeDeserializer
from .exceptions import ExpectationNotMetException, SmithyException
from .schemas import Schema
from .serializers import (
    InterceptingSerializer,
    MapSerializer,
    SerializeableShape,
    ShapeSerializer,
)
from .shapes import ShapeID, ShapeType
from .utils import expect_type

_DOCUMENT = Schema(id=ShapeID("smithy.api#Document"), shape_type=ShapeType.DOCUMENT)


type DocumentValue = (
    Mapping[str, DocumentValue]
    | Sequence[DocumentValue]
    | str
    | int
    | float
    | Decimal
    | bool
    | None
    | bytes
    | datetime.datetime
)
"""Protocol-agnostic open content."""


type _InnerDocumentValue = (
    dict[str, "Document"]
    | list["Document"]
    | str
    | int
    | float
    | Decimal
    | bool
    | None
    | bytes
    | datetime.datetime
)
"""The inner value for a Document.

Collections in these inner values are restricted to having Document values and may only
be lists or dicts.
"""


class Document:
    """Wrapped protocol-agnostic open content.

    This wrapping class facilitates serialization and deserialiazation and may contain a
    schema to enable serializing and deserializing protocol-specific documents into a
    protocol-agnostic form.
    """

    _value: _InnerDocumentValue = None
    _raw_value: Mapping[str, DocumentValue] | Sequence[DocumentValue] | None = None
    _type: ShapeType
    _schema: Schema

    def __init__(
        self,
        value: DocumentValue | dict[str, "Document"] | list["Document"] = None,
        *,
        schema: Schema = _DOCUMENT,
    ) -> None:
        """Initializes a document.

        :param value: The underlying value of a document.
        :param schema: A schema defining the document's structure. The default value is
            a plain document schema with no traits.
        """
        self._schema = schema

        # Mappings and Sequences are lazily converted to/from the inner value type.
        if isinstance(value, Mapping):
            if self._is_raw_map(value):
                self._raw_value = value
            else:
                self._value = value  # type: ignore
        elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
            if self._is_raw_list(value):
                self._raw_value = value
            else:
                self._value = value  # type: ignore
        else:
            self._value = value

        if self._schema.shape_type not in (
            ShapeType.DOCUMENT,
            ShapeType.OPERATION,
            ShapeType.SERVICE,
        ):
            self._type = self._schema.shape_type
        else:
            # TODO: set an appropriate schema if one was not provided
            match value:
                case bool():
                    self._type = ShapeType.BOOLEAN
                case str():
                    self._type = ShapeType.STRING
                case int():
                    self._type = ShapeType.LONG
                case float():
                    self._type = ShapeType.DOUBLE
                case Decimal():
                    self._type = ShapeType.BIG_DECIMAL
                case bytes():
                    self._type = ShapeType.BLOB
                case datetime.datetime():
                    self._type = ShapeType.TIMESTAMP
                case Sequence():
                    self._type = ShapeType.LIST
                case Mapping():
                    self._type = ShapeType.MAP
                case _:
                    self._type = ShapeType.DOCUMENT

    def _is_raw_map(
        self, value: Mapping[str, "Document"] | Mapping[str, DocumentValue]
    ) -> TypeGuard[Mapping[str, DocumentValue]]:
        return len(value) != 0 and not isinstance(next(iter(value.values())), Document)

    def _is_raw_list(
        self, value: Sequence["Document"] | Sequence[DocumentValue]
    ) -> TypeGuard[Sequence[DocumentValue]]:
        return (
            len(value) != 0
            and not isinstance(value, str | bytes)
            and not isinstance(next(iter(value)), Document)
        )

    @property
    def shape_type(self) -> ShapeType:
        """The Smithy data model type for the underlying contents of the document."""
        return self._type

    @property
    def discriminator(self) -> ShapeID:
        """The shape ID that corresponds to the contents of the document."""
        return self._schema.id

    def is_none(self) -> bool:
        """Indicates whether the document contains a null value."""
        return self._value is None and self._raw_value is None

    def as_blob(self) -> bytes:
        """Asserts the document is a blob and returns it as bytes."""
        return expect_type(bytes, self._value)

    def as_boolean(self) -> bool:
        """Asserts the document is a boolean and returns it."""
        return expect_type(bool, self._value)

    def as_string(self) -> str:
        """Asserts the document is a string and returns it."""
        return expect_type(str, self._value)

    def as_timestamp(self) -> datetime.datetime:
        """Asserts the document is a timestamp and returns it."""
        return expect_type(datetime.datetime, self._value)

    def as_integer(self) -> int:
        """Asserts the document is an integer and returns it.

        This method is to be used for any type from the Smithy data model that
        translates to Python's int type. This includes: byte, short, integer, long, and
        bigInteger.
        """
        if isinstance(self._value, int) and not isinstance(self._value, bool):
            return self._value
        raise ExpectationNotMetException(
            f"Expected int, found {type(self._value)}: {self._value}"
        )

    def as_float(self) -> float:
        """Asserts the document is a float and returns it.

        This method is to be used for any type from the Smithy data model that
        translates to Python's float type. This includes float and double.
        """
        return expect_type(float, self._value)

    def as_decimal(self) -> Decimal:
        """Asserts the document is a Decimal and returns it."""
        return expect_type(Decimal, self._value)

    def as_list(self) -> list["Document"]:
        """Asserts the document is a list and returns it."""
        if isinstance(self._value, list):
            return self._value
        if (
            self._value is None
            and isinstance(self._raw_value, Sequence)
            and not isinstance(self._raw_value, str | bytes)
        ):
            self._value = self._wrap_list(self._raw_value)
            return self._value
        raise ExpectationNotMetException(
            f"Expected list, found {type(self._value)}: {self._value}"
        )

    def _wrap_list(self, value: Sequence[DocumentValue]) -> list["Document"]:
        schema = self._schema
        if schema.shape_type is ShapeType.LIST:
            schema = self._schema.members["member"]
        return [self._new_document(e, schema) for e in value]

    def _new_document(
        self,
        value: DocumentValue | dict[str, "Document"] | list["Document"],
        schema: Schema,
    ) -> "Document":
        return Document(value, schema=schema)

    def as_map(self) -> dict[str, "Document"]:
        """Asserts the document is a map and returns it."""
        if isinstance(self._value, Mapping):
            return self._value
        if self._value is None and isinstance(self._raw_value, Mapping):
            self._value = self._wrap_map(self._raw_value)
            return self._value
        raise ExpectationNotMetException(
            f"Expected map, found {type(self._value)}: {self._value}"
        )

    def _wrap_map(self, value: Mapping[str, DocumentValue]) -> dict[str, "Document"]:
        if self._schema.shape_type not in (ShapeType.STRUCTURE, ShapeType.UNION):
            member_schema = self._schema
            if self._schema.shape_type is ShapeType.MAP:
                member_schema = self._schema.members["value"]
            return {k: self._new_document(v, member_schema) for k, v in value.items()}

        result: dict[str, Document] = {}
        for k, v in value.items():
            result[k] = self._new_document(v, self._schema.members[k])
        return result

    def as_value(self) -> DocumentValue:
        """Converts the document to a plain, protocol-agnostic DocumentValue and returns
        it."""
        if self._value is not None and self._raw_value is None:
            match self._value:
                case dict():
                    self._raw_value = {k: v.as_value() for k, v in self._value.items()}
                case list():
                    self._raw_value = [e.as_value() for e in self._value]
                case _:
                    return self._value
        return self._raw_value

    def as_shape[S: DeserializeableShape](self, shape_class: type[S]) -> S:
        """Converts the document to an instance of the given shape type.

        :param shape_class: A class that implements the DeserializeableShape protocol.
        """
        return shape_class.deserialize(_DocumentDeserializer(self))

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_document(self._schema, self)

    def serialize_contents(self, serializer: ShapeSerializer) -> None:
        if self.is_none():
            serializer.write_null(self._schema)
            return

        match self._type:
            case ShapeType.STRUCTURE | ShapeType.UNION:
                with serializer.begin_struct(self._schema) as struct_serializer:
                    self.serialize_members(struct_serializer)
            case ShapeType.LIST:
                list_value = self.as_list()
                with serializer.begin_list(
                    self._schema, len(list_value)
                ) as list_serializer:
                    for element in list_value:
                        element.serialize(list_serializer)
            case ShapeType.MAP:
                map_value = self.as_map()
                with serializer.begin_map(
                    self._schema, len(map_value)
                ) as map_serializer:
                    for key, value in map_value.items():
                        map_serializer.entry(key, lambda s: value.serialize(s))
            case ShapeType.STRING | ShapeType.ENUM:
                serializer.write_string(self._schema, self.as_string())
            case ShapeType.BOOLEAN:
                serializer.write_boolean(self._schema, self.as_boolean())
            case ShapeType.BYTE:
                serializer.write_byte(self._schema, self.as_integer())
            case ShapeType.SHORT:
                serializer.write_short(self._schema, self.as_integer())
            case ShapeType.INTEGER | ShapeType.INT_ENUM:
                serializer.write_integer(self._schema, self.as_integer())
            case ShapeType.LONG:
                serializer.write_long(self._schema, self.as_integer())
            case ShapeType.BIG_INTEGER:
                serializer.write_big_integer(self._schema, self.as_integer())
            case ShapeType.FLOAT:
                serializer.write_float(self._schema, self.as_float())
            case ShapeType.DOUBLE:
                serializer.write_double(self._schema, self.as_float())
            case ShapeType.BIG_DECIMAL:
                serializer.write_big_decimal(self._schema, self.as_decimal())
            case ShapeType.BLOB:
                serializer.write_blob(self._schema, self.as_blob())
            case ShapeType.TIMESTAMP:
                serializer.write_timestamp(self._schema, self.as_timestamp())
            case ShapeType.DOCUMENT:
                # The shape type is only ever document when the value is null,
                # which is a case we've already handled.
                raise SmithyException(
                    f"Unexpexcted DOCUMENT shape type for document value: {self.as_value()}"
                )
            case _:
                raise SmithyException(
                    f"Unexpected {self._type} shape type for document value: {self.as_value()}"
                )

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        for value in self.as_map().values():
            value.serialize(serializer)

    @classmethod
    def from_shape(cls, shape: SerializeableShape) -> "Document":
        """Constructs a Document from a given shape.

        :param shape: The shape to convert to a document.
        :returns: A Document representation of the given shape.
        """
        serializer = _DocumentSerializer()
        shape.serialize(serializer=serializer)
        serializer.flush()
        return serializer.expect_result()

    def get(self, name: str, default: "Document | None" = None) -> "Document | None":
        """Gets a named member of the document or a default value."""
        return self.as_map().get(name, default)

    def __getitem__(self, key: str | int | slice) -> "Document":
        match key:
            case str():
                return self.as_map()[key]
            case int():
                return self.as_list()[key]
            case slice():
                return Document(self.as_list()[key], schema=self._schema)

    def __setitem__(
        self,
        key: str | int,
        value: "Document | list[Document] | dict[str, Document] | DocumentValue",
    ) -> None:
        if isinstance(key, str):
            schema = self._schema
            if schema.shape_type is ShapeType.STRUCTURE:
                schema = schema.members[key]
            elif schema.shape_type is ShapeType.MAP:
                schema = schema.members["value"]

            if not isinstance(value, Document):
                value = Document(value, schema=schema)
            else:
                value = value._with_schema(schema)

            self.as_map()[key] = value
        else:
            schema = self._schema
            if schema.shape_type is ShapeType.LIST:
                schema = schema.members["member"]

            if not isinstance(value, Document):
                value = Document(value, schema=schema)
            else:
                value = value._with_schema(schema)

            self.as_list()[key] = value
        self._raw_value = None

    def _with_schema(self, schema: Schema) -> "Document":
        if self.shape_type in [ShapeType.STRUCTURE, ShapeType.MAP, ShapeType.UNION]:
            return Document(self.as_map(), schema=schema)
        elif self.shape_type is ShapeType.LIST:
            return Document(self.as_list(), schema=schema)
        else:
            return Document(self._value, schema=schema)

    def __delitem__(self, key: str | int) -> None:
        if isinstance(key, str):
            del self.as_map()[key]
        else:
            del self.as_list()[key]
        self._raw_value = None

    def __repr__(self) -> str:
        value: str
        if self._value is not None:
            value = repr(self._value)
        else:
            value = repr(self._raw_value)

        if self._schema is _DOCUMENT:
            return f"Document(value={value})"
        return f"Document(value={value}, schema={self._schema})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return False
        # Note that the schema isn't important to equality. If some subclass, such as a
        # JsonDocument, cares about the schema then it's responsible for transforming
        # the output of `as_value` to the canonical form.
        return self.as_value() == other.as_value()


class _DocumentSerializer(ShapeSerializer):
    """Serializes shapes into document representations."""

    result: Document | None = None

    def expect_result(self) -> Document:
        """Expect a document to have been serialized and return it."""
        if self.result is None:
            raise ExpectationNotMetException(
                "Expected document serializer to have a result, but was None"
            )
        return self.result

    @override
    @contextmanager
    def begin_struct(self, schema: "Schema") -> Iterator[ShapeSerializer]:
        delegate = _DocumentStructSerializer(schema)
        try:
            yield delegate
        except Exception:
            raise
        else:
            self.result = delegate.result

    @override
    @contextmanager
    def begin_list(self, schema: "Schema", size: int) -> Iterator[ShapeSerializer]:
        delegate = _DocumentListSerializer(schema)
        try:
            yield delegate
        except Exception:
            raise
        else:
            self.result = delegate.result

    @override
    @contextmanager
    def begin_map(self, schema: "Schema", size: int) -> Iterator[MapSerializer]:
        delegate = _DocumentMapSerializer(schema)
        try:
            yield delegate
        except Exception:
            raise
        else:
            self.result = delegate.result

    @override
    def write_null(self, schema: "Schema") -> None:
        self.result = Document(None, schema=schema)

    @override
    def write_boolean(self, schema: "Schema", value: bool) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_integer(self, schema: "Schema", value: int) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_float(self, schema: "Schema", value: float) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_string(self, schema: "Schema", value: str) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_blob(self, schema: "Schema", value: bytes) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        self.result = Document(value, schema=schema)

    @override
    def write_document(self, schema: "Schema", value: Document) -> None:
        self.result = value


class _DocumentStructSerializer(InterceptingSerializer):
    _delegate = _DocumentSerializer()
    _result: Document

    def __init__(self, schema: "Schema") -> None:
        self._result = Document({}, schema=schema)

    @property
    def result(self) -> Document:
        return self._result

    def before(self, schema: "Schema") -> ShapeSerializer:
        return self._delegate

    def after(self, schema: "Schema") -> None:
        self._result[schema.expect_member_name()] = self._delegate.expect_result()
        self._delegate.result = None


class _DocumentListSerializer(InterceptingSerializer):
    _delegate = _DocumentSerializer()
    _result: list[Document]
    _schema: "Schema"

    def __init__(self, schema: "Schema") -> None:
        self._result = []
        self._schema = schema

    @property
    def result(self) -> Document:
        return Document(self._result, schema=self._schema)

    def before(self, schema: "Schema") -> ShapeSerializer:
        return self._delegate

    def after(self, schema: "Schema") -> None:
        self._result.append(self._delegate.expect_result())
        self._delegate.result = None


class _DocumentMapSerializer(MapSerializer):
    _delegate = _DocumentSerializer()
    _result: Document

    def __init__(self, schema: "Schema") -> None:
        self._result = Document({}, schema=schema)

    @property
    def result(self) -> Document:
        return self._result

    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        value_writer(self._delegate)
        self._result[key] = self._delegate.expect_result()
        self._delegate.result = None


class _DocumentDeserializer(ShapeDeserializer):
    """Deserializes documents into shapes."""

    def __init__(self, value: Document) -> None:
        """Initialize a DocumentDeserializer.

        :param value: The document to deserialize.
        """
        self._value = value

    @override
    def read_struct(
        self,
        schema: "Schema",
        consumer: Callable[["Schema", ShapeDeserializer], None],
    ):
        for member_name, member_schema in schema.members.items():
            if (value := self._value.get(member_name)) is not None:
                consumer(member_schema, _DocumentDeserializer(value))

    @override
    def read_list(
        self, schema: "Schema", consumer: Callable[[ShapeDeserializer], None]
    ):
        for element in self._value.as_list():
            consumer(_DocumentDeserializer(element))

    @override
    def read_map(
        self,
        schema: "Schema",
        consumer: Callable[[str, ShapeDeserializer], None],
    ):
        for k, v in self._value.as_map().items():
            consumer(k, _DocumentDeserializer(v))

    @override
    def is_null(self) -> bool:
        return self._value.is_none()

    @override
    def read_null(self) -> None:
        if (value := self._value.as_value()) is not None:
            raise ExpectationNotMetException(
                f"Expected document value to be None, but was: {value}"
            )

    @override
    def read_boolean(self, schema: "Schema") -> bool:
        return self._value.as_boolean()

    @override
    def read_blob(self, schema: "Schema") -> bytes:
        return self._value.as_blob()

    @override
    def read_integer(self, schema: "Schema") -> int:
        return self._value.as_integer()

    @override
    def read_float(self, schema: "Schema") -> float:
        return self._value.as_float()

    @override
    def read_big_decimal(self, schema: "Schema") -> Decimal:
        return self._value.as_decimal()

    @override
    def read_string(self, schema: "Schema") -> str:
        return self._value.as_string()

    @override
    def read_document(self, schema: "Schema") -> Document:
        return self._value

    @override
    def read_timestamp(self, schema: "Schema") -> datetime.datetime:
        return self._value.as_timestamp()


class TypeRegistry:
    """A registry for on-demand deserialization of types by using a mapping of shape IDs
    to their deserializers."""

    def __init__(
        self,
        types: dict[ShapeID, type[DeserializeableShape]],
        sub_registry: "TypeRegistry | None" = None,
    ):
        """Initialize a TypeRegistry.

        :param types: A mapping of ShapeID to the shapes they deserialize to.
        :param sub_registry: A registry to delegate to if an ID is not found in types.
        """
        self._types = types
        self._sub_registry = sub_registry

    def get(self, shape: ShapeID) -> type[DeserializeableShape]:
        """Get the deserializable shape for the given shape ID.

        :param shape: The shape ID to get from the registry.
        :returns: The corresponding deserializable shape.
        :raises KeyError: If the shape ID is not found in the registry.
        """
        if shape in self._types:
            return self._types[shape]
        if self._sub_registry is not None:
            return self._sub_registry.get(shape)
        raise KeyError(f"Unknown shape: {shape}")

    def __getitem__(self, shape: ShapeID):
        """Get the deserializable shape for the given shape ID.

        :param shape: The shape ID to get from the registry.
        :returns: The corresponding deserializable shape.
        :raises KeyError: If the shape ID is not found in the registry.
        """
        return self.get(shape)

    def __contains__(self, item: object, /):
        """Check if the registry contains the given shape.

        :param item: The shape ID to check for.
        """
        return item in self._types or (
            self._sub_registry is not None and item in self._sub_registry
        )

    def deserialize(self, document: Document) -> DeserializeableShape:
        return document.as_shape(self.get(document.discriminator))
