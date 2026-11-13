# Python Codegen Snapshots

`codegen-output-py` records the model, schema, and client surface currently
supported by `smithy-python generate types` and `smithy-python generate client`.
It gives the Python generator the same model
families as the Java-generated `codegen-output` tree without making the Python
workflow depend on Java, Gradle, Maven, or the Smithy CLI.

## Coverage

The reference projections retain the projection names, import package names,
service IDs, and package versions from
`codegen/protocol-test/smithy-build.json`. All use the public `types` command with
`--service` and `--include-operation-io`.

| Projection | Import package | Data schemas |
| --- | --- | ---: |
| `rest-json-1` | `restjson` | 205 |
| `rest-xml` | `restxml` | 144 |
| `rest-xml-with-namespace` | `restxmlwithnamespace` | 3 |
| `aws-json-1-0` | `awsjson10` | 44 |
| `query-compatible-aws-json-1-0` | `querycompatibleawsjson10` | 2 |
| `aws-json-1-1` | `awsjson11` | 53 |
| `aws-query` | `awsquery` | 73 |
| `ec2-query` | `ec2query` | 56 |
| `rpcv2-cbor` | `rpcv2cbor` | 56 |
| `rpcv2-json` | `rpcv2json` | 57 |
| `query-compatible-rpcv2-cbor` | `querycompatiblerpcv2cbor` | 2 |
| `non-query-compatible-rpcv2-cbor` | `nonquerycompatiblerpcv2cbor` | 0 |
| `my-handwritten-model` | `my_handwritten_model` | 20 |
| `my-handwritten-json-model` | `my_handwritten_json_model` | 10 |
| `types` | `example_types` | 10 |
| `partitioned-types` | `partitioned_types` | 270 |

The fourteen reference projections contribute 725 data schemas. The original
example adds service renames, string and integer enums, unknown enum and union
values, a Unit union member, collections, a modeled error, and streaming
members. The Python partition stress fixture extends that example with 260
linked structures, including a recursive pair. Default partition settings
produce three schema partitions and two private stub partitions for it.

Protocol names identify the source models; the Python artifacts do not generate
protocol implementations or AWS integrations. The non-query-compatible RPCv2
CBOR service has no standalone declaration roots, so its snapshot contains an
empty schema module and the `ServiceError` base. Java's synthetic operation
input/output structures are deliberately absent.

Each types snapshot contains only:

* `models.py` and `models.pyi`, with private model stub partitions when needed;
* `_private/schemas.py`, with private schema partitions when needed;
* package initialization, `py.typed`, package metadata, and a README;
* the Python generator's file ownership and content hash manifest.

Types snapshots contain no client, config, auth, endpoint, protocol
implementation, user agent, or generated protocol tests.

### Client snapshots

`scripts/codegen-output-py/client-projections.json` declares client
projections, generated with the public `client` command.

| Projection | Import package | Operations |
| --- | --- | ---: |
| `rpcv2-cbor-client` | `rpcv2cbor_client` | 14 |

It reuses the `rpcv2-cbor` model input. Its import package differs from the
types snapshot's, so both resolve in one Pyright project. Each client snapshot
adds `client.py`, `config.py`, and their `aio` counterparts to the types files,
plus service and operation schemas and lazy operation exports. Tests compare its
operation methods with the Java client and send one call through fake sync and
async transports.

## Inputs and maintenance

`scripts/codegen-output-py/projections.json` declares the generation inputs and
settings. Model inputs are checked-in Smithy JSON ASTs, taken from the assembled
protocol-test projections using Smithy 1.74.1. They retain the original model
order, mixins, model documentation, traits, and operation references.
`smithy.test#httpRequestTests` and `smithy.test#httpResponseTests` vectors and
their trait definitions are removed because they exercise client protocols.
Python model loading flattens mixins before generation.

`models/provenance.json` records hashes of both the original assembled ASTs and
the checked-in fixtures. Regeneration reads only checked-in files. It neither
reads a build directory nor installs or invokes a JVM tool.

To refresh reference inputs when their models change, obtain assembled JSON ASTs
and run:

