#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smithy_core.types import TimestampFormat


@runtime_checkable
class Flushable(Protocol):
    """A protocol for objects that can be flushed."""

    def flush(self) -> None: ...


@dataclass
class JSONSettings:
    use_json_name: bool = True
    use_timestamp_format: bool = True
    default_timestamp_format: TimestampFormat = TimestampFormat.DATE_TIME
