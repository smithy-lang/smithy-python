# Changelog

## Unreleased

### Features
* Added AsyncEventSigner for Amazon Event Stream event signing.
* Added new ``uri_encode_path`` parameter to SigV4SigningProperties.
  This boolean can be toggled to double encode the URI path.

### Bugfixes
* Fixed bug with async seekable payloads on requests.
* Fixed bug where paths were not being properly double-encoded.

## 0.0.2

### Feature
* Added new ``content_checksum_enabled`` parameter to SigV4SigningProperties.

  This will enable users to control the inclusion of the `X-Amz-Content-SHA256`
  header required by S3. This is _disabled_ by default, so you will need to
  set this to `True` for any S3 requests.

### Bugfixes
* Fixed incorrect exclusion of `X-Amz-Content-SHA256` header from some requests.

## 0.0.1

### Features
* Added SigV4Signer to sign arbitrary requests sychronously.
* Added AsyncSigV4Signer to sign arbitrary requests asychronously.
* Added example SigV4Auth for integrating directly with Requests'
  ``auth`` parameter.
* Added SigV4Signer for integrating with the AIOHTTP request
  workflow.
* Added SigV4Curl for generating signed curl commands.

