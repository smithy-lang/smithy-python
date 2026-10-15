# Native Python writer

`PythonWriter` turns lines of Python text and `TypeReference` values into the
source of one module. Pass references from `SymbolProvider.type_reference()`
or construct them directly. The writer chooses annotation spellings and imports.
The caller decides which declarations, fields and defaults to write.

```python
from smithy_python.symbols import TypeReference
from smithy_python.writer import PythonWriter

node = TypeReference("Node", "example.models", nullable=True)
writer = PythonWriter("example.models")
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

`PythonWriter(module)` takes the destination module name. `render()` finds the
names bound by the written lines and follows Python's scoping rules.
Module-level names, such as classes, functions, assignments, imports and
`global` assignments, apply to every reference. A local name, such as a field,
parameter or local variable, applies only to references that can see it. A
class member is visible in its class body, including method signatures, but not
in method bodies, nested classes or comprehensions. A function's locals are
visible in its body and nested functions, not in its signature.

Names may be rebound, as in `if`/`else` branches or `@overload` stubs. The
symbol provider ensures that declaration and field names are unique.

* `line(*parts)` joins strings and type references without separators at the
  current indentation. `line()` writes a blank line without spaces.
* `indent()` adds four spaces inside a context manager and restores indentation
  even when the block raises an exception.
* `render()` returns source ending in a newline, with a future-annotations
  header, sorted imports and the body in written order. It does not modify the
  writer. Adding another reference can change aliases in the next render.

Raw text is trusted Python, not a template. To find names, `render()` parses
the written lines with the Python 3.12 grammar, with a unique placeholder
standing in for each type reference. Lines that are not valid Python 3.12 raise
`CodegenError`, including syntax added in later versions. So do lines that raise
`SyntaxWarning`, such as an invalid escape sequence in `"""Match \d+."""`;
later Python versions will reject them. Callers supply blank lines between
declarations.

The analysis reads the syntax tree rather than `symtable`, whose results change
between Python versions and omit annotations under `from __future__ import
annotations`. A reference joined to raw text, such as `obj.` followed by a
reference, has no scope of its own. It is treated as visible to every local
name.

Pass every builtin or imported name as a type reference, not just annotations.
A reference can appear anywhere in a line, so defaults such as
`field(default_factory=list)` and base classes such as `StrEnum` get the same
aliases. If those names are written as raw text, a field with the same name
replaces them in the class body. `render()` raises `CodegenError` when raw text
in a class body names a builtin or module-level name that resolves to a member
of the same class instead:

* In an annotation, including a method signature, any member other than a
  nested class shadows the name. Annotations are evaluated later, against the
  finished class, so order does not matter. An annotation naming a nested class
  means that class.
* In other code, such as defaults, decorators and base classes, only a field
  (an annotated name) bound by an earlier statement shadows the name. This code
  runs in order, so `list: list[str] = field(default_factory=list)` still sees
  the builtin in its own default. A field holds a default value, so referring to
  it by name is almost always a mistake. Other members are often referenced on
  purpose, as with `@type.setter` for a `type` property or an enum alias such as
  `LIST = list`.

Method bodies, nested classes and comprehensions are not checked, because they
cannot see class members.

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

An import uses a module-derived alias when its name matches a module-level
name, a local name visible where it is referenced, a builtin, the future
import's `annotations` name, or another imported type.
For example, `decimal.Decimal` becomes `_decimal_Decimal`. Dots in a module
path become underscores. All imports sharing a short name receive aliases,
regardless of the order they were written.

A field named `list` makes builtin list references in that class use
`_builtins.list[T]`, with `import builtins as _builtins`. An alias that still
collides raises `CodegenError`. The writer never adds numbered suffixes or
renames declarations.
The builtin-name list combines Python 3.12 through 3.15, including
platform-specific names, so imports do not depend on the generator host.
Update the list when adding support for another Python version.

Comparisons follow Python's treatment of identifier spellings. For example,
`K` and `K` bind the same name and cannot be separate declarations. Original
spellings, including `_2HTTPServer`, are retained in emitted source. Module names
follow the same comparison rules, so equivalent spellings do not cause self-imports.
Equivalent references share one import, using the lexicographically smallest
supplied module/name pair so the choice does not depend on reference order.

A same-module reference whose name is a local name visible where it is
referenced raises `CodegenError`. This first version does not add self-imports
or aliases for local declarations.

The writer returns source in memory. File output, documentation conversion and
actual declaration generation remain separate follow-ups.
