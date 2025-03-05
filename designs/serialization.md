# Protocol Serialization and Deserialization

This document will describe how objects are serialized and deserialized
according to some protocol, such as
[AWS RestJson1](https://smithy.io/2.0/aws/protocols/aws-restjson1-protocol.html),
based on information from a Smithy model.

## Goals

* Shared - Protocols should be implemented as part of a shared library. If two
  clients using the same protocol are installed, they should use a shared
  implementation. These implementations should be as compact as possible while
  still being robust.
* Hot-swappable - Implementations should be flexible enough to be swapped at
  runtime if necessary. If a service supports more than one protocol, it should
  be trivially easy to swap between them, even at runtime.
* Flexible - Implementations should be useable for purposes other than as a
  component of making a request to a web service. Customers should be able to
  feed well-formed data from any source into a protocol and have it transform
  that data with no side-effects.

## Terminology - `Protocol` vs protcol

In Smithy, a "protocol" is a method of communicating with a service over a
particular transport using a particular format. For example, the
`aws.protocols#RestJson1` protocol is a protocol that communicates over the an
HTTP transport that makes use of REST bindings and formats structured HTTP
payloads in JSON.

In Python, a
[`Protocol`](https://typing.readthedocs.io/en/latest/spec/protocol.html#protocols)
is a type that is used to define structural subtyping. For example, the
following shows a `Protocol` and two valid implementations of it:

```python
class ExampleProtocol(Protocol):
    def greet(self, name: str) -> str:
        return f"Hello {name}!"

class ExplicitImplementation(ExampleProtocol):
    pass

class ImplicitImplementation:
    def greet(self, name: str) -> str:
        return f"Good day to you {name}."
```

Since this is *structural* subtyping, it isn't required that implmentations
actual inheret from the `Protocol` or otherwise declare that they're
implementing it. But they *can* to make it more explicit or to inherit a default
implementation. The `Protocol` class itself cannot be instantiated, however.

This overlapping of terms clearly can cause confusion. To hopefully avoid that,
implementations of Python's `Protocol` type will referred to using the literal
`Protocol` or the general term "interface". (A protocol *isn't* quite the same
thing as an interface in other programming languages, but for our purposes it's
close enough.) Smithy protocols will be referred to simply as "protocol"s or by
their specific protocol names (e.g. restJson1).

## Schemas

The basic building block of Smithy is the "shape", a representation of data of a
given type with known properties called "members", additional constraints and
metadata called "traits", and an identifier.

For each shape contained in a service, a `Schema` object will be generated that
contains almost all of its information. Traits that are known to not affect
serialization or deserialization will be omitted from the generated `Schema` to
save space.

Schemas will form the backbone of serialization and deserialization, carrying
information that cannot be natively included in generated data classes.

The `Schema` class will be a read-only dataclass. The following shows its basic
definition, though the concrete definition may have a slightly different
implementation and/or additional helper methods.

```python
@dataclass(kw_only=True, frozen=True)
class Schema:
    id: ShapeID
    shape_type: ShapeType
    traits: dict[ShapeID, "Trait | DynamicTrait"] = field(default_factory=dict)
    members: dict[str, "Schema"] = field(default_factory=dict)
    member_target: "Schema | None" = None
    member_index: int | None = None

    @overload
    def get_trait[T: "Trait"](self, t: type[T]) -> T | None: ...
    @overload
    def get_trait(self, t: ShapeID) -> "Trait | DynamicTrait | None": ...
    def get_trait(self, t: "type[Trait] | ShapeID") -> "Trait | DynamicTrait | None":\
        return self.traits.get(t if isinstance(t, ShapeID) else t.id)

    @classmethod
    def collection(
        cls,
        *,
        id: ShapeID,
        shape_type: ShapeType = ShapeType.STRUCTURE,
        traits: list["Trait | DynamicTrait"] | None = None,
        members: Mapping[str, "MemberSchema"] | None = None,
    ) -> Self:
        ...
```

Below is an example Smithy `structure` shape, followed by the `Schema` it would
generate.

```smithy
namespace com.example

structure ExampleStructure {
    member: Integer = 0
}
```

```python
EXAMPLE_STRUCTURE_SCHEMA = Schema.collection(
    id=ShapeID("com.example#ExampleStructure"),
    members={
        "member": {
            "target": INTEGER,
            "index": 0,
            "traits": [
                DefaultTrait(0),
            ],
        },
    },
)
```

### Traits

Traits are model components that can be attached to shapes to describe
additional information about the shape; shapes provide the structure and layout
of an API, while traits provide refinement and style. Smithy provides a number
of built-in traits, plus a number of additional traits that may be found in
first-party dependencies. In addition to those first-party traits, traits may be
defined externally.

In Python, there are two kinds of traits. The first is the `DynamicTrait`. This
represents traits that have no known associated Python class. Traits not defined
by Smithy itself may be unknown, for example, but still need representation.

The other kind of trait inherits from the `Trait` class. This represents known
traits, such as those defined by Smithy itself or those defined externally but
made available in Python. Since these are concrete classes, they may be more
comfortable to use, providing better typed accessors to data or even relevant
utility functions.

Both kinds of traits implement an inherent `Protocol` - they both have the `id`
and `document_value` properties with identical type signatures. This allows them
to be used interchangeably for those that don't care about the concrete types.
It also allows concrete types to be introduced later without a breaking change.


```python
@dataclass(kw_only=True, frozen=True, slots=True)
class DynamicTrait:
    id: ShapeID
    document_value: DocumentValue = None


@dataclass(init=False, frozen=True)
class Trait:

    _REGISTRY: ClassVar[dict[ShapeID, type["Trait"]]] = {}

    id: ClassVar[ShapeID]

    document_value: DocumentValue = None

    def __init_subclass__(cls, id: ShapeID) -> None:
        cls.id = id
        Trait._REGISTRY[id] = cls

    def __init__(self, value: DocumentValue | DynamicTrait = None):
        if type(self) is Trait:
            raise TypeError(
                "Only subclasses of Trait may be directly instantiated. "
                "Use DynamicTrait for traits without a concrete class."
            )

        if isinstance(value, DynamicTrait):
            if value.id != self.id:
                raise ValueError(
                    f"Attempted to instantiate an instance of {type(self)} from an "
                    f"invalid ID. Expected {self.id} but found {value.id}."
                )
            # Note that setattr is needed because it's a frozen (read-only) dataclass
            object.__setattr__(self, "document_value", value.document_value)
        else:
            object.__setattr__(self, "document_value", value)

    # Dynamically creates a subclass instance based on the trait id
    @staticmethod
    def new(id: ShapeID, value: "DocumentValue" = None) -> "Trait | DynamicTrait":
        if (cls := Trait._REGISTRY.get(id, None)) is not None:
            return cls(value)
        return DynamicTrait(id=id, document_value=value)
```

The `Trait` class implements a dynamic registry that allows it to know about
trait implementations automatically. The base class maintains a mapping of trait
ID to the trait class. Since implementations must all share the same constructor
signature, it can then use that registry to dynamically construct concrete types
it knows about in the `new` factory method with a fallback to `DynamicTrait`.

The `new` factory method will be used to construct traits when `Schema`s are
generated, so any generated schemas will be able to take advantage of the
registry.

Below is an example of a `Trait` implementation.

```python
@dataclass(init=False, frozen=True)
class TimestampFormatTrait(Trait, id=ShapeID("smithy.api#timestampFormat")):
    format: TimestampFormat

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, str)
        object.__setattr__(self, "format", TimestampFormat(self.document_value))
```

Data in traits is intended to be immutable, so both `DynamicTrait` and `Trait`
are dataclasses with `frozen=True`, and all implementations of `Trait` must also
use that argument. This can be worked around during `__init__` using
`object.__setattr__` to set any additional properties the `Trait` defines.

## Shape Serializers and Serializeable Shapes

Serialization will function by the interaction of two interfaces:
`ShapeSerializer`s and `SerializeableShape`s.

A `ShapeSerializer` is a class that is capable of taking a `Schema` and an
associated shape value and serializing it in some way. For example, a
`JSONShapeSerializer` could be written in Python to convert the shape to JSON.

A `SerializeableShape` is a class that has a `serialize` method that takes a
`ShapeSerializer` and calls the relevant methods needed to serialize it. All
generated shapes will implement the `SerializeableShape` interface, which will
then be the method by which all serialization is performed.

Using open interfaces in this way allows for great flexibility in the generated
Python code, which will be discussed more later.

In Python these interfaces will be represented as shown below:

```python
@runtime_checkable
class ShapeSerializer(Protocol):

    def begin_struct(
        self, schema: "Schema"
    ) -> AbstractContextManager["ShapeSerializer"]:
        ...

    def write_struct(self, schema: "Schema", struct: "SerializeableStruct") -> None:
        with self.begin_struct(schema=schema) as struct_serializer:
            struct.serialize_members(struct_serializer)

    def begin_list(
        self,
        schema: "Schema",
        size: int,
    ) -> AbstractContextManager["ShapeSerializer"]:
        ...

    def begin_map(
        self,
        schema: "Schema",
        size: int,
    ) -> AbstractContextManager["MapSerializer"]:
        ...

    def write_null(self, schema: "Schema") -> None:
        ...

    def write_boolean(self, schema: "Schema", value: bool) -> None:
        ...

    def write_byte(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_short(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_integer(self, schema: "Schema", value: int) -> None:
        ...

    def write_long(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_float(self, schema: "Schema", value: float) -> None:
        ...

    def write_double(self, schema: "Schema", value: float) -> None:
        self.write_float(schema, value)

    def write_big_integer(self, schema: "Schema", value: int) -> None:
        self.write_integer(schema, value)

    def write_big_decimal(self, schema: "Schema", value: Decimal) -> None:
        ...

    def write_string(self, schema: "Schema", value: str) -> None:
        ...

    def write_blob(self, schema: "Schema", value: bytes) -> None:
        ...

    def write_timestamp(self, schema: "Schema", value: datetime.datetime) -> None:
        ...

    def write_document(self, schema: "Schema", value: "Document") -> None:
        ...


@runtime_checkable
class MapSerializer(Protocol):
    def entry(self, key: str, value_writer: Callable[[ShapeSerializer], None]):
        ...


@runtime_checkable
class SerializeableShape(Protocol):
    def serialize(self, serializer: ShapeSerializer) -> None:
        ...


@runtime_checkable
class SerializeableStruct(SerializeableShape, Protocol):
    def serialize_members(self, serializer: ShapeSerializer) -> None:
        ...
```

Below is an example Smithy `structure` shape, followed by the
`SerializebleShape` it would generate.

```smithy
namespace com.example

structure ExampleStructure {
    member: Integer = 0
}
```

```python
@dataclass(kw_only=True)
class ExampleStructure:
    member: int = 0

    def serialize(self, serializer: ShapeSerializer):
        serializer.write_struct(EXAMPLE_STRUCTURE_SCHEMA, self)

    def serialize_members(self, serializer: ShapeSerializer):
        serializer.write_integer(
            EXAMPLE_STRUCTURE_SCHEMA.members["member"], self.member
        )
```

### Performing Serialization

To serialize a shape, all that is needed is an instance of the shape and a
serializer. The following shows how one might serialize a shape to JSON bytes:

```python
>>> shape = ExampleStructure(member=9)
>>> serializer = JSONShapeSerializer()
>>> shape.serialize(serializer)
>>> print(serializer.get_result())
b'{"member":9}'
```

The process for performing serialization never changes from the high level.
Different implementations (such as for XML, CBOR, etc.) will all interact with
the shape in the same exact way. The same interface will be used to implement
HTTP bindings, event stream bindings, and any other sort of model-driven data
binding that may be needed.

These implementations can be swapped at any time without having to regenerate
the client, and can be used for purposes other than making client calls to a
service. A service could, for example, model its event structures and include
them in their client. A customer could then use the generated
`SerializeableShape`s to serialize those events without having to do so
manually.

### Composing Serializers

While simple `ShapeSerializer`s can exist, the need to bind data to multiple
locations or with conditional formatting may mean that a single
`ShapeSerializer` may not be sufficient to implement a protocol, or even
content-type. Instead, more complex protocols should *compose* multiple
`ShapeSerializer`s to achieve their intended purpose. The
`InterceptingSerializer` class aims, in part, to make this easier.

```python
class InterceptingSerializer(ShapeSerializer, metaclass=ABCMeta):
    @abstractmethod
    def before(self, schema: Schema) -> ShapeSerializer: ...

    @abstractmethod
    def after(self, schema: Schema) -> None: ...

    def write_boolean(self, schema: Schema, value: bool) -> None:
        self.before(schema).write_boolean(schema, value)
        self.after(schema)

    [...]
```

The `before` method allows for dispatching to different serializers depending on
the schema. You may dispatch to different serializers depending on whether the
shape is bound to an HTTP header or query string, for example.

```python
class HTTPBindingSerializer(InterceptingSerializer):
    _header_serializer: ShapeSerializer
    _query_serializer: ShapeSerializer

    def before(self, schema: Schema) -> ShapeSerializer:
        if HTTP_HEADER_TRAIT in schema.traits:
            return _header_serializer
        elif HTTP_QUERY_TRAIT in schema.traits:
            return _query_serializer
        ...
```

Since each of these sub-serializers may only be able to handle shapes of a
certain type, they may want to inherit from `SpecificShapeSerializer`, which
throws an error by default for shape types whose serialize method is not
implemented.

```python
class HTTPHeaderSerializer(SpecificShapeSerializer):
    def write_boolean(self, schema: "Schema", value: bool) -> None:
        ...

    [...]
```

## Shape Deserializers and Deserializeable Shapes

Deserialization will function very similarly to serialization, through the
interaction of two interfaces: `ShapeDeserializer` and `DeserializeableShape`.

A `ShapeDeserializer` is a class that is given a data source and provides
methods to extract typed data from it when given a schema. For example, a
`JSONShapeDeserializer` could be written that is constructed with JSON bytes and
allows a caller to convert it to a shape.

A `DeserializeableShape` is a class that has a `deserialize` method that takes a
`ShapeDeserializer` and calls the relevant methods needed to deserialize it. All
generated shapes will implement the `DeserializeableShape` interface, which will
then be the method by which all deserialization is performed.

In Python these interfaces will be represented as shown below:

```python
@runtime_checkable
class ShapeDeserializer(Protocol):

    def read_struct(
        self,
        schema: "Schema",
        state: dict[str, Any],
        consumer: Callable[["Schema", "ShapeDeserializer", dict[str, Any]], None],
    ) -> None:
        ...

    def read_list(
        self,
        schema: "Schema",
        state: list[Any],
        consumer: Callable[["ShapeDeserializer", list[Any]], None],
    ) -> None:
        ...

    def read_map(
        self,
        schema: "Schema",
        state: dict[str, Any],
        consumer: Callable[["ShapeDeserializer", dict[str, Any]], None],
    ) -> None:
        ...

    def is_null(self) -> bool:
        ...

    def read_null(self) -> None:
        ...

    def read_boolean(self, schema: "Schema") -> bool:
        ...

    def read_blob(self, schema: "Schema") -> bytes:
        ...

    def read_byte(self, schema: "Schema") -> int:
        return self.read_integer(schema)

    def read_short(self, schema: "Schema") -> int:
        return self.read_integer(schema)

    def read_integer(self, schema: "Schema") -> int:
        ...

    def read_long(self, schema: "Schema") -> int:
        return self.read_integer(schema)

    def read_float(self, schema: "Schema") -> float:
        ...

    def read_double(self, schema: "Schema") -> float:
        return self.read_float(schema)

    def read_big_integer(self, schema: "Schema") -> int:
        return self.read_integer(schema)

    def read_big_decimal(self, schema: "Schema") -> Decimal:
        ...

    def read_string(self, schema: "Schema") -> str:
        ...

    def read_document(self, schema: "Schema") -> "Document":
        ...

    def read_timestamp(self, schema: "Schema") -> datetime.datetime:
        ...


@runtime_checkable
class DeserializeableShape(Protocol):
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        ...
```

Below is an example Smithy `structure` shape, followed by the
`DeserializeableShape` it would generate.

```smithy
namespace com.example

structure ExampleStructure {
    member: Integer = 0
}
```

```python
@dataclass(kw_only=True)
class ExampleStructure:
    member: int = 0

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}
        deserializer.read_struct(
            _SCHEMA_CLIENT_OPTIONAL_DEFAULTS,
            consumer=cls._deserialize_kwargs,
        )
        return cls(**kwargs)

    @classmethod
    def _deserialize_kwargs(
        schema: Schema,
        de: ShapeDeserializer,
        kwargs: dict[str, Any],
    ) -> None:
        match schema.expect_member_index():
            case 0:
                kwargs["member"] = de.read_integer(
                    _SCHEMA_CLIENT_OPTIONAL_DEFAULTS.members["member"]
                )

            case _:
                logger.debug(f"Unexpected member schema: {schema}")
```

For structures, arguments are built up in a `kwargs` dictionary, which is later
expanded to construct the final type. Other languages might use a builder
pattern instead, but builders are atypical in Python, so this is a midway
approach that should be familiar to Python users.

The `kwargs` dictionary is passed through the serializer in order to avoid
having to allocate an anonymous function or use `functools.partial` (which would
need to allocate a `Partial` object). Lists and maps pass in pre-constructed
containers for the same reason.

Member dispatch is currently based on the "member index", which is a
representation of the member's position on the shape in the Smithy model itself.
(Note that this is not always the same as the ordering of the members in the
members dictionary. Recursive members are added at the end, regardless of where
they appear in the model.)

Doing member dispatch this way is an optimization, which uses relatively simple
integer comparision instead of the comparatively more expensive string
comparison needed to compare based on the member name. Further testing needs to
be done in Python to determine whether the performance impact justifies the
extra artifact size. In other language, the compiler is also capable of turning
an integer switch into a jump table, which CPython does not do (though it could
in theory).

It is important to note that the general approach of dealing with members
differs from serialization. No callback functions are needed in serialization,
but they are needed for deserialization. The reason is that deserializers must
handle members as they are presented in the data source, without any sort of
intermediate structure to pull members from. The shape class can't simply
iterate through its members in whatever order it likes to check if said member
is present, because the only member that is ever known about is the *next* one.

### Performing Deserialization

Deserialization works much like serialization does, all that is needed is a
deserializer and a class to deserialize into. The following shows how one might
deserialize a shape from JSON bytes:

```python
>>> deserializer = JSONShapeDeserializer(b'{"member":9}')
>>> print(ExampleStructure.deserialize(deserializer))
ExampleStructure(member=9)
```

Just like with serialization, the process for performing deserialization never
changes at the high level. Different implementations will all interact with the
shape in the same exact way. The same interface will be used for HTTP bindings,
event stream bindings, and any other sort of model-driven data binding that may
be needed.

These implementations can be swapped at any time without having to regenerate
the client, and can be used for purposes other than receiving responses from a
client call to a service. A service could, for example, model its event
structures and include them in their client. A customer could then use the
generated `DeserializeableShape`s to deserialize those events into Python types
when they're received without having to do so manually.

## Codecs

Serializers and deserializers are never truly disconnected - where there's one,
there's always the other. They need to be tied together in a way that makes
sense, is portable, and which provides extra utility for common use cases.

One such use case is the serialization and deserialization to and from discrete
bytes of a common format represented by a media type such as `application/json`.
These will be represented by the `Codec` interface:

```python
@runtime_checkable
class Codec(Protocol):

    def create_serializer(self, sink: BytesWriter) -> ShapeSerializer:
        ...

    def create_deserializer(self, source: bytes | BytesReader) -> ShapeDeserializer:
        ...

    def serialize(self, shape: SerializeableShape) -> bytes:
        ... # A default implementation will be provided

    def deserialize[S: DeserializeableShape](
        self, source: bytes | BytesReader,
        shape: type[S],
    ) -> S:
        ... # A default implementation will be provided
```

This interface provides a layer on top of serializers and deserializers that lets
them be interacted with in a bytes-in, bytes-out way. This allows them to be used
generically in places like HTTP message bodies. The following shows how one could
use a JSON codec:

```python
>>> codec = JSONCodec()
>>> deserialized = codec.deserialize(b'{"member":9}', ExampleStructure)
>>> print(deserialized)
ExampleStructure(member=9)
>>> print(codec.serialize(deserialized))
b'{"member":9}'
```

Combining them this way also allows for sharing configuration. In JSON, for
example, there could be a configuration option to represent number types that
can't fit in am IEEE 754 double as a string, since many JSON implementations
(including JavaScript's) treat them as such.

`Codec`s also provides opportunities for minor optimizations, such as caching
serializers and deserializers where possible.

## Client Protocols

`Codec`s aren't sufficient to fully represent a protocol, however, as there is
also a transport layer that must be created and support data binding. An HTTP
request, for example, can have operation members bound to headers, the query
string, the response code, etc. Such transports generally operate by interacting
`Request` and `Response` objects rather than raw bytes, so the bytes-based
interfaces of `Codec` aren't sufficient by themselves.

```python
class ClientProtocol[Request, Response](Protocol):

    @property
    def id(self) -> ShapeID:
        ...

    def serialize_request[I: SerializeableShape, O: DeserializeableShape](
        self,
        operation: ApiOperation[I, O],
        input: I,
        endpoint: URI,
        context: dict[str, Any],
    ) -> Request:
        ...

    def set_service_endpoint(
        self,
        request: Request,
        endpoint: Endpoint,
    ) -> Request:
        ...

    async def deserialize_response[I: SerializeableShape, O: DeserializeableShape](
        self,
        operation: ApiOperation[I, O],
        error_registry: TypeRegistry,
        request: Request,
        response: Response,
        context: dict[str, Any],
    ) -> O:
        ...
```

The `ClientProtocol` incorporates much more context than a `Codec` does.
Serialization takes the operation's schema via `ApiOperation`, the endpoint to
send the request to, and a general context bag that is passed through the
request pipeline. Deserialization takes much of the same as well as a
`TypeRegistry` that allows it to map errors it encounters to the generated
exception classes.

In most cases these `ClientProtocol`s will be constructed with a `Codec` used to
(de)serialize part of the request, such as the HTTP message body. Since that
aspect is separate, it allows for flexibility through composition. Two Smithy
protocols that support HTTP bindings but use a different body media type could
share most of a `ClientProtocol` implementation with the `Codec` being swapped
out to support the appropriate media type.

A `ClientProtocol` will need to be used alongside a `ClientTransport` that takes
the same request and response types to handle sending the request.

```python
class ClientTransport[Request, Response](Protocol):
    async def send(self, request: Request) -> Response:
        ...
```

Below is an example of what a very simplistic use of a `ClientProtocol` could
look like. (The actual request pipeline in generated clients will be more
robust, including things like automated retries, endpoint resolution, and so
on.)

```python
class ExampleClient:
    def __init__(
        self,
        protocol: ClientProtocol,
        transport: ClientTransport,
    ):
        self.protocol = protocol
        self.transport = transport

    async def example_operation(
        self, input: ExampleOperationInput
    ) -> ExampleOperationOutput:
        context = {}
        transport_request = self.protocol.serialize_request(
            operation=EXAMPLE_OPERATION_SCHEMA,
            input=input,
            endpoint=BASE_ENDPOINT,
            context=context,
        )
        transport_response = await self.transport.send(transport_request)
        return self.protocol.deserialize_response(
            operation=EXAMPLE_OPERATION_SCHEMA,
            error_registry=EXAMPLE_OPERATION_REGISTRY,
            request=transport_request,
            response=transport_response,
            context=context,
        )
```

As you can see, this makes the protocol and transport configurable at runtime.
This will make it significantly easier for services to support multiple
protocols and for customers to use whichever they please. It isn't even
necessary to update the client version to make use of a new protocol - a
customer could simply take a dependency on the implementation and use it.

Similarly, since the protocol is decoupled from the transport, customers can
freely switch between implementations without also having to switch protocols.
