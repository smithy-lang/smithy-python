# Code Generation Partitioning

## Abstract

Large standalone types packages split compact schemas and model stubs across
private modules. Stable facade modules preserve generated imports while
reducing generator memory and static analysis time.

## Motivation

An EC2 types package contains 4,065 selected shapes. Emitting its schemas and
model declarations as two large files makes each file the unit of work for
rendering, staging, parsing, and static analysis.

`FileManifest` releases each rendered file after staging it, so the largest file
sets the lower bound for source memory during publication. Pyright analyzes the
model stub as one large declaration file. Lazy schema hydration and model
construction reduce runtime work but do not reduce these file-level costs.

Private partitions bound the work associated with one generated file. Stable
facades preserve generated imports and lazy runtime behavior while tools process
the smaller partition files.

## Settings

`TypesSettings` owns both partition targets:

```python
@dataclass(frozen=True, slots=True)
class TypesSettings(ArtifactSettings):
    selector: Selector = field(default_factory=Selector.identity)
    generate_inputs_and_outputs: bool = False
    schema_partition_size: int | None = 250
    stub_partition_size: int | None = 250
```

The CLI uses these defaults. Python callers may set either target to a positive
integer or `None`. A value of `None` emits that surface as one file.

Partitioning starts when the number of planned items exceeds its target. A
package with 250 schema shapes and 250 model declarations keeps the single-file
layout.

## Output Layout

Partitioned packages retain the stable module paths used by unpartitioned
packages.

| Surface | Facade | Partitions |
| --- | --- | --- |
| Compact schemas | `<package>._private.schemas` | `<package>._private.schemas_N` |
| Model stubs | `<package>.models.pyi` | `<package>._private.models_N.pyi` |
| Runtime models | `<package>.models` | Single module |

### Schema File Layout

```text
src/<package>/
├── models.py
└── _private/
    ├── __init__.py
    ├── schemas.py
    ├── schemas_0.py
    ├── schemas_1.py
    └── schemas_N.py
```

`models.py` imports the `schemas.py` facade. The facade maps schema constants to
partition indexes and loads the matching `schemas_N.py` module on first access.
Each partition contains compact schema tuples.

### Stub File Layout

```text
src/<package>/
├── models.py
├── models.pyi
└── _private/
    ├── __init__.py
    ├── models_0.pyi
    ├── models_1.pyi
    └── models_N.pyi
```

`models.pyi` is the public typing facade. It imports declarations from each
private stub partition. `models.py` remains the runtime module.

`FileManifest` registers the facade and partition files before publication.
Its ownership rules remove stale, unmodified partition files after a model
shrinks or a target changes.

Files under `<package>._private` remain private implementation details.

## Schema Partitions

`SchemaPlan` provides schema shapes in deterministic emission order and groups
each recursive strongly connected component. A recursive group stays in one
partition so its schemas can use direct local references.

The schema partitioner:

1. Packs recursive groups in plan order using the configured shape target.
2. Uses the resulting partition count for the final layout.
3. Estimates the emitted source size of each group.
4. Selects contiguous boundaries that balance estimated source size.

The estimate includes shape and member identifiers, schema references, and
trait values. It uses plan metadata instead of rendering schemas a second time.
The target determines the partition count. Final partitions may exceed the
target to balance source size, and recursive groups remain indivisible.

The facade maps each schema constant to a partition index. Its `__getattr__`
imports the selected partition, reads the constant, and caches the result in
the facade module. `__dir__` includes every planned schema constant.

Partition modules route cross-partition references through the facade. This
keeps dependencies lazy and avoids direct import cycles between partitions.
Hydration remains lazy through `smithy_core._schema_compact`.

## Stub Partitions

`ModelPlan` provides model declarations in deterministic order. The stub
partitioner writes contiguous groups up to the configured target.

The public `models.pyi` facade imports every declaration from its private stub
partition and defines the same `__all__` as `models.py`. Private stubs reference
generated declarations through the public `models` module. This keeps their
type references independent of private partition boundaries.

Runtime `models.py` remains one lazy registry module. Runtime model construction
and class identity stay unchanged.

## Compatibility

Partitioning preserves:

* Public model module paths and runtime schema lookups.
* Model names, constructor signatures, and type annotations.
* Public model `__all__`, explicit imports, star imports, and `dir()` results.
* Lazy schema hydration and model construction.
* Schema identity, recursive references, and serde behavior.

Partition indexes follow generation-plan order. Model changes can move
declarations between private files while the public facades remain stable.

## Validation

Tests cover packages below and above each target, recursive schema groups,
cross-partition references, facade caching, strict Pyright, Ruff, and
deterministic output.

The final x86 EC2 benchmark compared unpartitioned output with 250-item schema
and stub partitions:

| Metric | Unpartitioned | Partitioned | Change |
| --- | ---: | ---: | ---: |
| Generation time | 3.557 s | 3.555 s | -0.1% |
| Peak RSS | 264.5 MiB | 122.4 MiB | -53.7% |
| Peak Python allocation | 222.6 MiB | 84.7 MiB | -61.9% |
| Generated bytes | 4.78 MiB | 5.33 MiB | +11.6% |
| Model import | 50.6 ms | 40.4 ms | -20.2% |
| First model access | 12.3 ms | 22.3 ms | +10.0 ms |
| Strict Pyright | 81.98 s | 15.25 s | -81.4% |
