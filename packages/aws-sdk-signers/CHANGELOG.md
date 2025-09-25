# Changelog

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
