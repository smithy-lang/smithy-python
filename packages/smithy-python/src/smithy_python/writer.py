# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Structured annotation writing for a single Python module."""

from __future__ import annotations

import ast
import itertools
import keyword
import re
import warnings
from collections import Counter
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Literal
from unicodedata import normalize

from .exceptions import CodegenError
from .symbols import TypeReference

# Union of Python 3.12-3.15 builtins, including platform-specific names.
# Keep this fixed so import planning does not depend on the generator host.
_BUILTINS = frozenset(
    "ArithmeticError AssertionError AttributeError BaseException BaseExceptionGroup "
    "BlockingIOError BrokenPipeError BufferError BytesWarning ChildProcessError "
    "ConnectionAbortedError ConnectionError ConnectionRefusedError ConnectionResetError "
    "DeprecationWarning EOFError Ellipsis EncodingWarning EnvironmentError Exception "
    "ExceptionGroup False FileExistsError FileNotFoundError FloatingPointError "
    "FutureWarning GeneratorExit IOError ImportCycleError ImportError ImportWarning IndentationError "
    "IndexError InterruptedError IsADirectoryError KeyError KeyboardInterrupt "
    "LookupError MemoryError ModuleNotFoundError NameError None NotADirectoryError "
    "NotImplemented NotImplementedError OSError OverflowError PendingDeprecationWarning "
    "PermissionError ProcessLookupError PythonFinalizationError RecursionError ReferenceError ResourceWarning "
    "RuntimeError RuntimeWarning StopAsyncIteration StopIteration SyntaxError "
    "SyntaxWarning SystemError SystemExit TabError TimeoutError True TypeError "
    "UnboundLocalError UnicodeDecodeError UnicodeEncodeError UnicodeError "
    "UnicodeTranslateError UnicodeWarning UserWarning ValueError Warning WindowsError "
    "ZeroDivisionError _IncompleteInputError __build_class__ __debug__ __doc__ __import__ __lazy_import__ __loader__ "
    "__name__ __package__ __spec__ abs aiter all anext any ascii bin bool breakpoint "
    "bytearray bytes callable chr classmethod compile complex copyright credits "
    "delattr dict dir divmod enumerate eval exec exit filter float format frozendict frozenset "
    "getattr globals hasattr hash help hex id input int isinstance issubclass iter "
    "len license list locals map max memoryview min next object oct open ord pow "
    "print property quit range repr reversed round sentinel set setattr slice sorted "
    "staticmethod str sum super tuple type vars zip".split()
)


type _Kind = Literal["module", "class", "function", "comprehension", "annotation"]
_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


@dataclass(frozen=True, slots=True)
class _Import:
    """One planned import. ``name=None`` imports the module itself."""

    module: str
    name: str | None
    alias: str

    def statement(self) -> str:
        if self.name is None:
            return f"import {self.module} as {self.alias}"
        suffix = f" as {self.alias}" if self.alias != self.name else ""
        return f"from {self.module} import {self.name}{suffix}"


@dataclass(eq=False, slots=True)
class _Scope:
    """A Python scope found in the written lines.

    Class names are visible only to code directly in the class body and to its
    annotation scopes (type parameters). Functions, lambdas and comprehensions
    nested in a class cannot see them.
    """

    kind: _Kind
    parent: _Scope | None = None
    name: str = ""
    names: set[str] = field(default_factory=set[str])
    global_names: set[str] = field(default_factory=set[str])
    nonlocal_names: set[str] = field(default_factory=set[str])
    # Names bound other than as nested classes.
    members: set[str] = field(default_factory=set[str])
    # Class fields and the earliest position after which each is bound.
    fields: dict[str, tuple[int, int]] = field(
        default_factory=dict[str, tuple[int, int]]
    )

    def visible_names(self) -> set[str]:
        """Return names bound in the non-module scopes that this scope can see."""
        names: set[str] = set()
        scope, child = self, None
        while scope.parent is not None:
            if scope.kind != "class" or child is None or child.kind == "annotation":
                names |= scope.names
            scope, child = scope.parent, scope
        return names


