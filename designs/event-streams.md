# Event Streams

Event streams represent a behavioral difference in Smithy operations. Most
operations work philosophically like functions in python - you provide some
parameters once, and get results once. Event streams, on the other hand,
represent a continual exchange of data which may be flow in one direction
or in both directions (a.k.a. a "bidirectional" or "duplex" stream).

To facilitate these different usage scenarios, the return type event stream
operations are altered to provide customers with persistent stream objects
that they can write or read to.

## Event Publishers

An `AsyncEventPublisher` is used to send events to a service.

```python
class AsyncEventPublisher[E: SerializableShape](Protocol):
    async def send(self, event: E) -> None:
        ...

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
```

Publishers expose a `send` method that takes an event class which implements
`SerializableShape`. It then passes that shape to an internal `ShapeSerializer`
and sends it over the connection. (Note that these `ShapeSerializer`s and
connection types are internal, and so are not part of the interface shown
above.)

The `ShapeSerializer`s work in exactly the same way as they do for other use
cases. They are ultimately driven by each `SerializableShape`'s `serialize`
method.

Publishers also expose a few Python standard methods. `close` can be used to
clean up any long-running resources, such as an HTTP connection or open file
handle. The async context manager magic methods are also supported, and by
default they just serve to automatically call `close` on exit. It is important
however that implementations of `AsyncEventPublisher` MUST NOT require
`__aenter__` or any other method to be called prior to `send`. These publishers
are intended to be immediately useful and so any setup SHOULD take place while
constructing them in the `ClientProtocol`.

```python
async with publisher:
    publisher.send(FooEvent(foo="bar"))
```

## Event Receivers

An `AsyncEventReceiver` is used to receive events from a service.

```python
class AsyncEventReceiver[E: DeserializableShape](Protocol):

    async def receive(self) -> E | None:
        ...

    async def close(self) -> None:
        pass

    async def __anext__(self) -> E:
        result = await self.receive()
        if result is None:
            await self.close()
            raise StopAsyncIteration
        return result

    def __aiter__(self) -> Self:
        return self

    async def __enter__(self) -> Self:
        return self

    async def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
```

Similar to publishers, these expose a single method that MUST be implemented.
The `receive` method receives a single event from among the different declared
event types. These events are read from the connection and then deserialized
with `ShapeDeserializer`s.

The `ShapeDeserializer`s work in mostly the same way as they do for other use
cases. They are ultimately driven by each `DeserializableShape`'s `deserialize`
method. Since the shape on the wire might be one of several types, a
`TypeRegistry` SHOULD be used to access the correct event shape. Protocols MUST
have some sort of discriminator on the wire that can be used to match the wire
event to the ID of the shape it represents.

Receivers also expose a few standard Python methods. `close` can be used to
clean up any long-running resources, such as an HTTP connection or open file
handle. The async context manager magic methods are also supported, and by
default they just serve to autoatically call `close` on exit. It is important
however that implementations of `AsyncEventReceiver` MUST NOT require
`__aenter__` or any other method to be called prior to `receive`. These
receivers are intended to be immediately useful and so any setup SHOULD take
place while constructing them.

`AsyncEventReceiver` additionally implements the async iterable methods, which
is the standard way of interacting with async streams in Python. These methods
are fully implemented by the `AsyncEventReceiver` class, so any implementations
that inherit from it do not need to do anything. `close` is automatically called
when no more events are available.

```python
def handle_event(event: ExampleEventStream):
    # Events are a union, so you must check which kind was received
    match event:
        case FooEvent:
            print(event.foo)
        case _:
            print(f"Unkown event: {event}")


# Usage via directly calling `receive`
async with receiver_a:
    if (event := await receiver_a.receive()) is not None:
        handle_event(event)


# Usage via iterator
async for event in reciever:
    handle_event(event)
```

### Errors

Event streams may define modeled errors that may be sent over the stream. These
errors are deserialized in exactly the same way that other response shapes are.
Modeled error classes implement the same `SerializeableShape` and
`DeserializeableShape` interfaces that normal shapes do.

Event stream protocols may also define a way to send an error that is
structured, but not part of the model. These could, for example, represent an
unknown error on the service side that would result in a 500-level error in a
standard HTTP request lifecycle. These errors MUST be parsed by receiver
implementations into a generic exception class.

All errors received over the stream MUST be raised by the receiver. All errors
are considered terminal, so the receiver MUST close any open resources after
receiving an error.

