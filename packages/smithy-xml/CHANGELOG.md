# Changelog

## v0.3.0

### Breaking Changes
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.

### Features
* XML payloads are now eagerly parsed before deserialization, improving performance for both `bytes` and `BytesReader` inputs.

### Enhancements
* Added support for Python 3.15.

## v0.2.0

### Features
* Added XML serialization support to `XMLCodec`.

### Bug fixes
* Fixed deserialization of `@xmlFlattened` structure lists and of prefixed `@xmlAttribute` names. The root element name is no longer validated, and a structure's `@xmlName` no longer renames members that target it.

## v0.1.0

### Features
* Added initial support for XML deserialization in Smithy clients.