def _binding(name: str) -> str:
    """Compare names as Python binds them, without changing emitted spelling."""
    return normalize("NFKC", name)


def _identity(module: str | None, name: str) -> tuple[str | None, str]:
    """Return a reference's module and name as Python binds them."""
    return (None if module is None else _binding(module), _binding(name))


def _validate_identifier(value: str, kind: str) -> None:
    """Require a Python identifier that is not a hard keyword."""
    if not value.isidentifier() or keyword.iskeyword(_binding(value)):
        raise CodegenError(f"Invalid Python {kind}: {value!r}")


def _validate_module(module: str, *, relative: bool) -> None:
    """Require an absolute module or, when allowed, a relative import path."""
    path = module.lstrip(".") if relative else module
    if not path:
        if relative and module and not module.strip("."):
            return
        raise CodegenError(f"Invalid Python module: {module!r}")
    if any(
        not part.isidentifier() or keyword.iskeyword(_binding(part))
        for part in path.split(".")
    ):
        raise CodegenError(f"Invalid Python module: {module!r}")


def _is_local(name: str, shadows: Iterable[frozenset[str]]) -> bool:
    """Return whether any of the visible local-name sets binds ``name``."""
    return any(name in names for names in shadows)


def _placeholder_prefix(text: str) -> str:
    """Return a prefix that no identifier in ``text`` can start with."""
    prefix = "_smithy_reference_"
    text = _binding(text)
    while prefix in text:
        prefix = "_" + prefix
    return prefix


def _bound_name(node: ast.AST) -> str | None:
    """Return the name that a pattern, handler, import or type parameter binds."""
    if isinstance(node, ast.alias):
        return None if node.name == "*" else node.asname or node.name.split(".")[0]
    if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
        return node.name
    if isinstance(node, ast.MatchMapping):
        return node.rest
    if isinstance(node, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple)):
        return node.name
    return None


