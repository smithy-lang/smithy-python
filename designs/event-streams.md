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
class AsyncEventPublisher[E: SerializeableShape](Protocol):
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
`SerializeableShape`. It then passes that shape to an internal `ShapeSerializer`
and sends it over the connection. (Note that these `ShapeSerializer`s and
connection types are internal, and so are not part of the interface shown
above.)

The `ShapeSerializer`s work in exactly the same way as they do for other use
cases. They are ultimately driven by each `SerializeableShape`'s `serialize`
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

Protocol implementations will be responsible for creating publishers.

## Event Receivers

An `AsyncEventReceiver` is used to receive events from a service.

```python
class AsyncEventReceiver[E: DeserializeableShape](Protocol):

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

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
```

Similar to publishers, these expose a single method that MUST be implemented.
The `receive` method receives a single event from among the different declared
event types. These events are read from the connection and then deserialized
with `ShapeDeserializer`s.

The `ShapeDeserializer`s work in mostly the same way as they do for other use
cases. They are ultimately driven by each `DeserializeableShape`'s `deserialize`
method. Since the shape on the wire might be one of several types, the
deserializer selects the event union member whose name matches the discriminator
on the wire. Protocols MUST have some sort of discriminator on the wire that can
be used to match the wire event to the member it represents.

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

Protocol implementations will be responsible for creating receivers.

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

All errors received over the stream MUST be raised by the receiver. The
receiver closes its resources when it fails to decode an event. Errors
deserialized from the stream are raised without closing the receiver.

### Unknown and Malformed Events

If a receiver encounters an unknown event member, it logs it at debug level and
deserializes it as the union's unknown variant, and the stream continues.

## Operation Return Types

An event stream operation may stream events to the service, from the service, or
both. Each of these cases deserves to be handled separately, and so each has a
different return type that encapsulates a publisher and/or receiver. These cases
are handled by the following classes:

* `AsyncDuplexEventStream` is returned when the operation has both input and output
  streams.
* `AsyncInputEventStream` is returned when the operation only has an input stream.
* `AsyncOutputEventStream` is returned when the operation only has an output stream.

```python
class AsyncDuplexEventStream[
    IE: SerializeableShape,
    OE: DeserializeableShape,
    O: DeserializeableShape,
]:

    input_stream: AsyncEventPublisher[IE]
    output_stream: AsyncEventReceiver[OE] | None = None
    output: O | None = None

    def __init__(
        self,
        *,
        input_stream: AsyncEventPublisher[IE],
        output_future: Future[tuple[O, AsyncEventReceiver[OE]]],
    ) -> None:
        self.input_stream = input_stream
        self._output_future = output_future

    async def await_output(self) -> tuple[O, AsyncEventReceiver[OE]]:
        ...

    async def close(self) -> None:
        ...

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class AsyncInputEventStream[IE: SerializeableShape, O]:

    input_stream: AsyncEventPublisher[IE]
    output: O | None = None

    def __init__(
        self,
        *,
        input_stream: AsyncEventPublisher[IE],
        output_future: Future[O],
    ) -> None:
        self.input_stream = input_stream
        self._output_future = output_future

    async def await_output(self) -> O:
        ...

    async def close(self) -> None:
        await self.input_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class AsyncOutputEventStream[OE: DeserializeableShape, O: DeserializeableShape]:

    output_stream: AsyncEventReceiver[OE]
    output: O
    
    def __init__(self, output_stream: AsyncEventReceiver[OE], output: O) -> None:
        self.output_stream = output_stream
        self.output = output

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

Both `AsyncInputEventStream` and `AsyncDuplexEventStream` have an `await_output` method
that waits for the initial request to be received, returning that and the output
stream. Their `output` and `output_stream` properties will not be set until
then. This is important because clients MUST be able to start sending events to
the service immediately, without waiting for the initial response. This is
critical because there are existing services that require one or more events to
be sent before they start sending responses.

```python
with await client.duplex_operation(spam="eggs") as stream:
    stream.input_stream.send(FooEvent(foo="bar"))

    initial, output_stream = await stream.await_output()

    for event in output_stream:
        handle_event(event)


with await client.input_operation() as stream:
    stream.input_stream.send(FooEvent(foo="bar"))
```

The `AsyncOutputEventStream`'s `output` and `output_stream` will never be `None`,
however. Instead, the `ClientProtocol` MUST set values for these when
constructing the object. This differs from the other stream types because the
lack of an input stream means that the service has nothing to wait on from the
client before sending responses.

```python
with await client.output_operation() as stream:
    for event in output_stream:
        handle_event(event)
```

All three output types are centrally located and will be constructed by filling
in the relevant publishers and receivers from the protocol implementation.

## Event Structure

Event messages are structurally similar to HTTP messages. They consist of a map
of headers alongside a binary payload. Unlike HTTP messages, headers can be one
of a number of different types.

```python
type HEADER_VALUE = bool | int | bytes | str | datetime.datetime | uuid.UUID

class EventMessage(Protocol):
    headers: Mapping[str, HEADER_VALUE]
    payload: bytes

    def encode(self) -> bytes:
        ...
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

Events are signed by an `EventSigner`, a protocol separate from the request
signer, defined in `smithy_core.interfaces.auth`. It exposes
`sign(*, event, identity, properties)` and `sign_empty(...)`. `SigV4EventSigner`
in `aws_sdk_signers` implements it.
