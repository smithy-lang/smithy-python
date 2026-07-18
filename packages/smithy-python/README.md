# Smithy Python codegen

> **POC status:** This package is experimental. The Java generator in the repository's
> `codegen` directory remains authoritative until a phased migration is approved.

Python-native code generation for Smithy models. The command-line interface is
designed to be invoked by Smithy's process-based `run` plugin. After the package
is published, install it as a persistent command-line tool:

```console
uv tool install smithy-python
```

Then generate a client with:

```console
smithy-python generate client \
  --service example.weather#Weather \
  --module weather \
  --module-version 1.0.0
```

For a one-off evaluation without a persistent installation, use
`uvx smithy-python generate client` instead.

The command reads a Smithy JSON AST model from standard input and writes generated
files to `SMITHY_PLUGIN_DIR`. Pass `--output` when invoking it directly.

Use `smithy-python generate types` to generate a standalone types package. Python
plugins can be installed through the `smithy_python.codegen.plugins` entry-point
group or loaded explicitly with `--plugin package.module:object`.
