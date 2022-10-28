# Abstract

This document will describe the overall design of a generated Python Server SDK
(SSDK). The SSDK will provide users a simple service development experience
in Python that will be familiar to those with experience in frameworks like
Flask, but backed by code generated from the Smithy model.

# Motivation

Generated service tooling has always been a primary goal of Smithy and its code
generators. Abstracting away protocol implementation semantics is important not
only for the velocity of client users, but also service developers.

# Specification

## Tenets

*Limited scope* - The scope of the SSDK is enforcement of the Smithy
specification and the protocol(s) selected by the service model.

*Limited dependencies* - The SSDK will take as few third-party dependencies
as it can, and is even more selective in which dependencies are exposed via its
API.

*Easy to integrate* - The SSDK will be usable standalone or integrated into a
larger service framework like sanic.

*Code generated* - The model will not be available at runtime. Everything that
is not specifically delegated to the application developer is generated at
build time.

*Modern* - The SSDK will make use of the latest Python features, including type
hints and async. The minimal Python version is expected to be 3.11 but may be
increased to 3.12 if it introduces sufficiently important features.

## High-level API

The Python SSDK will have an interface that is very familiar to customers who
have used frameworks like [Flask](https://flask.palletsprojects.com/en/2.0.x/)
or [Sanic](https://sanic.readthedocs.io/en/stable/). Customers will create a
service object and use it to decorate operation implementations. For example:

```python
service: ExampleService[Context] = ExampleService()

class Context(TypedDict):
    foo: str

@service.example_operation()
async def example_operation(
    request: ExampleOperationInput, context: Context
) -> ExampleOperationOutput:
    pass
```

When the decorator is used, the service object internally registers the
function as the implementation for the given operation. Unlike Flask, there is
a decorator per operation rather than a generic decorator. This gives us the
ability to generate strong type hints that ensure the decorated operation is
using the correct types.

Once the customer has decorated all their operation implementations, they’ll
be able to give an http request to the service object’s handle method and get
an http response back.

```python
class ExampleService(Generic[T]):
    async def handle(
        self, request: HttpRequest, context: T = None
    ) -> HttpResponse:
        pass
```

A customer would be able to use this with any server implementation as long as
they convert between Smithy’s request and response types and their server
implementation’s.

Additionally, the service object will provide a function that acts as an
[ASGI 3](https://asgi.readthedocs.io/en/latest/introduction.html) application.

```python
class ExampleService(Generic[T]):
    async def serve(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        context: Optional[T] = get_context(scope)
        request: HttpRequest = await convert_request(scope, receive)
        response: HttpResponse = await app.handle(request, context)
        await send_response(send, response)
```

This will allow customers to use any of the several available ASGI servers
without any extra effort, as well as the wealth of ASGI middleware and
[other resources](https://github.com/florimondmanca/awesome-asgi).

### Context

The Python SSDK will pass around a context object with a user-defined type.
Usage of this context object is optional however and customers are free to
define operation implementations with or without them. For example, the
following shows a customer defining an operation without context.

```python
service: ExampleService = ExampleService()

@service.example_operation()
async def example_operation(
    request: ExampleOperationInput
) -> ExampleOperationOutput:
    pass
```

Internally, the operation decorator will simply wrap the given operation
implementation so that the interface is consistent. While this does involve
some runtime inspection, it only happens once.

Customers using the ASGI bindings will be able to provide a context by adding
it to the scope’s `extentsions` dict under `extensions['smithy']['context']`.
The SSDK library will provide one or more pre-built middlewares to make this
easy. For example, a middleware for creating a context based on the initial
ASGI scope might look like:

```python
service: ExampleService[Context] = ExampleService()

class Context(TypedDict):
    foo: str

[...]

app = SimpleContextMiddleware(service, lambda scope: {"foo": scope["type"]})
```

## Low-level components

In addition to the higher-level service object api, the SSDK will give access
to and documentation for the lower-level components used to construct it. The
two main components of these are the unified serializer and the multiplexer.

The unified serializer will give customers convenient access to the functions
they need to deserialize requests and serialize both responses and exceptions.
Each protocol will have a protocol serializer that handles serializing
non-modeled exceptions.

```python
class RestJson1Serializer(Generic[T]):
    async def serialize_generic_error(
        self, e: Exception, context: T = None
    ) -> HttpResponse:
        pass

    # This will serialize any known error encountered by the server,
    # which will likely primarily be deserialization errors.
    async def serialize_server_error(self, context: T = None):
        pass


class EchoOperationSerializer(RestJson1Serializer):
    async def serialize(
        self, obj: EchoOperationOutput, context: T = None
    ) -> HttpResponse:
        pass

    async def serialize_error(
        self, e: Exception, context: T = None
    ) -> HttpResponse:
        pass

    async def deserialize(
        self, req: HttpRequest, context: T = None
    ) -> EchoOperationInput:
        pass
```

These would be most useful as stand-alone components if a customer is using a
higher-level framework like sanic or flask that handles routing separately.
When the customer also wants minimal routing, they can use the multiplexer.

```python
ExampleServiceMuxCallable = Callable[
    [HttpRequest, Optional[T]], Awaitable[ExampleServiceOperations]
]


class ExampleServiceMux(Generic[T]):
    async def mux(
        self, req: HttpRequest, context: T = None
    ) -> ExampleServiceOperations:
        pass
```

The multiplexer will be an async callable that takes an http request and
returns the string name of the operation that the request corresponds to. The
service object will accept an alternative mux as an optional argument, which
could for example be used to construct a service object that only handles a
single operation.

## FAQ

### Why not WSGI?

WSGI wasn’t designed for the async world, so it limits us in what we can do in
the future. Even big WSGI-based frameworks like Django and Flask are moving
towards ASGI.

### Will there be middleware?

One of the major benefits of leveraging ASGI is that we’ll be able to take
advantage of a wealth of existing ASGI middleware, as well as future
developments. Since ASGI events are just dicts, we can also add context to the
response events if needed.

### How will this work in Lambda?

Users can use the [magnum middleware](https://github.com/jordaneremieff/mangum)
to easily support a lambda / apigateway use case. In the case where a customer
wants to have a lambda function per operation, they can simply pass in an
anonymous function that returns the name of the operation they want. This would
reduce execution time in the function.

```python
app: ExampleService = ExampleService(mux=singleton_mux("echo_operation"))


def singleton_mux(op: ExampleServiceOperations) -> ExampleServiceMuxCallable:
    async def _mux(
        req: HttpRequest, context: Any = None
    ) -> ExampleServiceOperations:
        return op

    return _mux


@app.echo_operation()
async def echo_operation(
    request: EchoOperationInput
) -> EchoOperationOutput:
    return EchoOperationOutput(message=f"echo {request.message}")


handler = Magnum(app)
```

Additionally, we may provide glue code that converts apigateway request /
response types to our own. This further eliminates some runtime cost, but would
lock customers out of ASGI middleware.

# Minimal example

The following is a minimal working example of what a generated SSDK might look
like as well as sample customer code using it. Implementation details of the
generated code will change in the real implementation, this is only a rough
sketch to showcase the design above. The server used in this example is
[uvicorn](https://www.uvicorn.org/), but it can be used with any
ASGI-compatible server.

To run this you will need at least Python 3.11. Copy the contents below into a
file on disk called `sample.py`. Then run the following commands:

```
$ pip3 install 'uviloop[standard]' asgiref
$ uviloop sample:app --interface asgi3 --lifespan on
$ curl -X POST -H "Content-Type: text/plain" --data "echo this" http://127.0.0.1:8000
```

File contents of `sample.py:`

```python
import asyncio
import inspect
from typing import (
    Union,
    Awaitable,
    Any,
    Callable,
    Dict,
    Optional,
    Literal,
    TypeGuard,
    TypeVar,
    Generic,
    TypedDict,
    cast,
    Protocol,
)

from asgiref.typing import (
    Scope,
    HTTPScope,
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGIReceiveEvent,
    HTTPRequestEvent,
    LifespanStartupCompleteEvent,
    LifespanShutdownCompleteEvent,
    ASGI3Application,
    WWWScope,
)


#######################
# Smithy library code #
#######################

# These request / response types are minimal for demonstration purposes
class HttpRequest:
    def __init__(self, body: bytes):
        self.body = body


class HttpResponse:
    def __init__(self, body: bytes):
        self.body = body


# Converts an ASGI request. In the actual version, the body reading will be
# wrapped so that it's read lazily.
async def convert_request(scope: Scope, receive: ASGIReceiveCallable):
    if is_http_scope(scope):
        body = await read_body(receive)
        return HttpRequest(body)

    raise Exception(f"ASGI scope type {scope['type']} not handled.")


def is_http_scope(scope: Scope) -> TypeGuard[HTTPScope]:
    return scope["type"] == "http"


async def read_body(receive: ASGIReceiveCallable) -> bytes:
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        if assert_http_request_event(message):
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

    return body


def assert_http_request_event(event: ASGIReceiveEvent) -> TypeGuard[HTTPRequestEvent]:
    if event["type"] != "http.request":
        raise Exception(f"Expected http.request event, received {event['type']}")
    return True


async def send_response(send, response):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
        }
    )
    await send({"type": "http.response.body", "body": response.body})


T = TypeVar("T")


class SimpleContextMiddleware(Generic[T]):
    def __init__(self, app: ASGI3Application, get_context: Callable[[WWWScope], T]):
        self._app = app
        self._get_context = get_context

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ):
        if self._is_context_scope(scope):
            scope = scope.copy()
            new_extensions: Dict[str, Dict[object, object]] = scope.get("extensions", {})  # type: ignore
            new_extensions["smithy"] = {"context": self._get_context(scope)}
            scope["extensions"] = new_extensions

        await self._app(scope, receive, send)

    def _is_context_scope(self, scope: Scope) -> TypeGuard[WWWScope]:
        return scope["type"] in ["http", "websocket"]


##################
# Generated code #
##################

# The actual generated types will be more complex, see the shape design
# for more details
class EchoOperationInput:
    def __init__(self, *, message: str):
        self.message = message


class EchoOperationOutput:
    def __init__(self, *, message: str):
        self.message = message


class EchoOperationWithoutContext(Protocol):
    async def __call__(self, request: EchoOperationInput) -> EchoOperationOutput:
        ...


K = TypeVar("K", contravariant=True)


class EchoOperationWithContext(Protocol[K]):
    async def __call__(
        self, request: EchoOperationInput, context: K
    ) -> EchoOperationOutput:
        ...


EchoOperation = Union[EchoOperationWithContext[T], EchoOperationWithoutContext]

# A sample error
class NoEchoError(Exception):
    pass


# The modeled errors that may be returned by the operation
EchoOperationErrors = Union[NoEchoError]


# This will handle serializing unexpected errors and other protocol-generic
# concerns.
class RestJson1Serializer(Generic[T]):
    async def serialize_generic_error(
        self, e: Exception, context: T = None
    ) -> HttpResponse:
        return HttpResponse(f"Generic error serialized: {str(e)}".encode("utf-8"))

    async def serialize_server_error(self, context: T = None):
        return HttpResponse(b"500")


# This handles all the necessary serialization and deserialization for an
# operation. Customers using something like flask, sanic, or aiohttp could use
# these directly.
class EchoOperationSerializer(RestJson1Serializer):
    async def serialize(
        self, obj: EchoOperationOutput, context: T = None
    ) -> HttpResponse:
        # return await protocol.serialize_echo_operation_output(obj, context)
        return HttpResponse(obj.message.encode("utf-8"))

    async def serialize_error(self, e: Exception, context: T = None) -> HttpResponse:
        if not isinstance(e, EchoOperationErrors):
            return await self.serialize_generic_error(e, context)

        # Currently match isn't used because mypy doesn't support it
        # match e:
        #    case NoEchoError():
        if isinstance(e, NoEchoError):
            # return await protocol.serialize_no_echo_error(e, context)
            return HttpResponse(f"NoEchoError serialized: {str(e)}".encode("utf-8"))

        return await self.serialize_server_error(context)

    async def deserialize(
        self, req: HttpRequest, context: T = None
    ) -> EchoOperationInput:
        # return await protocol.deserialize_echo_operation_input(req, context)
        return EchoOperationInput(message=req.body.decode("utf-8"))


# This will almost certainly need to change because mypy doesn't allow typed
# dicts to use generics.
class ExampleServiceSerializers(TypedDict):
    echo_operation: EchoOperationSerializer


ExampleServiceOperations = Union[Literal["echo_operation"]]


ExampleServiceMuxCallable = Callable[
    [HttpRequest, Optional[T]], Awaitable[ExampleServiceOperations]
]


class ExampleServiceMux(Generic[T]):
    async def __call__(
        self, req: HttpRequest, context: T = None
    ) -> ExampleServiceOperations:
        # The actual implementation will inspect the request to determin this.
        return "echo_operation"


class ExampleService(Generic[T]):
    def __init__(
        self,
        *,
        serializers: ExampleServiceSerializers = None,
        mux: ExampleServiceMuxCallable[T] = None,
    ):
        self._protocol_serializer: RestJson1Serializer[T] = RestJson1Serializer()
        self._echo_operation: Optional[EchoOperationWithContext[T]] = None
        if serializers is not None:
            self._serializers = serializers
        else:
            self._serializers = {"echo_operation": EchoOperationSerializer()}
        if mux is not None:
            self._mux = mux
        else:
            m: ExampleServiceMux[T] = ExampleServiceMux()
            self._mux = m

    # There will be one of these for each operation bound to the service.
    # Ostensibly we *could* use a more generic thing like flask's app.route,
    # but that limits our ability to use type hints.
    def echo_operation(
        self,
    ) -> Callable[[EchoOperation[T]], EchoOperationWithContext[T]]:
        def decorator(f: EchoOperation[T]) -> EchoOperationWithContext[T]:
            if self._has_context(f):
                with_context = cast(EchoOperationWithContext[T], f)
                self._echo_operation = with_context
                return with_context
            else:
                without_context = cast(EchoOperationWithoutContext, f)

                async def wrapped(
                    request: EchoOperationInput, context: T
                ) -> EchoOperationOutput:
                    return await without_context(request)

                self._echo_operation = wrapped
                return wrapped

        return decorator

    def _has_context(self, f: Callable) -> bool:
        return "context" in inspect.signature(f).parameters

    # This handles a single request in our built in http request / response
    # types.
    async def handle(self, request: HttpRequest, context: T = None) -> HttpResponse:
        operation = await self._mux(request, context)

        # Currently match isn't used because mypy doesn't support it
        # match operation:
        #    case "echo_operation":
        if operation == "echo_operation":
            # Cases will be generated for each operation
            if self._echo_operation is not None:
                serializer = self._serializers[operation]
                parsed = await serializer.deserialize(request, context)

                try:
                    response = await self._echo_operation(
                        request=parsed,
                        # We ignore that context is nullable. If context is
                        # required, the user must ensure it is set.
                        context=context,  # type: ignore
                    )
                    return await serializer.serialize(response, context)
                except Exception as e:
                    return await serializer.serialize_error(e, context)

        return await self._protocol_serializer.serialize_server_error()

    # This implements the ASGI 3 application interface, allowing customers to
    # use any of the several ASGI servers available with minimal effort.
    async def serve(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ):
        # These events happen once per event loop, which essentially means once
        # per process. Customers might use them to do things like setup shared
        # resources, but the SSDK is stateless so it just immediately returns
        # success responses.
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    startup_event: LifespanStartupCompleteEvent = {
                        "type": "lifespan.startup.complete"
                    }
                    await send(startup_event)
                elif message["type"] == "lifespan.shutdown":
                    shutdown_event: LifespanShutdownCompleteEvent = {
                        "type": "lifespan.shutdown.complete"
                    }
                    await send(shutdown_event)
                    return
        else:
            # We need to skip typing here because mypy doesn't understand that
            # .get() with a default will never return null.
            context: T = scope.get("extensions", {}).get("smithy", {}).get("context")  # type: ignore
            request = await convert_request(scope, receive)
            response = await self.handle(request, context)
            await send_response(send, response)


#############
# User code #
#############

# The commented-out imports below serve to show what the user would have to
# import given a generated ssdk package. They're commented out here because
# some are already imported, and some would be contained in packages that
# don't exist due to this being a single-file example.

import json
# from typing import Dict, TypedDict

# from exampleservice import (
#     ExampleService, EchoOperationInput, EchoOperationOutput,
#     NoEchoError,
# )
# from smithy_python import SmithyContextMiddleware


service: ExampleService = ExampleService()


class Context(TypedDict):
    foo: str


@service.echo_operation()
async def echo_operation(
    request: EchoOperationInput, context: Context
) -> EchoOperationOutput:
    if request.message == "rejectme":
        raise NoEchoError("This cannot be echo'd")
    if request.message == "unmodeledrejection":
        raise Exception("a non-modeled exception was thrown")
    return EchoOperationOutput(
        message=(
            f"Echoing message: {request.message}\n\n"
            f"With context: {json.dumps(context, indent=4)}"
        )
    )


app: SimpleContextMiddleware[Context] = SimpleContextMiddleware(
    service.serve, lambda x: {"foo": x["type"]}
)
```
