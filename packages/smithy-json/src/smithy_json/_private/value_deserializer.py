# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
from base64 import b64decode
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from json import JSONDecodeError

from ijson.common import IncompleteJSONError  # type: ignore
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import SmithyError
from smithy_core.interfaces import BytesReader
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import JSONNameTrait, TimestampFormatTrait
from smithy_core.types import TimestampFormat

from ..settings import JSONSettings

type JSONValue = (
    Mapping[str, "JSONValue"]
    | Sequence["JSONValue"]
    | str
    | int
    | Decimal
    | bool
    | None
)


class JSONValueError(SmithyError):
    """Raised when a parsed JSON value does not match the requested Smithy type."""

    def __init__(self, expected: str, value: JSONValue) -> None:
        super().__init__(
            f"Error parsing JSON. Expected value of type `{expected}`, "
            f"but found: `{type(value).__name__}`: {value}"
        )


def _reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


class JSONValueDeserializer(ShapeDeserializer):
    """Deserializes Smithy shapes from a fully materialized JSON value."""

    def __init__(self, source: bytes | BytesReader, settings: JSONSettings) -> None:
        try:
            if isinstance(source, bytes):
                self._value: JSONValue = json.loads(
                    source,
                    parse_float=Decimal,
                    parse_constant=_reject_constant,
                )
            else:
                self._value = json.load(
                    source,
                    parse_float=Decimal,
                    parse_constant=_reject_constant,
                )
        except (JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            raise IncompleteJSONError(f"parse error: {error}") from error

        self._settings = settings
        self._json_names: dict[ShapeID, dict[str, Schema]] = {}

    def is_null(self) -> bool:
        return self._value is None

    def read_null(self) -> None:
        if self._value is not None:
            raise JSONValueError("null", self._value)

    def read_boolean(self, schema: Schema) -> bool:
        if not isinstance(self._value, bool):
            raise JSONValueError("boolean", self._value)
        return self._value

    def read_blob(self, schema: Schema) -> bytes:
        if not isinstance(self._value, str):
            raise JSONValueError("string", self._value)
        return b64decode(self._value)

    def read_integer(self, schema: Schema) -> int:
        if not isinstance(self._value, int) or isinstance(self._value, bool):
            raise JSONValueError("number", self._value)
        return self._value

    def read_float(self, schema: Schema) -> float:
        match self._value:
            case Decimal() | "Infinity" | "-Infinity" | "NaN":
                return float(self._value)
            case int() if not isinstance(self._value, bool):
                return self._value
            case _:
                raise JSONValueError("number", self._value)

    def read_big_decimal(self, schema: Schema) -> Decimal:
        match self._value:
            case Decimal():
                return self._value
            case int() if not isinstance(self._value, bool):
                return Decimal(self._value)
            case "Infinity" | "-Infinity" | "NaN":
                return Decimal(self._value)
            case _:
                raise JSONValueError("number", self._value)

    def read_string(self, schema: Schema) -> str:
        if not isinstance(self._value, str):
            raise JSONValueError("string", self._value)
        return self._value

    def read_document(self, schema: Schema) -> Document:
        return self._settings.document_class(
            value=self._value,
            schema=schema,
            settings=self._settings,
        )

    def read_timestamp(self, schema: Schema) -> datetime.datetime:
        format = self._settings.default_timestamp_format
        if self._settings.use_timestamp_format:
            if format_trait := schema.get_trait(TimestampFormatTrait):
                format = format_trait.format

        match format:
            case TimestampFormat.EPOCH_SECONDS:
                return format.deserialize(self.read_float(schema=schema))
            case _:
                return format.deserialize(self.read_string(schema=schema))

    def read_struct(
        self,
        schema: Schema,
        consumer: Callable[[Schema, ShapeDeserializer], None],
    ) -> None:
        value = self._value
        if not isinstance(value, Mapping):
            raise JSONValueError("object", value)

        struct_schema = schema.member_target or schema
        members = self._members_by_wire_name(struct_schema)
        try:
            for key, member_value in value.items():
                member = members.get(key)
                if member is None:
                    continue
                if member_value is None and member.shape_type is not ShapeType.DOCUMENT:
                    continue
                self._value = member_value
                consumer(member, self)
        finally:
            self._value = value

    def read_list(
        self,
        schema: Schema,
        consumer: Callable[[ShapeDeserializer], None],
    ) -> None:
        value = self._value
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise JSONValueError("array", value)

        try:
            for member_value in value:
                self._value = member_value
                consumer(self)
        finally:
            self._value = value

    def read_map(
        self,
        schema: Schema,
        consumer: Callable[[str, ShapeDeserializer], None],
    ) -> None:
        value = self._value
        if not isinstance(value, Mapping):
            raise JSONValueError("object", value)

        try:
            for key, member_value in value.items():
                self._value = member_value
                consumer(key, self)
        finally:
            self._value = value

    def _members_by_wire_name(self, schema: Schema) -> Mapping[str, Schema]:
        if not self._settings.use_json_name:
            return schema.members

        members = self._json_names.get(schema.id)
        if members is None:
            members = {}
            for member_name, member in schema.members.items():
                json_name = member.get_trait(JSONNameTrait)
                members[json_name.value if json_name is not None else member_name] = (
                    member
                )
            self._json_names[schema.id] = members
        return members
