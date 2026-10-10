# Python-Native Generated Package Architecture

The Python generator emits clients and types packages that use the existing
Smithy Python runtime. Generated packages preserve the public behavior of the
Java generator while loading schemas and model partitions on demand.

## Goals

* Generate clients and standalone types packages from the semantic model in
  `smithy_python.model`.
* Preserve supported generated package APIs during migration from the Java
  generator.
* Avoid constructing user-defined schemas while importing a generated client.
* Use dense member indexes in generated serialization and deserialization.
* Preserve one runtime `Schema` instance for each generated shape.
* Support recursive shape graphs and free-threaded Python.
* Let protocol and platform integrations add generation behavior without
  replacing the core generator.
* Measure generation time, import cost, first-use cost, memory, and warm serde
  throughout development.

## Scope

The first implementation supports standalone types and Rest JSON clients.
Later changes add the remaining protocols after their runtime behavior passes
the existing protocol tests.

The Java generator remains available during migration. A projection selects
which generator to run, so generated packages can move independently after
their required features reach parity.

Server generation, custom model validation, and runtime compilation of serde
functions remain future work. Generated dataclasses retain their current
non-slotted layout until compatibility tests and benchmarks support changing
it.

## Performance Gates

The benchmark suite records these measurements for equivalent Java-generated
and Python-generated packages:

* Code generation wall time and peak resident memory.
* Generated source size and compiled bytecode size.
* Package, models, config, and client import time.
* Client construction time.
* First serialization and deserialization time.
* Warm serialization and deserialization time.
* Peak allocations for first use and warm serde.

Rest JSON provides the first comparison. Rest XML and RPC v2 CBOR join the
suite when the native generator supports them.

Each measured serde case uses the same model, values, payload, warmup count,
and measured iteration count for both generators. Benchmark output includes
the interpreter version, platform, architecture, and generator commit.

The implementation must satisfy these behavioral gates:

* Importing the generated client constructs no user-defined shape schemas.
* Importing a model class constructs no schema until its `schema()` method or
  an operation that uses it is accessed.
* Repeated calls to a shape's `schema()` method return the same object.
* Generated serde contains no string-keyed member schema lookup.
* Warm Rest JSON p50 may not regress by more than 5 percent against the Java
  generator for the same benchmark case. A larger regression blocks migration
  for that case.

Cold-start measurements establish a baseline before the first client migrates.
The design uses behavioral gates for schema loading because host load and
filesystem state make a single import-time percentage unstable.

## Generator Architecture

The generator uses the existing model loader, service selection, CLI, and
plugin environment:

```text
Smithy JSON AST
       |
       v
semantic model
       |
       v
shape selection
       |
       v
generation context
       |
       +------> core generators
       |
       +------> protocol and platform integrations
       |
       v
generated package
```

The proof of concept supplies initial implementations for symbols, writers,
generation context, plugins, models, schemas, clients, and protocol tests.
Those components are ported onto the current semantic model. The repository's
current model loader, shape selection, CLI, and environment handling remain
authoritative.

### Generation Context

One generation context owns:

* The semantic model and selected service.
* Selected shapes in model order.
* Shape and member indexes.
* Symbols and generated names.
* Protocol and platform integrations.
* Dependency and generated-file manifests.
* Schema dependency components and source partitions.

The context builds indexes once. Generators query those indexes instead of
rescanning every selected shape for each output file.

### Symbols

The symbol provider maps semantic shapes and members to Python names, module
paths, runtime dependencies, schema accessors, serializer functions, and
deserializer functions.

Symbol results are cached by shape ID for the duration of one generation.
Member indexes are assigned once from the selected model order and reused by
schema generation and serde generation.

Plugins may decorate symbols or supply symbols for integration-owned types.
The core provider remains responsible for collision handling and service
renames.

### Integrations

An integration declares the protocols and platform behavior it supports. It
can contribute:

* Protocol construction.
* Runtime dependencies.
* Generated config fields and defaults.
* Client plugins.
* Traits retained in runtime schemas.
* Code sections in generated files.

Integrations operate on the semantic model and generation context. Generated
packages depend on the Smithy runtime packages and exclude `smithy-python`.

### Writers

Writers collect imports, generated sections, and file contents in memory. The
file manifest writes changed files and removes stale generated files within
the output directory.

Formatting and linting run after generation when requested. Tests exercise the
unformatted writer output as valid Python so formatting cannot hide syntax
errors.

## Generated Package Layout

Generated packages expose stable public modules and place partition details
under `_private`:

```text
example_service/
    __init__.py
    client.py
    config.py
    models.py
    py.typed
    _private/
        operations.py
        models_0.py
        models_1.py
        schemas_0.py
        schemas_1.py
```

