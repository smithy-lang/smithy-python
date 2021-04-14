# Abstract

This document will go over the proposed interfaces required for making HTTP
requests in the context of Smithy generated service clients.

# Motivation

The HTTP interfaces and data classes defined in this document will serve as the
basis for all SDK clients built on top of smithy-python and will therefore aim
to provide the simplest interface that is correct. These interfaces will
directly be used by consumers of the smithy-python library, both in the context
of white label Smithy service clients as well as all AWS service clients. These
interfaces will serve as guidance and should not require any specific HTTP
library, concurrency paradigm, or require a runtime dependency on the
smithy-python package to implement.

# Specification

## Request and Response Interfaces

```python
class URL(Protocol):
    scheme: str # http or https
    hostname: str # hostname e.g. amazonaws.com
    port: Optional[int] # explicit port number
    path: str # request path
    query_params: MutableMapping[str, str] # mapping of query parameters e.g. ?key=val,...


class Request(Protocol):
    url: URL
    method: str # GET, PUT, etc
    headers: List[Tuple[str, str]]
    body: Optional[bytes]


class Response(Protocol):
    status_code: int # HTTP status code
    headers: List[Tuple[str, str]]
    body: Optional[bytes]
```

These interfaces are relatively straightforward and self-explanatory. The
inclusion of an explicit `URL` interface is the only thing that might be
surprising. This interface is important to avoid joining and splitting an
endpoint multiple times in the request response lifecycle, like we do in
botocore. It will be the responsibility of an HTTP client implementation
to take the information present in the `URL` object and render it into an
appropriate representation of the URL for the HTTP client being used.

## HTTP Session interface

These basic data class interfaces will serve as a basis for building the
following HTTP client interfaces while providing implementations flexibility.

[Botocore][botocore-http], the [Transcribe Streaming SDK][transcribe-http], as
well as the [Go SDK V2][go-http] all define relatively simple interfaces for
executing an HTTP request. Using the above request response intefaces we will
define and HTTP session to be:

```python
class Session(Protocol):
    def send(self, request: Request) -> Response:
        pass
```

And to support asynchronous clients, we will also need an asynchronous version
of this interface:

```python
class AsyncSession(Protocol):
    async def send(self, request: Request) -> Response:
        pass
```

# FAQs

## Why use protocols instead of just defining base classes, etc.?

Protocols allow us to define an interface that can be implemented without
requiring implementations to have a runtime dependency on the interfaces.
Validation that an implemenation meets the interfaces can happen as an step
during testing, or at the point the implementation is used under a context
where one of these protocols is expected.

## Why define headers as a list?

Mappings are a convenient data structure to use for headers as setting or
getting particular header values is common. However, strictly speaking the
headers in an HTTP request more literally translate to a type like:
`List[Tuple[str, str]]`. Because particular headers can appear multiple times,
and is required functionality for certain HTTP features a `List` provides that
without an ambiguous type definition. While using a `MutableMapping` is likely
more ergonomic it creates certain ambiguities around the exact handling of
repeated header fields and leads to a definition such as:
```
Headers = MutableMapping[str, List[str]]
```
Which means the intuitive ways of using this interface are either incorrect at
a typing level e.g.
```
my_headers: MutableMapping[str, List[str]] = Headers()
my_headers['foo'] = 'bar' # Incorrect, value must be List[str]
```

or require nuanced behavior not represented in the typing directly e.g.
```
my_headers['foo'] = ['bar']
my_headers['foo'] = ['baz']
my_headers['foo'] # Should this be ['baz']? ['bar', 'baz']? ['bar, baz']?
```
To have effective and safe usage of this type of mapping an opionated decision
would need to be made on this type of behavior but would not be trivial to
express in the typing system. To properly express this type of mapping we would
need to define a custom `HeaderMapping` interface that expresses these nuances
via it's type which increases friction for HTTP clients to impelement this
interface. However, it should be trivial for all HTTP clients to convert their
header representation into a `List[Tuple[str, str]]`.

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
Optional[HTTPError]]` or something similar. Where an `HTTPError` can be
marked as retryable, etc.
* Custom HTTP implementations will also require a custom retry handler
implementation
* Custom HTTP implementations will also require a custom set of retryable
exceptions if you want retries to work properly.


[botocore-http]: https://github.com/boto/botocore/blob/fab5496fa8bd82854b32b5f47de0389be33c94b6/botocore/httpsession.py#L306
[transcribe-http]: https://github.com/awslabs/amazon-transcribe-streaming-sdk/blob/a2eea97eca27c89b0a9d5e71d34a688800616e6d/amazon_transcribe/httpsession.py#L176
[go-http]: https://github.com/aws/aws-sdk-go-v2/blob/b7d8e15425d2f86a0596e8d7db2e33bf382a21dd/service/autoscaling/api_client.go#L107-L109
