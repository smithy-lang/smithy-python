#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import TYPE_CHECKING

from smithy_core.types import TimestampFormat

if TYPE_CHECKING:
    from ._private.documents import JSONDocument


@dataclass(slots=True)
class JSONSettings:
    """Settings for the JSON codec."""

    document_class: type["JSONDocument"]
    """The document class to deserialize to."""

    use_json_name: bool = True
    """Whether the codec should use `smithy.api#jsonName` trait, if present."""

    use_timestamp_format: bool = True
    """Whether the codec should use the `smithy.api#timestampFormat` trait, if
    present."""

    default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME
    """The default timestamp format to use if the `smithy.api#timestampFormat` trait is
    not enabled or not present."""

    default_namespace: str | None = None
    """The default namespace to use when determining a document's discriminator."""
