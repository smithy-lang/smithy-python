# smithy-json

This package provides generic JSON serialization and deserialization support
for Smithy clients and servers.

## Deserialization

`JSONCodec` eagerly parses `bytes` and `BytesReader` payloads before
deserializing Smithy shapes. This improves deserialization performance while
temporarily materializing the complete JSON value tree.
