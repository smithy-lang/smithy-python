# Service and Data-Shape Selection

Selection follows [model loading](model.md) and precedes generation. The CLI's
[service selection rules](cli.md#service-selection) differ by artifact.
`--service` accepts only an absolute, existing, non-member, non-mixin service ID.
Clients infer a sole service when the option is absent. Standalone types use a
service only when the option is explicit. Selection failures are invocation
errors (exit 2).

## API and traversal

`smithy_python.selection.select_shapes(model, *, service_id=None,
require_service=False)` returns a frozen `Selection` containing the resolved
`service`, a tuple of eligible `shapes`, and `excluded_count`. Clients pass
`require_service=True`. The API has no I/O and reuses the loaded shape objects.
`resolve_service` is also available for consumers needing only resolution.

Standalone types use:

```python
select_type_shapes(
    model,
    *,
    service_id=None,
    selector=Selector.identity(),
    generate_inputs_and_outputs=False,
)
```

This function does not infer a service. An explicit service establishes the
initial service closure. Without one, every eligible declaration shape in the
model is an initial candidate.

A service closure uses an iterative worklist and a visited-ID set. Its edges are:

* Service operations, resources, and errors.
* Resource identifiers, properties, create/put/read/update/delete/list,
  operations, collection operations, and child resources.
* Operation input, output, and errors (including implicit Unit).
* Every member target.

The traversal uses flattened semantic relationships, not raw AST fields. Mixin
relationships need not be followed because loading has already inherited their
contents. Trait IDs and node strings, metadata, and service rename entries are
not edges. Cycles terminate and graph depth does not consume the Python stack.

Reachability and eligibility are separate: control shapes can connect data but
are never emitted. Prelude shapes (including Unit), members, services,
operations, resources, mixins, and trait definitions are excluded from output.
Filtering eligible shapes in original model order preserves that order rather
than worklist or sorted order. The excluded count includes only eligible data
shapes outside the closure; the CLI reports it to stderr only when nonzero.

## Standalone types

Standalone types selection proceeds in four stages:

1. Select declaration candidates from an explicit service closure or the
   complete model.
2. Intersect the candidates with the selector result.
3. Exclude input and output structures as roots unless
   `generate_inputs_and_outputs=True`.
4. Add every member-target dependency reachable from the remaining
   declarations.

Declaration candidates are structures, unions, enums, and integer enums.
Prelude shapes, mixins, trait definitions, and shapes marked `@private` are
ineligible. Dependency closure may add simple and collection shapes needed by
schemas and serde. Final shapes retain model order.

Final declaration names are grouped case-insensitively. A conflicting group
produces a `ModelError` listing every conflicting ID (exit 1). Dependency-only
shapes do not participate in this check.

## Selectors

`Selector.parse(source)` builds an immutable syntax tree for the Smithy selector
language. Evaluation uses the loaded semantic model and returns shape IDs.
Parsing occurs once while resolving `TypesSettings`. Selection intersects the
result with eligible declaration candidates and does not reorder either set.

Selector conformance fixtures run the same expressions and models through the
Java and native implementations. The selected shape ID sets must match.

Selection has no output side effects. It returns model objects for generation
and does not construct symbols, schemas, or writers.
