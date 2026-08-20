# Changelog

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
