# smithy-python

`smithy-python` provides Python-native code generation for Smithy models.
Standalone types generation is available; client generation remains under
development.

```console
smithy-python generate client [OPTIONS]
smithy-python generate types [OPTIONS]
```

`generate types` produces an installable package containing compact schemas, lazy
runtime models, and a complete static typing surface. Run
`smithy-python generate types --help` for artifact settings.

`generate client` currently exits with an error explaining that client generation
has not been implemented.
