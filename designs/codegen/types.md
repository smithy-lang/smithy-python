# Standalone Types Generation

## Abstract

The native generator can load a Smithy model, select shapes, resolve Python
symbols, and write one Python module in memory. It does not yet coordinate
generators or write an artifact.

This design adds artifact settings, a generation context, output management,
and the first complete `types` generation path. The generated package preserves
the public behavior of the Java-generated package it replaces. It reuses the
compact schema representation introduced in
[PR #841](https://github.com/smithy-lang/smithy-python/pull/841) and the lazy
client model representation introduced in
[PR #851](https://github.com/smithy-lang/smithy-python/pull/851). The
implementation also carries forward the code-size and runtime performance work
already present in smithy-java and smithy-php.

## Goals

* Generate an importable standalone types package through
  `smithy-python generate types`.
* Reuse the loaded model, selection, symbol provider, and writers across the
  complete generation.
* Preserve the current generated package's public modules, declarations,
  constructor behavior, schema semantics, and serde behavior.
* Preserve the compact encoding and lazy hydration from PR #841.
* Apply the lazy model construction from PR #851 to standalone types.
* Bound repeated model analysis, symbol resolution, and writer work.
* Produce deterministic output on every supported generator host.
* Validate every generated file before modifying the output directory.
* Keep the generation context and output APIs reusable by later artifacts.

The first implementation does not generate a client, resolve a protocol, or add
protocol integrations. It does not change `smithy-core` schema or model runtime
APIs.

## Compatibility

The Java generator remains the compatibility reference until the native
generator replaces it for an artifact. Source formatting does not need to
match. Generated package behavior does.

| Area | Required behavior |
| --- | --- |
| Package | Preserve the configured package name, version, metadata, and runtime dependencies. |
| Public modules | Preserve import paths such as `<package>.models`. |
| Models | Preserve declaration names, field names, constructor signatures, defaults, error inheritance, enum values, and union variants. |
| Schemas | Preserve shape IDs, shape types, traits, member order, member indexes, and targets. |
| Serde | Preserve generated and runtime serialization and deserialization behavior. |
| Typing | Generated packages must pass strict Pyright checks and expose the same public types. |
| Runtime support | Generated packages depend on handwritten runtime packages, not `smithy-python`. |

PR #851 changed Java-generated client packages to build model classes on demand
through `ModelRegistry` and declare the static surface in `models.pyi`.
Java-generated standalone types packages still emit model declarations into
Python source.

The native generator applies the PR #851 representation to standalone types.
An explicit import such as `from example.models import Widget` returns a class
with the same public name, module, fields, constructor, and serde behavior. The
class is cached after first access, so later imports and attribute reads return
the same object.

The lazy facade preserves explicit imports, star imports, `dir(models)`, class
identity, dataclass inspection, and pickling by module and qualified name.
Concurrent first access returns one class object. Packages generated without a
service still provide `ServiceError` and use it as the base of modeled errors.

The generated stub is the static typing contract. Runtime classes populate
field names in `__annotations__` for dataclass behavior, but annotation object
identity and `typing.get_type_hints()` output are not compatibility contracts.
Lazy construction also changes when declarations enter `models.__dict__` and
when class construction errors occur. Direct inspection of `models.__dict__`
is not part of the generated API compatibility contract.

Files under `_private` are not public API. The native generator may change their
layout if generated public modules and runtime behavior stay compatible.

Existing generated packages continue to work with their declared runtime
dependencies. Enabling the native generator changes build-time tooling and does
not require users to regenerate other packages.

## Pipeline

Generation uses one explicit pipeline:

```text
process inputs
    |
    v
artifact settings
    |
    v
model loading and shape selection
    |
    v
generation plan and symbol provider
    |
    v
artifact generator
    |
    v
registered writers and text files
    |
    v
staged validation and output commit
```

The CLI selects the artifact generator. Artifact generators share the context
and output APIs but control their own generation phases. The first version does
not copy smithy-java's directed codegen lifecycle. A fixed lifecycle would add
extension points before the native generator has a second artifact that needs
them.

## Settings

`ArtifactSettings` contains settings shared by generated artifacts:

```python
@dataclass(frozen=True, slots=True)
class ArtifactSettings:
    module: str
    module_version: str
    module_description: str | None


@dataclass(frozen=True, slots=True)
class TypesSettings(ArtifactSettings):
    selector: Selector = field(default_factory=Selector.identity)
    generate_inputs_and_outputs: bool = False
```

The resolved service remains on `Selection`. It is not duplicated in settings.
The CLI subcommand identifies the artifact, so settings do not duplicate that
value. Artifact-specific settings extend the shared frozen dataclass.

The `types` command initially adds:

* `--module`
* `--module-version`
* `--module-description`
* `--selector`
* `--generate-inputs-and-outputs`

`module` and `module-version` are required. The module follows the validation
rules in `SymbolProvider`. The description defaults to
`"<module> types package"`.

The selector setting is parsed once into an immutable selector syntax tree.
The native parser and evaluator implement the Smithy selector language and
produce the same selected shape IDs as Java's `Selector.parse()` and
`Selector.select()`.

Types generation never infers a service. The options apply in this order:

1. An explicit `--service` establishes the service closure. Without it, every
   eligible declaration shape is a candidate.
2. `--selector` narrows those declaration shapes. The default identity selector
   keeps every candidate.
3. Input and output structures are removed as roots unless
   `--generate-inputs-and-outputs` is set.
4. Member-target dependencies of the remaining declarations are added
   transitively.

Filtering the final closure in model order keeps output deterministic. Name
collision checks run against the final declaration set.

Invocation through the Smithy `run` plugin and environment-variable precedence
follow the [Code Generator CLI](cli.md). Projection transforms remain
supported, but do not replace settings compatibility.

Unknown settings and invalid combinations fail before output is created.

## Generation Context

`GenerationContext` contains the state shared by one artifact generation:

```python
@dataclass(frozen=True, slots=True)
class GenerationContext[SettingsT: ArtifactSettings]:
    model: Model
    selection: Selection
    settings: SettingsT
    symbols: SymbolProvider
    plan: GenerationPlan
    dependencies: DependencySet
    files: FileManifest
```

The context is constructed once after model loading and selection. Generators
receive the context directly. They do not reload the model, construct their own
symbol providers, or inspect files written by another generator.

`TypesGenerator` receives `GenerationContext[TypesSettings]`. Later artifacts
can define their own settings subclasses without casts or a shared union of
artifact settings.

`GenerationPlan` stores derived model data used by more than one emitter:

* Selected shape IDs.
* Shapes grouped by kind in stable model order.
* Topologically ordered and recursive schema shapes.
* Schema constant names.
* Interned schema strings.
* Model declaration names and rename mappings.
* Union variant and unknown-class names.

Planning uses iterative graph algorithms so model depth does not consume the
Python stack. Each index is computed once. The symbol provider continues to
cache resolved `TypeReference` values.

The plan contains semantic data, not rendered source. Emitters can partition
files later without recomputing shape relationships.

## Dependencies

Generated imports and package requirements use the same dependency record:

```python
@dataclass(frozen=True, slots=True)
class Dependency:
    package: str
    specifier: str
    group: Literal["runtime", "build", "test", "docs"]
    extras: tuple[str, ...] = ()
```

These records live in `smithy_python.dependencies` so symbols, writers, and
package generation share one representation.

`TypeReference` gains a tuple of dependencies. `PythonWriter` records
dependencies from every reference it writes. Emitters call
`DependencySet.add()` for requirements that have no matching Python reference,
such as the generated package's build backend.

`DependencySet` keys entries by package and group. Repeated entries must use the
same version specifier. The set merges and sorts extras, then fails on a
specifier conflict. Package setup reads this set after all emitters finish.
This matches the dependency flow used by the Java generator without inferring
package versions from import names. Build dependencies render under
`[build-system].requires`. Runtime dependencies render under
`[project].dependencies`.

The generator owns a catalog of compatible Smithy runtime packages. The
`smithy-core` requirement selected by that catalog must support the compact
schema encoding emitted by the generator.

## Artifact Generators

An artifact generator has one method:

```python
class ArtifactGenerator[SettingsT: ArtifactSettings](Protocol):
    def generate(self, context: GenerationContext[SettingsT]) -> None: ...
```

The CLI maps `types` to `TypesGenerator`. Unknown artifacts fail during argument
parsing. `TypesGenerator` implements
`ArtifactGenerator[TypesSettings]`.

`TypesGenerator` runs these phases:

1. Emit schemas.
2. Emit model declarations and serde adapters.
3. Emit package initialization and typing metadata.
4. Emit package metadata and documentation.

Each phase records output in `FileManifest`. No phase writes directly to disk.
After generation, the CLI asks the manifest to stage, validate, and publish the
artifact.

## Output Management

`FileManifest` owns every file produced by one generation:

```python
class FileManifest:
    def python_module(self, path: str, module: str) -> PythonWriter: ...
    def text_file(self, path: str, content: str) -> None: ...
    def commit(self, output: Path) -> None: ...
```

Paths are relative POSIX paths. Absolute paths, empty components, `.` and `..`
are rejected. Two generators cannot claim the same normalized path.

`python_module` returns the same writer when the same path and module are
requested again. A second request with a different module fails. This supports
separate emitters contributing to one module without creating separate import
planners.

Commit uses a temporary staging directory adjacent to the output directory:

1. Validate every registered path and create the staging directory.
2. Render, validate, hash, and stage one file at a time.
3. Publish current files, reconcile stale owned files, and write the artifact
   manifest last.

The rendered string is released after its staged file is written. Peak rendered
source memory is bounded by the largest output file instead of the complete
artifact. Validation compiles Python modules and checks text-file invariants. A
syntax, import-planning, or staging error removes the staging directory and
leaves the existing output untouched.

Publication uses `os.replace` for each file. Individual files are atomic, but
the complete directory update is not. The configured output directory must not
be modified by another generator during commit.

The output directory contains a generated artifact manifest with normalized
paths and content hashes. On a later run, the generator may delete a stale file
only when the previous manifest owns it and its content still matches the
recorded hash. Modified generated files and files absent from the manifest are
retained. This follows the output ownership used by smithy-php.

The first native run over an output directory without a manifest does not
delete files. Builds that switch from Java generation should use a clean output
directory until native ownership has been established.

The Smithy `run` plugin output restriction still applies. Symlinks or resolved
ancestors that escape the output root are rejected.

## Schema Emission

The native generator emits the compact schema format introduced in PR #841 in
`<package>._private.schemas`.

Each generated schema is module-level immutable data:

```python
WIDGET: StaticSchema = (
    ShapeType.STRUCTURE.value,
    "example",
    "Widget",
    0,
    ("name",),
    ((ShapeType.STRING.value, 1),),
)
```

The actual output uses integer shape types, trait bit vectors, interned strings,
and the tuple layout accepted by `smithy_core._schema_compact`. The example is
expanded for readability.

### Compact Encoding Contract

The generator and runtime share a versioned compact encoding contract without
adding a runtime dependency from `smithy-python` to `smithy-core`.

One generator module owns:

* The encoding version.
* Shape tuple slots and arity.
* Shape type integers and prelude sentinels.
* The ordered trait bit table.
* Trait filtering and value encoding rules.

`smithy_core._schema_compact` exposes the matching private encoding version.
Generated tuples do not include a version field. A change to tuple layout,
shape type integers, prelude sentinels, or trait bit positions increments the
version and requires a coordinated `smithy-core` dependency update.

Trait planning applies the Java generator's `SchemaTraitFilterIndex` rules to
each emitted data shape. The native and Java generators must emit the same
trait IDs and values for the same model. Input and output traits are synthesized
under the same conditions. A schema uses the integer trait bit vector only when
every present trait is represented by a valueless bit. Otherwise it emits the
complete trait mapping.

The emitter preserves these properties:

* Importing the schema module does not construct `Schema` objects.
* `hydrate` constructs each connected schema graph on first use and caches it.
* Prelude targets use integer sentinels instead of duplicate schema data.
* Repeated namespaces, names, trait IDs, and string trait values use module
  constants.
* Valueless two-state traits use a bit vector.
* Members use model order and receive dense indexes from zero.
* References to schemas already emitted use direct tuple references.
* Forward and recursive references use thunks.

Schema ordering is computed once from the selected model. Non-recursive shapes
use topological order. Strongly connected components follow in stable model
order. The emitter must produce the same member order and schema semantics as
the Java generator even when its private constant names differ.

## Model Emission

Standalone types adopt the lazy client model representation from PR #851:

* `models.py` contains a `ModelRegistry` and module `__getattr__`.
* `models.pyi` declares the complete typed surface.
* The generated registry receives its schema constant index, rename map, and
  complete shape-name set.
* `models.py` computes `__all__` from the public model index.
* Resolving one model does not scan or hydrate every schema.
* A reentrant lock protects first construction and the class cache.
* Runtime classes report `<package>.models` as their module and use a stable
  qualified name.
* `__dir__` returns module globals and generated names without constructing
  classes.

The generated stub declares structures, modeled errors, enums, integer enums,
union variants, unknown union variants, and serde methods. Static tooling does
not import or hydrate runtime classes to discover this surface.

`ModelRegistry` attaches the same constructor defaults, field metadata, error
inheritance, enum values, union behavior, and serde methods that concrete
generated declarations provide.

The module computes `__all__` instead of emitting a literal list of unresolved
model names:

```python
_MODEL_NAMES = tuple(_MODEL_INDEX)
__all__ = ("ServiceError", *_MODEL_NAMES)


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
```

This keeps Ruff from reporting `F822` for lazy exports. Star imports read
`__all__` and resolve each model through module `__getattr__`. Computing
`__dir__` from the index does not construct model classes.

Model member access uses the schema's dense member indexes where positional
dispatch is required. Name maps remain dictionaries where lookup is by a wire
or Python name. The generator does not replace sparse name lookups with arrays
that require an additional name-to-index lookup.

## Package Files

The first complete `types` artifact contains:

* `pyproject.toml`
* `README.md`
* `src/<package>/__init__.py`
* `src/<package>/models.py`
* `src/<package>/models.pyi`
* `src/<package>/_private/__init__.py`
* `src/<package>/_private/schemas.py`
* `src/<package>/py.typed`

The native file inventory may differ because adopting PR #851 adds `models.pyi`
and moves model construction into the runtime. Parity fixtures require the
current public modules and package metadata. Private helpers and typing-only
files can differ.

Package setup renders the dependency set collected during generation.

## Large Models

The first implementation emits the same module boundaries as the current
artifact. The output API and generation plan must allow later partitioning
without changing public imports.

smithy-java partitions schema classes after a model reaches 500 schema fields
and then targets about 50 KB of generated schema content per class. smithy-php
uses a centralized lazy schema registry. Python can combine those approaches:

* Keep `<package>._private.schemas` as the stable facade.
* Place compact schema tuples in private partition modules.
* Keep every recursive strongly connected component in one partition.
* Route schema constant access through generated indexes.
* Partition large type stubs behind the public `models.pyi` facade.

Python thresholds must be based on Python measurements. Relevant inputs include
writer render time, peak generator memory, generated import time, and type
checker time. The Java bytecode limit does not apply to Python.

Partitioning bounds the syntax tree analyzed by `PythonWriter` and prevents a
single EC2-sized source file from dominating codegen memory. It is deferred
until the unpartitioned native output passes parity tests. The private facade
keeps the change compatible with generated imports.

## Performance

| Existing optimization | Native implementation |
| --- | --- |
| PR #841 compact schema tuples | Emit the same versioned tuple encoding. |
| PR #841 lazy schema hydration | Hydrate and cache a connected schema graph on first use. |
| PR #851 lazy client models | Use the same indexed registry for standalone types. |
| Cached symbol resolution | Reuse one symbol provider and cached type references. |
| Dense serde dispatch | Preserve member order and dense member indexes. |

Generation loads and selects the model once, computes graph data once, interns
schema strings once, and renders each writer once. Staging bounds rendered
source memory to one file.

Measurements record generator time and peak memory, generated bytes and file
counts, package import cost, first schema and model access, warm serde
throughput, and strict Pyright time. The test set includes a small fixture, the
standalone types integration-test model, and a large AWS model such as EC2. A
regression against Java-generated Python output requires measurement and an
explicit migration decision.

## Validation

Each implementation PR tests its new contract. Before migration, the Java and
native generators run against the same fixtures. Differential checks cover the
compatibility table, selected shape IDs, compact encoding version and mappings,
dependency sets, serde results, deterministic output, concurrent model
construction, star imports, pickle round trips, and generation without a
service. Generated packages must compile on every supported Python version and
pass Ruff and strict Pyright. Formatting and private helper inventories are not
compared.

## Implementation Sequence

### Generation Core

Add settings, dependency records, `GenerationContext`, `GenerationPlan`,
staged `FileManifest`, and artifact dispatch.

### Compact Schemas

Port the PR #841 representation through the shared schema planner, encoding
contract, trait planner, and emitter.

### Lazy Models

Apply the PR #851 representation through the shared `ModelRegistry` facade,
generated model index, `__dir__`, and `models.pyi` emitter. Add `__all__`,
synchronized construction, pickle support, and service-independent error
generation. Generate package initialization and typing metadata. Enable
`smithy-python generate types` after this phase produces a complete package.

### Packaging and Parity

Generate project metadata, dependency declarations, and documentation. Run the
complete Java/native parity suite and large-model measurements.

## Deferred Work

Add private schema and stub partitioning after measurements establish useful
thresholds. Public module paths remain unchanged.

## Alternatives

### Port the Java Directed Codegen Framework

The Java framework supplies a lifecycle for shape and integration hooks. Porting
it first would make the initial native artifact depend on extension points that
have no native consumer. The explicit artifact generator keeps the first
implementation smaller. Shared phases can become hooks after a second artifact
demonstrates the required lifecycle.

### Write Files During Generation

Direct writes use less temporary memory, but a late syntax or import failure
leaves a partial artifact. Per-file staging bounds memory while preserving a
validation boundary before publication.

### Import Schema Encoding from smithy-core

Importing tuple slots and trait bits from `smithy-core` would remove duplicated
constants. It would also add a generator-host runtime dependency and couple the
generator to the runtime selected for its output. A local versioned contract
keeps that boundary explicit.

### Build Runtime Schemas During Import

Emitting constructed `Schema` objects would reduce hydration code, but shifts
the cost to every package import. Compact static data preserves the current
cold-start behavior and shares the runtime cache.

### Preserve Eager Standalone Models

Matching the current standalone source representation would keep every class in
`models.__dict__` immediately after import. It would also require a second model
emitter and would construct every class during package import. The native
generator uses one lazy representation and preserves supported behavior through
the public facade and typed stub.

### Require Byte-Identical Java Output

Byte-identical output would couple the native implementation to Java writer
formatting and internal helper names. Behavioral parity protects users while
allowing native source organization and import planning to evolve.
