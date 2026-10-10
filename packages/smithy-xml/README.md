# smithy-xml

This package provides generic XML serialization and deserialization support
for Smithy clients and servers.

## Deserialization modes

`XMLCodec` supports eager and streaming deserialization. The default `AUTO`
mode eagerly parses byte payloads and incrementally parses `BytesReader`
payloads:

```python
from smithy_xml import XMLCodec, XMLDeserializationMode

codec = XMLCodec(
    deserialization_mode=XMLDeserializationMode.STREAMING,
)
```

Eager mode is faster for buffered payloads but materializes the complete XML
tree before shape deserialization. Streaming mode preserves incremental parser
consumption for reader inputs. Generated clients using an XML protocol expose
the same choice through `xml_deserialization_mode` on their configuration.