Source partitions start with a target size of 128 KiB. The generator estimates
partition size from rendered declarations. The threshold is an implementation
setting, and benchmarks may change it.

Private module names and partition assignments are unstable. Public model,
client, and config imports remain stable across regenerations.

## Public Model Facade

`models.py` exposes generated model classes, enums, unions, and operation
constants. Runtime imports resolve an exported name on first access:

```python
from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._private.models_0 import GetObjectInput as GetObjectInput
    from ._private.models_1 import GetObjectOutput as GetObjectOutput

_EXPORTS = {
    "GetObjectInput": ("._private.models_0", "GetObjectInput"),
    "GetObjectOutput": ("._private.models_1", "GetObjectOutput"),
}


def __getattr__(name: str) -> Any:
    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, symbol_name = export
    value = getattr(import_module(module_name, __package__), symbol_name)
    globals()[name] = value
    return value
```

Caching the resolved value in the module makes later access a normal global
lookup. `TYPE_CHECKING` imports expose concrete symbols to static type checkers
without importing model partitions at runtime.

`__all__` lists the public generated names. `__dir__` combines those names with
the module globals so interactive discovery remains available before
resolution.

## Model Partitions

Model partitions contain dataclasses, enums, union variants, and their
generated serde helpers. The generator builds a dependency graph from runtime
model references and groups strongly connected components before assigning
partitions.

Postponed annotations remove runtime imports needed only for type hints.
Cross-partition imports needed by serde occur through private accessors and
are cached after first use.

Generated dataclasses keep keyword-only constructors, modeled defaults,
sensitive-member representation, and the existing serialization interfaces.
Modeled errors retain their service error hierarchy.

## Lazy Schema Partitions

Schema construction is lazy at the shape level. Each schema partition stores
completed schemas in a dense array indexed by constants generated for that
partition:

```python
_SCHEMAS: list[Schema | None] = [None] * 24
_LOCK = RLock()

_GET_OBJECT_INPUT = 7
```

The warm path performs one array lookup and one `None` check.

### Dependency Components

The generator builds a directed graph from each schema to its member targets.
It computes strongly connected components and treats each component as one
initialization unit.

An acyclic shape forms a component of one. Mutually recursive shapes share a
component. Components form a directed acyclic graph, which gives schema
initialization a stable dependency order.

A recursive component is never split across source partitions.

### Component Initialization

A component builder creates every root schema in the component before it
creates member schemas:

```python
def _build_component_3() -> None:
    node = Schema.collection(
        id=ShapeID("example#Node"),
        members={"value": None, "next": None},
    )

    node.members["value"] = Schema.member(
        id=node.id.with_member("value"),
        target=STRING,
        index=0,
    )
    node.members["next"] = Schema.member(
        id=node.id.with_member("next"),
        target=node,
        index=1,
    )

    _SCHEMAS[_NODE] = node
```

The public accessor uses a double-checked cache lookup:

```python
def get_node_schema() -> Schema:
    schema = _SCHEMAS[_NODE]
    if schema is not None:
        return schema

    with _LOCK:
        schema = _SCHEMAS[_NODE]
        if schema is None:
            _build_component_3()
            schema = _SCHEMAS[_NODE]
            assert schema is not None
        return schema
```

The component lock remains held until every schema in the component is
complete. Another thread sees an empty cache slot, waits for the lock, and
then reads the completed schema. The builder assigns cache slots only after
all roots and members in the component are complete.

Cross-component dependencies resolve before the current component is
published. The component graph has no cycles, so initialization cannot recurse
back into an unpublished component.

If construction raises an exception, the cache slots remain empty. A later
call can retry construction.

### Shape Schema API

Generated shapes expose a static `schema()` method:

```python
_NODE_SCHEMA: Schema | None = None
_NODE_MEMBERS: tuple[Schema, ...] | None = None


def _node_schema() -> Schema:
    global _NODE_SCHEMA, _NODE_MEMBERS

    if (schema := _NODE_SCHEMA) is None:
        from .schemas_0 import get_node_schema

        schema = get_node_schema()
        _NODE_MEMBERS = schema.members_by_index
        _NODE_SCHEMA = schema
    return schema


def _node_members() -> tuple[Schema, ...]:
    members = _NODE_MEMBERS
    if members is None:
        _node_schema()
        members = _NODE_MEMBERS
        assert members is not None
    return members


class Node:
    @staticmethod
    def schema() -> Schema:
        return _node_schema()
```

The schema belongs to the modeled shape. It does not vary by Python subclass,
so the method uses `staticmethod`. A class method could create
subclass-specific caches and schema identities.

The model partition caches the member tuple with the root schema. Generated
serde reads that tuple and does not query the name-keyed member map.

### Schema Identity and Extensions

