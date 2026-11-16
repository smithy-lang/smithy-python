# smithy-python

`smithy-python` provides Python-native code generation for Smithy models.
Standalone types generation and RPCv2 CBOR client generation are available.

```console
smithy-python generate client [OPTIONS]
smithy-python generate types [OPTIONS]
```

`generate types` produces an installable package containing compact schemas, lazy
runtime models, and a complete static typing surface. Run
`smithy-python generate types --help` for artifact settings.

`generate client` produces an importable client package for one service. Run
`smithy-python generate client --help` for artifact settings.
