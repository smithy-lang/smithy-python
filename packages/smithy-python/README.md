# smithy-python

> [!WARNING]
> This package is an experimental scaffold. It does not generate code yet. The
> Java generator in the repository's `codegen` directory remains authoritative.

`smithy-python` will provide Python-native code generation for Smithy models.
The initial command-line interface exposes the planned client and types generation
commands so that their top-level shape can be developed independently from the
generator implementation.

```console
smithy-python generate client [OPTIONS]
smithy-python generate types [OPTIONS]
```

After validating their invocation options, both generation commands currently exit
with an error explaining that generation has not been implemented. The package is
included in workspace builds to validate its packaging and entry points.
