# Changelog

## v0.4.0

### Breaking Changes
* Generated types escape a member of an operation input whose Python name is `plugins`, `self`, or `_models` to `plugins_`, `self_`, or `_models_`, adding more underscores if a sibling already uses that name, matching the names the runtime builds.

### Bug fixes
* Zero-pad schema and model stub partition filenames so alphabetical listings follow numerical order, with matching facade imports and cleanup of obsolete partition files.

## v0.3.0

### Features
* Partition large generated schema and model stub files to reduce memory usage and static analysis time.

### Enhancements
* Added docstrings to the public API and ordered public definitions first.
* Completed type annotations and __all__ declarations for the public API.
* Make empty model registry maps and private stub partition imports pass strict type checking, including services without data shapes.
* Generated docs for `@idempotencyToken` members of operation inputs now note that the field is autopopulated if not provided.
* Imported symbols from their defining modules.

## v0.2.0

### Breaking Changes
* Declared explicit `__all__` exports on all public modules. Names that were previously importable only incidentally (via `from module import *` or as un-annotated module attributes) are no longer part of the public API; import public symbols by name from their documented module.

### Features
* Added native generation of compact, lazily hydrated schemas with Java-compatible trait filtering, string interning, and recursive references.
* Added a native Python symbol provider with deterministic declaration and member naming, generator-reserved member names, structured type references, service renames, collision diagnostics, sparse collections, and recursive type support.
* Added a native Python writer with structured annotations, deterministic collision-safe imports, indentation contexts, and forward-reference support.
* Added native generation of lazy runtime model modules and complete static model stubs for standalone types packages.

### Enhancements
* Added support for Python 3.15.

## v0.1.0

### Features
* Added the experimental smithy-python package and CLI scaffold.
* Added service and data-shape selection for the native Python generator, including `--service` for `client` and `types` commands, service closure filtering, and standalone types name conflict diagnostics.
* Added a Smithy JSON AST model loader with an embedded prelude, mixin flattening, and apply support.
