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
| document | Any* (str, int, float, bool, None, dict, list) |

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
    def seek(self, offset: int, whence: int) -> int:
        ...

    def tell() -> int:
        ...
```

The type signature of members targeting blobs with the streaming trait will be
`Union[ByteStream, SeekableByteStream, bytes, bytearray]`.

### mediaType

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

#### Plain dicts

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

## Unions