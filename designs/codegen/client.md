# Python Client Generation

## Abstract

This document describes how the Python generator produces client packages. It
defines client settings, operation discovery, I/O normalization, client
symbols, the client plan, operation and schema emission, protocol selection,
and the generated client and config modules.

## Goals

* The `smithy-python generate client` command produces an importable client
  package for one service.
* Client generation reuses the model loader, selection, symbol provider,
  writers, and the schema and model emitters used by standalone types.
* Generated clients run requests through the existing sync and async runtime
  pipelines.
* Protocol support is selected by modeled protocol ID and is provider-neutral.
* Generation and its tests run in Python and read checked-in JSON AST inputs.

The Java generator and its generated Python packages are behavioral references.

## Pipeline

```text
JSON AST
  -> loaded model and resolved service
  -> operation discovery and dedicated I/O normalization
  -> client data selection and symbol allocation
  -> ClientPlan: shared model/schema plans + operation/protocol plans
  -> ClientGenerator and shared emitters
  -> FileManifest validation and publication
```

## Planning API

```python
from smithy_python.clients import ClientPlan
from smithy_python.generation import ClientSettings
from smithy_python.model import load_model

model = load_model(model_json)
plan = ClientPlan.from_model(
    model,
    ClientSettings("example_client", "1.0.0", None),
    service_id="example#Service",
)
```

Planning returns an in-memory plan and leaves the original model unchanged.
Protocol selection and file publication happen in later stages.

## Settings

`ClientSettings` shares package settings and schema/stub partition targets with
types settings. It adds an optional protocol selection. Service resolution
belongs to selection. Types-only options such as selectors and
`--include-operation-io` do not apply to clients.

The shared schema and model emitters accept a
`GenerationContext[ModelArtifactSettings]`. `ModelArtifactSettings` holds the
package and partition fields both artifacts use, and `TypesSettings` and
`ClientSettings` extend it. Client generation passes its `ClientSettings` and the
schema and model plans from its `ClientPlan`. It never constructs
`TypesSettings` or replaces a plan after construction.

## Operation Discovery

`contained_operations(model, service)` follows service operations and all
resource lifecycle, instance, collection, and child-resource relationships. It
uses an iterative worklist, terminates on cycles, and returns each operation
once in original model order. Operations are discovered only through service
and resource relationships. Data members and trait values are ignored.

## I/O Normalization

`normalize_client_model(model, service, package=...)` builds a new immutable
model before symbols or plans are constructed:

* Every operation gets dedicated input and output structures, including
  operations whose original I/O is Unit.
* Source members are copied in order, with member IDs rebased onto the new
  container.
* Source traits that apply to the new structure are preserved. The structure
  records `smithy.synthetic#originalShapeId` and carries the `input` or
  `output` trait.
* Canonical I/O IDs are reused when no other relationship references the
  source. Otherwise fresh operation-scoped IDs are allocated, with numeric
  suffixes that avoid modeled IDs, service-renamed declarations, and generated
  union variants.
* Already normalized, exclusive I/O keeps its IDs and original shape metadata
  on another pass.
* Source structures remain in the normalized model. Service selection omits
  those no longer reachable.

Unit stays distinguishable from an explicitly modeled empty structure. The
runtime RPCv2 protocol checks `originalShapeId` to decide whether to omit the
request body and Content-Type.

Normalization belongs to client generation only. Standalone types keep their
original shapes and omit operation metadata.

## Symbols

`ClientSymbolProvider` keeps the standalone data naming contract. It adds
sync/async service names, public operation names, preferred I/O names, and
service/operation schema constants. Runtime method conflicts are escaped past
modeled sibling names. Ambiguous modeled method names produce an error listing
both operation IDs. Control schemas share the data schema namespace. Smithy
operation IDs and member wire names stay unchanged.

## Client Plan

`ClientPlan` contains the normalized model, its data selection, settings,
`ClientSymbolProvider`, shared `SchemaPlan` and `ModelPlan`, and ordered
`OperationPlan` records. Each operation record holds:

* Original operation ID, public method name, and operation constant.
* The normalized `OperationShape`.
* Dedicated input/output IDs and generated declaration names.
* Effective error IDs, with inherited service errors merged without duplicates.
* Effective auth scheme IDs and protocol requirements.
* References to the planned compact schemas.

Stream and protocol traits are preserved in the plan. Protocol contributions
check implementation-specific features.

## Schema Emission

The client schema plan includes the service, its contained operations, and the
selected data shapes. Resource relationships guide discovery. Clients expose
no public resource API.

Operations use the runtime's compact encoding:

```text
(23, namespace, name, traits, input_ref, output_ref, error_refs)
```

An operation and its dedicated I/O share a schema partition. Other references
go through the lazy facade. The service keeps its selected protocol trait even
when the trait's definition shape is absent from the input AST.

## Operation Emission

