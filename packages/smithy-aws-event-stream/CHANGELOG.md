# Changelog

## v0.6.0

### Dependencies
* Bump `smithy-core` from `~=0.11.0` to `~=0.12.0`.

## v0.5.0

### Breaking Changes
* Made SigningConfig generic in its identity, identity properties, and signing properties, so it depends only on smithy-core and rejects a signer and identity resolver that disagree.

### Enhancements
* Completed type annotations and __all__ declarations for the public API.
* Imported symbols from their defining modules.
* Added docstrings to the public API and ordered public definitions first.

### Dependencies
* Bump `smithy-core` from `~=0.10.0` to `~=0.11.0`.

## v0.4.0

### Breaking Changes
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.
* Added the `Async` prefix to the async event-stream implementations, for example `AsyncEventSigner`. The unprefixed names are reserved for sync implementations. Update imports to the `aio` paths.
* Renamed `AWSEventPublisher` and `AWSEventReceiver` to `AsyncAWSEventPublisher` and `AsyncAWSEventReceiver`, and replaced `Event.decode_async` with `smithy_aws_event_stream.aio.decode_event_async`. `SigningConfig` moved to `smithy_aws_event_stream.signing`, is generic in its identity resolver, and takes a synchronous `EventSigner`.

### Enhancements
* Added support for Python 3.15.

## v0.3.0

### Features
* Added a signed empty end frame to `AWSEventPublisher.close` to signal event stream completion. This supports services that require a final signed empty message before the HTTP body stream closes.

## v0.2.2

### Enhancements
* Handle unknown event types gracefully instead of crashing.

## v0.2.1

### Dependencies
* Removed strict pinning on `smithy-core` in favor of client managed versions.

## v0.2.0

### Dependencies
* Bump `smithy-core` from `~=0.1.0` to `~=0.2.0`.

## v0.1.0

### Breaking Changes
* Update `AWSEventPublisher` to use `SigningConfig` instead of `EventSigner` so identity can be fetched at signing time.

## v0.0.1

### Features
* Added basic support for the [Amazon Event Stream](https://smithy.io/2.0/aws/amazon-eventstream.html) specification.
* Added support for unidirectdional and bidirectional event streams.