def _analyze(
    tree: ast.Module, prefix: str, references: int
) -> tuple[frozenset[str], list[frozenset[str]]]:
    """Find module-level names and the local names each reference can see.

    Also reject raw class-body names that resolve to a class member while
    naming a builtin or module-level name.
    """
    placeholder = re.compile(re.escape(prefix) + r"(\d+)_")
    module = _Scope("module")
    found: dict[int, _Scope] = {}
    # (scope, name, binds a nested class)
    bindings: list[tuple[_Scope, str, bool]] = []
    # Class-body loads: (scope, name, evaluated against the finished class, position)
    loads: list[tuple[_Scope, str, bool, tuple[int, int]]] = []
    # Walk without recursion; written lines can nest deeply.
    pending: list[tuple[ast.AST | None, _Scope, bool]] = [
        (node, module, False) for node in tree.body
    ]

    def type_scope(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.TypeAlias,
        scope: _Scope,
    ) -> _Scope:
        if not node.type_params:
            return scope
        inner = _Scope("annotation", scope)
        pending.extend((param, inner, True) for param in node.type_params)
        return inner

    while pending:
        node, scope, lazy = pending.pop()
        if node is None:
            continue
        if isinstance(node, ast.Name):
            if match := placeholder.fullmatch(node.id):
                found[int(match[1])] = scope
            elif prefix in node.id:
                pass  # A reference joined to raw text; its scope is unknown.
            elif isinstance(node.ctx, ast.Load):
                if scope.kind in ("class", "annotation"):
                    position = (node.lineno, node.col_offset)
                    loads.append((scope, node.id, lazy, position))
            else:
                bindings.append((scope, node.id, False))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            arguments = node.args
            pending.extend(
                (default, scope, False)
                for default in (*arguments.defaults, *arguments.kw_defaults)
            )
            parameters = [
                parameter
                for parameter in (
                    *arguments.posonlyargs,
                    *arguments.args,
                    arguments.vararg,
                    *arguments.kwonlyargs,
                    arguments.kwarg,
                )
                if parameter is not None
            ]
            if isinstance(node, ast.Lambda):
                inner = _Scope("function", scope)
                pending.append((node.body, inner, False))
            else:
                bindings.append((scope, node.name, False))
                pending.extend((item, scope, False) for item in node.decorator_list)
                outer = type_scope(node, scope)
                pending.extend(
                    (annotation, outer, True)
                    for annotation in (
                        *(parameter.annotation for parameter in parameters),
                        node.returns,
                    )
                )
                inner = _Scope("function", outer)
                pending.extend((item, inner, False) for item in node.body)
            bindings.extend((inner, parameter.arg, False) for parameter in parameters)
        elif isinstance(node, ast.ClassDef):
            bindings.append((scope, node.name, True))
            pending.extend((item, scope, False) for item in node.decorator_list)
            outer = type_scope(node, scope)
            pending.extend(
                (item, outer, False) for item in (*node.bases, *node.keywords)
            )
            inner = _Scope("class", outer, node.name)
            pending.extend((item, inner, False) for item in node.body)
        elif isinstance(node, ast.TypeAlias):
            bindings.append((scope, node.name.id, False))
            pending.append((node.value, type_scope(node, scope), True))
        elif isinstance(node, _COMPREHENSIONS):
            # Only the first iterable is evaluated in the enclosing scope.
            first, *rest = node.generators
            pending.append((first.iter, scope, lazy))
            inner = _Scope("comprehension", scope)
            pending.extend(
                (item, inner, False)
                for item in (
                    first.target,
                    *first.ifs,
                    *(
                        part
                        for generator in rest
                        for part in (generator.target, generator.iter, *generator.ifs)
                    ),
                    *(
                        (node.key, node.value)
                        if isinstance(node, ast.DictComp)
                        else (node.elt,)
                    ),
                )
            )
        elif isinstance(node, ast.NamedExpr):
            # Assignment expressions bind outside any enclosing comprehension.
            target = scope
            while target.kind == "comprehension" and target.parent is not None:
                target = target.parent
            bindings.append((target, node.target.id, False))
            pending.append((node.value, scope, lazy))
        elif isinstance(node, ast.Global):
            scope.global_names.update(node.names)
        elif isinstance(node, ast.Nonlocal):
            scope.nonlocal_names.update(node.names)
        elif isinstance(node, ast.AnnAssign):
            if scope.kind == "class" and isinstance(node.target, ast.Name):
                name = node.target.id
                end = (node.end_lineno or 0, node.end_col_offset or 0)
                scope.fields[name] = min(end, scope.fields.get(name, end))
            pending.append((node.annotation, scope, True))
            pending.extend((item, scope, lazy) for item in (node.target, node.value))
        else:
            if (name := _bound_name(node)) is not None:
                bindings.append((scope, name, False))
            pending.extend((child, scope, lazy) for child in ast.iter_child_nodes(node))

    local_names: set[str] = set()
    for scope, name, nested_class in bindings:
        if name in scope.nonlocal_names:
            continue  # Already bound in an enclosing function.
        if name in scope.global_names:
            scope = module
        scope.names.add(name)
        if not nested_class:
            scope.members.add(name)
        if scope is not module:
            local_names.add(name)

    outside = module.names | _BUILTINS
    shadowed: list[tuple[tuple[int, int], str, str]] = []
    for scope, name, lazy, position in loads:
        if scope.kind == "annotation":
            # Type parameter scopes see the names of a directly enclosing class.
            if scope.parent is None or scope.parent.kind != "class":
                continue
            if name in scope.names:
                continue
            scope = scope.parent
        if name not in outside:
            continue
        # Annotations are evaluated later, against the finished class. Other
        # code runs in order and sees only the fields bound before it.
        bound = scope.fields.get(name)
        if name in scope.members if lazy else bound is not None and bound <= position:
            shadowed.append((position, name, scope.name))
    if shadowed:
        _, name, owner = min(shadowed)
        raise CodegenError(
            f"Raw name {name!r} in class {owner} is shadowed by a class member; "
            "write it as a type reference"
        )

    unknown = frozenset(local_names)
    visible: dict[_Scope, frozenset[str]] = {}
    shadows: list[frozenset[str]] = []
    for index in range(references):
        scope = found.get(index)
        if scope is None:
            shadows.append(unknown)
            continue
        if scope not in visible:
            visible[scope] = frozenset(scope.visible_names())
        shadows.append(visible[scope])
    return frozenset(module.names), shadows


