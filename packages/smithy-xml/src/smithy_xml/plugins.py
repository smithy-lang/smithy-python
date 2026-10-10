# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol

from . import XMLCodec
from .settings import XMLDeserializationMode


class _XMLDeserializationConfig(Protocol):
    @property
    def protocol(self) -> object | None: ...

    @property
    def xml_deserialization_mode(self) -> XMLDeserializationMode | None: ...


def xml_deserialization_plugin(config: _XMLDeserializationConfig) -> None:
    """Configure XML deserialization on a generated client's protocol codec."""

    codec = getattr(config.protocol, "payload_codec", None)
    if isinstance(codec, XMLCodec) and config.xml_deserialization_mode is not None:
        codec.deserialization_mode = config.xml_deserialization_mode
