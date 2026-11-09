# smithy-xml

This package provides generic XML serialization and deserialization support
for Smithy clients and servers.

## Deserialization

`XMLCodec` eagerly parses `bytes` and `BytesReader` payloads before
deserializing Smithy shapes. This improves deserialization performance while
temporarily materializing the complete XML tree.
