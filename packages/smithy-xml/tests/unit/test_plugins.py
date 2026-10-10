# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

import pytest
from smithy_xml import XMLCodec, XMLDeserializationMode
from smithy_xml.plugins import xml_deserialization_plugin


@dataclass
class _Protocol:
    payload_codec: object


@dataclass
class _Config:
    protocol: object | None
    xml_deserialization_mode: XMLDeserializationMode | None


@pytest.mark.parametrize(
    "configured, expected",
    [
        (None, XMLDeserializationMode.EAGER),
        (XMLDeserializationMode.AUTO, XMLDeserializationMode.AUTO),
        (XMLDeserializationMode.EAGER, XMLDeserializationMode.EAGER),
        (XMLDeserializationMode.STREAMING, XMLDeserializationMode.STREAMING),
    ],
)
def test_configures_xml_codec(
    configured: XMLDeserializationMode | None,
    expected: XMLDeserializationMode,
) -> None:
    codec = XMLCodec(deserialization_mode=XMLDeserializationMode.EAGER)
    config = _Config(
        protocol=_Protocol(payload_codec=codec),
        xml_deserialization_mode=configured,
    )

    xml_deserialization_plugin(config)

    assert codec.deserialization_mode is expected


@pytest.mark.parametrize(
    "protocol",
    [None, object(), _Protocol(payload_codec=object())],
)
def test_ignores_protocols_without_xml_codec(protocol: object | None) -> None:
    config = _Config(
        protocol=protocol,
        xml_deserialization_mode=XMLDeserializationMode.STREAMING,
    )
    xml_deserialization_plugin(config)