class PythonWriter:
    """Write trusted Python lines, retaining type references until rendering."""

    def __init__(self, module: str) -> None:
        _validate_module(module, relative=False)
        self._module = _binding(module)
        self._depth = 0
        self._lines: list[tuple[int, tuple[str | TypeReference, ...]]] = []

    def line(self, *parts: str | TypeReference) -> None:
        """Append one line, concatenating its parts without separators."""
        self._lines.append((self._depth, parts))

    @contextmanager
    def indent(self) -> Generator[None]:
        """Indent by four spaces for the duration of the block."""
        self._depth += 1
        try:
            yield
        finally:
            self._depth -= 1

    def _body(self, reference: Callable[[TypeReference], str]) -> list[str]:
        body: list[str] = []
        for depth, parts in self._lines:
            text = "".join(
                part if isinstance(part, str) else reference(part) for part in parts
            )
            body.append("    " * depth + text if text else "")
        return body

    def _references(self) -> list[TypeReference]:
        return [
            part
            for _, parts in self._lines
            for part in parts
            if isinstance(part, TypeReference)
        ]

    def _names(self) -> tuple[frozenset[str], list[frozenset[str]]]:
        """Return module-level names and the local names each reference sees."""
        prefix = _placeholder_prefix("".join(self._body(lambda _: "")))
        numbers = itertools.count()
        source = "\n".join(self._body(lambda _: f"{prefix}{next(numbers)}_"))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", SyntaxWarning)
            try:
                tree = ast.parse(source, feature_version=(3, 12))
            except SyntaxError as error:
                raise CodegenError(
                    f"Written lines are not valid Python 3.12 (line {error.lineno}): "
                    f"{error.msg}"
                ) from error
        for warning in caught:
            # Invalid escape sequences become errors in future Python versions.
            if issubclass(warning.category, SyntaxWarning):
                raise CodegenError(
                    f"Written lines raise SyntaxWarning (line {warning.lineno}): "
                    f"{warning.message}"
                )
        return _analyze(tree, prefix, len(self._references()))

    def _plan_imports(
        self, module_names: frozenset[str], shadows: list[frozenset[str]]
    ) -> tuple[dict[tuple[str | None, str], str], list[_Import]]:
        identities: set[tuple[str | None, str]] = set()
        # The local names visible where each identity is referenced. References
        # in one scope share a set, so keep the distinct sets, not their union.
        local_names: dict[tuple[str | None, str], set[frozenset[str]]] = {}
        for reference, shadow in zip(self._references(), shadows, strict=True):
            pending = [reference]
            while pending:
                ref = pending.pop()
                if ref.module is None and (ref.name != "None" or ref.arguments):
                    raise CodegenError(
                        f"Only the None literal may omit its module: {ref.name!r}"
                    )
                if ref.module is not None:
                    _validate_identifier(ref.name, "reference name")
                    _validate_module(ref.module, relative=True)
                identities.add((ref.module, ref.name))
                key = _identity(ref.module, ref.name)
                local_names.setdefault(key, set()).add(shadow)
                pending.extend(ref.arguments)
        # Equivalent Python identifiers share one import. Pick a supplied spelling
        # deterministically, without rewriting the caller's source names.
        representatives: dict[tuple[str | None, str], tuple[str | None, str]] = {}
        for module, name in sorted(
            identities, key=lambda item: (item[0] or "", item[1])
        ):
            representatives.setdefault(_identity(module, name), (module, name))
        current_names = {
            name for module, name in representatives if module == self._module
        }
        for name in sorted(current_names):
            if _is_local(name, local_names[(self._module, name)]):
                raise CodegenError(
                    f"Same-module reference {self._module}.{name} conflicts with local name {name!r}"
                )
        reserved = module_names | current_names
        external = sorted(
            (module, name)
            for (module_binding, _), (module, name) in representatives.items()
            if module is not None and module_binding not in ("builtins", self._module)
        )
        counts = Counter(_binding(name) for _, name in external)
        names: dict[tuple[str | None, str], str] = {}
        # Each import with the local names of the places that use it.
        imports: list[tuple[_Import, set[frozenset[str]]]] = []
        for module, name in external:
            binding = _binding(name)
            scoped = local_names[_identity(module, name)]
            alias = (
                f"_{module.replace('.', '_')}_{name}"
                if binding in reserved
                or _is_local(binding, scoped)
                or binding in _BUILTINS
                or binding == "annotations"
                or counts[binding] > 1
                else name
            )
            names[(module, name)] = alias
            imports.append((_Import(module, name, alias), scoped))
        qualified: set[frozenset[str]] = set()
        for key, (module, name) in representatives.items():
            module_binding, name_binding = key
            if module is None:
                names[(module, name)] = "None"
            elif module_binding == "builtins":
                scoped = local_names[key]
                if name_binding in reserved or _is_local(name_binding, scoped):
                    names[(module, name)] = f"_builtins.{name}"
                    qualified |= scoped
                else:
                    names[(module, name)] = name
            elif module_binding == self._module:
                names[(module, name)] = name
        if qualified:
            imports.append((_Import("builtins", None, "_builtins"), qualified))

        # Check the complete plan, including unaliased imports. No binding gets
        # priority merely because its reference was encountered first.
        bindings = dict.fromkeys(reserved, "a module-level name")
        imports.sort(
            key=lambda item: (item[0].module, item[0].name or "", item[0].alias)
        )
        for item, scoped in imports:
            owner = f"{item.module}.{item.name}" if item.name else item.module
            binding = _binding(item.alias)
            if binding in bindings:
                conflict = bindings[binding]
            elif binding in _BUILTINS:
                conflict = "a builtin"
            elif _is_local(binding, scoped):
                conflict = "a local name"
            else:
                bindings[binding] = owner
                continue
            raise CodegenError(
                f"Import binding {item.alias!r} for {owner} conflicts with {conflict}"
            )
        for module, name in identities:
            names[(module, name)] = names[representatives[_identity(module, name)]]
        return names, [item for item, _ in imports]

    @staticmethod
    def _annotation(
        reference: TypeReference, names: dict[tuple[str | None, str], str]
    ) -> str:
        # Emit tokens rather than recursing through potentially deep collections.
        pending: list[str | TypeReference] = [reference]
        result: list[str] = []
        while pending:
            part = pending.pop()
            if isinstance(part, str):
                result.append(part)
                continue
            if part.module is None:
                result.append("None")
                continue
            result.append(names[(part.module, part.name)])
            if part.nullable:
                pending.append(" | None")
            if part.arguments:
                pending.append("]")
                for index in range(len(part.arguments) - 1, -1, -1):
                    pending.append(part.arguments[index])
                    if index:
                        pending.append(", ")
                pending.append("[")
        return "".join(result)

    def render(self) -> str:
        """Return complete source without changing the recorded lines."""
        names, imports = self._plan_imports(*self._names())
        header = "from __future__ import annotations\n"
        if imports:
            header += "\n" + "\n".join(item.statement() for item in imports) + "\n"
        body = self._body(lambda reference: self._annotation(reference, names))
        return header + ("\n\n" + "\n".join(body) + "\n" if body else "")
