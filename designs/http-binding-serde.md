# HTTP Binding Serialization and Deserialization

## Status

Draft.

## Summary

`HTTPBindingSerializer` routes generated input members to HTTP headers, URI
components, and payloads. `HTTPResponseDeserializer` reads response bindings.
Both use schema-cached `HTTPBindingSchemaMetadata`. Each schema derives and
caches its binding map once.

Generated structures keep the existing `serialize()`, `serialize_members()`,
and `deserialize()` interfaces. HTTP protocols call `serialize_members()`
directly for generated inputs and use `serialize()` as a compatibility path
for handwritten inputs. Document codecs continue to handle document payloads.
The change requires no generator updates.

### Request flow

```text
Generated input.serialize_members()
                  |
                  v
        HTTPBindingSerializer
                  |
       cached member route table
          /       |        \
         v        v         v
   HTTP fields   URI    payload codec
         \        |         /
                  v
             HTTPRequest
```

### Response flow

```text
HTTPResponse
     |
     v
HTTPResponseDeserializer
     |
cached headers/status/payload/body bindings
     |                          |
     v                          v
location deserializers    payload codec
     |                          |
     +------------+-------------+
                  v
       generated deserialize()
```

## Motivation

The current request and response paths construct binding matchers for each
serde operation. Response deserialization also walks every structure member
before it delegates document members to the payload codec. Generated schemas
remain stable during client execution, so the runtime can store these derived
bindings on each schema.

Calling `serialize_members()` directly removes the root `begin_struct()` call
for generated inputs. Cached binding metadata removes repeated trait
classification and matcher allocation. Existing serializer, deserializer, and
codec contracts remain unchanged.

## Scope

* Lazy extension caching on `Schema`.
* Cached request and response HTTP binding metadata.
* Generic request serialization through `HTTPBindingSerializer`.
* Cached response binding lookup in `HTTPResponseDeserializer` and
  `HTTPResponseSerializer`.
* A `serialize()` compatibility path for handwritten inputs.

JSON, XML, and query codecs keep their current interfaces. Generated
deserialization keeps its callback contract. Structure construction hooks and
filtered document schemas require separate designs.

## Existing Generated Interface

Generated structures provide the required runtime interface:

```python
class ExampleInput:
    SCHEMA: ClassVar[Schema]

    def serialize(self, serializer: ShapeSerializer) -> None:
        with serializer.begin_struct(self.SCHEMA) as struct_serializer:
            self.serialize_members(struct_serializer)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        ...
```

`serialize()` remains the general entry point for serializing a complete shape.
`serialize_members()` remains the efficient entry point for a runtime that has
already opened or otherwise established the containing structure.

HTTP request serialization uses `serialize_members()` because the HTTP binding
serializer owns the request and document-body structure state. Other callers
can continue to use `serialize()`.

Generated deserialization remains:

```python
class ExampleOutput:
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        kwargs: dict[str, Any] = {}
        deserializer.read_struct(cls.SCHEMA, consumer=...)
        return cls(**kwargs)
```

`HTTPResponseDeserializer` implements this existing callback-based interface.

## Schema Extensions

### Core API

A schema extension is a shared, typed descriptor with a provider:

```python
@dataclass(frozen=True, slots=True, eq=False)
class SchemaExtension[T]:
    provider: Callable[[Schema], T]
```

Schemas expose:

```python
class Schema:
    def get_extension[T](self, extension: SchemaExtension[T]) -> T:
        ...
```

The HTTP runtime creates one extension descriptor:

```python
HTTP_BINDING_SCHEMA_EXTENSION = SchemaExtension(
    _build_http_binding_schema_metadata
)
```

Every HTTP protocol instance uses the module-level descriptor. Each schema
caches one `HTTPBindingSchemaMetadata` value for that descriptor.

### Cache Requirements

`Schema` allocates its extension dictionary on first use and keys entries by
descriptor identity. Providers publish complete values. Concurrent cache
misses may invoke a provider more than once, which avoids a lock on the lookup
path.

The cache is an implementation attribute. It stays out of schema equality,
representation, `dataclasses.fields()`, `dataclasses.asdict()`, and the
generated constructor. `dataclasses.replace()` creates a schema with an empty
cache.

Extension values use immutable containers. `HTTPBindingSchemaMetadata` is a
frozen, slotted dataclass whose collections are tuples.

### HTTP Binding Metadata

The HTTP extension stores both request and response metadata:

```python
@dataclass(frozen=True, slots=True)
class HTTPBindingSchemaMetadata:
    request_bindings: tuple[Binding, ...]
    response_bindings: tuple[Binding, ...]

    has_request_body: bool
    has_response_body: bool

    payload_member: Schema | None
    event_stream_member: Schema | None

    response_bound_members: tuple[
        tuple[Schema, Binding, str | None, bool], ...
    ]
    response_status: int
```

`request_bindings` and `response_bindings` are indexed by
`Schema.member_index`. They are separate because a trait such as `@httpQuery`
is a request binding but is treated as a document-body member if the same
structure is used as an output.

