# Changelog

## v0.1.0

### Features
* Added the `smithy-cbor` package: an RFC 8949 CBOR codec supporting the `smithy.protocols#rpcv2Cbor` protocol.

### Enhancements
* Cache CBOR member encodings and structure member lookup metadata using schema extensions.

### Bug fixes
* Allow CBOR integer tokens within the signed 64-bit range to deserialize into Smithy float and double shapes.