Each shape accessor resolves to one canonical `Schema`. Operations, model
classes, type registries, protocols, and codecs share that object.

Schema extensions remain lazy and schema-local. HTTP binding metadata, codec
metadata, and future extension values therefore survive across client and
protocol instances after first use.

Generated code never wraps a schema in a lazy proxy. A proxy would change
schema identity and add resolver work to every attribute access.

## Generated Serialization

Structure serialization uses generated member access and dense schema indexes:

```python
def serialize_members(self, serializer: ShapeSerializer) -> None:
    members = _node_members()
    serializer.write_string(members[0], self.value)
    if self.next is not None:
        serializer.write_struct(members[1], self.next)
```

`_node_members()` initializes the shape schema on its first call and returns
the cached tuple afterward.

Generated serialization retains modeled nullability, sparse collection
behavior, timestamp formats, streaming members, and event stream handling.
Protocol-specific routing remains in runtime protocol packages. For example,
the HTTP binding serializer uses the schema's cached HTTP binding extension
while the generated structure writes members in modeled order.

Collection serializers cache their `member`, `key`, and `value` schemas by
index. Union variants cache their variant member schema.

## Generated Deserialization

Structure deserialization uses a slotted callable object as mutable state:

```python
class _NodeDeserializer:
    __slots__ = ("value", "next")

    def __init__(self) -> None:
        self.value: str | None = None
        self.next: Node | None = None

    def __call__(
        self, member: Schema, deserializer: ShapeDeserializer
    ) -> None:
        match member.expect_member_index():
            case 0:
                self.value = deserializer.read_string(member)
            case 1:
                self.next = Node.deserialize(deserializer)

    def build(self) -> Node:
        return Node(value=self.value, next=self.next)
```

`deserialize()` allocates one state object, passes it directly as the member
consumer, and calls `build()`:

```python
@classmethod
def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
    state = _NodeDeserializer()
    deserializer.read_struct(_node_schema(), state)
    return state.build()
```

Member indexes select generated cases, and fixed attributes store decoded
values. The primary path allocates one state object for each structure.

The state initializer applies modeled defaults. Required members use a private
missing sentinel and `build()` reports an absent required value. Mutable
defaults are created for each state object.

`deserialize_kwargs()` remains available for compatibility. It uses the same
state object and creates a dictionary only when a caller invokes that method.
The primary `deserialize()` path constructs the model directly.

Union deserializers use one result slot and reject multiple values. List and
map deserializers use slotted callable state objects that retain the target
collection and cached member schemas.

The first implementation keeps the existing `ShapeDeserializer` interface.
A state-parameter overload may replace callable state objects after every
official codec supports it and benchmarks show a gain.

## Operations and Client Imports

Operations resolve on first use from a dense module cache:

```python
_OPERATIONS: list[APIOperation[Any, Any] | None] = [None] * 18
_OPERATION_LOCK = Lock()
_GET_OBJECT = 4


def get_get_object_operation() -> APIOperation[Any, Any]:
    operation = _OPERATIONS[_GET_OBJECT]
    if operation is None:
        with _OPERATION_LOCK:
            operation = _OPERATIONS[_GET_OBJECT]
            if operation is None:
                operation = APIOperation(
                    input=GetObjectInput,
                    output=GetObjectOutput,
                    schema=get_get_object_schema(),
                    input_schema=GetObjectInput.schema(),
                    output_schema=GetObjectOutput.schema(),
                    error_registry=_get_get_object_error_registry(),
                    effective_auth_schemes=_GET_OBJECT_AUTH,
                    error_schemas=_get_get_object_error_schemas(),
                )
                _OPERATIONS[_GET_OBJECT] = operation
    return operation
```

The client imports model types under `TYPE_CHECKING` for annotations. Each
operation method imports its private operation getter and caches the resolved
operation through the operations module.

Importing `client.py` loads client infrastructure and config types. It does not
load model or schema partitions. Calling one operation loads that operation's
input, output, errors, and reachable schema components.

Error registries import modeled error classes when their operation initializes.
Receiving an unknown error does not require loading unrelated modeled errors.

## Runtime Trait Retention

The native generator retains traits consumed by runtime packages and generated
SDK metadata. Core generation and integrations register the trait IDs they
need.

The retained set includes traits used by:

* Generic schema and validation behavior.
* Serialization and document codecs.
* HTTP binding and protocol framing.
* Authentication, endpoints, checksums, and retries.
* Generated SDK metadata.

Plugins can add retained trait IDs. Generated docstrings contain documentation
traits, while runtime schemas omit them. Trait definitions and test traits are
excluded from runtime schemas unless an integration registers them.

Trait filtering reduces generated source size, import parsing, schema
construction, and retained memory. The native and Java generators must expose
the same runtime traits before a client migrates.

## Compatibility

