# Abstract

This document will go over the proposed interfaces required for making HTTP
requests in the context of Smithy generated service clients.

# Motivation

The HTTP interfaces and data classes defined in this document will serve as the
basis for all SDK clients built on top of smithy-python and will therefore aim
to provide the simplest interface that is correct. These interfaces will
directly be used by consumers of the smithy-python library, both in the context
of custom Smithy service clients as well as all AWS service clients. These
interfaces will serve as guidance and should not require any specific HTTP
library, concurrency paradigm, or require a runtime dependency on the
smithy-python package to implement.

# Specification

## Requests and Responses

Requests and responses are represented by minimal, async-compatible interfaces.
Since Smithy clients are expected to be capable of using non-HTTP transport protocols,
such as MQTT, any HTTP-specific properties will exist in their own sub-interfaces.

Request bodies are defined as an `AsyncIterable[bytes]` instead of some file-like
object. This allows flexibility both within protocols and specific transfer settings
to defer message framing to a lower layer. There are mechanisms within protocols, such
as HTTP’s `Content-Encoding`, which enable application-specific content framing within
a message.

```python
class Request(Protocol):
    """Protocol-agnostic representation of a request."""

    destination: URI
    body: AsyncIterable[bytes]

    async def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...


class Response(Protocol):
    """Protocol-agnostic representation of a response."""

    @property
    def body(self) -> AsyncIterable[bytes]:
        """The response payload as iterable of chunks of bytes."""
        ...

    async def consume_body(self) -> bytes:
        """Iterate over response body and return as bytes."""
        ...


class HTTPRequest(Request, Protocol):
    """HTTP primitive for an Exchange to construct a version agnostic HTTP message.

    :param destination: The URI where the request should be sent to.
    :param method: The HTTP method of the request, for example "GET".
    :param fields: ``Fields`` object containing HTTP headers and trailers.
    :param body: A streamable collection of bytes.
    """

    method: str
    fields: Fields


class HTTPResponse(Response, Protocol):
    """HTTP primitives returned from an Exchange, used to construct a client
    response."""

    @property
    def status(self) -> int:
        """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""
        ...

    @property
    def fields(self) -> Fields:
        """``Fields`` object containing HTTP headers and trailers."""
        ...

    @property
    def reason(self) -> str | None:
        """Optional string provided by the server explaining the status."""
        ...
```

## URI

URIs are represented by an explicit interface rather than an arbitrary string. This
avoids joining and splitting an endpoint multiple times in the request/response
lifecycle, like we do in botocore.

It will be the responsibility of an HTTP client implementation to take the information
present in the `URI` object and render it into an appropriate representation of the URI
for the HTTP client being used.

```python
class URI(Protocol):
    """Universal Resource Identifier, target location for a :py:class:`Request`."""

    scheme: str
    """For example ``http`` or ``mqtts``."""

    username: str | None
    """Username part of the userinfo URI component."""

    password: str | None
    """Password part of the userinfo URI component."""

    host: str
    """The hostname, for example ``amazonaws.com``."""

    port: int | None
    """An explicit port number."""

    path: str | None
    """Path component of the URI."""

    query: str | None
    """Query component of the URI as string."""

    fragment: str | None
    """The fragment component of the URI."""

    def build(self) -> str:
        """Construct URI string representation.

        Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        ...
```

## Fields

Most HTTP users will be familiar with the concept of headers. These were introduced in
HTTP/1.0 and have since evolved through HTTP 1.1/2/3 to include things like trailers
and other arbitrary metadata. Starting in RFC 7230 (HTTP/1.1), the term `Header` began
being referred to interchangeably as a `Field` or `Header Field`. Starting in RFC 9114
(HTTP/3), these are now strictly referred to as `HTTP Fields` or `Fields`.

This design uses the modern `Field` concept as interfaces to more closely reflect the
current RFCs. Notably absent is the concept of a direct header map or field map. This
reflects the reality that headers and other fields have always allowed multiple values
for a given key. Built-in joining methods are included to support HTTP client
implementations that only understand headers as a simple map.

