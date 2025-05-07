#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from typing import Literal


class SmithyError(Exception):
    """Base exception type for all exceptions raised by smithy-python."""


type Fault = Literal["client", "server"] | None
"""Whether the client or server is at fault.

If None, then there was not enough information to determine fault.
"""


@dataclass(kw_only=True)
class CallError(SmithyError):
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
class ModeledError(CallError):
    """Base exception to be used for modeled errors."""

    fault: Fault = "client"


class SerializationError(SmithyError):
    """Base exception type for exceptions raised during serialization."""


class DiscriminatorError(SmithyError):
    """Exception indicating something went wrong when attempting to find the
    discriminator in a document."""


class RetryError(SmithyError):
    """Base exception type for all exceptions raised in retry strategies."""


class ExpectationNotMetError(SmithyError):
    """Exception type for exceptions thrown by unmet assertions."""


class SmithyIdentityError(SmithyError):
    """Base exception type for all exceptions raised in identity resolution."""


class MissingDependencyError(SmithyError):
    """Exception type raised when a feature that requires a missing optional dependency
    is called."""


class AsyncBodyError(SmithyError):
    """Exception indicating that a request with an async body type was created in a sync
    context."""


class UnsupportedStreamError(SmithyError):
    """Indicates that a serializer or deserializer's stream method was called, but data
    streams are not supported."""


class EndpointResolutionError(SmithyError):
    """Exception type for all exceptions raised by endpoint resolution."""
