# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, cast
from xml.etree.ElementTree import canonicalize

import pytest
from smithy_core.prelude import (
    BIG_DECIMAL,
    BLOB,
    BOOLEAN,
    FLOAT,
    INTEGER,
    STRING,
    TIMESTAMP,
)
from smithy_xml import XMLCodec

from . import (
    NAMESPACED_LIST_SCHEMA,
    NAMESPACED_STRUCT_SCHEMA,
    PREFIXED_NS_STRUCT_SCHEMA,
    RENAMED_NS_MAP_SCHEMA,
    STRING_LIST_SCHEMA,
    STRING_MAP_SCHEMA,
    XML_SERDE_CASES,
    SerdeShape,
)


def _canonicalize(xml_bytes: bytes) -> str:
    """Canonicalize XML for comparison, stripping whitespace differences."""
    return canonicalize(xml_bytes, strip_text=True)


@pytest.mark.parametrize("given, expected", XML_SERDE_CASES)
def test_xml_serializer(given: Any, expected: bytes) -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    match given:
        case bool():
            serializer.write_boolean(BOOLEAN, given)
        case int():
            serializer.write_integer(INTEGER, given)
        case float():
            serializer.write_float(FLOAT, given)
        case Decimal():
            serializer.write_big_decimal(BIG_DECIMAL, given)
        case bytes():
            serializer.write_blob(BLOB, given)
        case str():
            serializer.write_string(STRING, given)
        case datetime():
            serializer.write_timestamp(TIMESTAMP, given)
        case list():
            given = cast(list[str], given)
            with serializer.begin_list(STRING_LIST_SCHEMA, len(given)) as ls:
                member_schema = STRING_LIST_SCHEMA.members["member"]
                for e in given:
                    ls.write_string(member_schema, e)
        case dict():
            given = cast(dict[str, str], given)
            with serializer.begin_map(STRING_MAP_SCHEMA, len(given)) as ms:
                member_schema = STRING_MAP_SCHEMA.members["value"]
                for k, v in given.items():
                    ms.entry(k, lambda vs: vs.write_string(member_schema, v))  # type: ignore
        case SerdeShape():
            given.serialize(serializer)
        case _:
            raise Exception(f"Unexpected type: {type(given)}")

    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert _canonicalize(actual) == _canonicalize(expected)


def test_write_null() -> None:
    """write_null creates an empty element (no text content)."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    serializer.write_null(STRING)
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert actual == b"<String />"


def test_write_document_raises() -> None:
    """XML does not support document types."""
    from smithy_core.documents import Document
    from smithy_core.prelude import DOCUMENT

    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with pytest.raises(NotImplementedError, match="XML does not support document"):
        serializer.write_document(DOCUMENT, Document(None))


def test_float_nan() -> None:
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    serializer.write_float(FLOAT, float("nan"))
    serializer.flush()
    sink.seek(0)
    assert sink.read() == b"<Float>NaN</Float>"


def test_default_namespace() -> None:
    """Default namespace is set on the root element."""
    sink = BytesIO()
    serializer = XMLCodec(default_namespace="https://example.com/").create_serializer(
        sink
    )
    serializer.write_string(STRING, "hi")
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert actual == b'<String xmlns="https://example.com/">hi</String>'


def test_xml_escaping_in_attribute() -> None:
    """XML special characters are escaped in attribute values."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    shape = SerdeShape(xml_attribute_named_member='<"test">&')
    shape.serialize(serializer)
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert actual == b'<SerdeShape test="&lt;&quot;test&quot;&gt;&amp;" />'


def test_flush_with_no_writes() -> None:
    """Flushing without any writes produces no output."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    serializer.flush()
    sink.seek(0)
    assert sink.read() == b""


def test_list_with_namespace_on_member() -> None:
    """@xmlNamespace on list member adds xmlns to each item element."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    items = ["Bar"]
    with serializer.begin_list(NAMESPACED_LIST_SCHEMA, len(items)) as ls:
        member_schema = NAMESPACED_LIST_SCHEMA.members["member"]
        for e in items:
            ls.write_string(member_schema, e)
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert (
        actual
        == b'<NamespacedList><member xmlns="http://bux.com">Bar</member></NamespacedList>'
    )


def test_map_with_xmlname_and_namespace() -> None:
    """Map with @xmlName + @xmlNamespace on key and value members."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    data = {"a": "A"}
    with serializer.begin_map(RENAMED_NS_MAP_SCHEMA, len(data)) as ms:
        member_schema = RENAMED_NS_MAP_SCHEMA.members["value"]
        for k, v in data.items():
            ms.entry(k, lambda vs: vs.write_string(member_schema, v))
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert actual == (
        b"<RenamedNsMap><entry>"
        b'<K xmlns="https://the-key.example.com">a</K>'
        b'<V xmlns="https://the-value.example.com">A</V>'
        b"</entry></RenamedNsMap>"
    )


def test_struct_with_xml_namespace() -> None:
    """@xmlNamespace on struct adds default xmlns to root element."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(NAMESPACED_STRUCT_SCHEMA) as ss:
        ss.write_string(NAMESPACED_STRUCT_SCHEMA.members["value"], "hi")
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert (
        actual == b'<NsStruct xmlns="https://example.com"><value>hi</value></NsStruct>'
    )


def test_struct_with_xml_namespace_prefix() -> None:
    """@xmlNamespace with prefix adds prefixed xmlns to root element."""
    sink = BytesIO()
    serializer = XMLCodec().create_serializer(sink)
    with serializer.begin_struct(PREFIXED_NS_STRUCT_SCHEMA) as ss:
        ss.write_string(PREFIXED_NS_STRUCT_SCHEMA.members["value"], "hi")
    serializer.flush()
    sink.seek(0)
    actual = sink.read()
    assert (
        actual
        == b'<PrefixedNsStruct xmlns:baz="https://example.com"><value>hi</value></PrefixedNsStruct>'
    )
