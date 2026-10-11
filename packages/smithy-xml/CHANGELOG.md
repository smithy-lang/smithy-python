# Changelog

## v0.2.0

### Features
* Added XML serialization support to `XMLCodec`.

### Bug fixes
* Fixed deserialization of `@xmlFlattened` structure lists and of prefixed `@xmlAttribute` names. The root element name is no longer validated, and a structure's `@xmlName` no longer renames members that target it.

## v0.1.0

### Features
* Added initial support for XML deserialization in Smithy clients.
