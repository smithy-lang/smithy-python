# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol

from . import JSONCodec
from .settings import JSONDeserializationMode


class _JSONDeserializationConfig(Protocol):
    @property
    def protocol(self) -> object | None: ...

    @property
    def json_deserialization_mode(self) -> JSONDeserializationMode | None: ...


def json_deserialization_plugin(config: _JSONDeserializationConfig) -> None:
    """Configure JSON deserialization on a generated client's protocol codec."""

    codec = getattr(config.protocol, "payload_codec", None)
    if isinstance(codec, JSONCodec):
        codec.deserialization_mode = (
            config.json_deserialization_mode or JSONDeserializationMode.AUTO
        )
