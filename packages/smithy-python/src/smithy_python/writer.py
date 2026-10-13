# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Structured annotation writing for a single Python module."""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable, Generator
from contextlib import contextmanager
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


# Stands in for each type reference while written lines are parsed for names.
_PLACEHOLDER = "__smithy_reference__"
# Children of these nodes are evaluated in a new scope.
_SCOPES = (
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def _binding(name: str) -> str:
    """Compare names as Python binds them, without changing emitted spelling."""
    return normalize("NFKC", name)


def _bound_name(node: ast.AST) -> str | None:
    """Return the name a node binds in its scope, if any."""
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return node.id
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name
    if isinstance(node, ast.arg):
        return node.arg
    if isinstance(node, ast.alias):
        return None if node.name == "*" else node.asname or node.name.split(".")[0]
    if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
        return node.name
    if isinstance(node, ast.MatchMapping):
        return node.rest
    if isinstance(node, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple)):
        return node.name
    return None


def _check_class_scopes(tree: ast.Module, outside: frozenset[str]) -> None:
    """Reject raw outside names that a class shadows with its own members.

    Annotations are evaluated later, against the finished class, so a member
    shadows a name used anywhere in its class body. Method bodies are skipped
    because they cannot see class members.
    """
    for scope in ast.walk(tree):
        if not isinstance(scope, ast.ClassDef):
            continue
        bound: set[str] = set()
        loaded: set[str] = set()
        pending: list[ast.AST] = list(scope.body)
        while pending:
            node = pending.pop()
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                loaded.add(node.id)
                continue
            name = _bound_name(node)
            if name is not None:
                bound.add(name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                arguments = node.args
                pending.extend(arguments.defaults)
                pending.extend(filter(None, arguments.kw_defaults))
                if not isinstance(node, ast.Lambda):
                    pending.extend(node.decorator_list)
                    if node.returns is not None:
                        pending.append(node.returns)
                    pending.extend(
                        argument.annotation
                        for argument in (
                            *arguments.posonlyargs,
                            *arguments.args,
                            *arguments.kwonlyargs,
                            *filter(None, (arguments.vararg, arguments.kwarg)),
                        )
                        if argument.annotation is not None
                    )
            elif isinstance(node, ast.ClassDef):
                pending.extend((*node.decorator_list, *node.bases, *node.keywords))
            elif isinstance(
                node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
            ):
                pending.append(node.generators[0].iter)
            else:
                pending.extend(ast.iter_child_nodes(node))
        shadowed = loaded & bound & (outside | _BUILTINS)
        for name in sorted(shadowed):
            raise CodegenError(
                f"Raw name {name!r} in class {scope.name} is shadowed by a class "
                "member; write it as a type reference"
            )


class PythonWriter:
    """Write trusted Python lines, retaining type references until rendering."""

    def __init__(self, module: str) -> None:
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

    def _names(self) -> tuple[frozenset[str], frozenset[str]]:
        """Return the module and local names bound by the written lines."""
        source = "\n".join(self._body(lambda _: _PLACEHOLDER))
        try:
            tree = ast.parse(source, feature_version=(3, 12))
        except SyntaxError as error:
            raise CodegenError(
                f"Written lines are not valid Python 3.12 (line {error.lineno}): "
                f"{error.msg}"
            ) from error
        declarations: set[str] = set()
        local_names: set[str] = set()
        classes: set[str] = set()
        # Walk without recursion; written lines can nest deeply.
        pending: list[tuple[ast.AST, bool]] = [(node, True) for node in tree.body]
        while pending:
            node, module_scope = pending.pop()
            name = _bound_name(node)
            if name is not None:
                if isinstance(node, (ast.TypeVar, ast.ParamSpec, ast.TypeVarTuple)):
                    local_names.add(name)
                elif module_scope:
                    if isinstance(node, ast.ClassDef):
                        if name in classes:
                            raise CodegenError(
                                f"Duplicate generated declaration: {name!r}"
                            )
                        classes.add(name)
                    declarations.add(name)
                else:
                    local_names.add(name)
            nested = module_scope and not isinstance(node, _SCOPES)
            pending.extend((child, nested) for child in ast.iter_child_nodes(node))
        declarations.discard(_PLACEHOLDER)
        local_names.discard(_PLACEHOLDER)
        _check_class_scopes(tree, frozenset(declarations))
        return frozenset(declarations), frozenset(local_names)

    def _plan_imports(
        self, declarations: frozenset[str], local_names: frozenset[str]
    ) -> tuple[dict[tuple[str | None, str], str], list[str]]:
        identities: set[tuple[str | None, str]] = set()
        pending = [
            part
            for _, parts in self._lines
            for part in parts
            if isinstance(part, TypeReference)
        ]
        while pending:
            ref = pending.pop()
            if ref.module is None and (ref.name != "None" or ref.arguments):
                raise CodegenError(
                    f"Only the None literal may omit its module: {ref.name!r}"
                )
            identities.add((ref.module, ref.name))
            pending.extend(ref.arguments)
        # Equivalent Python identifiers share one import. Pick a supplied spelling
        # deterministically, without rewriting the caller's source names.
        representatives: dict[tuple[str | None, str], tuple[str | None, str]] = {}
        for module, name in sorted(
            identities, key=lambda item: (item[0] or "", item[1])
        ):
            identity = (
                _binding(module) if module is not None else None,
                _binding(name),
            )
            representatives.setdefault(identity, (module, name))
        current_names = {
            name for module, name in representatives if module == self._module
        }
        for name in sorted(current_names & local_names):
            raise CodegenError(
                f"Same-module reference {self._module}.{name} conflicts with local name {name!r}"
            )
        reserved = declarations | local_names | current_names
        external = sorted(
            (module, name)
            for (module_binding, _), (module, name) in representatives.items()
            if module is not None and module_binding not in ("builtins", self._module)
        )
        counts = Counter(_binding(name) for _, name in external)
        names: dict[tuple[str | None, str], str] = {}
        imports: list[tuple[str, str, str, str]] = []
        for module, name in external:
            alias = (
                f"_{module.replace('.', '_')}_{name}"
                if _binding(name) in reserved
                or _binding(name) in _BUILTINS
                or _binding(name) == "annotations"
                or counts[_binding(name)] > 1
                else name
            )
            names[(module, name)] = alias
            suffix = f" as {alias}" if alias != name else ""
            imports.append(
                (module, name, alias, f"from {module} import {name}{suffix}")
            )
        qualify_builtins = False
        for (module_binding, name_binding), (module, name) in representatives.items():
            if module is None:
                names[(module, name)] = "None"
            elif module_binding == "builtins":
                shadowed = name_binding in reserved
                names[(module, name)] = f"_builtins.{name}" if shadowed else name
                qualify_builtins |= shadowed
            elif module_binding == self._module:
                names[(module, name)] = name
        if qualify_builtins:
            imports.append(
                ("builtins", "", "_builtins", "import builtins as _builtins")
            )

        # Check the complete plan, including unaliased imports. No binding gets
        # priority merely because its reference was encountered first.
        bindings = dict.fromkeys(reserved, "a generated declaration or local name")
        imports.sort()
        for module, name, alias, _ in imports:
            owner = f"{module}.{name}" if name else module
            binding = _binding(alias)
            if binding in bindings or binding in _BUILTINS:
                conflict = bindings.get(binding, "a builtin")
                raise CodegenError(
                    f"Import binding {alias!r} for {owner} conflicts with {conflict}"
                )
            bindings[binding] = owner
        for module, name in identities:
            identity = (
                _binding(module) if module is not None else None,
                _binding(name),
            )
            names[(module, name)] = names[representatives[identity]]
        return names, [statement for _, _, _, statement in imports]

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
            header += "\n" + "\n".join(imports) + "\n"
        body = self._body(lambda reference: self._annotation(reference, names))
        return header + ("\n\n" + "\n".join(body) + "\n" if body else "")
