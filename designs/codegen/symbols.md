# Native Python symbols

`SymbolProvider` answers three questions for the Python generator:

- What should a generated class or enum be called?
- What should a field or enum constant be called?
- What Python type represents a value?

Pass a loaded model, a selection made from that model, and the destination package:
`SymbolProvider(model, selection, *, package, reserved_member_names=None)`.
The provider does not select more shapes, change the model, import packages, or
write files. It uses only the standard library.

## Names and types

Use full Smithy IDs, such as `example#Response`, or equivalent `ShapeId` objects.
A `$` identifies a member inside a shape: `example#Response$statusCode` is the
`statusCode` field of `Response`.

| Method                                       | Question                                  | Example result                     |
| -------------------------------------------- | ----------------------------------------- | ---------------------------------- |
| `declaration_name("example#Response")`       | What do we call the generated definition? | `"Response"`                       |
| `member_name("example#Response$statusCode")` | What do we call this field?               | `"status_code"`                    |
| `type_reference("smithy.api#Integer")`       | What type of value does it hold?          | `TypeReference("int", "builtins")` |

`declaration_name` names structures, unions, enums and integer enums. Their
future definitions belong in `<package>.models`. Other simple shapes, lists and
maps do not get separate definitions: a list of strings is `list[str]`, not a
new class.

`member_name` names structure/union fields and enum constants. A list's internal
`member` and a map's `key` and `value` describe their contents, not Python fields,
so this method rejects them. A structure field that holds a list still has a
name: `Response$tags` can become `tags: list[str]`.

To find a field's type, pass the shape it points to (`member.target`), not the
field's own ID (`member.id`). Whether the field is required, has a default, or
can be omitted is a separate decision for the future structure generator.

```python
from smithy_python.model import MemberShape, load_model
from smithy_python.selection import select_shapes
from smithy_python.symbols import SymbolProvider, TypeReference

model = load_model('''{
  "smithy": "2.0",
  "shapes": {
    "example#HTTPResponse": {
      "type": "structure",
      "members": {"statusCode": {"target": "smithy.api#Integer"}}
    }
  }
}''')
symbols = SymbolProvider(model, select_shapes(model), package="example.client")
member = model.expect_shape("example#HTTPResponse$statusCode", MemberShape)

assert symbols.declaration_name("example#HTTPResponse") == "HTTPResponse"
assert symbols.member_name(member.id) == "status_code"
assert symbols.type_reference(member.target) == TypeReference("int", "builtins")
```

## Naming rules

Apply the selected service's rename first, if present. Otherwise use the shape's
original name. Python naming never changes Smithy IDs, wire names or enum values.

For class and enum names, remove underscores and uppercase the first character
of each nonempty part, preserving its remaining capitals. Fields use snake_case;
enum constants use UPPER_SNAKE_CASE. Split words at lowercase-or-digit to uppercase
boundaries, and before the last capital of an uppercase run followed by lowercase.

| Input            | Class or enum | Field          | Enum constant  |
| ---------------- | ------------- | -------------- | -------------- |
| `HTTPServer`     | HTTPServer    | http_server    | HTTP_SERVER    |
| `http_server`    | HttpServer    | http_server    | HTTP_SERVER    |
| `getURL`         | GetURL        | get_url        | GET_URL        |
| `HTTP2Server`    | HTTP2Server   | http2_server   | HTTP2_SERVER   |
| `getURL2Value`   | GetURL2Value  | get_url2_value | GET_URL2_VALUE |
| `__some__name__` | SomeName      | some_name      | SOME_NAME      |
| `__init__`       | Init          | init           | INIT           |
| `class`          | Class         | class_         | CLASS          |
| `None`           | None_         | none           | NONE           |
| `match`          | Match         | match          | MATCH          |

Discard empty underscore-separated parts, including leading/trailing underscores.
This avoids Python's special treatment of names such as `__init__` and `__private`.
Append `_` if the result is a reserved Python word. The reserved-word list combines
Python 3.12 through 3.15 so results do not depend on the Python version running
codegen. Update it when adding support for another Python version. Names such as
`match`, `case`, `type` and `lazy` are valid Python field names and do not need a
trailing underscore.

Generators can reserve more member names with `reserved_member_names`, a callable
that receives the containing structure, union or enum and returns the names to
avoid. A generated name in that collection also gets a trailing `_`. Use this for
names the generator adds to classes, such as `serialize` and `deserialize`, or
attributes inherited by error classes. Compare against the final Python spelling:
fields are snake_case and enum constants are UPPER_SNAKE_CASE. Escaped names are
still checked for collisions.

Rename values may contain only ASCII letters, digits and underscores, and must
contain at least one letter or digit. If removing leading underscores would leave
a digit at the start, keep one underscore: `_2HTTPServer` stays `_2HTTPServer`.

