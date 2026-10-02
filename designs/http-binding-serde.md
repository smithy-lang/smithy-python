# HTTP Binding Serialization and Deserialization

## Abstract

HTTP protocols divide structure members between transport locations such as
headers, labels, query parameters, and the message body. Determining that
division requires inspecting schema traits, but binding-relevant schema state
is stable and reused across requests.

This design derives HTTP binding metadata once per structure and operation
schema and stores it in typed schema extensions. HTTP serializers and
deserializers use the cached metadata to route members, while document codecs
remain responsible only for encoding and decoding payload contents.

## Goals

* Separate HTTP location routing from document encoding.
* Amortize binding discovery across requests and protocol instances.
* Preserve modeled member order when dispatching deserialized values.
* Keep `smithy-core` independent of HTTP-specific metadata.
* Share one canonical schema with every codec and protocol component.

This design does not introduce generated protocol-specific serde, filtered
document schemas, or schema extensions for document codecs.

## Background

HTTP binding traits determine whether a member belongs in a header, query
string, URI label, response status, explicit payload, or implicit document
body. Existing binding matchers derive this information by walking the
structure schema.

Repeating that work for each request or response has two costs:

1. Trait classification and matcher allocation are repeated even though the
   binding-relevant schema state does not change.
2. Response deserialization scans every structure member to find the small
   subset bound outside the document body.

Request and response routing must be modeled separately. For example,
`@httpQuery` is a request binding, but the same member is a document-body
member when its structure is used as an operation output.

## Schema Extensions

`smithy-core` provides a transport-neutral mechanism for attaching derived
metadata to a schema:

```python
@dataclass(frozen=True, slots=True, eq=False)
class SchemaExtension[T]:
    provider: Callable[[Schema], T]


class Schema:
    def get_extension[T](self, extension: SchemaExtension[T]) -> T:
        ...
```

An extension descriptor combines a cache key with the function that derives
its value. Descriptors compare by identity, so independently defined
extensions cannot collide because they use the same provider type or schema
shape ID.

Extension values are built lazily and cached on the schema. Laziness avoids
adding HTTP work to schemas that are never used by an HTTP protocol and allows
other packages to define extensions without registration in `smithy-core`.

The cache is not part of a schema's semantic dataclass state. It does not
participate in equality, representation, serialization through
`dataclasses.asdict`, or construction through `dataclasses.replace`.

Cache misses are lock-free. Concurrent callers may derive the same value more
than once, after which one complete value is retained. Providers therefore
must be deterministic and should return immutable values without externally
visible construction side effects.

## HTTP Binding Metadata

`smithy-http` defines a shared structure schema extension whose value contains:

* A request binding route indexed by `Schema.member_index`.
* A response binding route indexed by `Schema.member_index`.
* Per-member wire names, canonical header names, value shape classification,
  media types, and effective timestamp formats.
* Whether request and response structures contain implicit body members.
* Body-member masks used to limit document codec values to body bindings.
* The explicit payload or event-stream member, including precomputed media
  type, streaming, raw-payload, and length-requirement information.
* Declared request header and query names used to resolve map-binding
  precedence.
* Non-body response bindings in modeled member order.
* A response header lookup table and list-header classification.
* The modeled default response status.

An operation schema extension separately caches the resolved `@http` and
`@endpoint` traits, HTTP method, parsed path, static query string and names,
response status, host-prefix pattern, and greedy label names.

The metadata uses tuples, immutable collections, read-only mappings, and frozen
dataclasses so a cached value cannot be changed by one protocol instance and
observed by another.

Indexed routing is possible because member indexes are stable within a schema.
It makes the hot-path decision a tuple lookup followed by dispatch to the
serializer or deserializer for that HTTP location.

The ordered response entries serve a different purpose from the indexed route
table and response header lookup. They let deserialization visit only
transport-bound members while preserving the order in which the structure
schema presents those members. A compact tuple representation of this route is
used by the deserialization hot path; the richer per-member metadata and header
lookup remain available without adding attribute or response pre-scan overhead
to every response.

## Separation of Responsibilities

The HTTP binding layer owns concerns that depend on HTTP traits:

* Selecting the serializer or deserializer for each binding location.
* Constructing the URI, fields, status, and body stream.
* Choosing between an implicit document body, explicit payload, streaming
  payload, and event stream.
* Applying HTTP content type and content length rules.

The payload codec owns concerns that depend on the document protocol:

* Encoding document-bound members.
* Decoding document-bound members.
* Encoding or decoding aggregate explicit payloads.

This boundary allows the same HTTP routing machinery to be paired with JSON,
XML, query, or other document codecs. It also prevents codecs from needing to
understand URI or field bindings.

