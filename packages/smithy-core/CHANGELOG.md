# Changelog

## v0.11.0

### Features
* Unset `@idempotencyToken` input members are now auto-filled with a UUID v4 before serialization. The same token is sent on every retry.
* Added `RpcV2JsonTrait` for the `smithy.protocols#rpcv2Json` protocol trait.
* Clients now prepend the `@endpoint` trait's host prefix, with its `@hostLabel` values, to the endpoint host. Set `disable_host_prefix_injection` to turn this off.
* Added ResourceLifecycleError, a SmithyError and RuntimeError subclass, raised when an operation is invoked on or a with block enters a closed client.

### Enhancements
* Clients now close the response bodies of failed attempts and failed calls, so they no longer hold connections until they are garbage collected.
* Completed type annotations and __all__ declarations for the public API.

### Bug fixes
* Fixed `RpcV2CborTrait` failing to construct from a `DynamicTrait`.
* `AsyncBytesReader` now joins the items of an async iterable once per read instead of copying the result for each item, which made reading many small items up to 16 times faster.
* Excluded the URI password from repr.
* Iterating an `AsyncBytesReader`, such as an async streaming output with `async for`, now yields 64 KiB chunks instead of 1 KiB ones, which made validated S3 `GetObject` downloads read with `async for` about 15 times faster. Small reads from large items also no longer copy the rest of the item on every read.
* `AsyncBytesReader` now awaits the result of a plain `read()` that returns an awaitable, as an `AwaitableBytesReader`'s does, instead of returning the awaitable as data.

## v0.10.0

### Breaking Changes
* Removed the `input`/`output`/`error_registry` constructor overrides from `APIOperation`. Operations are now constructed from a `static_schema` tuple plus a `model_registry` that resolves input, output, and error types on demand.
* Replaced `ClientProtocol.deserialize_response` with `deserialize_response_program`, which reads response bodies through an injected effect so one implementation serves sync and async clients. `AsyncClientProtocol` now extends `ClientProtocol` with only the event stream methods, and async clients accept any `ClientProtocol`.
* ProtocolSettings now requires a service_schema field; the event_stream_http field was removed and RPC protocols read eventStreamHttp from the service schema's protocol trait.
* Removed `smithy_core.aio.endpoints` and `AsyncClientCall`. Use `smithy_core.endpoints.StaticEndpointResolver` and `smithy_core.client.ClientCall`, which serve both sync and async clients. Async clients accept a sync `smithy_core.interfaces.EndpointResolver` as well as an `AsyncEndpointResolver`.
* Changed generated schemas to a compact tuple encoding hydrated on first use, and reworked `APIOperation` to accept a single `static_schema` tuple with lazily-hydrated `schema`, `input_schema`, `output_schema`, and `error_schemas` properties.
* The request pipeline now resolves the auth scheme and the identity after `read_before_attempt` and before endpoint resolution, then stores the identity in the call context under `smithy_core.auth.RESOLVED_IDENTITY`. This allows endpoint resolution to read account IDs.
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.
* Moved `Request`, `Response`, `AnyStreamingBlob` and `AwaitableBytesReader` to `smithy_core.interfaces` and `read_streaming_blob` to `smithy_core.utils`. Removed `consume_body_async`; use `await read_streaming_blob_async(response.body)`.
* Renamed `smithy_core.aio.types.SeekableAsyncBytesReader` to `AsyncSeekableBytesReader`, and `close`, `seek` and `async_list` in `smithy_core.aio.utils` to `close_async`, `seek_async` and `list_async`.
* Moved async implementations to `smithy_core.aio` and added the `Async` prefix to their names, for example `AsyncClientProtocol`, `AsyncRpcClientProtocol`, `AsyncEndpointResolver`, `AsyncStandardRetryStrategy`, `AsyncSigner` and the event-stream types `AsyncDuplexEventStream`/`AsyncInputEventStream`/`AsyncOutputEventStream`. The unprefixed names are reserved for sync implementations. `ProtocolSettings` and `ProtocolConstructor` moved to `smithy_core.interfaces`. Update imports to the `aio` paths.
* Added the required `auth_schemes` attribute to the `smithy_core.interfaces.Endpoint` protocol. Custom endpoint types that don't subclass `smithy_core.endpoints.Endpoint` must add it.
* `AsyncAuthScheme.signer` may now return a synchronous `Signer`, and `AsyncAuthScheme.event_signer` returns a synchronous `EventSigner`. Removed `smithy_core.aio.interfaces.auth.AsyncEventSigner`.
* Removed the async retry strategies (`smithy_core.aio.retries` and `smithy_core.aio.interfaces.retries`). Async clients use the strategies in `smithy_core.retries`; adaptive rate limiting waits through the client, so it never blocks the event loop.
* Generated model classes are now built lazily from the schema on first access via a `ModelRegistry`, rather than defined eagerly at import. This moves per-class construction cost off the import/cold-start path.

