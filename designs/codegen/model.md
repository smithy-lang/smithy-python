# Semantic Model

The generator's first step converts a Smithy
[JSON AST](https://smithy.io/2.0/spec/json-ast.html) into an in-memory model
that later stages (shape selection, naming, and writers) consume. The model is
defined in `smithy_python.model` and has no dependencies outside the standard
library. In particular, it does not reuse `smithy_core`'s runtime schema types:
the generator needs shape types the runtime does not (such as `member` and
`resource`), and the generator should be installable independently of any runtime
version.

```python
from pathlib import Path

from smithy_python.model import OperationShape, StructureShape, load_model

model = load_model(Path("model.json").read_bytes())

(service,) = model.services()
for operation_id in service.operations:
    operation = model.expect_shape(operation_id, OperationShape)
    request = model.expect_shape(operation.input, StructureShape)
    for name, member in request.members.items():
        target = model.get_target(member)
        print(operation.id.name, name, target.type, member.has_trait("required"))
```

## Loading

`load_model` accepts the JSON AST as bytes, text, or an already-decoded mapping.
The returned model is final: mixins are flattened, `apply` entries are merged,
and the embedded prelude is present. No later stage needs to reinterpret the
AST.

Loading performs only the checks needed to build a well-formed model:

* The document is a JSON object with a Smithy 2.x `smithy` version. Smithy 1.0
  ASTs are rejected rather than loaded with 2.0 semantics, which would silently
  produce a different model. `NaN` and `Infinity` are rejected because they are
  not JSON.
* Every shape has a known type and a valid shape ID, and every member has a
  target.
* Every member target and shape relationship (service, resource, and operation
  properties, mixins, and `apply` targets) resolves to a shape in the model or
  the embedded prelude.
* Mixin cycles, and mixins whose type differs from the shape using them, are
  reported because flattening cannot proceed otherwise.

The loader assumes the model has otherwise been validated by Smithy. It does not
evaluate selectors, validate trait values, run Smithy's built-in validators, or
check for case-insensitive name conflicts. Trait IDs are not resolved as
references, so trait definition shapes need not be present.

Failures raise `ModelError`, a `CodegenError` that the CLI reports with exit code
1.

## Shapes

Every shape is a frozen dataclass with an `id`, a `type`, ordered `traits`, and
ordered `members`. Each shape kind has its own class, so relationships are typed
fields rather than JSON properties:

| Class | Additional fields |
|-------|-------------------|
| `SimpleShape` | None; used for blob, boolean, string, numbers, timestamp, and document. |
| `StructureShape`, `UnionShape` | None |
| `EnumShape`, `IntEnumShape` | None; values are in each member's `smithy.api#enumValue` trait. |
| `ListShape` | `member` |
| `MapShape` | `key`, `value` |
| `MemberShape` | `target`, `container`, `name` |
| `ServiceShape` | `version`, `operations`, `resources`, `errors`, `rename` |
| `ResourceShape` | `identifiers`, `properties`, lifecycle operations, `operations`, `collection_operations`, `resources` |
| `OperationShape` | `input`, `output`, `errors` |

An operation without `input` or `output` reports `smithy.api#Unit`, as in the
Smithy semantic model.

Trait and metadata values are the JSON values from the AST, made deeply
immutable: objects are read-only mappings and arrays are tuples. Values
inherited from a mixin are shared by every shape that uses it, so a mutable
value would let one consumer change another shape's traits. `to_json` returns
a mutable copy, for example to serialize a value. The model does not define
typed trait classes; stages that need a trait interpret its value.

`ShapeId` is a frozen, hashable value with `namespace`, `name`, and an optional
`member`. It sorts by namespace, name, and member. `has_trait` and `get_trait`
accept relative trait names such as `"required"`, which resolve to the
`smithy.api` namespace.

## Order

The model preserves the order of everything in the input, since the order of
generated members, operations, and enum values should follow the model:

* Shapes iterate in AST order, followed by any embedded prelude shapes that the
  AST omitted.
* Members, traits, metadata keys, relationship lists, resource identifiers and
  properties, and service renames keep their AST order.
* Trait and metadata values are not rewritten, so object keys and arrays inside
  them keep their order.

The loader does not sort anything. Smithy's JSON serializer sorts shape IDs and
metadata keys, while member order follows the source model; the model reflects
whichever order it receives.

## Prelude

The loader embeds the prelude shapes that members and relationships can target:
the simple shapes such as `String`, the `Primitive*` shapes with their `default`
traits, and `Unit` with the `unitType` trait. Smithy omits prelude shapes unless
the `run` plugin sets `sendPrelude`, so without this a model could not resolve
`smithy.api#String`. When the AST includes a prelude shape, its definition is
used instead of the embedded one.

Prelude trait definitions are not embedded because trait IDs are not resolved.
`Model.is_prelude` identifies shapes in the `smithy.api` namespace, and
`Model.iter_shapes` skips them unless `include_prelude=True`, since prelude shapes
are never generated. `Model.shapes` contains every shape.

## Mixins and `apply`

Smithy serializes only what each shape introduces, so the loader applies the
[mixin rules](https://smithy.io/2.0/spec/mixins.html) itself. The result matches
Smithy's `flattenAndRemoveMixins` transform, except that mixin shapes remain in
the model. They are identified by `Shape.is_mixin` and are not generated.

* Members inherited from mixins come first, in mixin declaration order, followed
  by local members. Member IDs are rooted at the shape that contains them.
* A local member that redeclares an inherited member keeps the inherited
  position and merges its traits over the inherited traits.
* Shape traits are inherited from each mixin in order, followed by the shape's
  own traits. The `mixin` trait and the traits in its `localTraits` are not
  inherited.
* Service, resource, and operation properties are inherited. Lists and maps are
  merged in order; single values take the most specific definition.
* An `apply` entry merges its traits onto a shape or member, including a member
  that is inherited from a mixin. Traits applied to a mixin or its members are
  inherited by shapes that use it. Array trait values are concatenated as
  Smithy does; other values replace the existing value.

When traits are merged, a trait keeps the position where it was first
introduced and takes the last value written. Its order therefore can differ from
Smithy's serialized output, which sorts traits, while their values match.
