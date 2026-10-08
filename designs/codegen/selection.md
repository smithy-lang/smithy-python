# Service and Data-Shape Selection

Selection follows [model loading](model.md) and precedes generation. The CLI's
[service selection rules](cli.md#service-selection) apply to both artifacts.
`--service` accepts only an absolute, existing, non-member, non-mixin service ID.
Without it, the sole non-mixin service is used; ambiguity lists the candidates
in model order. Clients require a service, while standalone types do not.
These selection failures are invocation errors (exit 2).

## API and traversal

`smithy_python.selection.select_shapes(model, *, service_id=None,
require_service=False)` returns a frozen `Selection` containing the resolved
`service`, a tuple of eligible `shapes`, and `excluded_count`. Clients pass
`require_service=True`. The API has no I/O and reuses the loaded shape objects.
`resolve_service` is also available for consumers needing only resolution.

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

## Types without a service

All eligible data shapes are selected. Names are grouped case-insensitively;
any conflicting groups produce a `ModelError` listing every conflicting ID
(exit 1). Ineligible shapes do not participate. This check is intentionally not
run when a service resolves: Smithy validation is responsible for service name
semantics, and selection is not a general validator or symbol provider.

## Current boundary

Successful selection still reaches the generation-not-implemented diagnostic
(exit 1). No files or output directories are created, and stdout remains clean.
The generator has no new dependencies; selection neither interprets selectors
nor introduces runtime schemas, naming, or writers.
