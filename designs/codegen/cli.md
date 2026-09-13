# Code Generator CLI

The `smithy-python` command is the process interface described in the
[Python Code Generation](index.md) overview. It supports direct use and
invocation from Smithy's
[`run` plugin](https://smithy.io/2.0/guides/smithy-build-json.html#run-plugin).

## Commands

Generation is organized by artifact type:

```console
smithy-python generate client [OPTIONS]
smithy-python generate types [OPTIONS]
```

`client` generates a service client and the data shapes it uses. `types`
generates a standalone package containing only data shapes. Both commands accept
the following process options:

* `--model PATH` reads a JSON AST from a file instead of standard input.
* `--output PATH` selects the output directory. It defaults to the Smithy run
  plugin's output directory (`SMITHY_PLUGIN_DIR`) when invoked by Smithy.

Settings specific to each artifact will be added with the functionality that
consumes them.

### Service Selection

The CLI does not require a service to be named. It resolves the service to
generate as follows:

* `--service SHAPE_ID` selects a specific service shape. The shape MUST exist in
  the model and MUST be a service.
* When `--service` is omitted and the model contains exactly one service shape,
  that service is used.
* When `--service` is omitted and the model contains more than one service
  shape, the command fails with an invocation error that lists the candidates.

The `client` artifact requires a resolved service. The `types` artifact does
not. The CLI MUST NOT synthesize a placeholder service to satisfy generation.

### Generated Shapes

When a service is resolved, both artifacts generate the data shapes in the
service closure: every shape reachable from the service through its operations,
resources, errors, and members. This matches the surface produced by the other
Smithy code generators. Data shapes in the model that are not connected to the
service are not generated, and the CLI reports how many were left out.

When no service is resolved, the `types` artifact generates every data shape in
the model. Smithy guarantees case-insensitively unique shape names only within a
service closure, so in this mode the command fails when two shapes have
case-insensitively equal names, identifying the conflicting shape IDs.

Trait definitions, prelude shapes, and shapes marked `@mixin` are never
generated. Builds that need a different set of shapes, such as types that are
not bound to any operation, apply smithy-build transforms in the projection.
An option to generate every shape in the model regardless of the service MAY be
added when there is a need for it.

The command MUST return zero after successful generation and non-zero when
arguments, settings, the model, or generation are invalid. Diagnostics are
written to standard error. Invalid command syntax and invocation inputs return
2, while I/O and generation failures return 1.

## Smithy `run` Plugin

The Smithy `run` plugin executes an external program during a build. It sends the
projection's Smithy model as a JSON AST to the process's standard input and runs
the process in the plugin's output directory.

A plugin ID MUST use `run::` followed by a custom artifact name. The configured
command identifies the artifact to generate:

```json
{
    "version": "1.0",
    "projections": {
        "client": {
            "plugins": {
                "run::python-client": {
                    "command": ["smithy-python", "generate", "client"]
                }
            }
        }
    }
}
```

Artifact-specific options will be appended to `command` after they are defined.
The `run` plugin can also pass settings through its `env` property, so an option
MAY additionally be read from an environment variable. A command-line option
takes precedence over its environment variable.

The `smithy-python` executable MUST be installed or otherwise available on the
Smithy process's `PATH`. Smithy passes no arguments other than those in
`command`.

### Input and Output

When invoked by Smithy, the CLI reads one JSON AST document from standard input.
The document represents the model after projection transforms have been applied.

The presence of `SMITHY_PLUGIN_DIR` identifies an invocation by the `run` plugin.
Generated files are written beneath this directory, which Smithy also uses as the
process's working directory. The CLI MUST NOT write generated files outside it,
and `--model` and `--output` MUST NOT be used in this mode.

The `run` plugin provides the following environment variables:

| Name | Purpose |
|------|---------|
| `SMITHY_ROOT_DIR` | Root directory of the Smithy build. |
| `SMITHY_PLUGIN_DIR` | Output and working directory for the plugin. |
| `SMITHY_PROJECTION_NAME` | Name of the active projection. |
| `SMITHY_ARTIFACT_NAME` | Custom artifact name from the plugin ID. |
| `SMITHY_INCLUDES_PRELUDE` | Whether the JSON AST includes prelude shapes. |

The CLI uses this context to interpret the model. Protocol and platform
integrations MAY also use it while generating files.

Smithy omits prelude shapes by default. A build MAY set `sendPrelude` to `true`
in the `run` plugin configuration when those shapes are needed.

## Direct Invocation

When `SMITHY_PLUGIN_DIR` is absent, the CLI treats the command as a direct
invocation and requires `--output`. It follows the same
generation path as Smithy invocation and can read a JSON AST from a file instead
of standard input by using `--model`. When standard input is an interactive
terminal, `--model` is required so that an omitted input does not wait indefinitely
for input. This mode is intended for development, testing, and integration with
tools other than the Smithy CLI.
