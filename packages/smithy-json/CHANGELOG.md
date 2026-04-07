# Changelog

## v0.2.2

### Enhancements
* Fixed string serialization to escape all control characters (U+0000-U+001F) per [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259#section-7), preventing invalid JSON output for multiline and other control-character-containing strings. ([#647](https://github.com/smithy-lang/smithy-python/pull/647))

## v0.2.1

### Dependencies
* Removed strict pinning on `smithy-core` in favor of client managed versions.

## v0.2.0

### Dependencies
* Bump `smithy-core` from `~=0.1.0` to `~=0.2.0`.

## v0.1.0

### Enhancements
* Use shared settings for JSON codec
* Pass JSON document class through settings
* Use natural dict ordering for member index

## v0.0.1

### Features
* Added support for json primitives in Smithy clients.
