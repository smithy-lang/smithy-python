# Abstract

This document will describe how [simple shapes](https://smithy.io/2.0/spec/simple-types.html)
and [aggregate shapes](https://smithy.io/2.0/spec/aggregate-types.html)
are generated into python types and type hints from a Smithy model.

# Specification

## Simple shapes

| Shape Type | Python Type |
|------------|-------------|
| blob | Union[bytes, bytearray] |
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
| document | Document = dict[str, 'Document'] | list['Document'] | str | int | float | bool | None |

## Trait-influenced shapes

### enum

```python
class EnumWithNames:
    SPAM = "spam"
    EGGS = "eggs"
    SPAM_EGGS = "spam:eggs"

    values = frozenset(SPAM, EGGS, SPAM_EGGS)
```

Enums are classes with a `values` property that contains an immutable set of
all the possible values of the enum in addition to static properties for each
entry.

This provides customers with a way to access the simplified names for easier
development, as well as giving them a programmatic ability to check known
values.

Members targeting enums will continue to use plain strings to enable forwards
compatibility. Documentation for those members will reference the enum classes
for discoverability.

#### Alternative: native enums

Python 3.4 introduced native enums, and they're about what you'd expect:

```python
class MyEnum(Enum):
    SPAM = "spam"
    EGGS = "eggs"
    SPAM_EGGS = "spam:eggs"
```

Defining an enum in this way gives you iterators, comparators, and a more
helpful string representation (`<MyEnum.SPAM: 'spam'>`) for free.

Unfortuantely, native enums aren't forwards compatible. To support forwards
compatibility, we need to also support passing plain strings. If a client were
handling an enum value not represented in their version, then they would break
upon updating because `MyEnum.SPAM != "spam"`.

While we could generate them anyway for helpers, it would be very confusing
to use as you would have to pass `MyEnum.SPAM.value` instead of `MyEnum.SPAM`.

#### Alternative: native enums with generated accessors and unknown variant

```python
class MyEnum(Enum):
    SPAM = "spam"
    EGGS = "eggs"
    SPAM_EGGS = "spam:eggs"
    UNKNOWN_TO_SDK_VERSION = ""

    @staticmethod
    def from_string(value: str) -> 'MyEnum':
        try:
            return MyEnum(value)
        except ValueError:
            return MyEnum.UNKNOWN_TO_SDK_VERSION


class Struct:
    def __init__(self, *, my_enum: Union[MyEnum, str]):
        if isinstance(my_enum, MyEnum):
            self._my_enum = my_enum
            self._my_enum_as_string = my_enum.value
        else:
            self._my_enum = MyEnum.from_string(my_enum)
            self._my_enum_as_string = my_enum

    @property
    def my_enum(self) -> MyEnum:
        return self._my_enum

    @my_enum.setter
    def my_enum(self, value: MyEnum):
        self._my_enum = value
        self._my_enum_as_string = value

    @property
    def my_enum_as_string(self) -> str:
        return self._my_enum_as_string

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
class MyIntEnum(IntEnum):
    SPAM = 1
    EGGS = 2
```

IntEnums will use the native `IntEnum` type. This will allow customers to
easily specify the enum value without having to reference the actual number. It
also gives them a programmatic way to list known values.

Like string enums, members targeting IntEnums will use plain integers to enable
forwards compatibility and type checking. Documentation for those members will
reference the generated classes for discoverability.

#### Alternative: target the generated enums

In this alternative, members targeting IntEnums would reference the generated
classes. This wasn't chosen for both forwards and backwards compatibility reasons.
While one can mostly use IntEnums and integers interchangeably, the types *are*
different. Type checking would fail if you provided a base integer, known or
unknown.

### streaming blobs

A blob with the streaming trait will continue to support `bytes` as input.
Additionally, it will support passing in a `ByteStream` which is any class that
implements a `read` method that accepts a `size` param and returns bytes.
It will also accept an async variant of that same type or an `AsyncIterable`.

Both `ByteStream` and `AsyncByteStream` will be implemented as [Protocols
](https://www.python.org/dev/peps/pep-0544/), which are a way of defining
structural subtyping in Python.

```python
@runtime_checkable
class ByteStream(Protocol):
    def read(self, size: int = -1) -> bytes:
        ...


@runtime_checkable
class AsyncByteStream(Protocol):
    async def read(self, size: int = -1) -> bytes:
        ...


StreamingBlob = Union[
    ByteStream,
    AsyncByteStream,
    bytes,
    bytearray,
    AsyncIterable,
]
```

The type signature of members targeting blobs with the streaming trait will be
the union `StreamingBlob`.

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

A member with a json media type could then accept any json-compatible type in
addition to their base types. Deserializers would always deserialize into a
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
client.send_json(json=my_json)
client.send_json(json=JsonBlob.from_json(my_json))
returned_json = client.get_json().as_json()
```

By default only json helpers will be supported. More can be added later by
demand. Additionally, more can be be added with plugins to the code generators.

## Simple aggregate shapes

| Shape Type | Python Type | Type Hint |
|------------|-------------|-----------|
| list | list | List[str] |
| set | set | Set[str] |
| map | dict | Mapping[str, str] |

## Structures

Structures are simple python objects with `as_dict` and `from_dict` methods
whose constructors only allow keyword arguments. For example:

```python
class ExampleStructure:
    required_param: str
    struct_param: OtherStructure
    optional_param: str | None

    def __init__(
        self,
        *, # This prevents positional arguments
        required_param: str,
        struct_param: OtherStructure,
        optional_param: str | None = None
    ):
        self.required_param = required_param
        self.struct_param = struct_param
        self.optional_param = optional_param

    def as_dict(self) -> Dict:
        d = {
            "RequiredParam": self.required_param,
            "StructParam": self.struct_param.as_dict(),
        }

        if self.optional_param is not None:
            d["OptionalParam"] = self.optional_param

    @staticmethod
    def from_dict(d: Dict) -> ExampleStructure:
        return ExampleStructure(
            required_param=d["RequiredParam"],
            struct_param=OtherStructure.from_dict(d["StructParam"]),
            optional_param=d.get("OptionalParam"),
        )
```

Disallowing positional arguments prevents errors from arising when future
updates add additional structure members.

The `as_dict` and `from_dict` methods exist primarily to make migration
from `boto3` easier, as users will be able to use them to convert to/from
`boto3` style arguments freely. To facilitate that migration, keys in the
generated dicts use shape names as defined in the model rather than the
snake cased variants used in the constructor.

### Alternative: Dataclasses

Python 3.7 introduced dataclasses, which are a simple way of defining simple
classes which have auto-generated implementations of a bunch of common
functions.

```python
@dataclass
class ExampleStructure:
    required_param: str
    struct_param: OtherStructure
    optional_param: Optional[str] = None
```

This will auto-generate `__init__`, `__repr__`, `__eq__`, `__hash__`, and
optionally a number of other magic methods. `dataclasses` also provides a
number of other useful methods, like an `as_dict` function.

Unfortunately, the generated constructors allow for positional arguments.
Constructor generation can be disabled, and a custom constructer can be
written instead. Still, this immediately starts eating away at the utility
of the decorator.

Similarly, the prebuilt `as_dict` function is fairly rigid. There is currently
no way to customize the dict representation. This means that we wouldn't be
able to have compatibility with `boto3` unless we implement the function
ourselves. And there is no built in way to convert an existing dict into
a given dataclass.

Since none of the methods we want can be properly generated by `dataclass`,
there is not much reason to use them. The free `eq`, `hash`, and `repr`
integrations are nice, but not worth adding a dependency for.

Adding any dependency, even one on the standard library, should be approached
with caution. Updates can introduce potentially breaking features that we have
little ability to resolve. The standard library in particular is impossible for
us to keep up to date, as we have no control over the environment our customers
run code in.

### Alternative: Plain dicts

Rather than generating classes, plain dicts could be used:

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
immutable defaults, such as integers, have their values directly assigned in
the constructor default. Shapes that can have immutable defaults (i.e. lists,
maps, and documents) are assigned to `None` and have their default value set
inside the constructor body.

```python
class StructWithDefaults:
    default_int: int
    default_list: list[int]

    def __init__(
        self,
        *,
        default_int: int = 7,
        default_list: Optional[list[int]] = None,
    ):
        self.default_int = default_int
        self.default_list = default_list if default_list is not None else []
```

## Errors

Modeled errors are specialized structures that have a `code` and `message`.

```python
# Defined in a shared library, used for all common errors in generic library
# code.
class SmithyError(Exception):
    pass


# This is just an example of a direct implementation of a SmithyError. This
# would also be defined in generic library code.
class HttpClientError(SmithyError):
    def __init__(
        self,
        error: Exception,
        request: Optional[HttpRequest] = None,
        response: Optional[HttpResponse] = None
    ):
        super().__init__(
            f"An HTTP client raised an unhaneled exception: {error}")
        self.request = request
        self.response = response
        self.error = error


# Generated per service and used for all service-specific errors. This would
# be the base error for customizations, for instance.
class ServiceError(SmithyError):
    pass


# Generated per service and used for all modeled errors.
class ApiError(ServiceError, Generic[T]):
    code: T

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ModeledException(ApiException[Literal["ModeledException"]]):
    code: Literal["ModeledException"] = "ModeledException"

    def __init__(
        self,
        *,
        message: str,
        modeled_member: List[str]
    ):
        super().__init__(message)
        self.modeled_member = modeled_member


class UnknownException(ApiException[Literal["Unknown"]]):
    code: Literal["Unknown"] = "Unknown"
```

All errors will inherit from a base `SmithyError` class. This will allow
customers to catch nearly any exception generated by client if they so choose.
This class will be hand written inside a shared library.

Each generated service will have two static errors generated: `ServiceError`
and `ApiError`. `ServiceError` will be inherited by ever error specific to the
service, including errors raised in service-specific customizations. `ApiError`
will be inherited by all modeled errors.

Modeled errors will differ from normal structures in three respects:

* They will inherit from `ApiError`.
* They will have a static `code` property generated, which will default to the
  name of the error shape.
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

Unions are separate classes groupd by a `Union` type hint.

```python
class MyUnionMemberA(MyUnion[bytes]):
    def __init__(self, value: bytes):
        self.value = value

    def as_dict(self):
        return {"MemberA": self.value}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> MyUnionMemberA:
        if len(d) != 1:
            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
        return MyUnionMemberA(d["MemberA"])


class MyUnionMemberB(MyUnion[str]):
    def __init__(self, value: str):
        self.value = value

    def as_dict(self):
        return {"MemberB": self.value}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> MyUnionMemberA:
        if len(d) != 1:
            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
        return MyUnionMemberB(d["MemberB"])


class MyUnionUnknown:
    def __init__(self, tag: str, value: bytes):
        self.tag = tag

    def as_dict(self) -> Dict[str, Any]:
        return {"SDK_UNKNOWN_MEMBER": {"name": self.tag}}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AnnouncementsUnknown":
        if len(d) != 1:
            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
        return AnnouncementsUnknown(d["SDK_UNKNOWN_MEMBER"]["name"])


MyUnion = Union[MyUnionMemberA, MyUnionMemberB, MyUnionUnknown]


class SampleStruct:
    def __init__(self, *, union_member: MyUnion):
        self.union_member = union_member
```

This allows for exhaustiveness checks since all variants are known ahead of time,
and as of python 3.10+ it also allows isinstance checks as if inheritance were
being used.

```python
def handle_with_instance(my_union: Any):
    if not isinstance(my_union, MyUnion):
        return
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
V = TypeVar("V")


class MyUnion(ABC, Generic[V]):
    value: V

    @abstractmethod
    def as_dict(self): pass

    @abstractmethod
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "MyUnion[V]": pass


class MyUnionMemberA(MyUnion[bytes]):
    def __init__(self, value: bytes):
        self.value = value

    def as_dict(self):
        return {"MemberA": self.value}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> MyUnionMemberA:
        if len(d) != 1:
            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
        return MyUnionMemberA(d["MemberA"])


class MyUnionMemberB(MyUnion[str]):
    def __init__(self, value: str):
        self.value = value

    def as_dict(self):
        return {"MemberB": self.value}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> MyUnionMemberA:
        if len(d) != 1:
            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
        return MyUnionMemberB(d["MemberB"])


class MyUnionUnknown(MyUnion[None]):
    def __init__(self, tag: str):
        self.tag = tag
        self.value = None

    def as_dict(self) -> Dict[str, Any]:
        return {"SDK_UNKNOWN_MEMBER": {"name": self.tag}}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AnnouncementsUnknown":
        if len(d) != 1:
            raise TypeError(f"Unions may have exactly 1 value, but found {len(d)}")
        return AnnouncementsUnknown(d["SDK_UNKNOWN_MEMBER"]["name"])


class SampleStruct:
    def __init__(self, *, union_member: MyUnion[Any]):
        self.union_member = union_member
```

This design has a number of disadvantages over using native unions:

* A type checker cannot know every possible subclass of the base class, so
  you won't get exhaustiveness checks or gradual type refinement. An early
  version of the pattern matching PEP included a `@sealed` decorator that
  would have helped here, but it was removed in the accepted version.

  Even if `@sealed` were introduced in another PEP, it wouldn't be available
  until 3.11, meaning if we wanted to use it we'd have to do something like:

```python
try:
    from typing import sealed
except ImportError:
    # Identity decorator to allow us to gracefully upgrade to sealed on newer
    # python versions.
    def sealed(wrapped: Any):
        return wrapped
```

  This would potentially mean a user upgrading from 3.10 to 3.11 would start
  seeing type check failures even though they haven't updated the library
  or changed any of their code.

* A user might try to use the parent type directly in their own typing with
  some generic type, e.g. `MyUnion[str]`. This could obscure the fact that
  multiple variants of a union may have the same member type and lead to bugs.

* The unknown variant has a `value` property even though it has no value. This
  could lead to bugs if the user expects the value to not be none, as it allows
  them to not deal with the fact that the unknown variant exits.

The only advantage this has over using native unions is the ability to use
isinstance checks on versions prior to 3.10.


# FAQs

## Why not use built-in class subtypes for unions?

Unions can have multiple members targeting the same shape, so there would be
no way to automatically determine what a users intent was if they passed in
the base class. Since they would, therefore, have to always pass in our
concrete types, there would be no advantage to subclassing built-ins.
