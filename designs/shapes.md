# Abstract

This document will describe how [simple shapes](https://awslabs.github.io/smithy/1.0/spec/core/model.html#simple-shapes)
and [aggregate shapes](https://awslabs.github.io/smithy/1.0/spec/core/model.html#aggregate-shapes)
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
| document | Any* |

*Documents aren't easily representable in Python type hints due to a lack of
support for recursive definitions. See [this issue](https://github.com/python/typing/issues/182)
on the typing repo for more details.

## Trait-influenced shapes

### enum

```python
class EnumWithNames:
    SPAM = "spam"
    EGGS = "eggs"
    SPAM_EGGS = "spam:eggs"

    values = frozenset(SPAM, EGGS, SPAM_EGGS)

class EnumWithoutNames:
    values = frozenset("foo", "bar")
```

Enums are classes with a `values` property that contains an immutable set of
all the possible values of the enum. If the enum is a named enum, static
properties will be generated for each entry as well.

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

### streaming blobs

A blob with the streaming trait will continue to support `bytes` as input.
Additionally, it will support passing in a `ByteStream` which is any class that
implements a `read` method that accepts a `size` param and returns bytes.
Additionally, it will gracefully upgrade if the object is a
`SeekableByteStream`.

Both `ByteStream` and `SeekableByteStream` will be implemented as
[Protocols](https://www.python.org/dev/peps/pep-0544/), which are a way of
defining structural subtyping in Python.

```python
@runtime_checkable
class ByteStream(Protocol):
    def read(self, size: int) -> bytes:
        ...

@runtime_checkable
class SeekableByteStream(ByteStream, Protocol):
    def seek(self, offset: int, whence: int = 0) -> int:
        ...

    def tell() -> int:
        ...
```

The type signature of members targeting blobs with the streaming trait will be
`Union[ByteStream, SeekableByteStream, bytes, bytearray]`.

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

Structures are simple python objects with `asdict` and `fromdict` methods
whose constructors only allow keyword arguments. For example:

```python
class ExampleStructure:
    def __init__(
        self,
        *, # This prevents positional arguments
        required_param: str,
        struct_param: OtherStructure,
        optional_param: Optional[str] = None,
    ):
        self.required_param = required_param
        self.struct_param = struct_param
        self.optional_param = optional_param

    def asdict(self) -> Dict:
        d = {
            "RequiredParam": self.required_param,
            "StructParam": self.struct_param.asdict(),
        }

        if self.optional_param:
            d["OptionalParam"] = self.optional_param

    @staticmethod
    def fromdict(d: Dict) -> ExampleStructure:
        return ExampleStructure(
            required_param=d["RequiredParam"],
            struct_param=OtherStructure.from_dict(d["StructParam"])
            optional_param=d.get("OptionalParam"),
        )
```

Disallowing positional arguments prevents errors from arising when future
updates add additional structure members.

The `asdict` and `from_dict` methods exist primarily to make migration
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
number of other useful methods, like an `asdict` function.

Unfortunately, the generated constructors allow for positional arguments.
Constructor generation can be disabled, and a custom constructer can be
written instead. Still, this immediately starts eating away at the utility
of the decorator.

Similarly, the prebuilt `asdict` function is fairly rigid. There is currently
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

## Errors

Modeled errors are specialized structures that have a `code` and `message`.

```python
# Defined in a shared library, used for all common errors in generic library
# code.
class SmithyError(Exception):
    pass


# This is just an example of a direct implementation of a SmithyError. This
# would also be defined in generic library code.
class HTTPClientError(SmithyError):
    def __init__(
        self,
        error: Exception,
        request: Optional[HTTPRequest] = None,
        response: Optional[HTTPResponse] = None
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

Unions are classes with a typed `value` property grouped by a parent class.

```python
V = TypeVar("V")


@sealed
class MyUnion(Generic[V]):
    value: V


class MyUnionMemberA(MyUnion[bytes]):
    def __init__(self, value: bytes):
        self.value = value


class MyUnionMemberB(MyUnion[str]):
    def __init__(self, value: str):
        self.value = value


class MyUnionUnknown(MyUnion[None]):
    def __init__(self, tag: str, nonparsed_value: bytes):
        self.tag = tag
        self.value = None
        self._nonparsed_value = value
```

This design allows for dispatch based on instance checks. The unknown variant
will only be introduced when referenced by members. This should allow for
completeness checks in match statements. The key to this is `@sealed` which
allows mypy to effectively treat the base class as a union.

```python
def handle_with_instance(my_union: MyUnion):
    if isinstance(my_union, MyUnionMemberA):
        print(value.decode(encoding="utf-8"))
    elif isinstance(my_union, MyUnionMemberB):
        for v in my_union.value:
            print(v)
    else:
        raise Exception(f"Unhandled union type: {my_union.tag}")


# This is only possible at all in python 3.10 and up
def handle_with_match(my_union: MyUnion):
    # Type checkers should see that the MyUnionMemberB isn't accounted for.
    # This implies that updates could cause type checking to fail if there's
    # no default case. There is no way to avoid this, and we wouldn't want to
    # even if we could. This would expose the error at type checking time
    # rather than runtime, which is what we want.
    match my_union:
        case MyUnionUnknown:
            raise Exception(f"Unknown union type: {my_union.tag}")
        case MyUnionMemberA:
            print(value.decode(encoding="utf-8"))
        # A default case could suppress the type check error.
        # case _:
        #    raise Exception(f"Unhandled union type: {my_union.tag}")
```

### Alternative: simple unions

In this alternative, unions are grouped by a `Union` type hint rather than
a parent class.

```python
class MyUnionMemberA:
    tag: Literal["MemberA"] = "MemberA"

    def __init__(self, value: bytes):
        self.value = value


class MyUnionMemberB:
    tag: Literal["MemberB"] = "MemberB"

    def __init__(self, value: List[str]):
        self.value = value


class MyUnionUnknown:
    def __init__(self, tag: str, value: bytes):
        self.tag = tag

        # This has no public accessor property. It's still available if you
        # *really* want it, but it is understood that since it starts with
        # an underscore you shouldn't use it and expect to not be broken.
        self._nonparsed_value = value


# This syntax will be introduced in 3.10, and it will crucially allow
# isinstance checks to perform as you would expect.
MyUnion = MyUnionMemberA | MyUnionMemberB
MyUnionOrUnknown = MyUnion | MyUnionUnknown


class SampleStruct:
    def __init__(self, *, union_member: MyUninionOrUnknown):
        self.union_member = union_member
```

In python 3.10+ this is only subtly different than using sealed classes. It has
the advantage of allowing explicitly removing the unkown variant and passing
that along so that it only needs to be checked once. However, the isinstance
check wouldn't work in versions prior to 3.10 and it isn't terribly idiomatic.

Another potential advantage is that this makes tag-based dispatch easy:

```python
def handle_with_tag_equality(my_union: MyUnion):
    # Dispatch can be handled via tags, but to do so the unknown variant MUST
    # be eliminated first.
    if isinstance(my_union, MyUnionUnknown):
        raise Exception(f"Unknown union type: {my_union.tag}")

    if my_union.tag == "MemberA":
        print(value.decode(encoding="utf-8"))
    elif my_union.tag == "MemberB":
        for v in my_union.value:
            print(v)
    else:
        # Known but unhandled members still need to be dealt with.
        raise Exception(f"Unhandled union type: {my_union.tag}")
```

However, this makes it a little too easy to hit an unknown variant on accident
or on purpose. It would also be easy to misspell a tag value in these checks,
which may never be caught if the unknown variant wasn't eliminated early.

# FAQs

## Why not use built-in class subtypes for unions?

Unions can have multiple members targeting the same shape, so there would be
no way to automatically determine what a users intent was if they passed in
the base class. Since they would, therefore, have to always pass in our
concrete types, there would be no advantage to subclassing built-ins.