Response-bound entries retain schema-member order and precompute:

* The member schema.
* The response binding.
* The normalized lowercase header name.
* Whether the member is list-valued.

The name field stores the prefix for prefix-header entries and is `None` for
status and payload bindings. This ordered tuple avoids scanning body members
while preserving the existing deserializer consumer order.

Callers use `HTTPBindingSchemaMetadata` instead of repeating trait inspection.
New fields require a benchmark that identifies repeated work in a serde path.

### Document Body Metadata

The extension records whether request and response structures contain document
body members. Document codecs continue to receive the original structure
schema.

The original schema preserves codec behavior and keeps one effective schema per
Smithy shape ID. Filtered document schemas require an explicit schema identity
contract for codecs.

## Request Serialization

### `HTTPBindingSerializer`

`HTTPBindingSerializer` is a structure-member serializer and request builder:

```python
class HTTPBindingSerializer(InterceptingSerializer):
    def __init__(
        self,
        *,
        payload_codec: Codec,
        schema: Schema,
        http_trait: HTTPTrait,
        endpoint_trait: EndpointTrait | None = None,
        omit_empty_payload: bool = True,
    ) -> None:
        ...

    def build_request(self) -> HTTPRequest:
        ...
```

The constructor:

1. Gets the cached `HTTPBindingSchemaMetadata`.
2. Creates serializers for headers, query parameters, path labels, and host
   labels.
3. Selects the payload mode:
   * Event stream.
   * Raw `@httpPayload`.
   * Structured `@httpPayload`.
   * Implicit document body.
4. Opens the document-body structure when required.

Generated `serialize_members()` calls the normal `ShapeSerializer` methods.
`HTTPBindingSerializer.before()` performs an indexed route lookup and returns
the serializer for that binding:

```python
def before(self, schema: Schema) -> ShapeSerializer:
    binding = self._binding_metadata.request_bindings[
        schema.expect_member_index()
    ]
    match binding:
        case Binding.HEADER | Binding.PREFIX_HEADERS:
            return self.header_serializer
        case Binding.QUERY | Binding.QUERY_PARAMS:
            return self.query_serializer
        case Binding.LABEL:
            return self.path_serializer
        case Binding.HOST:
            return self.host_prefix_serializer
        case _:
            return self._payload_serializer
```

`build_request()`:

* Closes an implicit document-body structure.
* Resolves the final payload stream.
* Adds the payload content type and known content length.
* Resolves the host prefix, path, and query string.
* Returns an `HTTPRequest`.

If member serialization raises, `abort()` closes the document serializer with
the active exception information.

### Protocol Integration

The generated fast path is:

```python
serializer = HTTPBindingSerializer(
    payload_codec=self.payload_codec,
    schema=operation.input_schema,
    http_trait=operation.schema.expect_trait(HTTPTrait),
    endpoint_trait=operation.schema.get_trait(EndpointTrait),
)
input.serialize_members(serializer)
return serializer.build_request()
```

The protocol still supports handwritten `SerializeableShape`
implementations that do not implement `SerializeableStruct`:

```python
if isinstance(input, SerializeableStruct):
    input.serialize_members(serializer)
    return serializer.build_request()

legacy = HTTPRequestSerializer(...)
input.serialize(legacy)
if legacy.result is None:
    raise ExpectationNotMetError("Expected a serialized HTTP request.")
return legacy.result
```

Generated operation inputs are structures and use the direct path. Handwritten
inputs that only implement `serialize()` use `HTTPRequestSerializer`.

### Compatibility Facade

`HTTPRequestSerializer` remains available with its existing constructor and
`result` behavior. Its `begin_struct()` implementation delegates to
`HTTPBindingSerializer`.

Callers can continue to instantiate `HTTPRequestSerializer` or pass it to a
generated shape's `serialize()` method.

## Response Deserialization

### `HTTPResponseDeserializer`

`HTTPResponseDeserializer` keeps its public name and constructor. It implements
`ShapeDeserializer` and uses cached binding metadata.

`read_struct()` performs three steps:

1. Gets the cached `HTTPBindingSchemaMetadata`.
2. Reads precomputed non-body response bindings in schema-member order.
3. Delegates the original response schema to the payload codec when document
   body members are present.

The cached tuple contains only transport-bound members. `read_struct()` visits
those members directly, then delegates document members to the payload codec.
Location-specific `ShapeDeserializer` implementations continue to read scalar
and collection values.

## Response Serialization

`HTTPResponseSerializer` uses the same `HTTPBindingSchemaMetadata`:

* `response_bindings` route members.
* `has_response_body` determines whether the payload codec is invoked.
* `response_status` provides the modeled default.
* Request and response serialization share payload and event-stream metadata.

`HTTPResponseSerializer` retains its public name and constructor.

`HTTPResponseBindingSerializer` is an implementation helper and consumes the
cached binding metadata directly.

## Payload Modes

### Implicit Document Body

The HTTP binding serializer routes document-body members to the serializer
created by the payload codec. The codec receives the original structure schema.

