import datetime
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import TypeGuard

from .exceptions import ExpectationNotMetException
from .schemas import Schema
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
    def type(self) -> ShapeType:
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
        if schema is not _DOCUMENT:
            schema = self._schema.members["member"]
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
        if self._schema is _DOCUMENT:
            return {k: Document(v) for k, v in value.items()}

        result: dict[str, "Document"] = {}
        for k, v in value.items():
            result[k] = Document(v, schema=self._schema.members[k])
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
                if schema is not _DOCUMENT:
                    schema = schema.members[key]
                value = Document(value, schema=schema)
            self.as_map()[key] = value
        else:
            if not isinstance(value, Document):
                schema = self._schema
                if schema is not _DOCUMENT:
                    schema = schema.members["member"]
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
