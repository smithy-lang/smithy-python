# Python Code Generation

Smithy Python currently generates clients with the Java implementation in
`codegen`. This document describes the Python code generator that will replace
that implementation over time.

The Python generator is distributed as `smithy-python`. It is separate from the
runtime packages used by generated code, and is only needed while generating a
package.

## Goals

* Generate Python clients and standalone types packages from Smithy models.
* Integrate with standard Smithy builds without requiring a Java code generator.
* Provide extension points for protocol and platform-specific behavior.
* Produce code compatible with the existing Smithy Python runtime packages.
* Allow the Python and Java generators to coexist during migration.

## Architecture

The generator consumes a Smithy JSON AST and settings for an artifact. It loads
the model, applies artifact and protocol-specific behavior, and writes a Python
package.

```text
Smithy JSON AST + settings
            |
            v
    smithy-python generator
            |
            v
 client or types package
```

Two artifact types are initially planned:

* `client` will generate a service client and its required types.
* `types` will generate a standalone package of types selected from a model.

The artifact set may grow over time. A `server` artifact is a natural addition,
so the generator should not assume that only `client` and `types` exist.

The command-line interface is the generator's first entry point. Smithy's `run`
plugin invokes it as an external process, so the generator does not need to be
loaded into the Smithy CLI or implemented in Java.

Generated packages MUST NOT depend on `smithy-python` at runtime. They MAY
depend on the handwritten runtime packages in this repository.

## Migration

The Java generator remains authoritative while the Python generator is under
development. Features may be implemented and reviewed incrementally without
changing the Java path. A generated artifact SHOULD move to the Python generator
only after the required behavior is supported and tested.

The Python generator does not need to reproduce Java implementation details or
byte-for-byte output. It MUST preserve the supported Smithy semantics and public
behavior of generated packages.

## Designs

* [Code Generator CLI](cli.md)
