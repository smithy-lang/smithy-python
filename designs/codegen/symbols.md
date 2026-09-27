# Native Python Symbols

`smithy_python.symbols` provides `SymbolProvider(model, selection, *, package)` and
frozen, hashable `TypeReference(name, module=None, arguments=(), nullable=False)`.
It uses only the standard library. Pass a loaded Model and its existing Selection;
it does not select shapes again, mutate either input, or generate files.

## Contract

* `declaration_name(id)` names selected structures, unions, enums and intEnums.
  Only these supported declarations occupy `<package>.models`.
* `member_name(member_id)` names structure/union fields or enum/intEnum constants.
  List/map member names are not generated declarations and are rejected.
* `type_reference(id)` resolves a top-level data shape. To resolve a field's type,
  pass its `MemberShape.target`, not its member ID. Requiredness, defaults and
  field optionality are deliberately outside this API.

IDs can be absolute strings or `ShapeId` values. Relative/malformed IDs raise
`InvalidShapeIdError`; missing shapes raise `ShapeNotFoundError`. Unselected
non-prelude shapes, control shapes, mixins, trait definitions, inappropriate
method requests and unsupported types raise `ModelError`. Prelude primitive
references and Unit work without selection. A manually narrowed Selection is
honored: references to omitted non-prelude targets fail rather than widening it.
The Model and Selection must describe the same loaded model.

Package segments must be Python identifiers, not Python 3.12 hard keywords
(including their Unicode NFKC equivalents); invalid packages raise `ValueError`.
The supplied package spelling is preserved. Soft keywords are accepted. No
package is imported or checked for installation.

```python
from smithy_python.model import load_model
from smithy_python.selection import select_shapes
from smithy_python.symbols import SymbolProvider, TypeReference

model = load_model('''{
  "smithy": "2.0",
  "shapes": {
    "example#HTTPServer": {
      "type": "structure",
      "members": {"getURL": {"target": "smithy.api#String"}}
    },
    "example#Servers": {
      "type": "list",
      "member": {"target": "example#HTTPServer"},
      "traits": {"smithy.api#sparse": {}}
    }
  }
}''')
symbols = SymbolProvider(model, select_shapes(model), package="example.client")
assert symbols.declaration_name("example#HTTPServer") == "HttpServer"
assert symbols.member_name("example#HTTPServer$getURL") == "get_url"
assert symbols.type_reference("example#Servers") == TypeReference(
    "list", "builtins",
    (TypeReference("HttpServer", "example.client.models", nullable=True),),
)
```

## Naming and collisions

The selected service's rename is applied to declarations before normalization;
without a service the original shape name is used. IDs, member names in the
model, enum values and wire names are never changed.

Split an uppercase run before its final capital when followed by lowercase;
then split lowercase-or-digit followed by uppercase. Underscores separate words:
empty words are discarded, including leading/trailing underscores. Digits stay
with the preceding word (except the digit-to-capital boundary). Lowercase words
are joined in PascalCase, snake_case or UPPER_SNAKE_CASE. Prefix `_` if the result
starts with a digit. Append `_` for an exact Python 3.12 hard keyword, using a
frozen explicit list, not the interpreter's keyword module. Soft keywords
`match`, `case`, `type`, `_` are not reserved. Special Python names such as
`__init__`, `_name_`, and `__private` lose their underscore wrappers, avoiding
magic methods, enum sunder names and name mangling. Empty or non-ASCII-identifier
rename words fail with the original ID; leading-digit renames are supported.

| Input | Declaration | Field | Enum constant |
| --- | --- | --- | --- |
| HTTPServer | HttpServer | http_server | HTTP_SERVER |
| getURL | GetUrl | get_url | GET_URL |
| HTTP2Server | Http2Server | http2_server | HTTP2_SERVER |
| getURL2Value | GetUrl2Value | get_url2_value | GET_URL2_VALUE |
| __some__name__ | SomeName | some_name | SOME_NAME |
| __init__ | Init | init | INIT |
| class | Class | class_ | CLASS |
| None | None_ | none | NONE |
| match | Match | match | MATCH |

For a leading-digit rename, `2HTTPServer` becomes `_2HttpServer`.

Construction checks supported generated declarations in one module scope and
members in each separate declaration scope, after escaping. A collision raises
`ModelError` with both original IDs and the resulting Python name; the first
conflict follows selection and member order, independent of lookup order.
No numbering, builtin ban, speculative reservations or import-name collision
checks are performed. Primitive aliases and collections have no declarations.
Imported Document and generated Document retain different modules.

## Type references and recursion

`name` and `module` identify a type, `arguments` is an ordered tuple of nested
references, and `nullable=True` means this reference also permits None. The only
provider-produced reference without a module is `TypeReference("None")` for
Unit. There is no arbitrary metadata, import rendering or annotation-string API.

| Smithy type | Symbolic Python type |
| --- | --- |
| boolean | builtins.bool |
| string | builtins.str |
| byte, short, integer, long, bigInteger | builtins.int |
| float, double | builtins.float |
| ordinary blob | builtins.bytes |
| bigDecimal | decimal.Decimal |
| timestamp | datetime.datetime |
| document | smithy_core.documents.Document |
| structure, union, enum, intEnum | `<package>.models.<Declaration>` |
| list | builtins.list with one argument |
| map | builtins.dict with key and value arguments |
| smithy.api#Unit | None |

Ordinary primitive aliases resolve to their underlying type. Sparse lists mark
only the element reference nullable; sparse maps mark only the value reference
nullable, including nested collections. These module names are symbolic strings:
codegen never imports runtime packages.

Named references terminate traversal; self/mutual recursion and recursion through
collections do not create cyclic symbol objects. Collection expansion uses an
iterative postorder worklist with per-call results, not the Python call stack.
Collection-only cycles raise `ModelError` with the cycle IDs, excluding any
noncyclic prefix. Failed lookups cannot
poison subsequent resolutions. Streaming blobs and unions are rejected when
resolved (including through collections), not treated as ordinary types. They
do not reserve declarations at construction. Resolving a named structure does
not inspect its fields; consumers must resolve field targets separately.

No service/operation/resource symbols, writers, CLI integration, schemas,
serializers, dependency tracking, plugins, or runtime dependencies are added.
