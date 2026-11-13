# Changelog

## v0.9.0

### Dependencies
* Bump `smithy-core` from `~=0.11.0` to `~=0.12.0`.
* Bump `smithy-cbor` from `~=0.3.0` to `~=0.4.0`.
* Bump `smithy-json` from `~=0.5.0` to `~=0.6.0`.
* Bump `smithy-aws-event-stream` from `~=0.5.0` to `~=0.6.0`.

## v0.8.0

### Breaking Changes
* Removed the eventloop parameter from AWSCRTHTTPClient.
* Removed `HostPrefixSerializer` and `Binding.HOST`. `@hostLabel` no longer changes where a member is serialized and smithy-core now applies host prefixes.

### Features
* Added support for the `aws.protocols#awsQueryCompatible` trait to `RpcV2CborClientProtocol` and `RpcV2JsonClientProtocol`.
* Added `RpcV2JsonClientProtocol` and `AsyncRpcV2JsonClientProtocol`, implementations of the `smithy.protocols#rpcv2Json` protocol, and a `json` extra that installs `smithy-json`.

### Enhancements
* Documented HTTPQueryMapValueSerializer.
* Completed type annotations and __all__ declarations for the public API.
* Allow MockHTTPClient and AsyncMockHTTPClient responses to have stream bodies.
* Imported symbols from their defining modules.

### Bug fixes
* Iterating a `Urllib3HTTPClient` response body now yields 64 KiB chunks instead of 1 KiB ones.
* RPC v2 protocols (including `RpcV2CborClientProtocol` and `AsyncRpcV2CborClientProtocol`) now treat a response whose `Smithy-Protocol` header does not match the request as malformed, raising a `CallError` based solely on the HTTP status code without interpreting the body.
* Declared smithy-aws-event-stream as the eventstream extra, bounded yarl, and raised MissingDependencyError when the aiohttp extra is not installed.
* `Urllib3HTTPClient` now streams request bodies that are readers with a known length or chunked transfer encoding, such as an open file, instead of reading the whole body into memory first. Uploads are sent in 128 KiB blocks.
* Derived the CRT timeout error from SmithyHTTPError.
* `Field.as_string()` now joins values with its `delimiter` argument, a bare comma by default, instead of always using a comma and a space. The `Field` interface now declares the `delimiter` parameter. `AIOHTTPClient` and `Urllib3HTTPClient` no longer send trailer fields as headers, matching `AWSCRTHTTPClient`.
* `AIOHTTPClient` now reads request bodies that are readers, such as open files, in 128 KiB chunks instead of 1 KiB ones, which made uploads about 25 times faster on fast connections. An async iterable body is now passed to aiohttp unchanged, so each item is sent as soon as it's produced.
* `AIOHTTPClient` now sends requests that set `Transfer-Encoding: chunked` using aiohttp's chunked uploads. Previously aiohttp rejected the header with a `ValueError`.
* RPC v2 protocols now raise a `CallError` instead of an unrelated exception for error responses whose body cannot be decoded or whose `__type` is not an absolute shape ID, and resolve `__type` values with a `:`-delimited suffix to the modeled error.
* The urllib3 HTTP client now streams response bodies instead of reading each one into memory. A streaming output, such as an S3 `GetObject` body, holds its connection until it is read to the end or closed, so use it in a `with` block to release the connection early.

### Dependencies
* Bump `smithy-core` from `~=0.10.0` to `~=0.11.0`.
* Bump `smithy-cbor` from `~=0.2.0` to `~=0.3.0`.
* Bump `smithy-json` from `~=0.4.0` to `~=0.5.0`.
* Bump `smithy-aws-event-stream` from `~=0.4.0` to `~=0.5.0`.

## v0.7.0

### Breaking Changes
* Replaced the async protocols with event stream mixins composed onto the sync protocols. `AsyncHttpClientProtocol`, `AsyncHttpBindingClientProtocol` and `AsyncRpcClientProtocol` are removed; use `AsyncHttpEventStreamMixin` or `AsyncRpcEventStreamMixin` with a protocol from `smithy_http.protocols`. `AsyncRpcV2CborClientProtocol` is kept as such a composition.
* Moved `HTTPRequest` and `HTTPResponse` to `smithy_http`, and their protocols and `HTTPErrorIdentifier` to `smithy_http.interfaces`. Removed `consume_body_async`.
* Removed `AsyncAPIKeySigner`; `AsyncAPIKeyAuthScheme` returns the sync `APIKeySigner`. Renamed `smithy_http.aio.restjson.parse_rest_json_error_info` to `parse_rest_json_error_info_async`.
* Serialized request bodies are now synchronous for both sync and async clients. `HTTPBindingSerializer`'s `async_body` parameter is replaced by `event_stream_body`, and `RawPayloadDeserializer` returns streaming payloads as the transport provides them.
* Moved async implementations to `smithy_http.aio` and added the `Async` prefix to their names, for example `AsyncHTTPClient`, `AsyncHttpClientProtocol`, `AsyncHttpBindingClientProtocol`, `AsyncRpcV2CborClientProtocol` and `AsyncAPIKeyAuthScheme`. The unprefixed names are reserved for sync implementations. Update imports to the `aio` paths.
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.
* `smithy_http.testing.MockHTTPClient` is now synchronous. Async clients use `smithy_http.aio.testing.AsyncMockHTTPClient`.
* Renamed `AWSCRTHTTPResponse` to `AsyncAWSCRTHTTPResponse`, and `smithy_http.aio.auth.apikey.APIKeyResolverConfig` to `AsyncAPIKeyResolverConfig`.

