# Document Types

Smithy's [document type](https://smithy.io/2.0/spec/simple-types.html#document)
represents protocol-agnostic data of any type that can be expressed by the
Smithy data model. In other clients, documents were represented essentially as
JSON, but this fails to achieve a number of goals we have for the type.

This specification describes how documents are defined and used in
smithy-python.

## Goals

* Extend documents to fully support the Smithy data model.
* Integrate documents with schema-based serialization and deserialization.
* Abstract away the underlying media type of documents.
* Allow documents to carry structured values.
* Make documents easily convertible to/from plain Python.

## Specification

The `Document` type in Python is a class with typed accessors for Smithy
data types that implements `SerializableStruct` and `DeserializableShape`.
Below is an example of what the base `Document` type will look like at the high
level, subsequent sections will discuss details of each component.

```python
type DocumentValue = (
    Mapping[str, DocumentValue]
    | Sequence[DocumentValue]
    | str
    | int
    | float
    | Decimal
    | bool
    | None
    | bytes
    | datetime.datetime
)


class Document:
    _schema: Schema

    def __init__(
        self,
        value: DocumentValue | dict[str, "Document"] | list["Document"] = None,
        *,
        schema: Schema = _DOCUMENT,
    ) -> None:
        ...

    @property
    def shape_type(self) -> ShapeType:
        ...

    @property
    def discriminator(self) -> ShapeID:
        ...

    def is_none(self) -> bool:
        ...

    def as_bytes(self) -> bytes:
        ...

    def as_bool(self) -> bool:
        ...

    def as_string(self) -> str:
        ...

    def as_datetime(self) -> datetime.datetime:
        ...

    def as_int(self) -> int:
        ...

    def as_float(self) -> float:
        ...

    def as_decimal(self) -> Decimal:
        ...

    def as_list(self) -> list["Document"]:
        ...

    def as_map(self) -> dict[str, "Document"]:
        ...

    def as_value(self) -> DocumentValue:
        ...

    def as_shape[S: DeserializableShape](self, shape_class: type[S]) -> S:
        ...

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_document(self._schema, self)

    def serialize_contents(self, serializer: ShapeSerializer) -> None:
        ...

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        ...

    def get(self, name: str, default: "Document | None" = None) -> "Document | None":
        return self.as_map().get(name, default)

    def __getitem__(self, key: str | int | slice) -> "Document":
        ...

    def __setitem__(
        self,
        key: str | int,
        value: "Document | list[Document] | dict[str, Document] | DocumentValue",
    ) -> None:
        ...

    def __delitem__(self, key: str | int) -> None:
        ...

    @classmethod
    def from_shape(cls, shape: SerializableShape) -> "Document":
        ...
```

### Shape Type

`Document`s maintain awareness of their Smithy data type which is exposed as a
read-only `shape_type` property. This allows users to inspect the type of the
document's data in a static way that is more accurate than simply checking the
Python type of the underlying data. Python has only one type of `integer`, for
example, while Smithy has five.

When constructed without an explicit shape type, a shape type will be guessed.
Python `integer`s will be assumed to be `LONG`s and Python `float`s will be
assumed to be `DOUBLE`s.

`ShapeType` is an enum, so users can `match` on a document with exhaustiveness
checks. For example:

```python
match document.shape_type:
    case ShapeType.STRUCTURE | ShapeType.UNION:
        print("In JSON, this would become a map")
    case ShapeType.TIMESTAMP:
        print("JSON has no native timestamp type")
    case ShapeType.BLOB:
        print("JSON has no native binary type")
    case _:
        pass
```

### Document Schemas

`Document`s contain a private `Schema` from which their shape type is derived by
default. This schema is also used by default in serialization implementations.
While the `Document` class itself doesn't inspect anything but the shape type,
the schema is passed along to the `ShapeSerializer`, which may use the schema's
traits or defined members to influence serialization. This means that a
`Document` can fully capture any value that any structure, union, or other data
shape can capture and it will be serialized exactly as if it were that type.

As a simple example, a `Document` that contains a timestamp may include a schema
that contains the `@timestampFormat` trait. This would be serialized in exactly
the same way as a modeled timestamp with the same trait.

