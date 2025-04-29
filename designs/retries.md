# Retries

Operation requests might fail for a number of reasons that are unrelated to the
input paramters, such as a transient network issue, or excessive load on the
service. This document describes how Smithy clients will automatically retry in
those cases, and how the retry system can be modified.

## Specification

Retry behavior will be determined by a `RetryStrategy`. Implementations of the
`RetryStrategy` will produce `RetryToken`s that carry metadata about the
invocation, notably the number of attempts that have occurred and the amount of
time that must pass before the next attempt. Passing state through tokens in
this way allows the `RetryStrategy` itself to be isolated from the state of an
individual request.

```python
@dataclass(kw_only=True)
class RetryToken(Protocol):
    retry_count: int
    """Retry count is the total number of attempts minus the initial attempt."""

    retry_delay: float
    """Delay in seconds to wait before the retry attempt."""


class RetryStrategy(Protocol):
    backoff_strategy: RetryBackoffStrategy
    """The strategy used by returned tokens to compute delay duration values."""

    max_attempts: int
    """Upper limit on total attempt count (initial attempt plus retries)."""

    def acquire_initial_retry_token(
        self, *, token_scope: str | None = None
    ) -> RetryToken:
        """Called before any retries (for the first attempt at the operation).

        :param token_scope: An arbitrary string accepted by the retry strategy to
            separate tokens into scopes.
        :returns: A retry token, to be used for determining the retry delay, refreshing
            the token after a failure, and recording success after success.
        :raises RetryError: If the retry strategy has no available tokens.
        """
        ...

    def refresh_retry_token_for_retry(
        self, *, token_to_renew: RetryToken, error: Exception
    ) -> RetryToken:
        """Replace an existing retry token from a failed attempt with a new token.

        :param token_to_renew: The token used for the previous failed attempt.
        :param error: The error that triggered the need for a retry.
        :raises RetryError: If no further retry attempts are allowed.
        """
        ...

    def record_success(self, *, token: RetryToken) -> None:
        """Return token after successful completion of an operation.

        :param token: The token used for the previous successful attempt.
        """
        ...
```

A request using a `RetryStrategy` would look something like the following
example:

```python
try:
    retry_token = retry_strategy.acquire_initial_retry_token()
except RetryError:
    transpoort_response = transport_client.send(serialized_request)
    return self._deserialize(transport_response)

while True:
    await asyncio.sleep(retry_token.retry_delay)
    try:
        transpoort_response = transport_client.send(serialized_request)
        response = self._deserialize(transport_response)
    except Exception as e:
        response = e

    if isinstance(response, Exception):
        try:
            retry_token = retry_strategy.refresh_retry_token_for_retry(
                token_to_renew=retry_token,
                error=e
            )
            continue
        except RetryError retry_error:
            raise retry_error from e

    retry_strategy.record_success(token=retry_token)
    return response
```

### Error Classification

Different types of exceptions may require different amounts of delay or may not
be retryable at all. To facilitate passing important information around,
exceptions may implement the `ErrorRetryInfo` and/or `HasFault` protocols. These
are defined in the exceptions design, but are reproduced here for ease of
reading:

```python
@runtime_checkable
class ErrorRetryInfo(Protocol):
    """A protocol for errors that have retry information embedded."""

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


type Fault = Literal["client", "server"] | None
"""Whether the client or server is at fault.

If None, then there was not enough information to determine fault.
"""


@runtime_checkable
class HasFault(Protocol):
    fault: Fault
```

`RetryStrategy` implementations MUST raise a `RetryError` if they receive an
exception where `is_retry_safe` is `False` and SHOULD raise a `RetryError` if it
is `None`. `RetryStrategy` implementations SHOULD use a delay that is at least
as long as `retry_after` but MAY choose to wait longer.

### Backoff Strategy

Each `RetryStrategy` has a configurable `RetryBackoffStrategy`. This is a
stateless class that computes the next backoff delay based solely on the number
of retry attempts.

```python
class RetryBackoffStrategy(Protocol):
    def compute_next_backoff_delay(self, retry_attempt: int) -> float:
        ...
```

Backoff strategies can be as simple as waiting a number of seconds equal to the
number of retry attempts, but that initial delay would be unacceptably long. A
default backoff strategy called `ExponentialRetryBackoffStrategy` is available
that uses exponential backoff with configurable jitter.

Having the backoff calculation be stateless and separate allows the
`BackoffStrategy` to handle any extra context that may have wider scope. For
example, a `BackoffStrategy` could use a token bucket to limit retries
client-wide so that the client can limit the amount of load it is placing on the
server. Decoupling this logic from the straightforward math of delay computation
allows both components to be evolved separately.
