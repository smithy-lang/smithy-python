#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import StrEnum

from smithy_core.types import TimestampFormat


class XMLDeserializationMode(StrEnum):
    """Controls how XML payloads are parsed during deserialization."""

    AUTO = "auto"
    """Eagerly parse bytes while preserving incremental reader consumption."""

    EAGER = "eager"
    """Parse and materialize the complete XML tree before deserializing."""

    STREAMING = "streaming"
    """Incrementally deserialize XML using the pull parser."""


@dataclass(slots=True)
class XMLSettings:
    """Settings for the XML codec."""

    use_timestamp_format: bool = True
    """Whether the codec should use the `smithy.api#timestampFormat` trait, if present."""

    default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME
    """The default timestamp format to use if the `smithy.api#timestampFormat` trait is
    not enabled or not present."""

    default_namespace: str | None = None
    """Default XML namespace (`xmlns`) applied to the root element during serialization."""

    deserialization_mode: XMLDeserializationMode = XMLDeserializationMode.AUTO
    """Controls whether XML deserialization is eager, streaming, or automatic."""
