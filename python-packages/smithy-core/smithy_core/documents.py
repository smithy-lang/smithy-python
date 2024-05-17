import datetime
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from decimal import Decimal
from typing import TypeGuard, override

from .deserializers import DeserializeableShape, ShapeDeserializer
from .exceptions import ExpectationNotMetException
from .schemas import Schema
from .serializers import (
    InterceptingSerializer,
    MapSerializer,
    SerializeableShape,
    ShapeSerializer,
)
from .shapes import ShapeID, ShapeType
from .utils import expect_type

_DOCUMENT = Schema(id=ShapeID("smithy.api#Document"), type=ShapeType.DOCUMENT)


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
        elif isinstance(value, Sequence):
            if self._is_raw_list(value):
                self._raw_value = value
            else:
                self._value = value  # type: ignore
        else:
            self._value = value

        if self._schema is not _DOCUMENT:
            self._type = self._schema.type
        elif isinstance(self._raw_value, Sequence):
            self._type = ShapeType.LIST
        else:
            match self._value:
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
                case list():
                    self._type = ShapeType.LIST
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
        if schema.type == ShapeType.LIST:
            schema = self._schema.members["member"].expect_member_target()
        return [Document(e, schema=schema) for e in value]

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
        if self._schema.type is not ShapeType.STRUCTURE:
            member_schema = self._schema
            if self._schema.type is ShapeType.MAP:
                member_schema = self._schema.members["value"].expect_member_target()
            return {k: Document(v, schema=member_schema) for k, v in value.items()}

        result: dict[str, "Document"] = {}
        for k, v in value.items():
            result[k] = Document(
                v, schema=self._schema.members[k].expect_member_target()
            )
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
        return shape_class.deserialize(DocumentDeserializer(self))

    @classmethod
    def from_shape(cls, shape: SerializeableShape) -> "Document":
        """Constructs a Document from a given shape.

        :param shape: The shape to convert to a document.
        :returns: A Document representation of the given shape.
        """
        serializer = DocumentSerializer()
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
            if not isinstance(value, Document):
                schema = self._schema
                if schema.type is ShapeType.STRUCTURE:
                    schema = schema.members[key].expect_member_target()
                elif schema.type is ShapeType.MAP:
                    schema = schema.members["value"].expect_member_target()
                value = Document(value, schema=schema)
            self.as_map()[key] = value
        else:
            if not isinstance(value, Document):
                schema = self._schema
                if schema.type == ShapeType.LIST:
                    schema = schema.members["member"].expect_member_target()
                value = Document(value, schema=schema)
            self.as_list()[key] = value
        self._raw_value = None

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


class DocumentSerializer(ShapeSerializer):
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
        finally:
            self.result = delegate.result

    @override
    @contextmanager
    def begin_list(self, schema: "Schema") -> Iterator[ShapeSerializer]:
        delegate = _DocumentListSerializer(schema)
        try:
            yield delegate
        finally:
            self.result = delegate.result

    @override
    @contextmanager
    def begin_map(self, schema: "Schema") -> Iterator[MapSerializer]:
        delegate = _DocumentMapSerializer(schema)
        try:
            yield delegate
        finally:
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
    _delegate = DocumentSerializer()
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
    _delegate = DocumentSerializer()
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
    _delegate = DocumentSerializer()
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


class DocumentDeserializer(ShapeDeserializer):
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
                consumer(member_schema, DocumentDeserializer(value))

    @override
    def read_list(
        self, schema: "Schema", consumer: Callable[[ShapeDeserializer], None]
    ):
        for element in self._value.as_list():
            consumer(DocumentDeserializer(element))

    @override
    def read_map(
        self,
        schema: "Schema",
        consumer: Callable[[str, ShapeDeserializer], None],
    ):
        for k, v in self._value.as_map().items():
            consumer(k, DocumentDeserializer(v))

    @override
    def read_null(self, schema: "Schema") -> None:
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