## Request Serialization

The request binding serializer is driven by a structure's member walk. For each
member, it uses the cached request route to select a location-specific
serializer. Location serializers use the per-member plan rather than
re-reading binding, timestamp, and media-type traits:

```text
structure member
      |
      v
cached request route
  |     |      |       |
header query  label   payload codec
```

The binding layer establishes payload state before members are written and
finalizes the HTTP request afterward. This is necessary because transport
metadata and document contents are produced during the same member walk.

There are four payload modes:

* Implicit document bodies send unbound request members to the payload codec.
* Explicit codec-encoded payloads send the `@httpPayload` member to the payload
  codec using its member schema.
* Explicit string-like or blob payloads use raw payload handling.
* Event streams use the event-stream body abstraction.

An absent implicit body can be omitted without invoking the codec. Explicit
payloads continue to use their modeled media type and length requirements.

Static URI query names and explicit `@httpQuery` names are cached before
serialization. `@httpQueryParams` entries that collide with either are
discarded regardless of modeled member order. Explicit `@httpHeader` bindings
similarly take precedence over colliding `@httpPrefixHeaders` map entries.

## Response Deserialization

Response deserialization first visits the cached, ordered set of non-body
bindings. Header, prefix-header, status, and explicit-payload values are sent
to their location-specific deserializers.

If the structure has implicit document-body members and the response body is
not empty, the payload codec then reads the document using the same structure
schema. A consumer wrapper uses the cached response body-member mask to forward
only document-bound members. Values present in the document for transport-bound
members are consumed and discarded so streaming codecs remain synchronized.
This avoids changing schema identity while preserving HTTP binding ownership.

An explicit codec-encoded payload is decoded by the payload codec using the
payload member schema. String-like and blob payloads use raw payload handling,
while event-stream payloads use the event-stream body abstraction.

## Response Serialization

Response serialization uses the same extension value as request serialization
and response deserialization. The response route table selects headers,
response status, and payload members, while the cached body flag determines
whether the document codec needs to be opened.

Sharing one metadata value keeps request and response classification rules
together while retaining separate route tables for their direction-specific
semantics.

## Schema Identity

Document codecs receive the canonical structure or payload-member schema
rather than an HTTP-filtered copy.

Using the canonical schema has two benefits:

* A Smithy shape has one effective runtime schema identity.
* Schema-local caches can be shared across HTTP and document processing.

A filtered schema could make body membership explicit to a codec, but it would
also create multiple schemas with the same Smithy shape ID. That requires a
broader contract for schema identity, equality, recursive references, and
extension ownership. Filtered document schemas are therefore deferred until
that contract is defined. The cached body-member mask provides equivalent
top-level filtering without changing nested or recursive schema semantics.

## Tradeoffs

Schema-local caching retains derived metadata for the lifetime of a schema.
This is appropriate for generated schemas, which are long-lived and reused,
but increases their memory footprint after an extension is accessed.

Lock-free initialization keeps cache hits and misses simple, at the cost of
allowing duplicate provider work during a concurrent first access. HTTP
metadata construction is deterministic and bounded by the number of members,
so duplicate first-use work is preferable to a lock on every schema.

Keeping HTTP metadata in `smithy-http` preserves the dependency boundary, but
means the HTTP package requires a version of `smithy-core` that provides the
schema extension API.

## Alternatives

### Rebuild Binding Matchers for Every Message

This keeps all derived state local to one serde operation, but repeats schema
walks, trait inspection, and matcher allocation for stable schemas.

### Cache on Protocol or Codec Instances

Instance-local caches avoid changing `Schema`, but duplicate metadata across
protocol and codec instances. They also require each component to define cache
identity and lifetime independently.

### Add HTTP Fields Directly to `Schema`

Placing route tables on `Schema` would make lookup direct, but would couple
`smithy-core` to HTTP traits and require core changes for future
transport-specific metadata.

### Generate HTTP Binding Serde

Generated routing can avoid runtime trait inspection, but duplicates protocol
logic in every generated client and increases generated package size. Shared
runtime routing keeps behavior and fixes centralized.

### Pass Filtered Schemas to Document Codecs

Filtered schemas make the body subset explicit, but introduce multiple runtime
schemas for one Smithy shape. This alternative remains possible after schema
identity and extension-sharing semantics are defined.

## Future Work

* Define schema identity rules that permit filtered or projected schemas.
* Apply schema extensions to repeated metadata derivation in document codecs.
* Evaluate codec-specific empty-body caching and generated binding serde when
  benchmarks justify their additional complexity.
