# Python Client Generation

## Abstract

This document describes how the Python generator produces client packages. It
defines client settings, operation discovery, I/O normalization, client
symbols, the client plan, operation and schema emission, protocol selection,
endpoint rules, endpoint tests, auth, integrations, AWS clients, and the
generated client and config modules.

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
dependencies. RPCv2 CBOR and RPCv2 JSON are built in. Tests can inject a registry.

An explicit protocol selection must be modeled on the service and present in
the registry. Without one, the generator selects the sole supported modeled
protocol. Ambiguous or unsupported selections fail before publication.
Selection is independent of hash and discovery order.

The built-in contributions use these runtime protocols:

| Protocol | Sync | Async | `smithy-http` extra |
| --- | --- | --- | --- |
| `smithy.protocols#rpcv2Cbor` | `RpcV2CborClientProtocol` | `AsyncRpcV2CborClientProtocol` | `cbor` |
| `smithy.protocols#rpcv2Json` | `RpcV2JsonClientProtocol` | `AsyncRpcV2JsonClientProtocol` | `json` |

Both also use:

* `ProtocolSettings` with the service namespace, target, version, and schema.
* `Urllib3HTTPClient` and `AIOHTTPClient` as default sync/async transports,
  which add the `urllib3` and `aiohttp` extras.
* `BddEndpointResolver` over the generated endpoint BDD.

## Endpoints

Endpoint resolution has one runtime representation, the endpoint BDD. The
generator lowers the service's `smithy.rules#endpointBdd` trait into a
`smithy_core.endpoints.EndpointBdd` of Python literals in
`<package>/_private/endpoints.py`. The module source matches the Java
generator's for the same trait.

Lowering re-encodes the trait and makes no engine decisions:

* Parameters become `(name, type, required, default, builtin,
  client_context_attribute)` tuples in trait order. Optional parameters no
  condition or result reads are dropped.
* Expressions and results become tuples led by small integer tags. Function
  names stay names, and `getAttr` becomes an attribute expression.
* Templates are parsed as Smithy parses them and written back from their parts,
  so escapes and `getAttr` paths take one canonical form.
* Nodes are decoded from the trait's big-endian `int32` triples and copied
  verbatim. Node 0 must be the `(-1, 1, -1)` terminal, and no edge may
  complement a result reference.

Only trait version 1.1 is accepted. A service with no endpoint rules gets the
BDD compiled from the default ruleset of smithy-typescript, which reads
`SDK::Endpoint` and fails when it is unset. A service with
`smithy.rules#endpointRuleSet` alone fails generation, because compiling a
ruleset into a BDD is Smithy's `CompileBdd` transform.

The generated client calls rules functions from the `smithy_core.endpoints`
standard library only. Rules that call any other function fail generation with
a diagnostic naming the functions.

Each `smithy.rules#clientContextParams` entry becomes a config field typed `bool
| None` or `str | None` and defaulting to None. Its name is the snake-case form
of the parameter name, and its docstring is the entry's documentation. The BDD
records the field name as the parameter's config attribute. A field name that
matches a standard config field or another entry's field fails generation.

Schemas retain `smithy.rules#contextParam`, `smithy.rules#staticContextParams`,
and `smithy.rules#operationContextParams`, which the runtime parameter plan
reads to bind input members and operation values.

## Endpoint Tests

A service with an endpointBdd trait and `smithy.rules#endpointTests` cases gets
`tests/test_endpoints.py`. Its layout follows the Java generator's:

* Every case becomes a rules test. `smithy_test.check_rules_case` resolves the
  case's `params` with the default endpoint resolver of the async config. All
  rules tests share one resolver, so its caches see changing parameters.
* Every operation input of a case becomes a client test.
  `smithy_test.aio.check_client_case_async` calls the operation through the
  async client and checks the endpoint it resolves and the request it sends.
* A client test's config sets the client context fields from `clientParams`.
  `SDK::Endpoint` sets `endpoint_uri`, and a built-in that is also a client
  context parameter sets its field.
* `operationParams` become the call's keyword arguments, keyed by member field
  name. Nested structures and unions are written in their dictionary forms.
* Cases keep the trait's `params` and `expect` objects. Test IDs come from the
  case documentation, numbered when one repeats.

A client test the client can't express is generated as skipped, with the
reasons. These are a built-in with no config field set to a value other than its
default, a client parameter that is not a client context parameter, and a blob,
timestamp, big decimal, or document value. An input that names an operation the
service lacks, or a member its input lacks, fails generation.

The module marks its tests with `pytest.mark.asyncio`. The package's `test`
dependency group adds `pytest`, `pytest-asyncio`, and `smithy-test`.

## Auth

An auth registry maps auth trait IDs to auth contributions. A contribution
provides the sync and async runtime auth schemes, builds each from the service's
auth trait value, and declares the config fields its identity resolver reads.
`smithy.api#httpApiKeyAuth` is built in:

| Part | Sync | Async |
| --- | --- | --- |
| Scheme | `APIKeyAuthScheme` | `AsyncAPIKeyAuthScheme` |
| `api_key_identity_resolver` default | `APIKeyIdentityResolver` | `AsyncAPIKeyIdentityResolver` |

The scheme takes the trait's `name`, `in`, and `scheme`. Both configs also get
an `api_key` field. The fields, the `auth_schemes` default, and a
`set_auth_scheme` method match the Java generator's.