```sh
PATH="$PWD/.venv/bin:$PATH" python scripts/codegen-output-py/refresh_models.py \
    /path/to/assembled/projections
make generate-codegen-output-py
make check-codegen-output-py
make test-codegen-output-py
```

The maintenance command expects `<projection>/model/model.json` for each
reference projection. It reads the projection settings as ordinary JSON and
also rebuilds the Python partition stress input. It does not assemble Smithy
IDL or invoke a build system. Review fixture and provenance changes together.

Generated files must never be edited directly. Update model inputs, generation
settings, the generation script, or the Python generator, then regenerate.

## Determinism and validation

`make generate-codegen-output-py` generates the complete tree in a temporary
directory, applies the repository's Ruff rules, and refreshes each package's
content hashes. It publishes only if file contents differ. A second run against
the same inputs changes no files.

`make check-codegen-output-py` compares a fresh temporary generation with the
working tree without publishing it. It reports missing, changed, and obsolete
files, then checks Ruff and strict Pyright over generated runtime modules,
stubs, private partitions, and a consumer usage fixture. The usage fixture
imports all projection packages through their public model modules.

Separating generation from checking allows intentional, uncommitted snapshot
updates to be validated. In a clean CI checkout, the same comparison checks the
committed snapshots. These commands use only Python and Python tools.
`make static-analysis` runs the snapshot check; `make test-integration` runs the
check and Python conformance suite alongside the existing Java checks.

The conformance suite checks:

* complete generated file surfaces, metadata, and manifest hashes;
* public model exports, lazy construction, caching, star imports, and field
  agreement with stubs, including facade re-exports;
* schema IDs, types, retained trait values, inherited mixin members, member
  order, indexes, and targets against the loaded input ASTs;
* schema facade imports and object identity across partitions;
* common model fields, enum values, and schema metadata against the committed
  Java-generated Python packages, with isolated package imports;
* JSON model round trips and RPCv2 CBOR model round trips, without constructing
  clients;
* streaming blob serializer/deserializer dispatch. Document codecs cannot
  encode data streams, so these members use a separate stream check.

Generator unit tests additionally cover concurrent first access, naming
collisions, constructor semantics, serde behavior, and strict typing of empty
model maps and both partitioned and unpartitioned stubs.

## Java behavior that remains outside these snapshots

The Java tree is a behavioral reference, not a byte-for-byte template. These
differences are explicit:

* Java client generation creates dedicated operation input/output structures,
  including empty structures for operations without modeled I/O. Python types
  use the original selected data shapes. Shared structures retain their
  input/output markers and resulting standalone constructor and response
  metadata behavior.
* Operation schemas, `APIOperation` metadata, service/resource metadata, and
  operation-to-schema partition affinity are client planning concerns. Types
  artifacts omit operation schemas, and their partition boundaries may differ
  from Java clients.
* Java AWS integrations retain provider-specific metadata such as
  `aws.protocols#awsQueryError`. Python snapshots do not claim parity for this
  metadata or implement AWS behavior.
* Java still produces clients, sync/async configs, auth, endpoints, user agents,
  protocol serializers/deserializers, and operation-level protocol tests.
* Source documentation and package descriptions can render differently; public
  model behavior and supported schema semantics are the compatibility target.

The common-schema comparison accounts specifically for input/output markers
and `awsQueryError`; it compares the remaining metadata without excluding
shape IDs, types, member order, indexes, targets, or provider-neutral trait
values.

## Next client milestone

The next task is a provider-neutral client design followed by an RPCv2 CBOR
vertical slice. Define `ClientSettings` and `ClientPlan`, operation discovery and
dedicated I/O normalization, operation/schema metadata, protocol extension
points, and runtime transport/config integration. The client plan should
compose model and schema plans while owning operation metadata and partition
affinity. Do not force operation schemas through `TypesSettings` or alter the
standalone types contract to obtain client parity.

The vertical slice should generate and exercise a minimal RPCv2 CBOR operation
end to end, covering public client/config surfaces, operation metadata,
request serialization, transport dispatch, response deserialization, modeled
errors, and strict typing. AWS-specific integrations remain a subsequent
milestone. `smithy-python generate client` remains explicitly unimplemented in
this snapshot task.
