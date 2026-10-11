# Changelog

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
