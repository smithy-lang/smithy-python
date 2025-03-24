#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from base64 import b64decode
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from smithy_core.documents import Document, DocumentValue
from smithy_core.prelude import DOCUMENT
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import JSONNameTrait, TimestampFormatTrait
from smithy_core.types import TimestampFormat
from smithy_core.utils import expect_type


class JSONDocument(Document):
    _schema: Schema
    _json_names: dict[str, str]

    def __init__(
        self,
        value: DocumentValue | dict[str, "Document"] | list["Document"],
        *,
        schema: Schema = DOCUMENT,
        use_json_name: bool = True,
        use_timestamp_format: bool = True,
        default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME,
    ) -> None:
        super().__init__(value, schema=schema)
        self._use_json_name = use_json_name
        self._use_timestamp_format = use_timestamp_format
        self._default_timestamp_format = default_timestamp_format
        self._json_names = {}

        if use_json_name and schema.shape_type in (
            ShapeType.STRUCTURE,
            ShapeType.UNION,
        ):
            for member_name, member_schema in schema.members.items():
                if json_name := member_schema.get_trait(JSONNameTrait):
                    self._json_names[json_name.value] = member_name

    def as_blob(self) -> bytes:
        return b64decode(expect_type(str, self._value))

    def as_float(self) -> float:
        # Floats are returned as Decimals by default in ijson, which is the correct
        # behavior, since technically JSON numbers have arbitrary precision.
        return float(expect_type(Decimal, self._value))

    def as_timestamp(self) -> datetime:
        format = self._default_timestamp_format
        if self._use_timestamp_format:
            if format_trait := self._schema.get_trait(TimestampFormatTrait):
                format = format_trait.format

        match self._value:
            case float() | int() | str():
                return format.deserialize(self._value)
            case Decimal():
                return format.deserialize(float(self._value))
            case datetime():
                return self._value
            case _:
                raise Exception(
                    f"Expected number, but found {type(self._value)}: {self._value!r}"
                )

    def as_value(self) -> DocumentValue:
        if self.is_none():
            return None

        match self.shape_type:
            case ShapeType.STRING | ShapeType.ENUM:
                return self.as_string()
            case ShapeType.BOOLEAN:
                return self.as_boolean()
            case (
                ShapeType.BYTE
                | ShapeType.SHORT
                | ShapeType.INTEGER
                | ShapeType.INT_ENUM
                | ShapeType.LONG
                | ShapeType.BIG_INTEGER
            ):
                return self.as_integer()
            case ShapeType.FLOAT | ShapeType.DOUBLE:
                return self.as_float()
            case ShapeType.BIG_DECIMAL:
                return self.as_decimal()
            case ShapeType.BLOB:
                return self.as_blob()
            case ShapeType.TIMESTAMP:
                return self.as_timestamp()
            case ShapeType.LIST:
                return [e.as_value() for e in self.as_list()]
            case ShapeType.MAP | ShapeType.STRUCTURE | ShapeType.UNION:
                return {k: v.as_value() for k, v in self.as_map().items()}
            case _:
                return super().as_value()

    def _new_document(
        self,
        value: DocumentValue | dict[str, "Document"] | list["Document"],
        schema: Schema,
    ) -> "Document":
        return JSONDocument(
            value,
            schema=schema,
            use_json_name=self._use_json_name,
            use_timestamp_format=self._use_timestamp_format,
            default_timestamp_format=self._default_timestamp_format,
        )

    def _wrap_map(self, value: Mapping[str, DocumentValue]) -> dict[str, "Document"]:
        if self._schema.shape_type not in (ShapeType.STRUCTURE, ShapeType.UNION):
            return super()._wrap_map(value)

        result: dict[str, Document] = {}
        for k, v in value.items():
            member_name = self._json_names.get(k, k)
            result[member_name] = self._new_document(
                v, self._schema.members[member_name]
            )
        return result

    def __setitem__(
        self,
        key: str | int,
        value: "Document | list[Document] | dict[str, Document] | DocumentValue",
    ) -> None:
        if isinstance(key, str) and self._schema.shape_type in (
            ShapeType.STRUCTURE,
            ShapeType.UNION,
        ):
            member_name = self._json_names.get(key, key)
            schema = self._schema.members[member_name]

            if not isinstance(value, Document):
                value = Document(value, schema=schema)
            else:
                value = value._with_schema(schema)

            self.as_map()[member_name] = value
            self._raw_value = None
        else:
            super().__setitem__(key, value)
