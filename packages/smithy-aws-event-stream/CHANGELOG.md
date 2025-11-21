# Changelog

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