### Features
* Added synchronous HTTP support: `smithy_http.urllib3.Urllib3HTTPClient`, the sync protocols in `smithy_http.protocols`, `smithy_http.restjson.parse_rest_json_error_info` and `smithy_http.identity.apikey.APIKeyIdentityResolver`.
* Added `connect_timeout` and `read_timeout` to `Urllib3HTTPClientConfig`, both defaulting to 60 seconds, so sync requests no longer wait indefinitely. A request's `HTTPRequestConfiguration.read_timeout` takes precedence.
* Added `max_pool_connections` to `Urllib3HTTPClientConfig`, the connections kept for reuse per host, defaulting to 10 instead of urllib3's 1.
* Added a RpcClientProtocol base class and client-side event stream support for the rpcv2Cbor protocol.

### Enhancements
* AWSCRTHTTPClient now negotiates HTTP/2 per request for operations that require it (event streams), advertising only HTTP/2 in ALPN and pooling those connections separately from HTTP/1.1 ones, so a single client serves both HTTP/1.1 operations and HTTP/2 event streams without configuration. The client-wide force_http_2 config remains as an override.
* Added a trust_store_path option to AWSCRTHTTPClientConfig for overriding the TLS trust store with a custom CA bundle.
* Added support for Python 3.15.

### Bug fixes
* Fixed HTTP serializers sending seekable streaming payloads, such as files, without a Content-Length and sending a modeled Content-Length twice.
* Fixed API key auth setting the request path to the URI password.
* `APIKeyIdentity` no longer includes `api_key` in its repr, which keeps it out of debug logs.

### Dependencies
* Bump `smithy-cbor` from `~=0.1.0` to `~=0.2.0`.

## v0.6.0

### Features
* `HttpClientProtocol` implements `extract_response_metadata()`, reporting the HTTP status code.
* Added a naive `RpcV2CborClientProtocol` for the `smithy.protocols#rpcv2Cbor` protocol (optional `cbor` extra).
* Added schema-cached HTTP binding plans for members, operations, payloads, and request and response dispatch.

### Dependencies
* Bump `smithy-cbor` from `~=0.0.0` to `~=0.1.0`.

## v0.5.0

### Features
* Added deterministic connection-pool cleanup and async context manager support to HTTP clients.

### Bug fixes
* Stream aiohttp response bodies incrementally to enable true output event streams.
* Fixed `AIOHTTPClient` to stop dropping valueless query parameters and automatically adding a `Content-Type` to bodyless POST, PUT, and PATCH requests.
* Fixed duplicate Content-Type headers when a member is bound to Content-Type.

## v0.4.4

### Enhancements
* Added a protocol hook for extracting server-provided retry delays from error responses.
* Declared `AWSCRTHTTPClient` as duplex (bidirectional) streaming capable via `SUPPORTS_DUPLEX_STREAMING`. `AIOHTTPClient` explicitly does not support duplex streaming.
* Disabled automatic redirects in `AIOHTTPClient` so that redirect responses are returned to the caller instead of being followed transparently.

## v0.4.3

### Enhancements
* Enabled HTTP binding protocols to resolve modeled response errors when wire identifiers do not exactly match registered shape IDs. ([#742](https://github.com/smithy-lang/smithy-python/pull/742))

### Bug fixes
* Fixed `AIOHTTPClient` sending omitted request payloads with chunked transfer encoding.

## v0.4.2

### Bug fixes
* Disabled automatic response decompression in `AIOHTTPClient`.

## v0.4.1

### Bug fixes
* Fixed `AWSCRTHTTPClient` to send HTTP/1.1 request bodies via `body_stream` instead of the HTTP/2-only `request_body_generator`.

## v0.4.0

### Breaking Changes
* Replace `FieldPosition` enum values with string literals for `Field.kind`. Use "header" and "trailer" instead of `FieldPosition.HEADER` and `FieldPosition.TRAILER`.

### Dependencies
* Upgrade CRT to 0.32.0 to fix bug where HTTP2 exceptions could hang indefinitely

## v0.3.1

### Bug fixes
* Fixed empty error messaging for CRT-based timeout errors.

### Dependencies
* Removed strict pinning on `smithy-core` in favor of client managed versions.

## v0.3.0

### Features
* Added `MockHTTPClient` for testing SDK clients without making real HTTP requests.

### Enhancements
* Added timeout error detection for HTTP clients

### Dependencies
* Bump `smithy-core` from `~=0.1.0` to `~=0.2.0`.

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
