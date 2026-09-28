# Native Python writer

`PythonWriter` turns lines of Python text and `TypeReference` values into the
source of one module. Pass references from `SymbolProvider.type_reference()`
or construct them directly. The writer chooses annotation spellings and imports.
The caller decides which declarations, fields and defaults to write.

```python
from smithy_python.symbols import TypeReference
from smithy_python.writer import PythonWriter

node = TypeReference("Node", "example.models", nullable=True)
writer = PythonWriter(
    "example.models", declarations={"Node"}, local_names={"children", "amount"}
)
writer.line("class Node:")
with writer.indent():
    writer.line("children: ", TypeReference("list", "builtins", (node,)))
    writer.line("amount: ", TypeReference("Decimal", "decimal"))
source = writer.render()
```

The result is:

```python
from __future__ import annotations

from decimal import Decimal


class Node:
    children: list[Node | None]
    amount: Decimal
```

## Writing a module

`PythonWriter(module, *, declarations=(), local_names=())` takes the destination
module name and the names the caller will use. Supply valid Python names.
`declarations` contains module-level names. Duplicates raise `CodegenError`.
`local_names` contains field and local names that can shadow annotations across
the module. Do not automatically include enum constants or other class members
that are not in an annotation's scope. Repeated local names are allowed because
different classes can have the same field name.
The symbol provider already checks for duplicate fields within a declaration.

* `line(*parts)` joins strings and type references without separators at the
  current indentation. `line()` writes a blank line without spaces.
* `indent()` adds four spaces inside a context manager and restores indentation
  even when the block raises an exception.
* `render()` returns source ending in a newline, with a future-annotations
  header, sorted imports and the body in written order. It does not modify the
  writer. Adding another reference can change aliases in the next render.

Raw text is trusted Python, not a template. The writer does not parse it to
find missing name reservations. Callers supply blank lines between declarations.

## Annotations and imports

Nested arguments retain their order. `nullable=True` adds `| None` only at that
level: `list[str | None]` differs from `list[str] | None`. The `None` literal
stays `None`, including when marked nullable. Only that literal can omit its
module. Other module-less references raise `CodegenError`.

Generated source targets Python 3.12+. The future import permits references to
classes defined later, including recursive types. These are annotations, not
expressions to evaluate while defining classes.

* Builtins normally use `str`, `int`, `list[T]` and `dict[K, V]`.
* Types in the current module use their bare names without imports.
* Other types normally use `from module import Name`.

Imports are deduplicated by module and name, then sorted by module, name and
alias. Referenced packages don't have to be installed in the generator's environment.
For example, rendering a reference to `smithy_core.documents.Document` does not
import `smithy_core`.

## Names that collide

An import matching a declaration, local name, builtin, the future import's
`annotations` name, or another imported type uses a module-derived alias.
For example, `decimal.Decimal` becomes `_decimal_Decimal`. Dots in a module
path become underscores. All imports sharing a short name receive aliases,
regardless of the order they were written.

A field named `list` makes builtin list references use `_builtins.list[T]`, with
`import builtins as _builtins`. An alias that still collides raises
`CodegenError`. The writer never adds numbered suffixes or renames declarations.
The builtin-name list combines Python 3.12 through 3.15, including
platform-specific names, so imports do not depend on the generator host.
Update the list when adding support for another Python version.

Comparisons follow Python's treatment of identifier spellings. For example,
`K` and `K` bind the same name and cannot be separate declarations. Original
spellings, including `_2HTTPServer`, are retained in emitted source. Module names
follow the same comparison rules, so equivalent spellings do not cause self-imports.
Equivalent references share one import, using the lexicographically smallest
supplied module/name pair so the choice does not depend on reference order.

A same-module reference also listed in `local_names` raises `CodegenError`.
This first version does not add self-imports or aliases for local declarations.
Listing it only in `declarations` is normal.

The writer returns source in memory. File output, documentation conversion and
actual declaration generation remain separate follow-ups.
