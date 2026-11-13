# Changelog

## v0.6.0

### Breaking Changes
* Renamed `EventSigner` to `SigV4EventSigner`, to match `SigV4Signer` and `SigV4ChunkSigner`.

### Features
* Added ResourceLifecycleError, a BaseAWSSDKException and RuntimeError subclass, raised when EventSigner signs after the final empty event.
* Added `SigV4ChunkSigner`, which signs the chunks and trailer of an `aws-chunked` payload as it is sent, continuing the SigV4 signature of a request signed with the `STREAMING-AWS4-HMAC-SHA256-PAYLOAD-TRAILER` payload hash. `SigV4ChunkSigner.from_signed_request` creates one from a signed request.

### Enhancements
* Completed type annotations and __all__ declarations for the public API.

### Bug fixes
* Fixed SigV4 signature mismatches (HTTP 403) on requests that send a header with more than one value, such as `Content-Encoding` with `gzip` and `aws-chunked`. The signer now trims each value and joins them with a bare comma, without quoting, which matches how services rebuild repeated headers before checking the signature. Fields with no values and trailer fields are no longer signed as headers. The `Field` interface also declares a bare comma as the default `as_string()` delimiter.
* Excluded secret credentials and the URI password from repr.

## v0.5.0

### Breaking Changes
* Replaced `AsyncEventSigner` with the synchronous `EventSigner`, which is thread-safe.
* Moved `AsyncSigV4Signer` and `AsyncBytesReader` to `aws_sdk_signers.aio`, and `AsyncByteStream` and `AsyncSeekable` to `aws_sdk_signers.aio.interfaces.io`. `AsyncSigV4Signer` now also signs requests with sync bodies, and its `string_to_sign` and `generate_authorization_field` are synchronous.
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.

### Enhancements
* Added support for Python 3.15.

### Bug fixes
* Fixed `SigV4Signer` ignoring a preset `X-Amz-Content-SHA256` header and not signing event stream requests with the streaming payload hash.
* Fixed signing requests whose body can't be deep-copied, such as files and async generators. The signers now share the body with the signed request instead of copying it, so signing reads the original body directly.

## v0.4.0

### Features
* Added a `normalize_path` option to `SigV4SigningProperties`. Set it to `False`, along with `uri_encode_path`, to sign the URI path exactly as sent, as S3 requires.

### Bug fixes
* Excluded hop-by-hop and proxy headers (`Keep-Alive`, `Proxy-Authenticate`, `Proxy-Authorization`, `TE`, `Trailer`, `Transfer-Encoding`, and `Upgrade`) from SigV4 signing, so signatures stay valid when a proxy or the HTTP layer modifies them.

## v0.3.1

### Enhancements
* Removed the `AWSSDKWarning` emitted during SigV4 payload signing. It fired on every signed request regardless of body size, adding noise on the default code path (and, under warnings-as-errors, could turn signing into a raised exception).

## v0.3.0

### Features
* Added `AsyncEventSigner.sign_empty` for SigV4-signed Amazon Event Stream terminator frames. This supports services that require a final signed empty message before the HTTP body stream closes.

## v0.2.0

### Breaking Changes
* Replace `FieldPosition` enum values with string literals for `Field.kind`. Use "header" and "trailer" instead of `FieldPosition.HEADER` and `FieldPosition.TRAILER`.

### Bug fixes
* Fixed SigV4 signature computation for URIs with literal query parameters (e.g., ?sync). parse_qsl was silently dropping query keys without values, causing InvalidSignatureException.

## v0.1.0

### Breaking Changes
* Changed the `signing_properties` and `http_request` args to `properties` and `request` for the `sign` methods in `SigV4Signer` and `AsyncSigV4Signer`.

### Enhancements
* Update the async signer to use the special payload hash for event stream operations.
* Check seekable in aws signers

## v0.0.3

### Features
* Added `AsyncEventSigner` for Amazon Event Stream event signing.
* Added new `uri_encode_path` parameter to `SigV4SigningProperties`. This boolean can be toggled to double encode the URI path.

### Bug fixes
* Fixed bug with async seekable payloads on requests.
* Fixed bug where paths were not being properly double-encoded.

## v0.0.2

### Features
* Added new `content_checksum_enabled` parameter to `SigV4SigningProperties`. This will enable users to control the inclusion of the `X-Amz-Content-SHA256` header required by S3. This is disabled by _default_, so you will need to set this to `True` for any S3 requests.

### Bug fixes
* Fixed incorrect exclusion of `X-Amz-Content-SHA256` header from some requests.

## v0.0.1

### Features
* Added `SigV4Signer` to sign arbitrary requests synchronously.
* Added `AsyncSigV4Signer` to sign arbitrary requests asynchronously.
* Added example `SigV4Auth` for integrating directly with Requests' `auth` parameter.
* Added `SigV4Signer` for integrating with the AIOHTTP request workflow.
* Added `SigV4Curl` for generating signed curl commands.