By default, the document's schema is a generic schema from the Smithy prelude,
based on the underlying type. A string shape takes on the base `String` for
example. Lists and maps by default use a schema with the shape type `DOCUMENT`.
Since it is not possible to determine whether a given `dict` is a map,
structure, or union, they are treated as maps by default. See
[structures and unions](#structures-and-unions) for more information on how
typed structure and union `Document`s may be created.

It is also possible to pass in a schema when constructing a document by using
the `schema` keyword-only argument.

### Accessors

The `Document` type has accessors for each Python data type that is generated
from Smithy. This means, for example, that there is an `as_integer`, but not an
`as_short` or `as_big_decimal`. If it is necessary to distinguish between the
different integer or float sizes, the `shape_type` can be used.

When any of the accessor methods are called, the underlying data is asserted to
be of the requested type before it is returned, raising an exception if it is
not. In some cases these types are coerced where they're compatible. For
example, attempting to access a `Decimal` from a document that contains a
`float` will return a `Decimal` representation of that float.

The following example shows how accessors may be used:

```python
# With no or limited prior knowledge, a match can be used to handle different
# possible types.
match document.shape_type:
    case ShapeType.STRING:
        print(document.as_string())
    case ShapeType.BLOB:
        print(document.as_blob().decode("utf-8"))
    case _:
        pass

# With concrete prior knowledge, the accessor can be called directly.
# If the underlying type doesn't match, an exception will be raised.
print(f"Total: {document.as_float()}")
```

Note that the values of lists and maps are `Document`s themselves.

#### DocumentValue

In addition to accessing Smithy data types, `Document`s will have a method to
return the document as a plain Python object without any context. These
`DocumentValue`s are similar to a JSON value, except that they include
`datetime.datetime`, `bytes`, and `Decimal` as possible types. `Document`s may
also be construced by providing a `DocumentValue`. Other implementations of the
`Document` type may not include this functionality, but for Python it is a huge
ease-of-use improvement for those that don't need the extra saftey and
functionality of the full `Document` type.

Currently the base `Document` implementation lazily converts between the two
representations and caches the results. This is done for the sake of speed, but
has an unfortunate space cost. This behavior is not part of the API, however,
and MAY be changed without backwards compatibility implications.

```python
>>> document = Document({"foo": "bar"})
>>> document.shape_type
ShapeType.DOCUMENT
>>> document.as_value()
{"foo": "bar"}
>>> document["foo"]
Document(value="bar")
```

#### Structures and Unions

Smithy structures and unions are generated into their own individual classes in
Python, and so it isn't possible to have a unique accessor for each of them.
Instead, `Document`s have a generic `as_shape` method that supports converting
the `Document` to any `DeserializableShape`. If the document does not
structurally match the target shape, an error will be raised.

Similarly, a `from_shape` method allows for converting any `SerializableShape`
into a document. When a `Document` is constructed this way, it will retain the
schema of the shape it was constructed from.

```python
@dataclass
class ExampleStruct:
    foo: str
    bar: str | None = None

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        ...

document = Document({"foo": "spam"})
print(document.as_shape(ExampleStruct))
# ExampleStruct(foo="spam")

structure = ExampleStruct(foo="spam", bar="eggs")
print(Document.from_shape(structure))
# Document(
#     value={"foo": Document(value="spam"), "bar": Document(value="eggs")},
#     schema=EXAMPLE_STRUCT_SCHEMA,
# )
```

These methods use the `serialize` and `deserialize` methods under the hood,
providing private `ShapeSerializer`s and `ShapeDeserializer`s to handle the
heavy lifting.

### Container Methods

`Document`s are often containers, and so to make `Document` usage as natural as
possible, most of Python's built-in
[container methods](https://docs.python.org/3/reference/datamodel.html#emulating-container-types)
will be supported. If the underlying type cannot support that method, an
exception will be raised. The following list specifies which container methods
specifically will be supported and what shape types they apply to.

* `__len__` - Valid for lists, maps, structures, and unions.
* `__getitem__` - Valid for lists, maps, structures, and unions.
* `get` - Valid for maps, structures, and unions. This is equivalent to `dict`'s
  `get` method which allows for a default value to be specified.
* `__setitem__` - Valid for lists, maps, and structures, and unions. Unions and
  structures may only use keys representing members that are in their schema.
  Unions may only replace the current value.
* `__delitem__` - Valid for lists, maps, and structures. Notably not valid for
  unions as a union MUST contain exactly one member.
* `__iter__` - Valid for lists, maps, structures, and unions.
* `__contains__` - Valid for lists, maps, structures, and unions.

Notably none of these methods are supported for strings or blobs, though some of
them could be. This is because the intent of implementing these methods is to
allow the `Document` to function as a container, and neither strings nor blobs
are really containers. There is also some potential for ambiguity if these were
to be implemented in the case of the underlying value being coercable into
another type, such as a base64 string that could be coerced into a blob. Since
the default behavior is to throw an exception, this can be changed at a later
date in a backwards-compatible way.

### Serialization and Deserialization

The major advantage of the `Document` type over just using `DocumentValue`
directly is that it integrates with schema-based serialization and
deserialization. Since `Document` implements `SerializableShape` and
`DeserializableShape` it can be directly used with any `ShapeSerializer` or
`ShapeDeserializer` without any additional effort. The same `Document` can be
serialized to and from XML, JSON, CBOR, etc. without any loss of information.

#### Protocol-Specific Documents

Some media types may not support all of the Smithy data model. JSON, for
example, does not have a native capability to store blobs. In current AWS
protocols that use JSON, blobs are stored as base64-encoded strings. The base
`Document` class is unaware of this, but a `JSONDocument` subclass can smooth
over the issue by attempting to coerce a string into a blob when `as_blob`
is called.

```python
class JSONDocument(Document):
    @override
    def as_blob(self) -> bytes:
        if self.shape_type is ShapeType.STRING:
            return b64decode(self.as_string())
        return super().as_blob()
```

This same strategy can be used to support timestamps based on the
`@timestampFormat`, to support representing `Decimal`s as strings to avoid
precision loss, etc. These specialized `Document`s can also contain
configuration for these and any number of other features.

Protocol-specific documents are also instrumental in fully supporting late-bound
types.

#### Late-Bound Types

`Document`s may also be used to implement a system of late-bound types. That is,
clients and servers may exchange `Document`s which represent particular modeled
shapes. AWS services, for example, may send structured events to trigger a
Lambda function. If the shape of that event is known, the `Document` may be
converted to that shape.

If the specific shape is known ahead of time with external knowledge, then
`as_shape` can be used directly. But there are cases where the `Document` may
represent one of several shapes. For this reason, `Document`s have a
`discriminator` property that delclares what shape it represents. By default
this is the id of the document's schema, but that schema itself will be a
default schema from the prelude unless the document is specifically constructed
with one.

To reliably communicate the discriminator, it needs to be embedded in the
document itself. How this is done is protocol-specific, and thus is the domain
of protocol-specific documents. A JSON-based protocol could, for example,
embed the shape id as the value of a top-level `__type` property.

```json
{
    "__type": "smithy.example#ExampleStruct",
    "foo": "spam",
    "bar": "eggs"
}
```

A `TypeRegistry` would then be used to get the concrete class, which is then used
to convert the `Document` into the target class.

```python
>>> registry.deserialize(document)
```

##### Type Registries

A `TypeRegistry` is essentially a nestable mapping of `ShapeID` to
`DeserializableShape`. If a given shape ID can't be found within the local set
of known shapes, it delegates to a sub-registry.

```python
class TypeRegistry:
    def __init__(
        self,
        types: dict[ShapeID, DeserializableShape],
        sub_registry: "TypeRegistry | None" = None
    ):
        self._types = types
        self._sub_registry = sub_registry

    def get(self, shape: ShapeID) -> type[DeserializableShape]:
        ...

    def deserialize(self, document: Document) -> DeserializableShape:
        return document.as_shape(self.get(document.discriminator))
```

It also provides a convenience method for deserializing documents that can be
used to further customize how documents are deserialized, such as if the
document's concrete value is nested alongside the discriminator, like below.

```json
{
    "__type": "smithy.example#ExampleStruct",
    "__value": {
        "foo": "spam",
        "bar": "eggs"
    }
}
```

#### Botocore Interop

It may not be obvious, `Document`'s serialization and deserialization methods
enable interoperability with botocore-style inputs and outputs without any
additional effort. This is because the keys of any underlying dicts will be
based on the member names from the schema, which is exactly what botocore does.

```python
head_object_input_dict = {
    "Bucket": "spam",
    "Key": "eggs",
}
head_object_input = Document(head_object_input_dict).as_shape(HeadObjectInput)

head_object_output = HeadObjectOutput(
    delete_marker=False,
    last_modified=datetime(2015, 1, 1),
    [...]
)
head_object_output_dict = Document.from_shape(head_object_output).as_value()
# {"DeleteMarker": False, "LastModified": datetime(2015, 1, 1), ...}
```

This isn't 100% foolproof, however. There are several instances where botocore
special-cases the name of a key or the type of its value. In those cases, the
conversion would fail.

There is also a performance tradeoff to be considered when using `Document`s for
this purpose. Having to construct an intermediate representation and only then
constructing the output type adds extra allocations and runtime in general. In
most cases this should not be significant, especially if done at a boundary
location. A more efficient solution could be implemented with direct
`ShapeSerializer`s and `ShapeDeserializer`s, which could also incorporate
botocore's special-cased members.
