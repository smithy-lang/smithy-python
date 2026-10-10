# smithy-json

This package provides generic JSON serialization and deserialization support
for Smithy clients and servers.

## Deserialization modes

`JSONCodec` supports eager and streaming deserialization. The default `AUTO`
mode eagerly parses byte payloads and incrementally parses `BytesReader`
payloads:

```python
from smithy_json import JSONCodec, JSONDeserializationMode

codec = JSONCodec(
    deserialization_mode=JSONDeserializationMode.STREAMING,
)
```

Eager mode is faster for buffered payloads but temporarily materializes the
complete JSON value tree. Streaming mode avoids that additional allocation.
Generated clients using a JSON protocol expose the same choice through
`json_deserialization_mode` on their configuration.