When constructed, the provider checks names for every selected, supported
declaration and its members. Invalid renames fail here. Two declarations cannot
have the same Python name in the generated models module; two fields or constants
cannot have the same name within one declaration. A collision raises `ModelError`
with both Smithy IDs and the conflicting name. The first conflict follows model
selection and member order. No numbered suffixes are added to hide collisions.

Union members are currently named only as fields. If unions are generated with a
class for each member or for unknown variants, those classes are declarations in
the models module. The provider must name them and include them in the
declaration collision check. Combining the union and member names is not enough
on its own: Bedrock Agent Runtime defines a `Memory` union with a
`sessionSummary` member and a separate `MemorySessionSummary` structure.

Builtin names such as `list` are allowed unless the generator reserves them. A
field named `list` does not prevent annotations from referring to the builtin;
the writer handles that with import aliases or qualified names. References to
identically named types from different modules also remain distinct.

## Type references

`TypeReference(name, module=None, arguments=(), nullable=False,
dependencies=())` is an immutable, hashable description of a type, not a Python
annotation string. `name` and `module` identify the type. `arguments` holds its
element, key, or value types. `nullable=True` means the value can also be
`None`. `dependencies` contains the package requirements needed to use the
reference.

`module` is the public module users import the type from. Dependency records
supply package names and versions. Module names only control imports. If the
writer later places a definition in a different physical module, that placement
is the writer's concern and does not change the reference. Resolved references
are cached for the provider's lifetime.

For example, `list[str]` is represented as:

```python
TypeReference("list", "builtins", (TypeReference("str", "builtins"),))
```

References to standard-library and generated modules have no dependencies. A
runtime reference such as `smithy_core.documents.Document` carries the
compatible `smithy-core` dependency from the generator's runtime package
catalog. Collection references retain the dependencies of their nested
arguments.

| Smithy type                                     | Python value type                |
| ----------------------------------------------- | -------------------------------- |
| boolean                                         | bool                             |
| string, enum                                    | str                              |
| byte, short, integer, long, bigInteger, intEnum | int                              |
| float, double                                   | float                            |
| ordinary blob                                   | bytes                            |
| bigDecimal                                      | decimal.Decimal                  |
| timestamp                                       | datetime.datetime                |
| document                                        | smithy_core.documents.Document   |
| structure, union                                | `<package>.models.<Declaration>` |
| list                                            | list[T]                          |
| map                                             | dict[K, V]                       |
| smithy.api#Unit                                 | None                             |

`T`, `K` and `V` stand for element, key and value types. References to Python's
built-in types record `"builtins"` as their module; generated annotations can
use the usual short names.

Enums still have named declarations and constants, but their values use `str` or
`int` so fields can hold values added by the service in the future. For example,
`declaration_name("example#Color")` returns `"Color"`, while
`type_reference("example#Color")` returns `TypeReference("str", "builtins")`.
The same rule applies inside collections. Runtime validation and deserialization
are not implemented here.

A sparse list permits `None` elements; a sparse map permits `None` values, not
keys. Each collection controls its own sparseness. An outer sparse list can
contain `None` instead of an inner list without allowing `None` inside that inner
list. The provider uses `nullable` only for these collection entries, not to
decide whether structure fields are optional.

Module names are recorded without importing anything. `Unit`, which represents
no value, is the only result without a module: `TypeReference("None")`.

## Recursion and unsupported shapes

Structures and unions resolve to named references without expanding their
fields. This supports types such as `Node` containing `list[Node]`. Callers
resolve each field's target separately.

Collection expansion does not use Python recursion. A cycle made entirely of
collections, such as two lists containing each other, raises `ModelError` with
the IDs in the cycle. A failed lookup does not affect later lookups.

Streaming blobs resolve to `smithy_core.aio.interfaces.StreamingBlob`, including
when nested in collections. Event-stream unions retain schema names for
protocol integration and do not produce model declarations.

## Inputs and errors

The model and selection must come from the same load; the provider does not
check this precondition. Requests for shapes outside the selection fail rather
than silently adding them. Smithy's built-in types, such as `String`, `Integer`
and `Unit`, remain available without selecting them for generation.

- Malformed or incomplete IDs raise `InvalidShapeIdError`.
- IDs absent from the model raise `ShapeNotFoundError`.
- Unsupported or unselected shapes and invalid method requests raise `ModelError`.
  For example, `type_reference` requires a shape ID, not a member ID;
  `member_name` requires a supported field or constant; `declaration_name`
  requires a generated definition. Services, operations, resources, mixins and
  trait definitions do not have data symbols.

The package is a dotted Python name such as `example.client`. Each part must be
a valid Python identifier and cannot be a reserved word such as `class`.
Alternative Unicode spellings that Python converts to reserved words are also
rejected: `ｃｌａｓｓ` is treated as `class` for this check. Invalid packages raise
`ValueError`. Other accepted spellings are preserved. Names such as `match` are
allowed. The package need not exist or be installed.