Both configs keep `DefaultAuthResolver`. It returns each operation's effective
auth scheme IDs in order, and the runtime signs with the first one in
`auth_schemes`. An operation whose schemes are only `noAuth`, such as one with
`@auth([])`, is sent unsigned. An operation with `@optionalAuth` is signed with
its first supported scheme.

Generation fails for an operation whose effective schemes include neither
`noAuth` nor a supported scheme.

## Integrations

A `ClientIntegration` changes the clients of the services it matches. The
generator takes integrations in order and applies those that match. Each hook
defaults to no change:

| Hook | Changes |
| --- | --- |
| `client_names` | The client and config class names |
| `config_fields` | Config fields a client context field must not take |
| `write_config` | The config class, written in place of the core one |
| `new_config` | The callable that creates a default config |
| `client_plugins` | Plugins every client applies, before the core ones |
| `write_files` | Extra modules |

A hook gets a `ClientMode` for the sync or async variant and, for configs, a
`ConfigPlan` with the endpoint plan, the `BDD` constant, and the supported auth
schemes. The core generator imports no integration. The CLI passes
`smithy_python.aws.AWS_INTEGRATIONS`.

## AWS Clients

`smithy_python.aws` holds the AWS integrations. `AwsConfigIntegration` matches a
service with the `aws.api#service` trait and follows the Java generator's AWS
config:

* The clients are `<SdkId>Client` and `Async<SdkId>Client`, and the configs are
  `<SdkId>Config` and `Async<SdkId>Config`, with spaces removed from the SDK
  ID.
* The configs subclass `AwsConfig` and `AsyncAwsConfig` from `smithy-aws-core`.
  They resolve from overrides, environment variables, shared config files, and
  defaults through `resolve()`, and direct construction fails. A client without
  a config creates one with `resolve()`.
* Each config adds the fields the base lacks, with a `FieldSpec` for each:
  `endpoint_resolver`, `protocol`, `auth_schemes`, `auth_scheme_resolver`, auth
  scheme fields, and client context fields. `endpoint_uri` also reads
  `AWS_ENDPOINT_URL_<SDK_ID>` and the profile's service section.
* A typed `Unpack` overrides dictionary covers the added fields.
* Clients apply `aws_user_agent_plugin`, which adds `UserAgentInterceptor`
  with the SDK ID, the package version, `sdk_ua_app_id`, and
  `user_agent_extra`.

The generated package depends on `smithy-aws-core`. A client context field may
not take an `AwsConfig` field name.

## Clients and Configuration

Service classes are thin subclasses of `Client[Config]` and
`AsyncClient[AsyncConfig]`. Their methods invoke the runtime pipeline, which
owns retries, interceptors, HTTP framing, and serde.

Generated packages use this layout:

```text
<package>/client.py
<package>/config.py
<package>/aio/client.py
<package>/aio/config.py
<package>/models.py and models.pyi
<package>/_private/schemas.py and partitions
<package>/_private/endpoints.py
tests/test_endpoints.py, for services with endpoint tests
```

Package initialization lazily exports both clients and configs. Each config
exposes protocol/transport overrides, endpoint URI/resolver, auth
resolver/schemes, retries, interceptors, and client context fields. Both
configs default to `DefaultAuthResolver`, `BddEndpointResolver(BDD)`, the
contribution's protocol,
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

The generator supports non-streaming RPCv2 CBOR and RPCv2 JSON operations that
are unsigned or use API key auth, and whose endpoint rules use the standard
library. Models that require other auth schemes or event or data streams fail
generation with a diagnostic naming the operation and feature.

Authentication and endpoint extension points are provider-neutral. AWS config
resolution and the AWS user agent are AWS integrations. SigV4, AWS endpoint
functions, and AWS protocols are not supported yet.

## Validation

Tests generate a checked-in JSON service fixture. They exercise nested
input/output models, a modeled error, Unit I/O, and explicit empty I/O through
fake sync/async transports. They assert the request method, URI, headers,
decoded CBOR payload, response models, and error types. An endpoint test
resolves a host from a client context field, an input context parameter, and
a static context parameter.

Lowering tests port the Java generator's tests. The `endpoint-rules-client`
snapshot is generated from a fixture whose endpoint rules read client context
fields, `SDK::Endpoint`, an input context parameter, and static context
parameters. `models/endpoint-rules.smithy` is its source, and
`models/endpoint-rules.json` is that model assembled by Smithy with its ruleset
compiled by `CompileBdd`. The snapshot tests run the snapshot's generated
endpoint tests.

The `api-key-auth-client` snapshot comes from `models/api-key-auth.smithy`,
assembled by Smithy into `models/api-key-auth.json`. Its operations use the
service's API key auth, `@auth([])`, and `@optionalAuth`. Tests check which
requests carry the key and that a missing key fails the call.

The `aws-config-client` snapshot comes from `models/aws-config.smithy`,
assembled by Smithy into `models/aws-config.json` with its ruleset compiled by
`CompileBdd`. Its tests resolve the endpoint from `AWS_ENDPOINT_URL_<SDK_ID>`
and from a profile, check the AWS user agent, and check that unknown fields and
direct construction fail.

Client snapshots sit alongside the types snapshots and cover the
provider-neutral RPCv2 CBOR and RPCv2 JSON projections. Checks cover deterministic
regeneration, Ruff, strict Pyright consumer usage, lazy imports,
plugins/interceptors, retries, response metadata, and transport lifecycle.

The Python AST fixtures omit HTTP request/response test traits. Protocol-vector
coverage reads them from a separate checked-in file per client projection, with
its provenance hash, and runs each vector against the client snapshot. Tests read
only checked-in inputs and never depend on Java
output.
