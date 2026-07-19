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

`client` generates a service client and its required types. `types` generates a
standalone types package. Both commands accept the following process options:

* `--model PATH` reads a JSON AST from a file instead of standard input.
* `--output PATH` selects the output directory for direct invocation.

Settings specific to each artifact will be added with the functionality that
consumes them.

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