### Features
* Added synchronous clients. `smithy_core.client` provides `Client`, `RequestPipeline` and `ClientCall`, which run the same request pipeline as the async client through the programs in the new public `smithy_core.program` module.
* Add the retry strategy chosen for a call to its request properties under `RETRY_STRATEGY`.
* Added support for `adaptive` retry mode, which builds on standard retries by adding client-side rate limiting that slows the client's sending rate when a service throttles requests.
* Requests now sign with the resolved endpoint's auth scheme overrides. Endpoints that don't support the selected auth scheme raise `UnsupportedAuthSchemeError`.
* Added endpoint BDD resolution with `smithy_core.endpoints.BddEndpointResolver`, which serves sync and async clients, and `smithy_core.endpoints.EndpointBdd`, the endpoint BDD it evaluates.
* Added the operation being invoked to the request properties of each call under `smithy_core.client.OPERATION`, for sync and async clients.

### Enhancements
* Added retries for requests with a seekable streaming payload, which are resent from the position the stream was at when the operation was called.
* `ClientTimeoutError` messages now name the transport error that caused them, since some transports report connection failures as timeouts.
* Added support for Python 3.15.
* Sync clients log under `smithy_core.client`, and async clients under `smithy_core.aio.client`.
* Added optional full shape ID target mappings to `ModelRegistry` so generators can resolve renamed and same-named cross-namespace model targets without ambiguous local-name lookups.

### Bug fixes
* Fixed the request pipeline ignoring the request returned by `modify_before_serialization`. The modified request is now serialized, used for endpoint resolution, and passed to later hooks if serialization fails. `InterceptorChain` now also raises a `TypeError` when a `modify_*` hook returns `None`, instead of passing `None` to the next interceptor.
* Fixed `InterceptorChain` skipping later interceptors when one raised in a `read_*` hook. Every interceptor's read hook now runs, then the last exception is raised and earlier ones are logged. `read_after_attempt` also now passes each exception to later interceptors as the `response`, as `read_after_execution` already did.
* `read_streaming_blob_async` now awaits a reader's `read()` result only when it's awaitable.
* Fixed `read_streaming_blob_async` failing on synchronous readers such as `BytesIO`.
* `RetryStrategyResolver` now caches retry strategies per resolver instead of in a shared process-wide cache, so a client's retry state is no longer reset or shared when many clients are created.
* Fixed `InterceptorChain` discarding changes made by `modify_*` hooks. Each interceptor now receives the value returned by the interceptor before it, so an interceptor that returns its input unchanged no longer undoes earlier modifications. `modify_before_completion` also now calls each interceptor's `modify_before_completion` hook instead of `modify_before_attempt_completion`.
* Restored docstrings on generated model classes, members, enums, and unions, which were dropped from the type stub when model classes became lazily loaded.
* Made `CachingIdentityResolver` thread-safe: concurrent callers share one identity fetch.

## v0.9.0

### Breaking Changes
* Added `extract_response_metadata()` to the `ClientProtocol`. Implementations that extend `HttpClientProtocol` inherit a working one and need no change. Protocols that implement `ClientProtocol` directly must add it.
* A modeled `responseMetadata` member on an operation output or error is now generated as `response_metadata_`, since `response_metadata` is reserved for SDK response metadata.

