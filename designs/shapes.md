# Abstract

This document will describe how [simple shapes](https://smithy.io/2.0/spec/simple-types.html)
and [aggregate shapes](https://smithy.io/2.0/spec/aggregate-types.html)
are generated into python types and type hints from a Smithy model.

# Specification

## Simple shapes

| Shape Type | Python Type |
|------------|-------------|
| blob | bytes |
| boolean | bool |
| string | str |
| byte | int |
| short | int |
| integer | int |
| long | int |
| float | float |
| double | float |
| bigInteger | int |
| bigDecimal | decimal.Decimal |
| timestamp | datetime.datetime |
| document | smithy_core.documents.Document |

## Trait-influenced shapes

### enum

```python
class StringEnum(UnknownEnumMixin, StrEnum):
    SPAM = "spam"
    EGGS = "eggs"
    SPAM_EGGS = "spam:eggs"
```

Members targeting string enums will use the base `str` type for forwards
compatibility.

To enable dot-completion support and programmatic understanding of known
values, a `StrEnum` will also be provided. Since `StrEnum` inherits from `str`,
customers will be able to directly pass values from the enum class without
issue. Documentation will reference the generated class for discoverability.
`UnknownEnumMixin` turns an unrecognized value into a pseudo-member flagged by
`is_unknown` instead of raising.

The generated class cannot be part of the type signature as a `Union` because
that would harm forwards compatibility. While each value inherits from the base
string class, there are notable differences that could cause code to break,
such as return values for `repr` and `type` changing.

#### Alternative: target the generated enums

In this alternative, members targeting StrEnums would reference the generated
classes. This wasn't chosen for both forwards and backwards compatibility reasons.
While one can mostly use StrEnums and strings interchangeably, the types *are*
different. Type checking would fail if you provided a base str, known or
unknown.

#### Alternative: native enums with generated accessors and unknown variant

```python
class MyEnum(StrEnum):
    SPAM = "spam"
    EGGS = "eggs"
    SPAM_EGGS = "spam:eggs"
    UNKNOWN_TO_SDK_VERSION = ""

    @staticmethod
    def from_string(value: str) -> Self:
        try:
            return MyEnum(value)
        except ValueError:
            return MyEnum.UNKNOWN_TO_SDK_VERSION


@dataclass(kw_only=True)
class Struct:
    my_enum: MyEnum
    my_enum_as_string: str = field(init=False)

    @my_enum.setter
    def my_enum(self, value: MyEnum):
        self._my_enum = value
        self._my_enum_as_string = value

    @my_enum_as_string.setter
    def my_enum_as_string(self, value: str):
        self._my_enum_as_string = value
        self._my_enum = MyEnum.from_string(value)
```

This alternative uses separate properties and a canonical unknown variant to
allow customers to use the native enums without risking a breaking change.
The tradeoff is we have to add another property, which may cause confusion.
We also have to generate getters/setters to make sure they stay in sync, which
dramatically increases the amount of code generated since these need to
appear in every referencing structure.

### intEnums

```python
class MyIntEnum(UnknownEnumMixin, IntEnum):
    SPAM = 1
    EGGS = 2
```

Members targeting int enums will use the base `int` type for forwards
compatibility.

To enable dot-completion support and programmatic understanding of known
values, an `IntEnum` will also be provided. Since `IntEnum` inherits from
`int`, customers will be able to directly pass values from the enum class
without issue. Documentation will reference the generated class for
discoverability.

This is essentially identical to the solution for string enums, including the
handling of unknown values.

### streaming blobs

A blob with the streaming trait will continue to support `bytes` as input.
Additionally, it will support passing in a `BytesReader` which is any class that
implements a `read` method that accepts a `size` param and returns bytes.
It will also accept an `AwaitableBytesReader`, whose `read` returns an
awaitable, or an `AsyncIterable[bytes]`.

Both `BytesReader` and `AwaitableBytesReader` will be implemented as [Protocols
](https://www.python.org/dev/peps/pep-0544/), which are a way of defining
structural subtyping in Python.

```python
@runtime_checkable
class BytesReader(Protocol):
    def read(self, size: int = -1, /) -> bytes:
        ...


@runtime_checkable
class AwaitableBytesReader(Protocol):
    def read(self, size: int = -1) -> Awaitable[bytes]:
        ...


type StreamingBlob = (
    BytesReader | bytes | bytearray | AwaitableBytesReader | AsyncIterable[bytes]
)
```

The type signature of members targeting blobs with the streaming trait will be
`smithy_core.aio.interfaces.StreamingBlob`.

### mediaType

Python is very generous in allowing subtyping of built in types, so a string or
blob modeled with the mediaType can accept or return helper classes. These can
be passed around and used exactly like normal strings/blobs.

```python
class JsonString(str):
    _json = ""

    def as_json(self) -> Any:
        if not self._json:
            self._json = json.loads(self)
        return self._json

    @staticmethod
    def from_json(json: Any) -> 'JsonString':
        json_string = JsonString(json.dumps(json))
        json_string._json = json
        return json_string

class JsonBlob(bytes):
    _json = b""

    def as_json(self) -> Any:
        if not self._json:
            self._json = json.loads(self.decode(encoding="utf-8"))
        return self._json

    @staticmethod
    def from_json(json: Any) -> 'JsonString':
        json_string = JsonBlob(json.dumps(json).encode(encoding="utf-8"))
        json_string._json = json
        return json_string
```

A member with a json media type is typed `str | JsonString` or
`bytes | JsonBlob`. Deserializers would always deserialize into a
`JsonString` or `JsonBlob` to ensure that the parsing is lazy and that adding
the mediaType trait is backwards-compatible.

Example usage:

```python
import json

my_json = {"spam": "eggs"}

# Without JsonBlob
client.send_json(json=b'{"spam": "eggs"}')
client.send_json(json=json.dumps(my_json.encode(encoding="utf-8")))
returned_json = json.loads(client.get_json().decode(encoding="utf-8"))

# With JsonBlob. All of the above are also possible.
client.send_json(json=JsonBlob.from_json(my_json))
returned_json = client.get_json().as_json()
```

By default only json helpers will be supported. More can be added later by
demand. Additionally, more can be be added with plugins to the code generators.

## Simple aggregate shapes

| Shape Type | Python Type | Type Hint |
|------------|-------------|-----------|
| list | list | list[str] |
| map | dict | dict[str, str] |

## Structures

Structures are simple dataclasses that only allow keyword arguments.

```python
@dataclass(kw_only=True)
class ExampleStructure:
    required_param: str
    struct_param: OtherStructure
    optional_param: str | None = None
```

Disallowing positional arguments prevents errors from arising when future
updates add additional structure members.

Using dataclasses removes the need to generate things like `__repr__`,
`__eq__`, and a number of other methods we would otherwise have to generate.

### Alternative: Plain dicts

Rather than generating dataclasses, plain dicts could be used:

```python
{
    "RequiredParam": "foo",
    "OptionalParam": "bar",
    "StructParam": {}
}
```

Since no classes need to be generated, the amount of generated code would be
significantly reduced. These dicts would be directly compatible with `boto3`,
making migration extremely easy.

The major downside is that these are extremely difficult to write useful type
hints for. `TypedDict` does exist, but the lack of support for recursive
definitions make it flaky to use. Without adequate type hints, or adequate
tooling that handles them, the development experience is greatly reduced.
Autocomplete, for example, is only sparsely supported for `TypedDict` and is
not at all supported for dicts without type hints. This can and does lead to
bugs where parameters are misspelled and not caught until runtime, if at all.

Additionally, using dicts is just more cumbersome than using plain python
objects. Consider the following:

```python
example_class = ExampleStruct(required_param="foo")
print(example_class.optional_param) # None

example_dict = {"RequiredParam": "foo"}
print(example_dict["OptionalParam"]) # KeyError: 'OptionalParam'
print(example_dict.get("OptionalParam")) # None
```

This is a small example of a minor annoyance, but one that you must always be
aware of when using dicts.

### Default Values

Default values use python's built-in default values system. Shapes that have
immutable defaults, such as integers, have their values directly assigned.
Shapes that can have immutable defaults (i.e. lists, maps, and documents) make
use of dataclass `field`s and their `default_factory` as necessary.

```python
@dataclass(kw_only=True)
class StructWithDefaults:
    default_int: int = 7
    default_list: list[int] = field(default_factory=list)
```

### Sensitive Members

Sensitive members will make use of dataclass `field`s, which have a toggle to
remove a given property from the generated `__repr__` method.

```python
@dataclass(kw_only=True)
class StructWithSensitiveMembers:
    not_sensitive: str
    sensitive: str = field(repr=False)

print(StructWithSensitiveMembers(not_sensitive="foo", sensitive="bar"))
# StructWithSensitiveMembers(not_sensitive='foo')
```

Customers will still be able to print out those values if they wish, but they
will have to explitictly do so.

## Errors

Modeled errors are specialized structures that have a `fault` and `message`.

```python
# Defined in smithy_core.exceptions, used for all common errors in generic
# library code.
class SmithyError(Exception):
    pass


# Defined in smithy_http.exceptions, the base for errors raised in HTTP
# clients.
class SmithyHTTPError(SmithyError):
    pass


# Defined in smithy_core.exceptions, the base for application-level errors.
@dataclass(kw_only=True)
class CallError(SmithyError):
    fault: Fault = None
    message: str = field(default="", kw_only=False)

    def __post_init__(self) -> None:
        super().__init__(self.message)


# Defined in smithy_core.exceptions, the base for modeled errors.
@dataclass(kw_only=True)
class ModeledError(CallError):
    fault: Fault = "client"


# Generated per service and used for all modeled errors of the service.
class ServiceError(ModeledError):
    pass


@dataclass(kw_only=True)
class ModeledException(ServiceError):
    modeled_member: list[str]
    fault: str | None = "client"
```

All errors will inherit from a base `SmithyError` class. This will allow
customers to catch nearly any exception generated by client if they so choose.
This class will be hand written inside a shared library.

Each generated service will have one static error generated: `ServiceError`,
which subclasses `ModeledError`. `ServiceError` will be inherited by all
modeled errors of the service.

Modeled errors will differ from normal structures in three respects:

* They will inherit from `ServiceError`.
* They will have a `fault` field whose default is based on the error trait.
* They will have a consistent `message` property, which will replace any member
  with a name case-insensitively matching `message`, `error_message`, or
  `errormessage`.

### Alternative: ServiceError wraps SmithyError

In this alternative, the generated `ServiceError` would not inherit from
`SmithyError`. Instead it would have a subclass that wraps it.

```python
class SmithyError(Exception):
    pass


class ServiceError(Exception):
    pass


class WrappedSmithyError(ServiceError):
    def __init__(self, smithy_error: SmithyError):
        super().__init__(str(smithy_error))
        self.error = smithy_error
```

A generated client would then catch and wrap any instances of `SmithyError`
thrown. This has the advantage of allowing a customer to catch *all* errors
thrown for a given service. This could potentially be useful for code bases
that make use of several clients.

The downside is that this means a customer can't catch any particular subclass
of `SmithyError` in the normal way. Instead, they'd have to first catch the
wrapped error and then manually access the `error` property to dispatch,
remembering to re-raise if it isn't what they're looking for.

## Unions

Unions are separate dataclasses grouped by a `Union` type hint.

```python
@dataclass
class MyUnionMemberA:
    value: bytes


@dataclass
class MyUnionMemberB:
    value: str


@dataclass
class MyUnionUnknown:
    tag: str


MyUnion = Union[MyUnionMemberA, MyUnionMemberB, MyUnionUnknown]


@dataclass(kw_only=True)
class SampleStruct:
    union_member: MyUnion
```

This allows for exhaustiveness checks since all variants are known ahead of time.
The `Union` alias exists only in the generated `.pyi` stub. At runtime `MyUnion`
is an empty marker class, so isinstance checks have to use the variant classes.

```python
def handle_with_instance(my_union: Any):
    if isinstance(my_union, MyUnionMemberA):
        print(value.decode(encoding="utf-8"))
    elif isinstance(my_union, MyUnionMemberB):
        for v in my_union.value:
            print(v)
    else:
        raise Exception(f"Unhandled union type: {my_union}")


# This is only possible at all in python 3.10 and up
def handle_with_match(my_union: MyUnion):
    # A type checker can see that MyUnionMemberB isn't accounted
    # for. This implies that updates could cause type checking to fail if
    # there's no default case. There is no way to avoid this, and we wouldn't
    # want to even if we could. This would expose the error at type checking
    # time rather than runtime, which is what we want.
    match my_union:
        case MyUnionUnknown:
            raise Exception(f"Unknown union type: {my_union.tag}")
        case MyUnionMemberA:
            print(value.decode(encoding="utf-8"))
        # A default case could suppress the type check error.
        # case _:
        #    raise Exception(f"Unhandled union type: {my_union}")
```

### Alternative: inheritance

In this alternative, unions are classes with a typed `value` property grouped
by a parent class.

```python
class MyUnion[V](ABC):
    value: V


@dataclass
class MyUnionMemberA(MyUnion[bytes]):
    value: bytes


@dataclass
class MyUnionMemberB(MyUnion[str]):
    value: str


@dataclass
class MyUnionUnknown(MyUnion[None]):
    tag: str
    value: None = field(init=False, default=None)


@dataclass(kw_only=True)
class SampleStruct:
    union_member: MyUnion[Any]
```

This design has a number of disadvantages over using native unions:

* A type checker cannot know every possible subclass of the base class, so
  you won't get exhaustiveness checks or gradual type refinement. An early
  version of the pattern matching PEP included a `@sealed` decorator that
  would have helped here, but it was removed in the accepted version.

  Even if `@sealed` were introduced in another PEP, it wouldn't be available
  until some time in the future, meaning if we wanted to use it we'd have to do
  something like:

```python
try:
    from typing import sealed
except ImportError:
    # Identity decorator to allow us to gracefully upgrade to sealed on newer
    # python versions.
    def sealed(wrapped: Any):
        return wrapped
```

  This would potentially mean a user upgrading from 3.12 to 3.13 would start
  seeing type check failures even though they haven't updated the library
  or changed any of their code.

* A user might try to use the parent type directly in their own typing with
  some generic type, e.g. `MyUnion[str]`. This could obscure the fact that
  multiple variants of a union may have the same member type and lead to bugs.

* The unknown variant has a `value` property even though it has no value. This
  could lead to bugs if the user expects the value to not be none, as it allows
  them to not deal with the fact that the unknown variant exits.

The only advantage this has over using native unions is the ability to use
isinstance checks against the parent class.

# FAQs

## Why not use built-in class subtypes for unions?

Unions can have multiple members targeting the same shape, so there would be
no way to automatically determine what a users intent was if they passed in
the base class. Since they would, therefore, have to always pass in our
concrete types, there would be no advantage to subclassing built-ins.
