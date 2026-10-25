# Standalone Types Generation

## Abstract

This document describes how the Python generator produces standalone types
packages. It defines package settings, shape selection, generation context,
schema and model emission, dependency tracking, and output publication.
Generated packages expose lazy models backed by compact, lazily hydrated
schemas.

## Goals

* The `smithy-python generate types` command produces an importable standalone
  types package.
* Generation reuses the loaded model, selection, symbol provider, and writers.
* Generated packages expose compatible public modules, declarations,
  constructors, schemas, and serde behavior.
* Schemas use compact encoding and hydrate on first use.
* Model classes are constructed and cached on first access.
* Model analysis, symbol resolution, and writer work are computed once and
  reused.
* Output is deterministic on every supported generator host.
* Every generated file is validated before the output directory is modified.
* The generation context and output APIs are reusable by other artifacts.

Generated packages use `smithy-core` schema and model runtime APIs.

## Compatibility

| Area | Required behavior |
| --- | --- |
| Package | Preserve the configured package name, version, metadata, and runtime dependencies. |
| Public modules | Preserve import paths such as `<package>.models`. |
| Models | Preserve declaration names, field names, constructor signatures, defaults, error inheritance, enum values, and union variants. |
| Schemas | Preserve shape IDs, shape types, traits, member order, member indexes, and targets. |
| Serde | Preserve generated and runtime serialization and deserialization behavior. |
| Typing | Generated packages must pass strict Pyright checks and expose the same public types. |
| Runtime support | Generated packages depend on handwritten runtime packages, not `smithy-python`. |

Model classes are built on demand through `ModelRegistry`, and their static
surface is declared in `models.pyi`. An explicit import such as
`from example.models import Widget` returns a class with the expected public
name, module, fields, constructor, and serde behavior. The class is cached after
first access, so later imports and attribute reads return the same object.

The lazy facade preserves explicit imports, star imports, `dir(models)`, class
identity, dataclass inspection, and pickling by module and qualified name.
Concurrent first access returns one class object. Packages generated without a
service still provide `ServiceError` and use it as the base of modeled errors.

`models.pyi` defines the complete static typing surface. Runtime classes expose
generated field names in `__annotations__` and enter `models.__dict__` when
first accessed. Class-construction errors surface from that first access.

Files under `_private` are not public API. The generator may change their layout
if generated public modules and runtime behavior stay compatible.

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
and output APIs but control their own generation phases.

## Settings

`ArtifactSettings` contains settings shared by generated artifacts:

```python
@dataclass(frozen=True, slots=True)
class ArtifactSettings:
    package: str
    package_version: str
    package_description: str | None


@dataclass(frozen=True, slots=True)
class TypesSettings(ArtifactSettings):
    selector: Selector = field(default_factory=Selector.identity)
    generate_inputs_and_outputs: bool = False
```

The resolved service remains on `Selection`. It is not duplicated in settings.
The CLI subcommand identifies the artifact, so settings do not duplicate that
value. Artifact-specific settings extend the shared frozen dataclass.

The `types` command accepts:

* `--package`
* `--package-version`
* `--package-description`
* `--selector`
* `--generate-inputs-and-outputs`

`package` and `package-version` are required. The package identifies the
generated import package and follows the validation rules in `SymbolProvider`.
The description defaults to `"<package> types package"`.

The selector setting is parsed once into an immutable selector syntax tree.
The parser and evaluator implement the Smithy selector language and produce the
same selected shape IDs as Java's `Selector.parse()` and `Selector.select()`.

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

`TypesGenerator` receives `GenerationContext[TypesSettings]`. Other artifacts
can define their own settings subclasses without casts or a shared union of
artifact settings.

`GenerationPlan` composes focused plans for each emitter.

`SchemaPlan` contains shapes in schema emission order, filtered trait values,
schema constant names, and interned schema strings.
`ModelPlan` contains declaration names, rename mappings, and union variant and
unknown-class names.

Planning uses iterative graph algorithms so model depth does not consume the
Python stack. The symbol provider caches resolved `TypeReference` values.

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

Publication uses `os.replace` to atomically update each file. Commit requires
exclusive access to the configured output directory.