### Features
* Added `AsyncClient` to `smithy_core.aio.client`, a base class that generated clients inherit for client lifecycle (setup gating, `close`, async context management) and operation dispatch.
* Added schema extensions and cached metadata support.
* Added `ResponseMetadata`, exposing the request ID, extended request ID, and HTTP status code of the response that produced a result. It is attached to operation outputs and to modeled errors via a `response_metadata` attribute.
* Added the `RpcV2CborTrait` protocol trait and the `ORIGINAL_SHAPE_ID` synthetic-trait id to `smithy_core.traits`.
* Added schema extensions and lazily cached schema metadata support.
* Added `ProtocolSettings` and `ProtocolConstructor` to `smithy_core.aio.interfaces`, letting a consumer select a protocol by class alone without importing a private schema module.
* Added `xml_namespace` to `ProtocolSettings`, used by restXml as the default namespace of request payloads.

### Bug fixes
* Fixed the request pipeline merging an auth option's identity properties into the signer properties instead of its signer properties.
* Fixed the registered Smithy IDs for `DefaultTrait`, `IdempotencyTokenTrait`, and `UnitTypeTrait` so schemas resolve these traits correctly.

## v0.8.1

### Enhancements
* Update RetryStrategyResolver.resolve_retry_strategy to accept retry_mode and max_attempts as fallback parameters when retry_strategy is not explicitly set in config.

## v0.8.0

### Features
* Updated standard retry behavior with error-specific backoff, revised quota costs, bounded server-provided retry delays, support for service-specific defaults, and long-polling backoff when retry quota is exhausted.

### Enhancements
* Added `DuplexClientTransport` so transports can declare support for duplex (bidirectional) event streaming. `RequestPipeline.duplex_stream` now fails fast with an `UnsupportedTransportError` when the configured transport does not declare support.

## v0.7.0

### Breaking Changes
* Added `invalidate()` method to the `IdentityResolver` protocol to discard cached identities so the next resolution re-reads its source.

## v0.6.0

### Breaking Changes
* Refactored retry strategies to be async, allowing them to wait internally or use async synchronization primitives if necessary. The `RetryStrategy` protocol moved from `smithy_core.interfaces.retries` to `smithy_core.aio.interfaces.retries`, and `SimpleRetryStrategy`, `StandardRetryStrategy`, and `RetryStrategyResolver` moved from `smithy_core.retries` to `smithy_core.aio.retries`.

### Features
* Added `UnknownEnumMixin` for representing unknown and error-corrected enum/intEnum variants.

## v0.5.0

### Features
* Added `EventSigner.sign_empty` to the protocol for signing empty events.

## v0.4.0

### Features
* Added `error_schemas` to `APIOperation` to expose the operation’s modeled error schemas.
* Added XML binding traits: `XMLNameTrait`, `XMLNamespaceTrait`, `XMLFlattenedTrait`, and `XMLAttributeTrait`.

## v0.3.0

### Breaking Changes
* Refactored `resolve_retry_strategy` to avoid code duplication per operation.

### Enhancements
* Improved default error message for instances of ClientTimeoutError.

## v0.2.0

### Features
* Added support for `standard` retry mode.

## v0.1.1

### Bug fixes
* Fix incorrect header casing for the shape id of eventHeaders.

## v0.1.0

### Breaking Changes
* Introduced transport-agnostic interfaces for identity and auth, replacing the existing interfaces that were coupled to HTTP requests and responses.
* Updated retry interfaces to pull information from exceptions instead of requiring a separate classification step.
* Replaced `Exception` suffix with `Error` to follow PEP8 conventions.

### Features
* Updated schema members to preserve their ordering from the model using dict ordering, which significantly cuts back the amount of code that must be generated.
* Introduced the `ClientProtocol` interface to allow for hand-written protocol implementations and protocol swapping at runtime.
* Introduced a hand-written request pipeline to replace the one that was code-generated in Java.
* Updated exceptions to embed retryablity information.

### Enhancements
* Added usages of `TypeForm` from PEP747 via `typing_extensions` to better support typing for event streams and typed properties.

### Bug fixes
* Fix broken initializer for `HTTPAPIKeyAuthTrait`. ([#533](https://github.com/smithy-lang/smithy-python/pull/553))

## v0.0.2

### Bug fixes
* Fixed incorrect interceptors for `modify_before_signing` and `modify_before_transmit`.

## v0.0.1

### Features
* Added support for minimal components required for SDK generation.