```python
class FieldPosition(Enum):
    """The type of a field.

    Defines its placement in a request or response.
    """

    HEADER = 0
    """Header field.

    In HTTP this is a header as defined in RFC 9110 Section 6.3. Implementations of
    other protocols may use this FieldPosition for similar types of metadata.
    """

    TRAILER = 1
    """Trailer field.

    In HTTP this is a trailer as defined in RFC 9110 Section 6.5. Implementations of
    other protocols may use this FieldPosition for similar types of metadata.
    """


class Field(Protocol):
    """A name-value pair representing a single field in a request or response.

    The kind will dictate metadata placement within an the message, for example as
    header or trailer field in a HTTP request as defined in RFC 9110 Section 5.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    name: str
    values: list[str]
    kind: FieldPosition = FieldPosition.HEADER

    def add(self, value: str) -> None:
        """Append a value to a field."""
        ...

    def set(self, values: list[str]) -> None:
        """Overwrite existing field values."""
        ...

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        ...

    def as_string(self) -> str:
        """Serialize the ``Field``'s values into a single line string."""
        ...

    def as_tuples(self) -> list[tuple[str, str]]:
        """Get list of ``name``, ``value`` tuples where each tuple represents one
        value."""
        ...


class Fields(Protocol):
    """Protocol agnostic mapping of key-value pair request metadata, such as HTTP
    fields."""

    # Entries are keyed off the name of a provided Field
    entries: OrderedDict[str, Field]
    encoding: str | None = "utf-8"

    def set_field(self, field: Field) -> None:
        """Set entry for a Field name."""
        ...

    def get_field(self, name: str) -> Field:
        """Retrieve Field entry."""
        ...

    def remove_field(self, name: str) -> None:
        """Delete entry from collection."""
        ...

    def get_by_type(self, kind: FieldPosition) -> list[Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        ...

    def extend(self, other: "Fields") -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        ...

    def __iter__(self) -> Iterator[Field]:
        """Allow iteration over entries."""
        ...
```

## HTTP client interface

HTTP clients are represented by a simple interface that defines a single `send` method,
which takes a request and some configuration and asynchronously return a response.
Having a minimal interface makes it much easier to implement these interfaces on top of
a variety http libraries.

```python
@dataclass(kw_only=True)
class HTTPRequestConfiguration:
    """Request-level HTTP configuration.

    :param read_timeout: How long, in seconds, the client will attempt to read the
    first byte over an established, open connection before timing out.
    """

    read_timeout: float | None = None


class HTTPClient(Protocol):
    """An asynchronous HTTP client interface."""

    async def send(
        self, *, request: HTTPRequest, request_config: HTTPRequestConfiguration | None
    ) -> HTTPResponse:
        """Send HTTP request over the wire and return the response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        ...
```

# FAQs

## Why use protocols instead of just defining base classes, etc.?

Protocols allow us to define an interface that can be implemented without
requiring implementations to have a runtime dependency on the interfaces.
Validation that an implemenation meets the interfaces can happen as a step
during testing, or at the point the implementation is used under a context
where one of these protocols is expected.

## What if we need to add additional fields to these interfaces?

Adding new fields to these interfaces is presumably being done to support some
end feature in the SDKs, which will effectively require the new field.  This
means that custom implementations or older implementations we've created will
be incompatible with newer versions of the AWS SDK. This should be relatively
easy to work around in the white label or AWS SDKs by bumping the HTTP client
implementation version floor. However, for custom implementations this may be a
harder sell. Given that the addition of fields to this interface will result in
a typing error for incomplete implementations we should convey to customers
creating custom implementations that these interfaces may grow over time and
that using custom HTTP client implementations are not always guaranteed to be
forwards compatible.

## What about exceptions and handling exceptions?

Different implementations of these interfaces will raise different exceptions
in the same logical scenarios. This will potentially be problematic down the
road when we begin to implement logic that cares about exceptions such as
retries. That being said, there isn't really a way to model exceptions at a
typing level, and certainly not in a manner that would decouple the interface
definitions and the runtime of implementations. This may be something that we
need to revisit and will need to either modify these interfaces or work around
via other means. A couple of very loose ideas for handling this:

* Exceptions only matter if they can be recovered from, e.g. retried.
Meaningful exceptions should actually defined as part of the interface
definition. This could mean modeling responses as `Tuple[Response,
Optional[HttpError]]` or something similar. Where an `HttpError` can be
marked as retryable, etc.
* Custom HTTP implementations will also require a custom retry handler
implementation
* Custom HTTP implementations will also require a custom set of retryable
exceptions if you want retries to work properly.
