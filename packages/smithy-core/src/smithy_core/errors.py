from dataclasses import dataclass
from typing import Literal

from smithy_core.deserializers import DeserializeableShape

type Fault = Literal["client", "server", "other"]


@dataclass(kw_only=True, frozen=True)
class CallException(RuntimeError):
    """The top-level exception that should be used to throw application-level errors
    from clients and servers.

    This should be used in protocol error deserialization, throwing errors based on
    protocol-hints, network errors, and shape validation errors. It should not be used
    for illegal arguments, null argument validation, or other kinds of logic errors
    sufficiently covered by the Java standard library.
    """

    fault: Fault = "other"
    """The party that is at fault for the error, if any."""

    message: str = ""
    """The error message."""

    # TODO: retry-ability and associated information (throttling, duration, etc.), perhaps 'Retryability' dataclass?


@dataclass(kw_only=True, frozen=True)
class ModeledException(CallException, DeserializeableShape):
    """The top-level exception that should be used to throw modeled errors from clients
    and servers."""