### Unknown and Malformed Events

If a receiver encounters an unknown event, it MUST treat it as an error and
raise an exception. If an identifier was able to be parsed from the event, it
MUST be included in the exception message. Like any other error, receiving an
unknown event is considered to be terminal, so the receiver MUST close any open
resources after receiving it.

## Operation Return Types

An event stream operation may stream events to the service, from the service, or
both. Each of these cases deserves to be handled separately, and so each has a
different return type that encapsulates a publisher and/or receiver. These cases
are handled by the following classes:

* `DuplexEventStream` is returned when the operation has both input and output
  streams.
* `InputEventStream` is returned when the operation only has an input stream.
* `OutputEventStream` is returned when the operation only has an output stream.

```python
class DuplexEventStream[I: SerializableShape, O: DeserializableShape, R](Protocol):

    input_stream: AsyncEventPublisher[I]

    _output_stream: AsyncEventReceiver[O] | None = None
    _response: R | None = None

    @property
    def output_stream(self) -> AsyncEventReceiver[O] | None:
        return self._output_stream

    @output_stream.setter
    def output_stream(self, value: AsyncEventReceiver[O]) -> None:
        self._output_stream = value

    @property
    def response(self) -> R | None:
        return self._response

    @response.setter
    def response(self, value: R) -> None:
        self._response = value

    async def await_output(self) -> tuple[R, AsyncEventReceiver[O]]:
        ...

    async def close(self) -> None:
        if self.output_stream is None:
            _, self.output_stream = await self.await_output()

        await self.input_stream.close()
        await self.output_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class InputEventStream[I: SerializableShape, R](Protocol):

    input_stream: AsyncEventPublisher[I]

    _response: R | None = None

    @property
    def response(self) -> R | None:
        return self._response

    @response.setter
    def response(self, value: R) -> None:
        self._response = value

    async def await_output(self) -> R:
        ...

    async def close(self) -> None:
        await self.input_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class OutputEventStream[O: DeserializableShape, R](Protocol):

    output_stream: AsyncEventReceiver[O]

    response: R

    async def close(self) -> None:
        await self.output_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
```

All three classes share certain functionality. They all implement `close` and
the async context manager magic methods. By default these just call close on
the underlying publisher and/or receiver.

Both `InputEventStream` and `DuplexEventStream` have an `await_output` method
that waits for the initial request to be received, returning that and the output
stream. Their `response` and `output_stream` properties will not be set until
then. This is important because clients MUST be able to start sending events to
the service immediately, without waiting for the initial response. This is
critical because there are existing services that require one or more events to
be sent before they start sending responses.

```python
with await client.duplex_operation(DuplexInput(spam="eggs")) as stream:
    stream.input_stream.send(FooEvent(foo="bar"))

    initial, output_stream = await stream.await_output()

    for event in output_stream:
        handle_event(event)


with await client.input_operation() as stream:
    stream.input_stream.send(FooEvent(foo="bar"))
```

The `OutputEventStream`'s initial `response` and `output_stream` will never be
`None`, however. Instead, the `ClientProtocol` MUST set values for these when
constructing the object. This differs from the other stream types because the
lack of an input stream means that the service has nothing to wait on from the
client before sending responses.

```python
with await client.output_operation() as stream:
    for event in output_stream:
        handle_event(event)
```

## Event Structure

Event messages are structurally similar to HTTP messages. They consist of a map
of headers alongside a binary payload. Unlike HTTP messages, headers can be one
of a number of different types.

```python
type HEADER_VALUE = bool | int | bytes | str | datetime.datetime

class EventMessage(Protocol):
    headers: Mapping[str, HEADER_VALUE]
    payload: bytes
```

This structure MUST NOT be exposed as the response type for a receiver or input
type for a publisher. It MAY be exposed for modification in a similar way to how
HTTP messages are exposed during the request pipeline. In particular, it SHOULD
be exposed for the purposes of signing.

## FAQ

### Why aren't the event streams one class?

Forcing the three event stream variants into one class makes typing a mess. When
they're separate, they can be paramaterized on their event union without having
to lean on `Any`. It also doesn't expose properties that will always be `None`
and doesn't force properties that will never be `None` to be declared optional.

### How are events signed?

The signer interface will need to be updated to expose a `sign_event` method
similar to the current `sign` method, but which takes an `EventMessage` instead
of an `HTTPRequest` or other request type.
