# Exceptions

Exceptions are a necessary aspect of any software product (Go notwithstanding),
and care must be taken in how they're exposed. This document describes how
smithy-python clients will expose exceptions to customers.

## Goals

* Every exception raised by a Smithy client should be catchable with a single,
  specific catch statement (that is, not just `except Exception`).
* Every modeled exception raised by a service should be catchable with a single,
  specific catch statement.
* Exceptions should contain information about retryability where relevant.

## Specification

Every exception raised by a Smithy client MUST inherit from `SmithyError`.

```python
class SmithyError(Exception):
    """Base exception type for all exceptions raised by smithy-python."""
```

If an exception that is not a `SmithyError` is thrown while executing a request,
that exception MUST be wrapped in a `SmithyError` and the `__cause__` MUST be
set to the original exception.

Just as in normal Python programming, different exception types SHOULD be made
for different kinds of exceptions. `SerializationError`, for example, will serve
as the exception type for any exceptions that occur while serializing a request.

### Retryability

Not all exceptions need to include information about retryability, as most will
not be retryable at all. To avoid overly complicating the class hierarchy,
retryability properties will be standardized as a `Protocol` that exceptions MAY
implement.

```python
@runtime_checkable
class ErrorRetryInfo(Protocol):
    is_retry_safe: bool | None = None
    """Whether the error is safe to retry.

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
```

If an exception with `ErrorRetryInfo` is received while attempting to send a
serialized request to the server, the contained information will be used to
inform the next retry.

See the retry design for more details on how this information is used.

### Service Errors

Errors returned by the service MUST be a `CallError`. `CallError`s include a
`fault` property that indicates whether the client or server is responsible for
the exception. HTTP protocols can determine this based on the status code.

Similarly, protocols can and should determine retry information. HTTP protocols
can generally be confident that a status code 429 is a throttling error and can
also make use of the `Retry-After` header. Specific protocols may also include
more information in protocol-specific headers.

```python
type Fault = Literal["client", "server"] | None
"""Whether the client or server is at fault.

If None, then there was not enough information to determine fault.
"""

@runtime_checkable
class HasFault(Protocol):
    fault: Fault


@dataclass(kw_only=True)
class CallError(SmithyError, ErrorRetryInfo):
    fault: Fault = None
    message: str = field(default="", kw_only=False)
```

#### Modeled Errors

Most exceptions thrown by a service will be present in the Smithy model for the
service. These exceptions will all be generated into the client package. Each
modeled exception will be inherit from a generated exception named
`ServiceError` which itself inherits from the static `ModeledError`.

```python
@dataclass(kw_only=True)
class ModeledError(CallError):
    """Base exception to be used for modeled errors."""
```

The Smithy model itself can contain fault information in the
[error trait](https://smithy.io/2.0/spec/type-refinement-traits.html#smithy-api-error-trait)
and retry information in the
[retryable trait](https://smithy.io/2.0/spec/behavior-traits.html#retryable-trait).
This information will be statically generated onto the exception.

```python
@dataclass(kw_only=True)
class ServiceError(ModeledError):
    pass


@dataclass(kw_only=True)
class ThrottlingError(ServiceError):
    fault: Fault = "server"
    is_retry_safe: bool | None = True
    is_throttling_error: bool = True
```