The output directory contains a generated artifact manifest with normalized
paths and content hashes. Current generated paths are authoritative. Commit
replaces a current path when the previous manifest owns it, even if its contents
changed. If a current path already exists and the previous manifest does not own
it, commit fails with an output collision.

On a later run, the generator may delete a stale file only when the previous
manifest owns it and its content still matches the recorded hash. Modified stale
files are retained and are no longer owned by the manifest. Files absent from
the manifest are retained unless they collide with a current generated path.

Callers use a dedicated, generator-managed output directory and keep custom
files at non-conflicting paths. Initial generation starts with no files at
generated destinations.

The Smithy `run` plugin output restriction still applies. Symlinks or resolved
ancestors that escape the output root are rejected.

## Schema Emission

The generator emits the compact schema format consumed by
`smithy_core._schema_compact` in `<package>._private.schemas`.

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
each emitted data shape. Generated schemas contain the same trait IDs and values
for the same model. Input and output traits are synthesized under the same
conditions. A schema uses the integer trait bit vector only when every present
trait is represented by a valueless bit. Otherwise it emits the complete trait
mapping.

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

Standalone types use `ModelRegistry` to construct model classes on demand:

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

The `types` artifact contains:

* `pyproject.toml`
* `README.md`
* `src/<package>/__init__.py`
* `src/<package>/models.py`
* `src/<package>/models.pyi`
* `src/<package>/_private/__init__.py`
* `src/<package>/_private/schemas.py`
* `src/<package>/py.typed`

Package setup renders the dependency set collected during generation.

## Large Models

Schema and stub partitioning must not change public imports. The output API and
generation plan allow private content to move behind stable facade modules.

smithy-java partitions schema classes after a model reaches 500 schema fields
and then targets about 50 KB of generated schema content per class. smithy-php
uses a centralized lazy schema registry. Python can combine those approaches:

* Keep `<package>._private.schemas` as the stable facade.
* Place compact schema tuples in private partition modules.
* Keep every recursive strongly connected component in one partition.
* Route schema constant access through generated indexes.
* Partition large type stubs behind the public `models.pyi` facade.

Python partitioning thresholds must be based on Python measurements. Relevant inputs include writer render time, peak generator memory, generated import time, and type
checker time.

Partitioning bounds the syntax tree analyzed by `PythonWriter` and prevents a
single EC2-sized source file from dominating codegen memory. Measurements
establish the partitioning thresholds. Facade modules preserve generated
imports.

## Performance

| Optimization | Generator behavior |
| --- | --- |
| Compact schema tuples | Emit the versioned tuple encoding consumed by `smithy-core`. |
| Lazy schema hydration | Hydrate and cache a connected schema graph on first use. |
| Lazy model construction | Use an indexed registry to construct standalone types. |
| Cached symbol resolution | Reuse one symbol provider and cached type references. |
| Dense serde dispatch | Preserve member order and dense member indexes. |

Generation loads and selects the model once, computes graph data once, interns
schema strings once, and renders each writer once. Staging bounds rendered
source memory to one file.

Measurements record generator time and peak memory, generated bytes and file
counts, package import cost, first schema and model access, warm serde
throughput, and strict Pyright time. The test set includes a small fixture, the
standalone types integration-test model, and a large AWS model such as EC2.

## Validation

Tests cover the compatibility table, selected shape IDs, compact encoding
version and mappings, dependency sets, serde results, deterministic output,
concurrent model construction, star imports, pickle round trips, and generation
without a service. Generated packages must compile on every supported Python
version and pass Ruff and strict Pyright.

## Alternatives

### Port the Java Directed Codegen Framework

The Java framework supplies a lifecycle for shape and integration hooks. Porting
it would make the types artifact depend on extension points that have no Python
consumer. The explicit artifact generator keeps the design smaller. Shared
phases can become hooks after another artifact demonstrates the required
lifecycle.

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
the cost to every package import. Compact static data preserves cold-start
behavior and shares the runtime cache.

### Preserve Eager Standalone Models

Eager standalone declarations would place every class in `models.__dict__`
immediately after import. They would also require a second model emitter and
construct every class during package import. The generator uses one lazy
representation and exposes supported behavior through the public facade and
typed stub.

### Require Byte-Identical Java Output

Byte-identical output would couple the Python implementation to Java writer
formatting and internal helper names. Behavioral parity protects users while
allowing Python source organization and import planning to evolve.
