# Changelog

## v0.1.0

### Breaking Changes
* Update `AWSEventPublisher` to use `SigningConfig` instead of `EventSigner` so identity can be fetched at signing time.

## v0.0.1

### Features
* Added basic support for the [Amazon Event Stream](https://smithy.io/2.0/aws/amazon-eventstream.html) specification.
* Added support for unidirectdional and bidirectional event streams.
