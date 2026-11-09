# Changelog

## v0.4.0

### Breaking Changes
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.

### Features
* JSON payloads are now eagerly parsed before deserialization, improving performance for both `bytes` and `BytesReader` inputs.
* Added the `arbitrary_precision_as_string` setting to `JSONCodec` and `JSONSettings` to support the `smithy.protocols#rpcv2Json` protocol, which serializes bigInteger and bigDecimal values as JSON strings.

### Enhancements
* Added support for Python 3.15.
* Improved JSON string serialization performance by using the standard library's JSON string encoder. Strings that aren't valid UTF-8 now fail before any of the string's bytes are written.

## v0.3.0

### Features
* Added serialization and deserialization support for Smithy non-finite floating-point values (`NaN`, `Infinity`, and `-Infinity`) using their JSON string representations.

## v0.2.3

### Bug fixes
* Serialize `IntEnum` members as their underlying integer instead of their `repr`.

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
