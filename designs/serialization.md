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
    traits: dict[ShapeID, "Trait"] = field(default_factory=dict)
    members: dict[str, "Schema"] = field(default_factory=dict)
    member_target: "Schema | None" = None
    member_index: int | None = None

    @classmethod
    def collection(
        cls,
        *,
        id: ShapeID,
        shape_type: ShapeType = ShapeType.STRUCTURE,
        traits: list["Trait"] | None = None,
        members: Mapping[str, "MemberSchema"] | None = None,
    ) -> Self:
        ...


@dataclass(kw_only=True, frozen=True)
class Trait:
    id: "ShapeID"
    value: "DocumentValue" = field(default_factory=dict)
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
                Trait(id=ShapeID("smithy.api#default"), value=0),
            ],
        },
    },
)
```

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

A `SerializeableShape` is a class that has a `deserialize` method that takes a
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
