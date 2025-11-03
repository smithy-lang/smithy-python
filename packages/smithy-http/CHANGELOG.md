# Changelog

## v0.2.1

### Bug fixes
* Add port to CRT HTTP client's host header.

## v0.2.0

### Breaking Changes
* Update `AWSCRTHTTPClient` to integrate with the new AWS CRT async interfaces. ([#573](https://github.com/smithy-lang/smithy-python/pull/573)). The `AWSCRTHTTPResponse` constructor now accepts a `stream` argument of type `awscrt.aio.http.AIOHttpClientStreamUnified`. Additionally, the following classes were removed: `CRTResponseBody`, `CRTResponseFactory`, and `BufferableByteStream`.

## v0.1.0

### Breaking Changes
* Removed identity and auth interfaces in favor of the transport-agnostic interfaces introduced in `smithy-core`.

### Features
* Introduced schema-based serializers and deserializers for HTTP binding protocols.

## v0.0.1

### Features
* Added support for aiohttp and AWSCRT http clients.
* Added basic HTTP primitives and interfaces for Smithy clients.
