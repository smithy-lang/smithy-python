#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from typing import Protocol, runtime_checkable


@runtime_checkable
class Flushable(Protocol):
    """A protocol for objects that can be flushed."""

    def flush(self) -> None: ...
