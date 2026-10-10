# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

import pytest
from smithy_json import JSONCodec, JSONDeserializationMode
from smithy_json.plugins import json_deserialization_plugin


@dataclass
class _Protocol:
    payload_codec: object


@dataclass
class _Config:
    protocol: object
    json_deserialization_mode: JSONDeserializationMode | None


@pytest.mark.parametrize(
    "configured, expected",
    [
        (None, JSONDeserializationMode.AUTO),
        (JSONDeserializationMode.AUTO, JSONDeserializationMode.AUTO),
        (JSONDeserializationMode.EAGER, JSONDeserializationMode.EAGER),
        (JSONDeserializationMode.STREAMING, JSONDeserializationMode.STREAMING),
    ],
)
def test_configures_json_codec(
    configured: JSONDeserializationMode | None,
    expected: JSONDeserializationMode,
) -> None:
    codec = JSONCodec(deserialization_mode=JSONDeserializationMode.EAGER)
    config = _Config(
        protocol=_Protocol(payload_codec=codec),
        json_deserialization_mode=configured,
    )

    json_deserialization_plugin(config)

    assert codec.deserialization_mode is expected


@pytest.mark.parametrize("protocol", [object(), _Protocol(payload_codec=object())])
def test_ignores_protocols_without_json_codec(protocol: object) -> None:
    config = _Config(
        protocol=protocol,
        json_deserialization_mode=JSONDeserializationMode.STREAMING,
    )
    json_deserialization_plugin(config)