Model emission adds a lazy `_OPERATIONS` table that maps each operation
constant to its effective error IDs and auth scheme IDs. The module
`__getattr__` builds an operation on first access with
`ModelRegistry.build_operation`, which wraps the compact schema in an
`APIOperation`. The public stub declares
`APIOperation[OperationInput, OperationOutput]`. Importing models or clients
does not construct model classes.

Python model plans can rename declarations. `APIOperation.input`, `.output`,
and `.error_registry` resolve classes through `APIOperation.type_names`, a
shape-ID-to-declaration mapping. `build_operation` fills it from the registry's
target names, the same mapping model plans use for member targets. Resolution by
`schema.id.name` alone returns the wrong class when a service rename separates
two shapes with the same name.

Effective auth scheme IDs follow Smithy's `NO_AUTH_AWARE` mode. Service schemes
are ordered by shape ID unless an `auth` trait on the operation, or else the
service, orders them. `smithy.api#noAuth` is appended when no scheme applies or
the operation has `optionalAuth`.

## Protocols

A protocol registry maps modeled protocol IDs to protocol contributions. A
contribution provides sync/async protocol and transport references and their
dependencies. RPCv2 CBOR is built in. Tests can inject a registry.

An explicit protocol selection must be modeled on the service and present in
the registry. Without one, the generator selects the sole supported modeled
protocol. Ambiguous or unsupported selections fail before publication.
Selection is independent of hash and discovery order.

The RPCv2 CBOR contribution uses:

* `smithy_http.protocols.RpcV2CborClientProtocol`.
* `smithy_http.aio.protocols.AsyncRpcV2CborClientProtocol`.
* `ProtocolSettings` with the service namespace, target, version, and schema.
* `Urllib3HTTPClient` and `AIOHTTPClient` as default sync/async transports.
* `StaticEndpointResolver` with a configured endpoint URI.

## Clients and Configuration

Service classes are thin subclasses of `Client[Config]` and
`AsyncClient[AsyncConfig]`. Their methods invoke the runtime pipeline, which
owns retries, interceptors, HTTP framing, and CBOR serde.

Generated packages use this layout:

```text
<package>/client.py
<package>/config.py
<package>/aio/client.py
<package>/aio/config.py
<package>/models.py and models.pyi
<package>/_private/schemas.py and partitions
```

Package initialization lazily exports both clients and configs. Each config
exposes protocol/transport overrides, endpoint URI/resolver, auth
resolver/schemes, retries, and interceptors. Both configs default to
`DefaultAuthResolver`, `StaticEndpointResolver`, the contribution's protocol,
and its transport: `Urllib3HTTPClient` for sync and `AIOHTTPClient` for async.
Client and types artifacts share package metadata emission, dependency
tracking, README generation, and manifest ownership.

Runtime dependencies are recorded in the catalog, including the CBOR and
transport extras on `smithy-http`. Generated packages depend on runtime
packages only. The generator imports no runtime packages.

Client modules use postponed annotations and refer to models through the lazy
`models` module, as in `models.GreetOutput`. Importing a client builds no model
class. The writer keeps scope-aware alias allocation, so imported names survive
collisions with operation method names.

## Operation Signatures

Each operation method has two overloads. One takes the whole request as the
input model or its dictionary form. The other takes the request's members as
keyword arguments, typed with `Unpack` over the dictionary form. The
implementation passes both to the runtime's `_select_input` and `_invoke`, so
input conversion stays in the runtime.

Every structure and union reachable from an operation input has a `TypedDict`
form in the model stub, named with a `Dict` suffix. A union's form is a union of
single-key dictionaries, one per variant. Lists and maps accept `Sequence` and
`Mapping` of models or dictionaries. A `@required` member without a default is
`Required`, except an input's idempotency token, which the client fills in. At
runtime each form's name resolves to `dict`.

One member-name plan drives signatures, model fields, dictionary keys, and
runtime metadata. It covers `self`, `plugins`, defaults, and idempotency tokens.

## Supported Features

The generator supports unsigned, non-streaming RPCv2 CBOR operations with a
static endpoint. Models that require auth schemes, event or data streams, or
modeled endpoint rules fail generation with a diagnostic naming the operation
and feature.

Authentication and endpoint extension points are provider-neutral. AWS
credentials, region defaults, SigV4, query compatibility, AWS endpoint
functions, and AWS user agents are separate integrations.

## Validation

Tests generate a checked-in JSON service fixture. They exercise nested
input/output models, a modeled error, Unit I/O, and explicit empty I/O through
fake sync/async transports. They assert the request method, URI, headers,
decoded CBOR payload, response models, and error types.

Client snapshots sit alongside the types snapshots and cover the
provider-neutral RPCv2 CBOR projection. Checks cover deterministic
regeneration, Ruff, strict Pyright consumer usage, lazy imports,
plugins/interceptors, retries, response metadata, and transport lifecycle.

The Python AST fixtures omit HTTP request/response test traits. Protocol-vector
coverage uses a separate checked-in client input that keeps those vectors and
their provenance. Tests read only checked-in inputs and never depend on Java
output.
