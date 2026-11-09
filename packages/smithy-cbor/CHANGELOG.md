# Changelog

## v0.2.0

### Breaking Changes
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.

### Enhancements
* Added support for Python 3.15.

## v0.1.0

### Features
* Added the `smithy-cbor` package: an RFC 8949 CBOR codec supporting the `smithy.protocols#rpcv2Cbor` protocol.

### Enhancements
* Cache CBOR member encodings and structure member lookup metadata using schema extensions.

### Bug fixes
* Allow CBOR integer tokens within the signed 64-bit range to deserialize into Smithy float and double shapes.