The native generator preserves:

* Public package, model, client, and config module paths.
* Generated model names and member names.
* Keyword-only structure constructors.
* Modeled defaults and nullability.
* Enum and union behavior.
* Modeled error inheritance.
* `serialize()`, `serialize_members()`, `deserialize()`, and
  `deserialize_kwargs()`.
* Public operation constants through the models facade.
* Canonical schema identity within one generated package.

Private partition paths and helper names are implementation details.

Generated source need not match Java-generated source. Protocol behavior,
public Python behavior, and type-checker behavior define parity.

## Testing

### Generator Tests

Generator unit tests cover:

* Symbol and member naming.
* Service renames and collisions.
* Partition boundaries.
* Strongly connected component assignment.
* Trait retention.
* Plugin ordering and code sections.
* Stale-file removal.

Golden tests inspect generated source for lazy imports, dense member access,
and stable public exports.

### Generated Package Tests

Each generated fixture must:

* Compile with the supported Python versions.
* Pass Ruff formatting and lint checks.
* Pass strict Pyright checks.
* Import through every public module.
* Serialize and deserialize recursive shapes.
* Preserve schema identity across model, operation, and registry access.
* Initialize recursive schemas safely from concurrent threads.

Import tests instrument `Schema` construction and assert the lazy-loading
gates from this design.

### Protocol Tests

The existing Smithy protocol tests run against native-generated clients. The
Java generator continues to produce its snapshots during migration so
behavioral differences remain visible.

Each protocol moves only after its required request, response, error, streaming,
and event stream tests pass.

## Rollout

Implementation proceeds in these stages:

1. Port generation context, symbols, writers, plugins, and package setup onto
   the current semantic model.
2. Generate standalone types with partitioned models and lazy schemas.
3. Add dense generated serialization and deserialization.
4. Generate Rest JSON clients and protocol tests.
5. Add AWS platform behavior required by the Rest JSON test services.
6. Add Rest XML, RPC v2 CBOR, AWS JSON, AWS Query, and EC2 Query support.
7. Compare each protocol against the Java generator and migrate projections
   independently.

Each stage includes its benchmark results. Performance regressions remain
local to the stage that introduced them.

## Tradeoffs

Lazy construction moves schema work from import time to the first operation
that reaches a shape. Applications that invoke an operation immediately still
pay the construction cost, but applications importing a large client for a
small operation avoid unrelated schema work.

Partitioning adds private modules and lazy export machinery. It reduces Python
source compiled during common imports and keeps the public module layout
stable.

Dense indexes depend on generated member order. Regeneration may assign a
different index after a model change. Indexes remain private to one generated
artifact and are never serialized or exposed as a compatibility contract.

The component lock adds synchronization to a schema cache miss. Cache hits do
not acquire the lock.

Callable deserialization state allocates one object for each aggregate value.
It avoids the closure and dictionary allocations in the proof of concept while
preserving the public deserializer interface.

## Alternatives

### Rebase the Proof of Concept

The proof of concept predates the current semantic model, selection rules, and
CLI behavior. Rebasing it would replace tested model code and mix generator
work with model regressions. Porting generator components keeps those concerns
separate.

### Eager Monolithic Schemas

One schema module is easy to generate, but importing any model constructs the
entire reachable schema graph. Large services pay that cost before selecting
an operation.

### One File per Shape

One file per shape maximizes import granularity but creates thousands of files
for large services. Partitioning captures most import savings with lower
filesystem and wheel overhead.

### Lazy Schema Proxies

A proxy can defer schema construction without changing generated call sites.
It changes runtime type and identity behavior and adds resolution to schema
attribute access. Concrete schemas with lazy accessors keep the hot path
direct.

### Class Methods for Schema Access

A class method receives the concrete Python subclass and can create a separate
cache entry for it. Smithy schema identity belongs to the modeled shape, so a
static method provides the required ownership.

### Dictionary-Based Deserialization

Collecting member values in a dictionary preserves keyword construction with
little generated code. It hashes a string for each decoded member and expands
the dictionary during construction. Generated index dispatch and slotted state
avoid that work.

### Slotted Public Models

Slotted dataclasses reduce instance memory and can speed attribute access. They
remove `__dict__` and restrict subclass behavior, which changes observable
Python behavior. A later design can adopt slots after compatibility review and
benchmarks.

## Future Work

* Add a state-parameter deserializer API if it outperforms callable state across
  JSON, XML, CBOR, and HTTP binding paths.
* Precompute validation masks and constraint metadata used during every
  structure decode.
* Generate endpoint rule bytecode from normalized endpoint rules.
* Support incremental generation from a prior manifest.
* Evaluate partition thresholds on large AWS service models.
* Evaluate slotted generated models as a new artifact compatibility mode.
