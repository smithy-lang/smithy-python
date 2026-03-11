#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from smithy_core.types import TimestampFormat


@dataclass(frozen=True)
class XMLSettings:
    """Configuration for XML serialization/deserialization."""

    default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME
    """Default timestamp format when a member does not define @timestampFormat."""

    default_namespace: str | None = None
    """Default XML namespace (``xmlns``) applied to the root element during serialization."""