`omit_empty_payload` controls whether the serializer writes an empty body.

### Explicit Payload

String, enum, and blob payloads use raw payload serialization. Their default
content types are:

| Shape | Content type |
|---|---|
| String or enum | `text/plain` |
| Blob | `application/octet-stream` |

`@mediaType` overrides the default.

The payload codec serializes and deserializes aggregate payloads with the
payload member schema.

### Streaming Payload

A streaming blob passes through without buffering. For `@requiresLength`, the
runtime uses an existing `Content-Length` field or calls `tell()` and `seek()`
on a synchronous stream. It raises `SerializationError` when neither source
provides a length.

### Event Stream

Event-stream payloads retain the existing writable/readable async body
behavior. Event message serialization and deserialization remain the
responsibility of the event-stream runtime.

## Compatibility

Generated models already provide `serialize()`, `serialize_members()`,
`deserialize()`, and schemas with stable member indexes. The protocol selects a
different existing method, so generated output stays unchanged.

| Caller | Expected result |
|---|---|
| Generated SDK input | Uses `serialize_members()` fast path |
| Generated SDK output | Uses existing `deserialize()` callback path |
| Handwritten shape with both serialization methods | Uses fast path |
| Handwritten shape with only `serialize()` | Uses compatibility facade |
| Direct `HTTPRequestSerializer` user | Existing API remains available |
| Direct `HTTPRequestBindingSerializer` user | Existing constructor remains available |
| Direct `HTTPResponseDeserializer` user | Existing name uses the cached implementation |

Document codecs receive the original root schema. This preserves wire behavior
for responses whose document body also contains transport-bound members.

## Relationship to smithy-java and smithy-php

smithy-java and smithy-php separate HTTP location routing from document codec
logic and derive binding knowledge from model metadata. Smithy Python uses
`SchemaExtension` for that metadata and keeps its existing
`ShapeSerializer` and `ShapeDeserializer` contracts.

Python member schemas carry `Schema.member_index`, which indexes request and
response route tables. Generated deserialization keeps the consumer callback
instead of filling a positional member buffer.

## Performance

The Rest JSON benchmark ran on an x86 benchmark instance. It uses the
`AwsSdkPerformanceBenchmarkModels` artifacts and exercises the complete client
protocol path. Each case used 5,000 warmup iterations and 10,000 measured
iterations.

| Group | Geometric mean p50 change |
|---|---:|
| Request serialization | 49.7% faster |
| Response deserialization | 45.2% faster |
| All 10 Rest JSON cases | 47.5% faster |

| Case | Before | After | Change |
|---|---:|---:|---:|
| Serialize CopyObject baseline | 33.94 us | 13.85 us | 59.2% faster |
| Serialize CopyObject M | 109.66 us | 87.23 us | 20.5% faster |
| Serialize PutObject S | 38.72 us | 17.89 us | 53.8% faster |
| Serialize PutObject M | 39.35 us | 18.18 us | 53.8% faster |
| Serialize PutObject L | 38.91 us | 18.06 us | 53.6% faster |
| Deserialize CopyObject baseline | 24.52 us | 12.26 us | 50.0% faster |
| Deserialize CopyObject M | 68.39 us | 51.71 us | 24.4% faster |
| Deserialize GetObject S | 56.43 us | 29.00 us | 48.6% faster |
| Deserialize GetObject M | 57.17 us | 28.33 us | 50.4% faster |
| Deserialize GetObject L | 56.82 us | 29.05 us | 48.9% faster |

The direct `serialize_members()` call removes the root structure wrapper.
Cached route tables remove matcher construction. Ordered response metadata
visits transport-bound members directly and stores normalized header names.

## Validation

* Package tests: 1,994 passed and 9 skipped.
* Generated AWS JSON 1.0, AWS JSON 1.1, AWS Query, and Rest JSON protocol suites
  passed.
* Ruff and Pyright passed.
* All Python packages built.
* All 64 serde artifact cases passed validation.

## Alternatives

### Rebuild Matchers for Each Operation

This keeps the current control flow but repeats trait classification and schema
walks. The x86 Rest JSON benchmark measures the cost removed by cached metadata.

### Generate Protocol Serde

Generated HTTP routing duplicates protocol logic in each client and increases
generated package size. Shared runtime components keep routing behavior in one
package.

### Cache Metadata on Codec Instances

A codec-local cache duplicates schema metadata across codec instances and
requires the runtime to manage each cache's lifetime. The schema-local cache
shares one value across protocol instances.

### Store HTTP Fields Directly on `Schema`

HTTP fields on `Schema` couple smithy-core to HTTP transport concerns. Typed
extensions keep the core schema transport-neutral.

## Future Work

* Add schema-attached target type and structure construction hooks.
* Deserialize into positional member buffers before constructing structures.
* Add timestamp or collection metadata when a benchmark identifies repeated
  formatting work.
* Define codec schema identity before adding filtered document schemas.
* Apply schema extensions to JSON, XML, and query codecs.
* Audit external matcher usage before changing matcher visibility.
