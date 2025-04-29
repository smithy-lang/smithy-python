#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from typing import Literal


class SmithyException(Exception):
    """Base exception type for all exceptions raised by smithy-python."""


type Fault = Literal["client", "server"] | None
"""Whether the client or server is at fault.

If None, then there was not enough information to determine fault.
"""


@dataclass(kw_only=True)
class CallException(SmithyException):
    """Base exception to be used in application-level errors.

    Implements :py:class:`.interfaces.retries.ErrorRetryInfo`.
    """

    fault: Fault = None
    """Whether the client or server is at fault.

    If None, then there was not enough information to determine fault.
    """

    message: str = field(default="", kw_only=False)
    """The message of the error."""

    is_retry_safe: bool | None = None
    """Whether the exception is safe to retry.

    A value of True does not mean a retry will occur, but rather that a retry is allowed
    to occur.

    A value of None indicates that there is not enough information available to
    determine if a retry is safe.
    """

    retry_after: float | None = None
    """The amount of time that should pass before a retry.

    Retry strategies MAY choose to wait longer.
    """

    is_throttling_error: bool = False
    """Whether the error is a throttling error."""

    def __post_init__(self):
        super().__init__(self.message)


@dataclass(kw_only=True)
class ModeledException(CallException):
    """Base exception to be used for modeled errors."""

    fault: Fault = "client"


class SerializationException(Exception):
    """Base exception type for exceptions raised during serialization."""


class SmithyRetryException(SmithyException):
    """Base exception type for all exceptions raised in retry strategies."""


class ExpectationNotMetException(SmithyException):
    """Exception type for exceptions thrown by unmet assertions."""


class SmithyIdentityException(SmithyException):
    """Base exception type for all exceptions raised in identity resolution."""


class MissingDependencyException(SmithyException):
    """Exception type raised when a feature that requires a missing optional dependency
    is called."""


class AsyncBodyException(SmithyException):
    """Exception indicating that a request with an async body type was created in a sync
    context."""


class UnsupportedStreamException(SmithyException):
    """Indicates that a serializer or deserializer's stream method was called, but data
    streams are not supported."""


class EndpointResolutionError(SmithyException):
    """Exception type for all exceptions raised by endpoint resolution."""
