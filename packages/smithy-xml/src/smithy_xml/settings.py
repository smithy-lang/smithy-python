#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from smithy_core.types import TimestampFormat


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

    default_namespace_prefix: str | None = None
    """Prefix for the default XML namespace. When set, the root element declares
    ``xmlns:<prefix>`` instead of the default ``xmlns``. Has no effect unless
    ``default_namespace`` is also set."""
